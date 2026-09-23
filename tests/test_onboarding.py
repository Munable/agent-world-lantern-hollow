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
        zh=resume_prompt("https://world.example.test")
        en=resume_prompt("https://world.example.test",language="en")
        for text in (zh,en):
            self.assertNotIn(chr(10),text);self.assertNotIn("awid_",text);self.assertNotIn("awjt_",text)
            self.assertIn("https://world.example.test/agent",text)
            self.assertIn("https://world.example.test/v1/whoami",text)
            self.assertIn("https://world.example.test/v1/bootstrap",text)
            self.assertNotRegex(text,r"ChatGPT|Claude|Codex|OpenCode|你是|You are")
        self.assertIn("用户提供的本世界身份令牌",zh)
        self.assertIn("user's identity token",en)
        guide=connection_guide("https://world.example.test")
        self.assertIn("Reading /agent alone is not resumed access",guide)
        self.assertIn("`identity.token` belongs to the user",guide)
        self.assertIn("wallet recovery key",guide)
        self.assertIn("optional convenience chosen by the user",guide)
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
        self.assertIn('Guide version: 5',response.text)
        self.assertIn('https://agents.example.test/v1/bootstrap',response.text)
        self.assertNotIn('awjt_',response.text);self.assertNotIn('awid_',response.text)
        self.assertNotRegex(response.text,r'(?i)if.*(ChatGPT|Claude|Codex|OpenCode|Kimi)')
    def test_browser_still_uses_local_origin_but_invites_use_public_origin(self):
        self.join_player()
        response=self.client.post('/play/agent',headers={'X-Lantern-Client':'1','Origin':'http://127.0.0.1:8840'},json={'name':'朋友','language':'zh'})
        self.assertEqual(response.status_code,200,response.text)
        invite=response.json()
        self.assertEqual(invite['guide_url'],'https://agents.example.test/agent')
        self.assertTrue(invite['identity_token'].startswith('awid_'))
        self.assertIn(invite['ticket'],invite['instructions'])
        self.assertNotIn(invite['identity_token'],invite['instructions'])
        self.assertNotIn('127.0.0.1',invite['instructions'])
        self.assertEqual(invite['instructions'],invitation_prompt('https://agents.example.test',invite['ticket']))
        self.assertEqual(invite['exchange_url'],'https://agents.example.test/v1/join/exchange')
        exchanged=self.client.post('/v1/join/exchange',json={'ticket':invite['ticket']})
        self.assertEqual(exchanged.status_code,200,exchanged.text)
        self.assertEqual(exchanged.json()['identity']['token'],invite['identity_token'])
        self.assertEqual(exchanged.json()['identity']['role_id'],invite['role_id'])
        with self.app.state.runtime._conn(readonly=True) as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM identity_tokens WHERE role_id=?',(invite['role_id'],)).fetchone()[0],1)
    def test_english_uses_same_server_generated_contract(self):
        self.join_player()
        r=self.client.post('/play/agent',headers={'X-Lantern-Client':'1'},json={'language':'en'})
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(r.json()['instructions'],invitation_prompt('https://agents.example.test',r.json()['ticket'],language='en'))
    def test_resume_endpoint_never_mints_role_ticket_or_identity(self):
        self.join_player()
        w=self.app.state.runtime
        with w._conn(readonly=True) as c:before=c.execute('SELECT COUNT(*) FROM roles').fetchone()[0]
        r=self.client.post('/play/agent/resume',headers={'X-Lantern-Client':'1'},json={'language':'zh'})
        self.assertEqual(r.status_code,200,r.text)
        data=r.json()
        self.assertEqual(data['mode'],'resume');self.assertEqual(data['guide_version'],'5')
        self.assertEqual(data['instructions'],resume_prompt('https://agents.example.test'))
        self.assertEqual(data['guide_url'],'https://agents.example.test/agent')
        for forbidden in ('ticket','role_id','exchange_url','token'):self.assertNotIn(forbidden,data)
        with w._conn(readonly=True) as c:self.assertEqual(c.execute('SELECT COUNT(*) FROM roles').fetchone()[0],before)
    def test_bad_language_does_not_create_role(self):
        self.join_player()
        w=self.app.state.runtime
        with w._conn(readonly=True) as c:before=c.execute('SELECT COUNT(*) FROM roles').fetchone()[0]
        r=self.client.post('/play/agent',headers={'X-Lantern-Client':'1'},json={'language':'bad'})
        self.assertEqual(r.status_code,422)
        with w._conn(readonly=True) as c:self.assertEqual(c.execute('SELECT COUNT(*) FROM roles').fetchone()[0],before)
    def test_observer_cannot_mint_but_can_read_public_resume_instructions(self):
        invite=self.client.post('/play/agent',headers={'X-Lantern-Client':'1'},json={'name':'bad'})
        resume=self.client.post('/play/agent/resume',headers={'X-Lantern-Client':'1'},json={'language':'zh'})
        self.assertEqual(invite.status_code,401);self.assertEqual(resume.status_code,200)
    def test_exact_guide_entry_shape_runs_without_guessed_api(self):
        self.join_player()
        invite=self.client.post('/play/agent',headers={'X-Lantern-Client':'1'},json={'name':'world guest'}).json()
        exchange=self.client.post('/v1/join/exchange',json={'ticket':invite['ticket']})
        self.assertEqual(exchange.status_code,200,exchange.text)
        data=exchange.json()
        self.assertEqual(data['identity']['token'],invite['identity_token'])
        headers={'Authorization':'Bearer '+data['identity']['token']}
        entered=self.client.post('/v1/functions/town.enter/invoke',headers=headers,json=data['next']['arguments'])
        self.assertEqual(entered.status_code,200,entered.text)
        self.assertTrue(entered.json()['result']['entered'])
        role_id=data['identity']['role_id']
        with self.app.state.runtime._conn(readonly=True) as c:roles_before=c.execute('SELECT COUNT(*) FROM roles').fetchone()[0]
        whoami=self.client.get('/v1/whoami',headers=headers)
        self.assertEqual(whoami.status_code,200,whoami.text);self.assertEqual(whoami.json()['role_id'],role_id)
        bootstrap=self.client.get('/v1/bootstrap',headers=headers)
        self.assertEqual(bootstrap.status_code,200,bootstrap.text);self.assertEqual(bootstrap.json()['role_id'],role_id)
        with self.app.state.runtime._conn(readonly=True) as c:self.assertEqual(c.execute('SELECT COUNT(*) FROM roles').fetchone()[0],roles_before)
        self.assertEqual(self.client.post('/v1/functions/town.look/invoke',headers=headers,json={'arguments':{}}).status_code,200)
        self.assertEqual(self.client.post('/v1/streams/conversation/read',headers=headers,json={'limit':10}).status_code,200)
    def test_html_uses_server_instructions_not_a_second_hardcoded_prompt(self):
        js=(Path(__file__).resolve().parents[1]/'lantern_hollow/web/app.js').read_text(encoding='utf-8')
        self.assertIn("agentCopyField(panel,r.instructions,'Private Agent invitation'",js)
        self.assertIn("agentCopyField(panel,r.identity_token,'Private Agent identity token'",js)
        self.assertIn("request('/play/agent/resume',{method:'POST',data:{language}})",js)
        self.assertIn("agentPanelActive(panel)",js)
        self.assertNotIn('Ask the human to configure the connector',js)
    def counts(self):
        with self.app.state.runtime._conn(readonly=True) as c:
            return tuple(c.execute('SELECT COUNT(*) FROM '+table).fetchone()[0]
                         for table in ('roles','identity_tokens','join_tickets'))

    def test_fresh_browser_resume_template_has_no_identity_side_effects(self):
        before=self.counts()
        for language in ('zh','en'):
            r=self.client.post('/play/agent/resume',headers={'X-Lantern-Client':'1'},json={'language':language})
            self.assertEqual(r.status_code,200)
            self.assertEqual(set(r.json()),{'mode','guide_url','guide_version','instructions'})
            self.assertNotIn('set-cookie',r.headers)
        self.assertEqual(self.counts(),before)
        self.assertEqual(self.client.get('/v1/whoami').status_code,401)
        self.assertEqual(self.counts(),before)

    def test_resume_template_rejects_token_and_role_arguments(self):
        before=self.counts()
        for extra in ({'token':'not-a-token'},{'role_id':'another-role'},{'ticket':'not-a-ticket'}):
            r=self.client.post('/play/agent/resume',headers={'X-Lantern-Client':'1'},json={'language':'zh',**extra})
            self.assertEqual(r.status_code,422)
        self.assertEqual(self.counts(),before)

    def test_saved_key_can_complete_first_entry_after_invitation_expiry(self):
        self.join_player()
        invite=self.client.post('/play/agent',headers={'X-Lantern-Client':'1'},json={'name':'Saved role'}).json()
        before=self.counts()
        with self.app.state.runtime._conn() as c:c.execute('UPDATE join_tickets SET expires_at=0')
        self.assertGreaterEqual(self.client.post('/v1/join/exchange',json={'ticket':invite['ticket']}).status_code,400)
        self.assertIn('world_entry_state.view.meta.self',connection_guide('https://world.test'))
        with TestClient(create_app(self.app.state.runtime.db_path)) as fresh:
            fresh.headers['Authorization']='Bearer '+invite['identity_token']
            who=fresh.get('/v1/whoami');self.assertEqual(who.status_code,200)
            boot=fresh.get('/v1/bootstrap');self.assertEqual(boot.status_code,200)
            self.assertIsNone(boot.json()['world_entry_state']['view']['meta']['self'])
            result=fresh.post('/v1/functions/town.enter/invoke',json={'operation_id':'first-entry-with-saved-key','arguments':{}})
            self.assertEqual(result.status_code,200)
            boot=fresh.get('/v1/bootstrap').json()
            self.assertEqual(boot['world_entry_state']['view']['meta']['self']['role_id'],invite['role_id'])
            self.assertEqual(who.json()['role_id'],invite['role_id'])
        self.assertEqual(self.counts(),before)

    def test_two_fresh_clients_use_one_key_without_copying_sessions(self):
        self.join_player()
        invite=self.client.post('/play/agent',headers={'X-Lantern-Client':'1'},json={'name':'Portable role'}).json()
        before=self.counts()
        for index in range(2):
            with TestClient(create_app(self.app.state.runtime.db_path)) as fresh:
                self.assertFalse(fresh.cookies)
                fresh.headers['Authorization']='Bearer '+invite['identity_token']
                who=fresh.get('/v1/whoami');self.assertEqual(who.status_code,200)
                self.assertEqual(who.json()['role_id'],invite['role_id'])
                boot=fresh.get('/v1/bootstrap').json()
                if boot['world_entry_state']['view']['meta']['self'] is None:
                    self.assertEqual(index,0)
                    result=fresh.post('/v1/functions/town.enter/invoke',json={'operation_id':'portable-entry','arguments':{}})
                    self.assertEqual(result.status_code,200)
                boot=fresh.get('/v1/bootstrap').json()
                self.assertEqual(boot['world_entry_state']['view']['meta']['self']['role_id'],invite['role_id'])
        with self.app.state.runtime._conn(readonly=True) as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM operations WHERE actor_role_id=?',(invite['role_id'],)).fetchone()[0],1)
        self.assertEqual(self.counts(),before)

    def test_missing_revoked_or_wrong_world_key_never_creates_identity(self):
        self.join_player()
        invite=self.client.post('/play/agent',headers={'X-Lantern-Client':'1'},json={}).json()
        w=self.app.state.runtime
        metadata=w.resolve_identity_token(invite['identity_token'])
        w.revoke_identity_token(metadata['token_id'])
        other=w.issue_identity_token('other-world',invite['role_id'])['token']
        before=self.counts()
        for token in ('',invite['identity_token'],other):
            headers={'Authorization':'Bearer '+token} if token else {}
            for path in ('/v1/whoami','/v1/bootstrap'):
                self.assertIn(self.client.get(path,headers=headers).status_code,(401,403))
        self.assertGreaterEqual(self.client.post('/v1/join/exchange',json={'ticket':invite['ticket']}).status_code,400)
        self.assertEqual(self.counts(),before)

    def test_shared_origin_validation_rejects_ambiguous_or_multiline_urls(self):
        bad=('https://world.test\n','https://world.test\t','https://world.test\\evil.test',
             'https://@world.test','https://world.test:bad',None)
        for origin in bad:
            with self.subTest(origin=origin):
                with self.assertRaises(ValueError):checked_origin(origin)
                with self.assertRaises(ValueError):create_app(Path(self.temp.name)/'bad.sqlite3',public_url=origin)
        self.assertEqual(checked_origin('HTTPS://World.Test:443/'),'https://world.test')
        self.assertEqual(checked_origin('http://localhost:80/'),'http://localhost')

    def test_public_agent_host_is_explicitly_allowed_without_relaxing_ui_origin(self):
        self.assertEqual(self.client.get('/agent',headers={'Host':'agents.example.test'}).status_code,200)
        self.assertEqual(self.client.get('/agent',headers={'Host':'untrusted.example'}).status_code,400)
        denied=self.client.post('/play/join',headers={'Host':'agents.example.test','Origin':'https://agents.example.test','X-Lantern-Client':'1'},json={'name':'Wrong origin'})
        self.assertEqual(denied.status_code,403)

    def test_mcp_accepts_configured_agent_origin(self):
        from mcp.types import LATEST_PROTOCOL_VERSION
        w=self.app.state.runtime
        role=w.create_role('MCP host probe')['role_id']
        token=w.issue_identity_token('lantern-hollow',role)['token']
        with TestClient(self.app) as client:
            headers={'Host':'agents.example.test','Origin':'https://agents.example.test',
                     'Authorization':'Bearer '+token,'Accept':'application/json, text/event-stream'}
            initialized=client.post('/mcp',headers=headers,json={'jsonrpc':'2.0','id':1,'method':'initialize',
                'params':{'protocolVersion':LATEST_PROTOCOL_VERSION,'capabilities':{},
                          'clientInfo':{'name':'identity-contract-test','version':'1'}}})
            self.assertEqual(initialized.status_code,200,initialized.text)
            self.assertIn('result',initialized.json())

    def test_bad_function_type_is_a_client_error(self):
        self.join_player()
        for name in ([],{},None):
            result=self.client.post('/play/action',headers={'X-Lantern-Client':'1'},json={'function':name})
            self.assertEqual(result.status_code,422)

    def test_version_metadata_has_one_source(self):
        import tomllib
        from lantern_hollow import __version__
        metadata=tomllib.loads((Path(__file__).resolve().parents[1]/'pyproject.toml').read_text())
        self.assertEqual(metadata['tool']['setuptools']['dynamic']['version']['attr'],'lantern_hollow.__version__')
        self.assertEqual(self.client.get('/play/map').json()['version'],__version__)

    def test_guide_includes_failure_and_wire_format_boundaries(self):
        guide=connection_guide('https://world.test')
        for expected in ('UTF-8','charset=utf-8','Unicode escapes','Authenticated reads','Do NOT reproduce',
                         'read-only URL','do NOT stop to install/configure MCP','Reading /agent alone is not resumed access',
                         '`identity.token` belongs to the user','wallet recovery key','same identity token',
                         'Do not mint another role','saved role key is required'):
            self.assertIn(expected,guide)

if __name__=='__main__':unittest.main()
