"""No-player browser observation plus independent authenticated clients. No model simulation claims."""
from __future__ import annotations
from contextlib import nullcontext
import json
import os
from pathlib import Path
import sys
import time
import uuid
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import httpx
from playwright.sync_api import sync_playwright, expect
from agent_world import WorldRuntime
from tests.live import LiveServer

def main():
    output=ROOT/'test-results';output.mkdir(exist_ok=True)
    origin=os.getenv('OBSERVATION_TEST_ORIGIN')
    if origin:
        if origin!='http://127.0.0.1:18900':raise ValueError('manual fixture must use isolated test port')
        context_server=nullcontext(SimpleNamespace(url=origin,db=Path(os.environ['OBSERVATION_TEST_DB'])))
    else:context_server=LiveServer()
    report={};errors=[]
    with context_server as server, sync_playwright() as p:
        runtime=WorldRuntime(server.db)
        with runtime._conn(readonly=True) as c:roles_before=c.execute('SELECT COUNT(*) FROM roles').fetchone()[0]
        try:browser=p.chromium.launch(headless=True)
        except Exception:
            if os.name!='nt':raise
            browser=p.chromium.launch(channel='msedge',headless=True)
        ctx=browser.new_context(viewport={'width':1440,'height':1000})
        page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(server.url+'/watch',wait_until='domcontentloaded')
        page.wait_for_function("() => document.body.classList.contains('spectating') && document.querySelector('#watch-health').textContent.includes('已同步')",timeout=30000)
        expect(page.locator('#welcome')).to_be_hidden()
        assert ctx.cookies()==[], 'guest observation must not mint a player cookie'
        with runtime._conn(readonly=True) as c:assert c.execute('SELECT COUNT(*) FROM roles').fetchone()[0]==roles_before
        report['fresh_guest_connected_without_player']=True
        a=runtime.create_role('ObserverTest A');b=runtime.create_role('ObserverTest B')
        ta=runtime.issue_identity_token('lantern-hollow',a['role_id'])['token']
        tb=runtime.issue_identity_token('lantern-hollow',b['role_id'])['token']
        clients=[httpx.Client(base_url=server.url,trust_env=False,timeout=10,headers={'Authorization':'Bearer '+t}) for t in (ta,tb)]
        def call(client,name,args,op=None):
            body={'arguments':args}
            if name not in ('town.look','town.messages'):body['operation_id']=op or 'browser-fixture-'+uuid.uuid4().hex
            response=client.post('/v1/functions/'+name+'/invoke',json=body)
            assert response.status_code==200,(name,response.status_code,response.text)
            return response.json()
        call(clients[0],'town.enter',{'appearance':'sage'})
        call(clients[1],'town.enter',{'appearance':'rose'})
        page.wait_for_function("() => document.querySelector('#travelers').textContent.includes('ObserverTest A') && document.querySelector('#travelers').textContent.includes('ObserverTest B')",timeout=15000)
        report['external_travelers_visible']=True
        walk=call(clients[0],'town.interact',{'target':'elia'})
        expect(page.locator('.traveler-row').filter(has_text='ObserverTest A')).to_contain_text('行走中',timeout=10000)
        page.screenshot(path=str(output/'observer-moving.png'),full_page=True)
        report['accepted_path_rendered_while_moving']=True
        started=time.monotonic()
        hello=call(clients[0],'town.say',{'text':'Beta, do you see the light?','to_role_id':b['role_id']},'observer-test-hello')
        expect(page.locator('#timeline')).to_contain_text('Beta, do you see the light?',timeout=10000)
        report['message_to_browser_seconds']=round(time.monotonic()-started,3)
        assert report['message_to_browser_seconds']<5
        read=clients[1].post('/v1/streams/conversation/read',json={})
        assert read.status_code==200,read.text
        assert any(e['event_id']==hello['result']['message_id'] for e in read.json()['events'])
        reply=call(clients[1],'town.say',{'text':'Yes Alpha, I am beside the path.','reply_to':hello['result']['message_id']},'observer-test-reply')
        assert reply['result']['thread_id']==hello['result']['thread_id']
        expect(page.locator('#timeline')).to_contain_text('Yes Alpha, I am beside the path.',timeout=10000)
        page.wait_for_function("() => document.querySelectorAll('#bubbles .bubble').length>=2",timeout=10000)
        report['addressed_message_read_and_reply_linked']=True
        report['simultaneous_speakers_not_overwritten']=True
        page.screenshot(path=str(output/'observer-conversation.png'),full_page=True)
        replay=call(clients[0],'town.say',{'text':'Beta, do you see the light?','to_role_id':b['role_id']},'observer-test-hello')
        assert replay['replayed'] is True
        page.wait_for_timeout(1100)
        assert page.locator('#timeline .event-text').filter(has_text='Beta, do you see the light?').count()==1
        # Reload receives retained history, but must not masquerade historical speech as current bubbles.
        page.reload(wait_until='domcontentloaded')
        page.wait_for_function("() => document.querySelector('#timeline').textContent.includes('Beta, do you see the light?')",timeout=20000)
        assert page.locator('#bubbles .bubble').count()==0
        report['refresh_recovers_labeled_history_without_replaying_speech']=True
        ctx.set_offline(True)
        page.wait_for_selector('#connection.offline',timeout=20000)
        call(clients[1],'town.say',{'text':'Message sent while the observer was disconnected.'})
        ctx.set_offline(False)
        expect(page.locator('#timeline')).to_contain_text('Message sent while the observer was disconnected.',timeout=20000)
        assert page.locator('#timeline .event-text').filter(has_text='Message sent while the observer was disconnected.').count()==1
        report['disconnect_catchup_no_duplicates']=True
        page.wait_for_timeout(1100)
        call(clients[0],'town.say',{'text':'<img src=x onerror=alert(1)> is only public text.'})
        expect(page.locator('#timeline')).to_contain_text('<img src=x',timeout=15000)
        assert page.locator('#timeline img').count()==0
        report['untrusted_public_text_not_executed']=True
        call(clients[0],'town.interact',{'target':'board'})
        deadline=time.monotonic()+20
        while time.monotonic()<deadline:
            state=call(clients[0],'town.look',{})['result']['meta']['self']
            if state['movement'] is None:break
            page.wait_for_timeout(100)
        else:raise AssertionError('note author never reached the board')
        call(clients[0],'town.note',{'text':'A durable note visible without creating a player.'})
        expect(page.locator('#public-notes')).to_contain_text('A durable note visible without creating a player.',timeout=10000)
        expect(page.locator('#timeline')).to_contain_text('A durable note visible without creating a player.')
        report['persistent_notes_visible_to_observers']=True

        # Observer cannot use action or invitation endpoints even while seeing the complete public world.
        denied=page.request.post(server.url+'/play/action',headers={'X-Lantern-Client':'1'},data={'function':'town.stop','operation_id':'deny','arguments':{}})
        assert denied.status==401
        report['public_observer_cannot_control']=True
        page.click('#language');page.wait_for_function("() => document.documentElement.lang==='en'")
        page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(500)
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        page.screenshot(path=str(output/'observer-mobile.png'),full_page=True)
        expect(page.locator('.live-panel')).to_be_visible()
        report['mobile_observer_layout']=True
        # Same page can deliberately choose to become a player; mere observation never does that.
        page.set_viewport_size({'width':1440,'height':1000})
        page.click('#join-mode');page.fill('#name','Human Observer');page.click('#join')
        page.wait_for_function("() => !document.body.classList.contains('spectating') && document.querySelector('#traveler-name').textContent==='Human Observer'",timeout=20000)
        expect(page.locator('#say')).to_be_enabled()
        expect(page.locator('#timeline')).to_contain_text('Beta, do you see the light?')
        reply_button=page.locator('#timeline li').filter(has_text='Yes Alpha, I am beside the path.').locator('button.reply')
        reply_button.click();page.fill('#modal textarea','I can see both travelers from the browser.')
        page.click('#modal form button[type=submit]')
        expect(page.locator('#timeline')).to_contain_text('I can see both travelers from the browser.',timeout=15000)
        report['human_player_can_reply_on_same_rules']=True
        page.click('#watch-mode');page.wait_for_selector('body.spectating')
        assert page.locator('#say').is_disabled()
        page.screenshot(path=str(output/'observer-final.png'),full_page=True)
        assert not errors,errors
        report['page_errors']=errors
        report['evidence_scope']='real browser + independent HTTP clients; no LLM autonomy claim'
        for client in clients:client.close()
        ctx.close();browser.close()
    (output/'observation-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
