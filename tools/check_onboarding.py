"""Browser acceptance for the exact server-generated, client-neutral invitation."""
from pathlib import Path
import json, os, re, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tests.live import LiveServer
from playwright.sync_api import sync_playwright, expect

def main():
    report={};errors=[]
    with LiveServer() as server, sync_playwright() as p:
        try: browser=p.chromium.launch(headless=True)
        except Exception:
            if os.name!='nt': raise
            browser=p.chromium.launch(channel='msedge',headless=True)
        context=browser.new_context(viewport={'width':1280,'height':900},permissions=['clipboard-read','clipboard-write'])
        page=context.new_page();page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto(server.url+'/watch',wait_until='domcontentloaded')
        page.wait_for_selector('body.spectating')
        page.click('#join-mode');page.fill('#name','Invitation Test');page.click('#join')
        page.wait_for_function("() => !document.body.classList.contains('spectating') && document.querySelector('#traveler-name').textContent==='Invitation Test'")
        page.click('#agent')
        with page.expect_response(lambda r:r.url.endswith('/play/agent') and r.request.method=='POST') as captured:
            page.click('#agent-generate')
        response=captured.value;assert response.status==200
        invitation=response.json()
        assert invitation['identity_token'].startswith('awid_')
        key_area=page.get_by_label('Private Agent identity token')
        expect(key_area).to_have_value(invitation['identity_token'])
        area=page.get_by_label('Private Agent invitation')
        expect(area).to_have_value(invitation['instructions'])
        prompt=area.input_value()
        assert chr(10) not in prompt and 'GET' in prompt and invitation['guide_url'] in prompt
        assert invitation['identity_token'] not in prompt
        assert not re.search(r'ChatGPT|Claude|Codex|OpenCode|你是|You are',prompt,re.I)
        urls=re.findall(r'https?://[^\s]+',prompt)
        assert all(invitation['ticket'] not in url for url in urls)
        page.click('#agent-key-copy')
        assert page.evaluate('navigator.clipboard.readText()')==invitation['identity_token']
        page.click('#agent-copy')
        assert page.evaluate('navigator.clipboard.readText()')==prompt
        guide=page.request.get(invitation['guide_url'])
        assert guide.status==200 and 'text/plain' in guide.headers['content-type']
        assert invitation['ticket'] not in guide.text() and 'awid_' not in guide.text()
        exchange=page.request.post(invitation['exchange_url'],data={'ticket':invitation['ticket']}).json()
        assert exchange['identity']['token']==invitation['identity_token']
        entered=page.request.post(server.url+'/v1/functions/town.enter/invoke',headers={'Authorization':'Bearer '+exchange['identity']['token']},data=exchange['next']['arguments'])
        assert entered.status==200 and entered.json()['result']['entered'] is True
        report.update(single_server_source=True,one_line_copy=True,clipboard_exact=True,neutral_identity=True,ticket_outside_url=True,public_guide_without_credentials=True,identity_key_shown_to_user=True,same_key_after_ticket_exchange=True,documented_entry_succeeds=True)
        page.locator('#modal-close').click() if page.locator('#modal-close').count() else page.keyboard.press('Escape')
        page.click('#agent')
        page.click('#agent-resume')
        saved_key=page.get_by_label('Saved Agent identity token')
        saved_key.fill(invitation['identity_token'])
        with page.expect_response(lambda r:r.url.endswith('/play/agent/resume') and r.request.method=='POST') as resumed:
            page.click('#agent-resume-build')
        resume=resumed.value;assert resume.status==200
        assert invitation['identity_token'] not in (resume.request.post_data or '')
        resume_data=resume.json()
        assert resume_data['mode']=='resume' and resume_data['guide_version']=='4'
        assert all(k not in resume_data for k in ('ticket','role_id','exchange_url','token'))
        resume_template=resume_data['instructions']
        assert '/v1/whoami' in resume_template and '/v1/bootstrap' in resume_template
        assert 'awjt_' not in resume_template and 'awid_' not in resume_template
        resume_area=page.get_by_label('Private Agent resume')
        resume_prompt=resume_area.input_value()
        assert invitation['identity_token'] in resume_prompt
        assert page.evaluate("JSON.stringify(localStorage)").find(invitation['identity_token'])==-1
        page.click('#agent-copy')
        assert page.evaluate('navigator.clipboard.readText()')==resume_prompt
        report.update(resume_without_mint=True,resume_token_composed_client_side=True,resume_token_not_uploaded=True,resume_token_not_persisted=True,resume_verification_paths=True)
        page.locator('#modal-close').click() if page.locator('#modal-close').count() else page.keyboard.press('Escape')
        page.click('#language');page.click('#agent')
        with page.expect_response(lambda r:r.url.endswith('/play/agent') and r.request.method=='POST') as captured:
            page.click('#agent-generate')
        en=captured.value.json()
        assert en['instructions'].startswith('Use your currently available tools to GET ')
        expect(page.get_by_label('Private Agent invitation')).to_have_value(en['instructions'])
        report['english_same_contract']=True
        assert not errors,errors
        report['page_errors']=errors
        context.close();browser.close()
    output=ROOT/'test-results';output.mkdir(exist_ok=True)
    (output/'onboarding-browser.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))
if __name__=='__main__':main()
