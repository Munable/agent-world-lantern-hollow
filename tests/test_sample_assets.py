"""Static frontend packaging and anonymous asset access, not kernel behavior."""
import hashlib,json,subprocess,unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from fastapi.testclient import TestClient
from lantern_hollow.server import create_app,WEB

class SampleAssetTests(unittest.TestCase):
    def test_png_and_manifest_are_packaged_and_consistent(self):
        manifest=json.loads((WEB/'sample-assets.json').read_text(encoding='utf-8'))
        data=(WEB/'sample-atlas.png').read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(),manifest['sha256'])
        self.assertEqual(data[:8],b'\x89PNG\r\n\x1a\n')
        self.assertEqual(len(manifest['frames']),400)
        self.assertTrue((WEB/'art-gallery.html').exists())
    def test_anonymous_asset_cors_is_bounded_and_has_no_credentials(self):
        with TemporaryDirectory() as temp,TestClient(create_app(Path(temp)/'fixture.sqlite3',observer_origins=['https://viewer.example'])) as client:
            for path in ('/static/sample-assets.json','/static/sample-atlas.png'):
                allowed=client.get(path,headers={'Origin':'https://viewer.example'})
                self.assertEqual(allowed.status_code,200)
                self.assertEqual(allowed.headers.get('access-control-allow-origin'),'https://viewer.example')
                self.assertNotIn('access-control-allow-credentials',allowed.headers)
                self.assertNotIn('set-cookie',allowed.headers)
                denied=client.get(path,headers={'Origin':'https://not-allowed.example'})
                self.assertNotIn('access-control-allow-origin',denied.headers)
            private=client.get('/play/session',headers={'Origin':'https://viewer.example'})
            self.assertEqual(private.status_code,401)
            self.assertNotIn('access-control-allow-origin',private.headers)
            self.assertEqual(client.get('/play/map').json()['assets']['manifest'],'/static/sample-assets.json')
    def test_client_asset_contract(self):
        result=subprocess.run(['node','tests/sample_assets.test.mjs'],cwd=Path(__file__).resolve().parents[1],capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
