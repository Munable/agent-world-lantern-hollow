from pathlib import Path
import subprocess,unittest
class FrontendGateTests(unittest.TestCase):
 def check(self,filename):
  r=subprocess.run(['node','tests/'+filename],cwd=Path(__file__).resolve().parents[1],capture_output=True,text=True,timeout=30)
  self.assertEqual(r.returncode,0,r.stdout+r.stderr)
 def test_nameplates(self):self.check('nameplate.test.mjs')
 def test_view_and_storage(self):self.check('frontend_contract.test.mjs')
 def test_independent_protocol(self):self.check('public_protocol.test.mjs')
