"""Real browser acceptance: the playable loop, persisted state, safe UI, mobile and reconnection."""
from __future__ import annotations
import json
import os
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tests.live import LiveServer
from playwright.sync_api import sync_playwright


def main():
    out=ROOT/'test-results'
    out.mkdir(exist_ok=True)
    errors=[]
    report={}
    with LiveServer() as server, sync_playwright() as p:
        try: browser=p.chromium.launch(headless=True)
        except Exception:
            if os.name!='nt': raise
            browser=p.chromium.launch(channel='chrome',headless=True)
        context=browser.new_context(viewport={'width':1440,'height':980},device_scale_factor=1)
        page=context.new_page()
        page.on('pageerror',lambda err:errors.append(str(err)))
        page.goto(server.url,wait_until='domcontentloaded')
        page.wait_for_selector('body.spectating')
        page.click('#join-mode')
        page.wait_for_selector('#welcome:not([hidden])')
        page.wait_for_timeout(900)
        page.screenshot(path=str(out/'welcome.png'),full_page=True)
        page.fill('#name','林间旅人')
        page.click('#join')
        page.wait_for_selector('#welcome[hidden]',state='attached',timeout=20000)
        page.wait_for_function("() => document.querySelector('#traveler-name').textContent === '林间旅人'")
        page.wait_for_timeout(1000)
        page.screenshot(path=str(out/'village.png'),full_page=True)
        report['browser_join']=True

        def state():
            response=page.request.get(server.url+'/play/session')
            assert response.status==200,response.text()
            return response.json()

        def wait_state(check,label,timeout=30):
            deadline=time.monotonic()+timeout
            while time.monotonic()<deadline:
                result=state()
                if check(result): return result
                page.wait_for_timeout(200)
            raise AssertionError('Timed out: '+label)

        first=state()
        role=first['role_id']
        page.click('#quest-action')
        page.wait_for_selector('#q1.done',timeout=30000)
        report['pathfinding_dialogue']=True
        page.screenshot(path=str(out/'dialogue.png'),full_page=True)
        for target in ('shard_moss','shard_sky','shard_water'):
            page.click('#inventory button[data-target="'+target+'"]')
            page.wait_for_selector('#inventory button[data-target="'+target+'"].collected',timeout=30000)
        page.click('#quest-action')
        page.wait_for_selector('#completion:not([hidden])',timeout=30000)
        completed=wait_state(lambda r:r['view']['snapshot']['meta']['self']['quest']=='complete','complete')
        assert completed['view']['snapshot']['meta']['beacon']['lit'] is True
        report['full_quest']=True
        page.screenshot(path=str(out/'complete.png'),full_page=True)
        page.click('#complete-continue')
        page.wait_for_selector('#modal[open] textarea',timeout=30000)
        page.fill('#modal textarea','愿下一位旅人，也有一束回家的光。')
        page.click('#modal form button[type=submit]')
        page.wait_for_selector('#modal:not([open])',state='attached')
        page.wait_for_function("() => document.querySelector('#notes').textContent.includes('愿下一位旅人')",timeout=15000)
        report['persistent_note']=True
        before=state()['view']['snapshot']['meta']['self']['position']
        page.reload(wait_until='domcontentloaded')
        page.wait_for_selector('#welcome[hidden]',state='attached',timeout=20000)
        recovered=state()
        assert recovered['role_id']==role
        assert recovered['view']['snapshot']['meta']['self']['position']==before
        assert recovered['view']['snapshot']['meta']['self']['quest']=='complete'
        report['reload_continuity']=True
        page.wait_for_timeout(600)

        page.click('#intent')
        page.fill('#modal textarea','我会先去河边，听一会儿水声。')
        page.click('#modal form button[type=submit]')
        page.wait_for_selector('.bubble.intent',timeout=15000)
        page.screenshot(path=str(out/'intent.png'),full_page=True)
        page.wait_for_timeout(1200)
        page.click('#say')
        page.fill('#modal textarea','<img src=x onerror=alert(1)> is only text.')
        page.click('#modal form button[type=submit]')
        page.wait_for_function("() => document.querySelector('#bubbles').textContent.includes('<img')",timeout=15000)
        assert page.locator('#bubbles img').count()==0
        report['safe_public_expression']=True

        page.click('.residents button[data-target="rowan"]')
        wait_state(lambda r:r['view']['snapshot']['meta']['self']['movement'] is not None,'movement start')
        page.wait_for_timeout(600)
        page.keyboard.press('Escape')
        stopped=wait_state(lambda r:r['view']['snapshot']['meta']['self']['movement'] is None,'cancel movement')
        pos=stopped['view']['snapshot']['meta']['self']['position']
        page.wait_for_timeout(1300)
        assert state()['view']['snapshot']['meta']['self']['position']==pos
        report['movement_cancel']=True

        context.set_offline(True)
        page.wait_for_selector('#connection.offline',timeout=20000)
        context.set_offline(False)
        page.wait_for_selector('#connection:not(.offline)',timeout=20000)
        assert state()['role_id']==role
        report['reconnect']=True
        page.click('#language')
        page.wait_for_function("() => document.documentElement.lang==='en'")
        page.wait_for_timeout(1200)
        page.screenshot(path=str(out/'english.png'),full_page=True)
        report['bilingual']=True
        page.set_viewport_size({'width':390,'height':844})
        page.wait_for_timeout(900)
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth+1')
        page.screenshot(path=str(out/'mobile.png'),full_page=True)
        page.click('#journal-toggle')
        page.screenshot(path=str(out/'mobile-journal.png'),full_page=True)
        report['mobile_layout']=True
        page.set_viewport_size({'width':1440,'height':980})
        page.click('#help')
        page.wait_for_selector('#modal[open]')
        page.click('#modal-close')
        assert not errors,errors
        report['page_errors']=errors
        report['state_source']='real HTTP server, kernel timers and persistent SQLite'
        context.close();browser.close()
    (out/'browser-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
