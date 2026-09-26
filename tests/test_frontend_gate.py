from pathlib import Path
import subprocess,unittest
class FrontendGateTests(unittest.TestCase):
 def check(self,filename):
  r=subprocess.run(['node','tests/'+filename],cwd=Path(__file__).resolve().parents[1],capture_output=True,text=True,timeout=30)
  self.assertEqual(r.returncode,0,r.stdout+r.stderr)
 def test_nameplates(self):self.check('nameplate.test.mjs')
 def test_view_and_storage(self):self.check('frontend_contract.test.mjs')
 def test_independent_protocol(self):self.check('public_protocol.test.mjs')
 def test_product_shell(self):self.check('product_shell.test.mjs')

 def test_two_static_fixtures_are_distinct_origins(self):
  import tempfile,httpx
  from tools.frontend_test_support import static_client
  with tempfile.TemporaryDirectory() as temp:
   a=Path(temp)/'first';b=Path(temp)/'second';a.mkdir();b.mkdir()
   (a/'marker.txt').write_text('first');(b/'marker.txt').write_text('second')
   with static_client(a) as first,static_client(b) as second,httpx.Client(trust_env=False,timeout=5) as client:
    self.assertNotEqual(first,second,'Different static fixtures must never bind the same origin')
    self.assertEqual(client.get(first+'/marker.txt').text,'first')
    self.assertEqual(client.get(second+'/marker.txt').text,'second')
