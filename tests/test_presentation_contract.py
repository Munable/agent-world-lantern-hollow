import subprocess
import tempfile
import unittest
from importlib.resources import files
from pathlib import Path
from fastapi.testclient import TestClient
from lantern_hollow.server import create_app

class PresentationContractTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.app=create_app(Path(self.temp.name)/'world.sqlite3',observer_origins=['https://viewer.example'])
        self.client=TestClient(self.app);self.addCleanup(self.client.close)
        self.headers={'Origin':'https://viewer.example','X-Lantern-Client':'1'}

    def test_public_preflight_does_not_allow_authentication(self):
        url='/watch/sync'
        pre={'Origin':'https://viewer.example','Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'content-type,x-lantern-client'}
        result=self.client.options(url,headers=pre)
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.headers['access-control-allow-origin'],'https://viewer.example')
        self.assertNotIn('access-control-allow-credentials',result.headers)
        pre['Access-Control-Request-Headers']='authorization'
        self.assertEqual(self.client.options(url,headers=pre).status_code,400)

    def test_public_view_never_inherits_cookie_identity(self):
        self.client.post('/play/join',headers={'X-Lantern-Client':'1'},json={'name':'Human'})
        public=self.client.get('/watch/session',headers=self.headers)
        self.assertEqual(public.status_code,200)
        self.assertIsNone(public.json()['view']['snapshot']['meta']['self'])
        self.assertNotIn('set-cookie',public.headers)
        self.assertEqual(public.headers['access-control-allow-origin'],'https://viewer.example')
        bad=self.client.post('/watch/sync',headers=self.headers,json={'role_id':'not-authorized'})
        self.assertEqual(bad.status_code,422)
        self.assertEqual(bad.headers['access-control-allow-origin'],'https://viewer.example')

    def test_cross_origin_cannot_mutate_or_read_player_identity(self):
        self.client.post('/play/join',headers={'X-Lantern-Client':'1'},json={'name':'Human'})
        result=self.client.post('/play/action',headers=self.headers,json={'function':'town.move','arguments':{'x':17,'y':21},'operation_id':'denied'})
        self.assertEqual(result.status_code,403)
        self.assertNotIn('access-control-allow-origin',result.headers)
        for route in ('/play/session','/v1/whoami','/agent'):
            self.assertNotIn('access-control-allow-origin',self.client.get(route,headers=self.headers).headers)
        self.assertEqual(self.client.get('/play/session').json()['view']['snapshot']['meta']['self']['position'],[18,21])

    def test_foreign_origin_not_enabled_by_default(self):
        app=create_app(Path(self.temp.name)/'default.sqlite3')
        with TestClient(app) as client:
            self.assertNotIn('access-control-allow-origin',client.get('/watch/session',headers=self.headers).headers)
            self.assertEqual(client.post('/watch/sync',headers=self.headers,json={}).status_code,403)

    def test_public_map_declares_world_presentation_version(self):
        result=self.client.get('/play/map',headers=self.headers)
        self.assertEqual(result.headers['access-control-allow-origin'],'https://viewer.example')
        data=result.json();self.assertEqual(data['world_id'],'lantern-hollow')
        self.assertEqual(data['world_version'],2);self.assertEqual(data['presentation_version'],1)
        for key in ('tiles','targets','buildings','width','height'):self.assertIn(key,data)

    def test_javascript_presentation_contract(self):
        root=Path(__file__).resolve().parents[1]
        shared=str(files('agent_world').joinpath('web','stream-client.js'))
        result=subprocess.run(['node','tests/presentation_client.test.mjs',shared],cwd=root,capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

if __name__=='__main__':unittest.main()
