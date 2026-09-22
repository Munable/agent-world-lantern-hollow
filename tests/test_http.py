from __future__ import annotations
import unittest
import httpx
from tests.live import LiveServer

class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.server=LiveServer().__enter__()
    @classmethod
    def tearDownClass(cls):cls.server.__exit__()
    def setUp(self):
        self.c=httpx.Client(base_url=self.server.url,trust_env=False,timeout=10,headers={'X-Lantern-Client':'1'})
        self.addCleanup(self.c.close)
    def join(self):
        r=self.c.post('/play/join',json={'name':'Tester'});self.assertEqual(r.status_code,200,r.text);return r
    def test_join_cookie_private_and_refresh_keeps_role(self):
        r=self.join();self.assertIn('HttpOnly',r.headers['set-cookie']);self.assertIn('SameSite=strict',r.headers['set-cookie'])
        body=self.c.get('/play/session').json();self.assertNotIn('awid_',str(body))
        role=body['role_id'];self.join();self.assertEqual(self.c.get('/play/session').json()['role_id'],role)
    def test_cross_origin_mutation_rejected(self):
        self.assertEqual(self.c.post('/play/join',json={'name':'Bad'},headers={'Origin':'https://evil.example'}).status_code,403)
    def test_anonymous_session_and_action_rejected(self):
        self.assertEqual(self.c.get('/play/session').status_code,401)
        self.assertEqual(self.c.post('/play/action',json={'function':'town.stop','arguments':{},'operation_id':'x'}).status_code,401)
    def test_map_matches_collision_and_script_loads(self):
        data=self.c.get('/play/map').json();self.assertEqual(data['width'],40);self.assertEqual(len(data['tiles']),26)
        for path in ['/','/static/app.js','/static/render.js','/static/style.css']:
            self.assertEqual(self.c.get(path).status_code,200)
    def test_action_receipt_and_sync(self):
        self.join();snap=self.c.get('/play/session').json()
        body={'function':'town.move','operation_id':'move-once','arguments':{'x':17,'y':21}}
        a=self.c.post('/play/action',json=body);self.assertEqual(a.status_code,200,a.text)
        b=self.c.post('/play/action',json=body).json();self.assertTrue(b['replayed'])
        r=self.c.get('/play/receipt/move-once').json();self.assertEqual(r['commit_seq'],b['commit_seq'])
        s=self.c.post('/play/sync',json={'cursor':snap['view']['cursor'],'after':snap['event_cursor']})
        self.assertEqual(s.status_code,200,s.text);self.assertIn('events',s.json())
    def test_invitation_exchange_native_token_not_browser_secret(self):
        self.join();r=self.c.post('/play/agent',json={'name':'A'});self.assertEqual(r.status_code,200,r.text)
        ticket=r.json()['ticket'];e=self.c.post('/v1/join/exchange',json={'ticket':ticket})
        self.assertEqual(e.status_code,200,e.text);token=e.json()['identity']['token']
        result=self.c.post('/v1/functions/town.enter/invoke',headers={'Authorization':'Bearer '+token},json={'operation_id':'agent-enter','arguments':{'appearance':'sage'}})
        self.assertEqual(result.status_code,200,result.text)

if __name__=='__main__':unittest.main()
