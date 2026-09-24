from pathlib import Path
import subprocess
import unittest

class ExperienceLayoutTests(unittest.TestCase):
    def test_actual_client_layout_helpers(self):
        result=subprocess.run(['node','tests/experience_layout.test.mjs'],cwd=Path(__file__).resolve().parents[1],capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
