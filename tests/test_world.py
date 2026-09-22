from __future__ import annotations
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from agent_world import WorldRuntime
from agent_world.world_sdk import install_world
from agent_world.errors import WorldRuntimeError, RuleViolation, PermissionDenied
from lantern_hollow.world import WORLD, SHARDS
from lantern_hollow.map import SPAWN, TARGETS, route, walkable, position, manifest

class WorldTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.clock=patch('time.time',return_value=1000.).start();self.addCleanup(patch.stopall)
        self.db=Path(self.tmp.name)/'world.sqlite3';self.rt=WorldRuntime(self.db);install_world(self.rt,'test',WORLD)
        self.role=self.rt.create_role('Traveler')['role_id'];self.token=self.rt.issue_identity_token('test',self.role)['token'];self.n=0
        self.call('town.enter',{})
    def call(self,name,args,op=None):
        self.n+=1
        return self.rt.call_function('test',name,self.role,args,operation_id=op or str(self.n),identity_token=self.token)
    def actor(self):return self.rt.get_state('test','town','actor:'+self.role)['value']
    def arrive(self,target):
        self.call('town.interact',{'target':target})
        self.settle()
    def settle(self):
        for _ in range(3):
            a=self.actor();action=a['movement'] or a['busy']
            if not action:return
            self.clock.return_value=action['end_at']+.01
            self.rt.run_due_timers('test')
    def test_all_targets_reachable_and_collision_map_consistent(self):
        self.assertTrue(walkable(*SPAWN))
        m=manifest();blocked={tuple(p)for p in m['blocked']}
        for target in TARGETS.values():
            path=route(SPAWN,target['approach']);self.assertIsNotNone(path,target['id'])
            self.assertTrue(all(tuple(p)not in blocked for p in path))
            self.assertTrue(all(sum(abs(a-b)for a,b in zip(path[i-1],path[i]))==1 for i in range(1,len(path))))
    def test_whole_story_and_note(self):
        self.arrive('elia');self.assertEqual(self.actor()['quest'],'collect')
        for shard in SHARDS:self.arrive(shard)
        self.assertEqual(self.actor()['quest'],'repair')
        self.arrive('beacon');self.assertEqual(self.actor()['quest'],'complete')
        self.assertTrue(self.rt.get_state('test','town','beacon')['value']['lit'])
        self.arrive('board');self.call('town.note',{'text':'A persistent light.'})
        self.assertEqual(self.rt.get_state('test','town','notes')['value'][0]['text'],'A persistent light.')
    def test_movement_and_stop_do_not_teleport(self):
        self.call('town.move',{'x':23,'y':12})
        a=self.actor();self.clock.return_value+=.45;expected,_=position(a,self.clock.return_value)
        self.call('town.stop',{});self.assertEqual(self.actor()['position'],expected);self.assertIsNone(self.actor()['movement'])
        self.clock.return_value+=40;self.rt.run_due_timers('test');self.assertEqual(self.actor()['position'],expected)
    def test_new_destination_cancels_old_timer(self):
        self.call('town.move',{'x':23,'y':12});old=self.actor()['movement']['timer_id']
        self.call('town.move',{'x':17,'y':21});self.settle()
        self.assertEqual(self.rt.get_timer('test',old)['status'],'cancelled')
        self.assertEqual(self.actor()['position'],[17,21])
    def test_unreachable_command_rolls_back_interruption(self):
        self.call('town.move',{'x':23,'y':12});original=self.actor()['movement']
        with self.assertRaises(WorldRuntimeError):self.call('town.move',{'x':0,'y':0})
        self.assertEqual(self.actor()['movement'],original)
        self.assertEqual(self.rt.get_timer('test',original['timer_id'])['status'],'pending')
    def test_repeated_move_has_one_timer_and_same_receipt(self):
        a=self.call('town.move',{'x':23,'y':12},'stable')
        b=self.call('town.move',{'x':23,'y':12},'stable')
        self.assertTrue(b['replayed']);self.assertEqual(a['commit_seq'],b['commit_seq'])
    def test_cannot_pick_up_shard_before_quest_or_twice(self):
        self.arrive('shard_moss');self.assertEqual(self.actor()['shards'],[])
        self.arrive('elia');self.arrive('shard_moss');self.arrive('shard_moss')
        self.assertEqual(self.actor()['shards'],['shard_moss'])
    def test_cannot_repair_without_shards(self):
        self.arrive('beacon');self.assertIsNone(self.actor()['busy']);self.assertFalse(self.rt.get_state('test','town','beacon')['value']['lit'])
    def test_can_cancel_repair_before_completion(self):
        self.arrive('elia')
        for shard in SHARDS:self.arrive(shard)
        self.call('town.interact',{'target':'beacon'});a=self.actor();self.clock.return_value=a['movement']['end_at']+.01;self.rt.run_due_timers('test')
        self.assertIsNotNone(self.actor()['busy']);self.call('town.stop',{});self.clock.return_value+=5;self.rt.run_due_timers('test')
        self.assertFalse(self.rt.get_state('test','town','beacon')['value']['lit'])
    def test_restart_recovers_accepted_path_and_quest(self):
        self.call('town.interact',{'target':'elia'});due=self.actor()['movement']['end_at']
        rt=WorldRuntime(self.db);install_world(rt,'test',WORLD);self.clock.return_value=due+2;rt.run_due_timers('test')
        self.assertEqual(self.actor()['quest'],'collect');self.assertIsNone(self.actor()['movement'])
    def test_other_role_does_not_receive_private_quest_inventory(self):
        self.arrive('elia');self.arrive('shard_moss')
        other=self.rt.create_role('Another')['role_id'];token=self.rt.issue_identity_token('test',other)['token']
        self.rt.call_function('test','town.enter',other,{},operation_id='enter',identity_token=token)
        snapshot=self.rt.view_snapshot('test',other,'village',identity_token=token)['snapshot']
        self.assertNotIn('shards',snapshot['entities'][self.role]);self.assertEqual(snapshot['meta']['self']['shards'],[])
    def test_readonly_identity_cannot_move_or_replay(self):
        receipt=self.call('town.move',{'x':17,'y':21},'move')
        token=self.rt.issue_identity_token('test',self.role,access_mode='observe')['token']
        with self.assertRaises(PermissionDenied):self.rt.call_function('test','town.move',self.role,{'x':17,'y':21},operation_id='move',identity_token=token)
    def test_public_intent_is_explicit_and_throttled(self):
        self.call('town.intent',{'text':'I will visit the beacon.'})
        self.assertEqual(self.actor()['expression']['channel'],'intent')
        with self.assertRaises(WorldRuntimeError):self.call('town.say',{'text':'too soon'})
    def test_note_requires_proximity_and_preserves_plain_text(self):
        with self.assertRaises(WorldRuntimeError):self.call('town.note',{'text':'from far away'})
        self.arrive('board');self.call('town.note',{'text':'<script>not executable</script>'})
        self.assertEqual(self.rt.get_state('test','town','notes')['value'][0]['text'],'<script>not executable</script>')
    def test_empty_and_unknown_inputs_rejected(self):
        for name,args in [('town.note',{'text':' '}),('town.say',{'text':' '}),('town.interact',{'target':'admin'}),('town.move',{'x':2,'y':'no'})]:
            with self.assertRaises(WorldRuntimeError):self.call(name,args)
    def test_enter_again_does_not_reset_progress(self):
        self.arrive('elia');self.call('town.enter',{});self.assertEqual(self.actor()['quest'],'collect')

if __name__=='__main__':unittest.main()
