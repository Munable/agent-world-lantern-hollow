"""Real-browser camera and same-role observation acceptance; disposable world only."""
from pathlib import Path
import json
import os
import sys
import time
import httpx
from playwright.sync_api import sync_playwright, expect
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tests.live import LiveServer

def main():
    out=ROOT/'test-results'/'camera';out.mkdir(parents=True,exist_ok=True)
    report={};errors=[]
    with LiveServer() as server, sync_playwright() as pw:
        options={'headless':True}
        if os.name=='nt':options['channel']='chrome'
        browser=pw.chromium.launch(**options)
        ctx=browser.new_context(viewport={'width':1280,'height':900})
        page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(server.url);expect(page.locator('#join-mode')).to_be_enabled()
        observer_writes=[]
        page.on('request',lambda r:observer_writes.append(r.url) if r.url.endswith('/play/action') else None)
        page.locator('#world').focus()
        for key in ('e','Escape','ArrowUp'):page.keyboard.press(key)
        page.wait_for_timeout(150)
        assert not observer_writes and not errors
        assert page.locator('#toast:visible').count()==0
        report['observer_keyboard_has_no_player_action']=True
        page.click('#join-mode');page.fill('#name','Camera player');page.click('#join')
        expect(page.locator('#return-role')).to_have_attribute('aria-pressed','true')
        original=page.request.get(server.url+'/play/session').json()['role_id']
        sent=[]
        page.on('request',lambda r:sent.append(r.post_data_json) if r.url.endswith('/play/action') else None)
        box=page.locator('#world').bounding_box()
        page.mouse.move(box['x']+box['width']*.5,box['y']+box['height']*.4)
        page.mouse.down();page.mouse.move(box['x']+box['width']*.7,box['y']+box['height']*.5,steps=8);page.mouse.up()
        page.wait_for_timeout(550);assert not sent
        expect(page.locator('#return-role')).to_have_attribute('aria-pressed','false')
        report['authenticated_drag_has_no_action']=True
        def settled(x):
            deadline=time.monotonic()+15
            while time.monotonic()<deadline:
                a=page.request.get(server.url+'/play/session').json()['view']['snapshot']['meta']['self']
                if not a['movement'] and a['position']==[x,21]:return
                page.wait_for_timeout(150)
            raise AssertionError('Authoritative movement did not settle')
        page.click('#overview');box=page.locator('#world').bounding_box()
        page.locator('#world').click(position={'x':box['width']*17.5/40,'y':box['height']*21.5/26})
        settled(17);assert sent[-1]['arguments']=={'x':17,'y':21}
        page.click('#return-role');page.wait_for_timeout(300)
        z=1.8;cx=17*16+8;cy=416-416/(2*z)
        sx=16.5*16*z+320-cx*z;sy=21.5*16*z+208-cy*z
        page.locator('#world').click(position={'x':sx/640*box['width'],'y':sy/416*box['height']})
        settled(16);assert sent[-1]['arguments']=={'x':16,'y':21}
        report['overview_and_zoom_hit_mapping']=True
        response=page.request.post(server.url+'/play/agent',headers={'X-Lantern-Client':'1'},data={'name':'Camera Agent','language':'zh'})
        assert response.status==200
        fixture=response.json();role=fixture['role_id']
        with httpx.Client(base_url=server.url,trust_env=False,timeout=10,headers={'Authorization':'Bearer '+fixture['identity_token']}) as actor:
            def invoke(name,args,operation):
                r=actor.post('/v1/functions/'+name+'/invoke',json={'operation_id':operation,'arguments':args});r.raise_for_status();return r.json()
            invoke('town.enter',{},'camera-enter')
            page.click('#follow-agent');page.fill('#watch-role-id',role);page.click('#watch-role-confirm')
            expect(page.locator('#camera-status')).to_contain_text('Camera Agent')
            assert page.locator('#say').is_disabled()
            assert page.evaluate('localStorage.getItem("lh.public-focus")')==role
            assert page.request.get(server.url+'/play/session').json()['role_id']==original
            report['public_focus_does_not_change_cookie_authority']=True
            page.reload();expect(page.locator('#camera-status')).to_contain_text('Camera Agent')
            report['refresh_remembers_same_agent']=True
            row=page.locator('.traveler-row').filter(has_text='Camera player');row.click()
            assert page.evaluate('localStorage.getItem("lh.public-focus")')==role
            page.click('#return-role');expect(page.locator('#camera-status')).to_contain_text('Camera Agent')
            report['select_other_does_not_replace_home_role']=True
            invoke('town.move',{'x':20,'y':21},'camera-agent-move');page.wait_for_timeout(1200)
            text='Camera test: a real published line.'
            invoke('town.say',{'text':text},'camera-speech');expect(page.locator('.bubble')).to_be_visible()
            page.wait_for_timeout(800);page.screenshot(path=str(out/'desktop.png'),full_page=True)
            page.wait_for_timeout(8200);assert page.locator('.bubble:visible').count()==0
            page.reload();expect(page.locator('#timeline')).to_contain_text(text);assert page.locator('.bubble:visible').count()==0
            report['speech_expires_and_reload_does_not_replay']=True
            ctx.set_offline(True)
            invoke('town.interact',{'target':'board'},'camera-board')
            deadline=time.monotonic()+15
            while time.monotonic()<deadline:
                snap=actor.post('/v1/functions/town.look/invoke',json={'arguments':{}}).json()['result']
                if not snap['meta']['self']['movement']:break
                time.sleep(.2)
            note='Camera acceptance: persisted while browser was offline.'
            invoke('town.note',{'text':note},'camera-note')
            ctx.set_offline(False);page.reload();expect(page.locator('#public-notes')).to_contain_text(note)
            server.restart();page.reload();expect(page.locator('#public-notes')).to_contain_text(note)
            expect(page.locator('#camera-status')).to_contain_text('Camera Agent')
            report['offline_action_and_server_restart_persist']=True
        mobilectx=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
        mobile=mobilectx.new_page();mobile.on('pageerror',lambda e:errors.append(str(e)))
        mobile.goto(server.url+'/watch?role='+role);expect(mobile.locator('#camera-status')).to_contain_text('Camera Agent')
        assert mobile.evaluate('document.documentElement.scrollWidth')<=390
        box=mobile.locator('#world').bounding_box();x=box['x']+box['width']/2;y=box['y']+box['height']/2
        cdp=mobilectx.new_cdp_session(mobile)
        points=lambda d:[{'id':1,'x':x-d,'y':y},{'id':2,'x':x+d,'y':y}]
        cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':points(25)})
        cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':points(55)})
        cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
        expect(mobile.locator('#return-role')).to_have_attribute('aria-pressed','false')
        mobile.click('#return-role');expect(mobile.locator('#return-role')).to_have_attribute('aria-pressed','true')
        mobile.screenshot(path=str(out/'mobile.png'),full_page=True)
        report['mobile_layout_pinch_and_return']=True
        assert 'role=' not in mobile.url
        mobile.click('#follow-agent');mobile.fill('#watch-role-id',original);mobile.click('#watch-role-confirm')
        expect(mobile.locator('#camera-status')).to_contain_text('Camera player')
        mobile.reload();expect(mobile.locator('#camera-status')).to_contain_text('Camera player')
        mobile.click('#follow-agent');mobile.click('#watch-role-forget')
        mobile.reload();expect(mobile.locator('#camera-status')).to_have_text('\u81ea\u7531\u89c2\u5bdf')
        assert mobile.evaluate('localStorage.getItem("lh.public-focus")') is None
        report['linked_role_switch_and_forget_survive_refresh']=True
        assert not errors,errors
        report['page_errors']=[]
        browser.close()
    (out/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(report,indent=2,ensure_ascii=False))

if __name__=='__main__':main()
