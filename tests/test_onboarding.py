from pathlib import Path
import re
import tempfile
import unittest
from fastapi.testclient import TestClient
from lantern_hollow.onboarding import invitation_prompt,resume_prompt,connection_guide,checked_origin
from lantern_hollow.server import create_app

class OnboardingPromptTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.app=create_app(Path(self.temp.name)/'world.sqlite3',public_url='http://127.0.0.1:8840',agent_public_url='https://agents.example.test')
        self.client=TestClient(self.app);self.addCleanup(self.client.close)
    def join_player(self):
        response=self.client.post('/play/join',headers={'X-Lantern-Client':'1'},json={'name':'访客'})
        self.assertEqual(response.status_code,200,response.text)
    def test_resume_is_client_neutral_and_does_not_embed_identity(self):
        text=resume_prompt("https://world.example.test")
        self.assertIn("GET",text);self.assertNotIn("awid_",text);self.assertNotIn("awjt_",text)
        self.assertNotRegex(text,r"ChatGPT|Claude|Codex|OpenCode|你是|You are")
        self.assertIn("/v1/whoami",connection_guide("https://world.example.test"))
    def test_prompt_is_one_line_and_client_neutral(self):
        for lang in ('zh','en'):
            p=invitation_prompt('https://world.example.test','awjt_example',language=lang)
            self.assertNotIn(chr(10),p);self.assertIn('GET',p);self.assertIn('https://world.example.test/agent',p)
            self.assertNotRegex(p,r'(?i)Claude|ChatGPT|OpenCode|Codex|Doubao|Kimi|PowerShell|Pi CLI|你是|You are')
            self.assertNotIn('town.interact',p)
    def test_ticket_is_not_put_in_url(self):
        p=invitation_prompt('https://world.example.test','awjt_example')
        urls=re.findall(r'https?://[^\s]+',p)
        self.assertTrue(urls);self.assertTrue(all('awjt_' not in u for u in urls))
    def test_unsafe_origin_or_ticket_is_rejected(self):
        for origin in ('https://user:secret@world.test','http://world.test','https://world.test/path','https://world.test?token=x','file:///tmp','https://world.test:bad'):
            with self.assertRaises(ValueError):checked_origin(origin)
        for ticket in ('wrong','awjt_bad'+chr(10)+'line','awjt_bad space','awjt_inject;run','awjt_bad\x00'):
            with self.assertRaises(ValueError):invitation_prompt('https://world.test',ticket)
    def test_public_guide_contains_no_credentials_and_no_model_branch(self):
        response=self.client.get('/agent')
        self.assertEqual(response.status_code,200,response.text)
        self.assertTrue(response.headers['content-type'].startswith('text/plain'))
        self.assertIn('no-store',response.headers['cache-control'])
        self.assertIn('https://agents.example.test/v1/bootstrap',response.text)
        self.assertNotIn('awjt_',response.text);self.assertNotIn('awid_',response.text)
        self.assertNotRegex(response.text,r'(?i)if.*(ChatGPT|Claude|Codex|OpenCode|Kimi)')
    def test_browser_still_uses_local_origin_but_invites_use_public_origin(self):
        self.join_player()
        response=self.client.post('/play/agent',headers={'X-Lantern-Client':'1','Origin':'http://127.0.0.1:8840'},json={'name':'朋友','language':'zh'})
        self.assertEqual(response.status_code,200,response.text)
        invite=response.json()
        self.assertEqual(invite['guide_url'],'https://agents.example.test/agent')
        self.assertIn(invite['ticket'],invite['instructions'])
        self.assertNotIn('127.0.0.1',invite['instructions'])
        self.assertEqual(invite['instructions'],invitation_prompt('https://agents.example.test',invite['ticket']))
        self.assertEqual(invite['exchange_url'],'https://agents.example.test/v1/join/exchange')
    def test_english_uses_same_server_generated_contract(self):
        self.join_player()
        r=self.client.post('/play/agent',headers={'X-Lantern-Client':'1'},json={'language':'en'})
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(r.json()['instructions'],invitation_prompt('https://agents.example.test',r.json()['ticket'],language='en'))
    def test_bad_language_does_not_create_role(self):
        self.join_player()
        w=self.app.state.runtime
        with w._conn(readonly=True) as c:before=c.execute('SELECT COUNT(*) FROM roles').fetchone()[0]
        r=self.client.post('/play/agent',headers={'X-Lantern-Client':'1'},json={'language':'bad'})
        self.assertEqual(r.status_code,422)
        with w._conn(readonly=True) as c:self.assertEqual(c.execute('SELECT COUNT(*) FROM roles').fetchone()[0],before)
    def test_observer_cannot_mint_invitation(self):
        r=self.client.post('/play/agent',headers={'X-Lantern-Client':'1'},json={'name':'bad'})
        self.assertEqual(r.status_code,401)
    def test_exact_guide_entry_shape_runs_without_guessed_api(self):
        self.join_player()
        invite=self.client.post('/play/agent',headers={'X-Lantern-Client':'1'},json={'name':'world guest'}).json()
        exchange=self.client.post('/v1/join/exchange',json={'ticket':invite['ticket']})
        self.assertEqual(exchange.status_code,200,exchange.text)
        data=exchange.json();headers={'Authorization':'Bearer '+data['identity']['token']}
        entered=self.client.post('/v1/functions/town.enter/invoke',headers=headers,json=data['next']['arguments'])
        self.assertEqual(entered.status_code,200,entered.text)
        self.assertTrue(entered.json()['result']['entered'])
        self.assertEqual(self.client.get('/v1/bootstrap',headers=headers).status_code,200)
        self.assertEqual(self.client.post('/v1/functions/town.look/invoke',headers=headers,json={'arguments':{}}).status_code,200)
        self.assertEqual(self.client.post('/v1/streams/conversation/read',headers=headers,json={'limit':10}).status_code,200)
    def test_html_uses_server_instructions_not_a_second_hardcoded_prompt(self):
        js=(Path(__file__).resolve().parents[1]/'lantern_hollow/web/app.js').read_text(encoding='utf-8')
        self.assertIn('const instructions=r.instructions',js)
        self.assertNotIn('Ask the human to configure the connector',js)
    def test_guide_includes_failure_and_wire_format_boundaries(self):
        guide=connection_guide('https://world.test')
        for expected in ('UTF-8','charset=utf-8','Unicode escapes','including GET reads','Do NOT recount','Expired ticket','read-only URL','do NOT stop to install/configure MCP'):
            self.assertIn(expected,guide)

if __name__=='__main__':unittest.main()
