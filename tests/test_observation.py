from __future__ import annotations
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
import json
from fastapi.testclient import TestClient
from agent_world import WorldRuntime
from agent_world.world_sdk import install_world
from agent_world.errors import RuleViolation, PermissionDenied
from lantern_hollow.world import WORLD
from lantern_hollow.server import create_app

class ObservationTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.db=Path(self.temp.name)/'world.sqlite3'
        self.app=create_app(self.db)
        self.client=TestClient(self.app)
        self.addCleanup(self.client.close)
        self.w=self.app.state.runtime
        self.a=self.w.create_role('Alpha')['role_id']; self.b=self.w.create_role('Beta')['role_id']
        self.ta=self.w.issue_identity_token('lantern-hollow',self.a)['token']
        self.tb=self.w.issue_identity_token('lantern-hollow',self.b)['token']
        self.clock=patch('time.time',return_value=2000).start();self.addCleanup(patch.stopall)
    def call(self,role,token,name,args,op):
        return self.w.call_function('lantern-hollow',name,role,args,operation_id=op,identity_token=token)
    def enter(self):
        self.call(self.a,self.ta,'town.enter',{},'enter-a');self.call(self.b,self.tb,'town.enter',{},'enter-b')
    def test_guest_watch_is_connected_without_creating_a_player(self):
        before=self.w.get_state('lantern-hollow','town','beacon')['value']
        r=self.client.get('/watch/session');self.assertEqual(r.status_code,200,r.text)
        b=r.json();self.assertIsNone(b['view']['snapshot']['meta']['self'])
        self.assertEqual(b['view']['snapshot']['entities'],{})
        self.assertEqual(self.client.cookies.get('lantern_identity'),None)
        self.assertEqual(self.w.get_state('lantern-hollow','town','beacon')['value'],before)
        with self.w._conn(readonly=True) as c:self.assertEqual(c.execute('SELECT COUNT(*) FROM roles').fetchone()[0],2)
    def test_external_action_is_observed_without_player_login(self):
        initial=self.client.get('/watch/session').json()
        self.enter()
        response=self.client.post('/watch/sync',headers={'X-Lantern-Client':'1'},json={'cursor':initial['view']['cursor'],'stream_cursor':initial['stream_cursor']})
        self.assertEqual(response.status_code,200,response.text)
        data=response.json()
        self.assertEqual(set(data['view']['delta']['entities']['upsert']),{self.a,self.b})
        self.assertEqual(len(data['events']),2)
        self.assertFalse(data['history'])
    def test_real_message_link_and_reply_are_retained(self):
        self.enter()
        first=self.call(self.a,self.ta,'town.say',{'text':'Hello Beta','to_role_id':self.b},'hello')
        mid=first['result']['message_id']
        self.clock.return_value+=2
        reply=self.call(self.b,self.tb,'town.say',{'text':'Hello Alpha','reply_to':mid},'reply')
        self.assertEqual(reply['result']['reply_to'],mid)
        self.assertEqual(reply['result']['to_role_id'],self.a)
        self.assertEqual(reply['result']['thread_id'],first['result']['thread_id'])
        self.clock.return_value+=100
        page=self.w.read_stream('lantern-hollow','conversation',self.b,identity_token=self.tb)
        self.assertEqual([e['payload']['data']['text'] for e in page['events']],['Hello Beta','Hello Alpha'])
        self.assertEqual(self.w.query_function('lantern-hollow','town.messages',self.b,{},identity_token=self.tb)['result']['messages'][0]['message_id'],mid)
    def test_fake_reply_or_unentered_target_is_rejected(self):
        self.enter()
        for args in ({'text':'bad','reply_to':'nonexistent'},{'text':'bad','to_role_id':'nonexistent'}):
            with self.assertRaises(RuleViolation):self.call(self.a,self.ta,'town.say',args,'bad')
    def test_reply_cannot_redirect_to_different_author(self):
        self.enter();mid=self.call(self.a,self.ta,'town.say',{'text':'hello'},'hello')['result']['message_id']
        with self.assertRaises(RuleViolation):self.call(self.b,self.tb,'town.say',{'text':'bad','reply_to':mid,'to_role_id':self.b},'bad')
    def test_replay_does_not_duplicate_timeline_or_reply(self):
        self.enter();a={'text':'only once','to_role_id':self.b}
        first=self.call(self.a,self.ta,'town.say',a,'hello')
        again=self.call(self.a,self.ta,'town.say',a,'hello')
        self.assertTrue(again['replayed']);self.assertEqual(first['result']['message_id'],again['result']['message_id'])
        self.assertEqual(len(self.w.read_stream('lantern-hollow','conversation')['events']),1)
    def test_fresh_observer_sees_history_not_stale_live_bubbles(self):
        self.enter();self.call(self.a,self.ta,'town.say',{'text':'old'},'old');self.clock.return_value+=60
        data=self.client.get('/watch/session').json()
        self.assertTrue(data['history']);self.assertTrue(any(e['payload']['data'].get('text')=='old' for e in data['events']))
        self.assertIsNone(data['view']['snapshot']['meta']['self'])
    def test_guest_cannot_inject_identity_or_control(self):
        r=self.client.post('/watch/sync',headers={'X-Lantern-Client':'1'},json={'role_id':self.a})
        self.assertEqual(r.status_code,422)
        r=self.client.post('/play/action',headers={'X-Lantern-Client':'1'},json={'function':'town.enter','arguments':{},'operation_id':'attack'})
        self.assertEqual(r.status_code,401)
        r=self.client.post('/play/agent',headers={'X-Lantern-Client':'1'},json={'name':'bad'})
        self.assertEqual(r.status_code,401)
    def test_two_npc_dialogues_are_retained_not_overwritten(self):
        self.enter()
        # Server rules do the movement and invoke the scripted NPCs on arrival.
        self.call(self.a,self.ta,'town.interact',{'target':'elia'},'meet-a')
        self.call(self.b,self.tb,'town.interact',{'target':'fern'},'meet-b')
        self.clock.return_value+=30;self.w.run_due_timers('lantern-hollow')
        speech=[e for e in self.w.read_stream('lantern-hollow','conversation')['events'] if e['payload']['name']=='dialogue']
        self.assertEqual(len(speech),2)
        self.assertEqual({e['payload']['subject_id'] for e in speech},{'elia','fern'})
    def test_snapshot_past_history_anchor_does_not_skip_new_write(self):
        self.enter();initial=self.client.get('/watch/session').json()
        self.call(self.a,self.ta,'town.say',{'text':'after snapshot'},'new')
        r=self.client.post('/watch/sync',headers={'X-Lantern-Client':'1'},json={'cursor':initial['view']['cursor'],'stream_cursor':initial['stream_cursor']}).json()
        self.assertEqual([e['payload']['data']['text'] for e in r['events']],['after snapshot'])

if __name__=='__main__':unittest.main()
