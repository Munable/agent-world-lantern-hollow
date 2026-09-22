from __future__ import annotations
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.live import LiveServer
from playwright.sync_api import sync_playwright, expect
from agent_world import WorldRuntime


def main():
    report = {}
    output = ROOT / 'test-results'
    output.mkdir(exist_ok=True)
    with LiveServer() as server, sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except Exception:
            if os.name != 'nt':
                raise
            browser = p.chromium.launch(channel='chrome', headless=True)
        context = browser.new_context(viewport={'width': 390, 'height': 844})
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(server.url, wait_until='domcontentloaded')
        page.wait_for_selector('body.spectating')
        page.click('#join-mode')
        expect(page.locator('#welcome')).to_be_visible()
        page.screenshot(path=str(output / 'mobile-first-visit.png'), full_page=True)
        button = page.locator('#join').bounding_box()
        wrap = page.locator('#canvas-wrap').bounding_box()
        assert button and wrap
        assert button['y'] >= wrap['y'] and button['y'] + button['height'] <= wrap['y'] + wrap['height'], (button, wrap)
        page.fill('#name', '独立验收旅人')
        page.click('#join')
        expect(page.locator('#welcome')).to_be_hidden(timeout=20000)
        report['mobile_first_entry'] = True
        page.set_viewport_size({'width': 1440, 'height': 980})
        page.wait_for_timeout(1000)
        session = page.request.get(server.url + '/play/session').json()
        role = session['role_id']
        runtime = WorldRuntime(server.db)
        def counts():
            with runtime._conn(readonly=True) as c:
                return c.execute("SELECT COUNT(*) FROM operations WHERE actor_role_id=? AND function_id='town.say'", (role,)).fetchone()[0]
        before = counts()
        intercepted = []
        def lose_response(route):
            response = route.fetch()
            assert response.status == 200, response.text()
            intercepted.append(True)
            route.abort('failed')
        page.route('**/play/action', lose_response, times=1)
        page.click('#say')
        page.fill('#modal textarea', '这句话只应提交一次。')
        page.click('#modal form button[type=submit]')
        expect(page.locator('#modal')).not_to_be_visible(timeout=20000)
        page.wait_for_function("() => document.querySelector('#bubbles').textContent.includes('这句话只应提交一次')", timeout=15000)
        assert intercepted and counts() == before + 1
        assert page.evaluate("sessionStorage.getItem('lh.pending')") is None
        report['lost_response_recovers_without_duplicate'] = True
        page.click('.residents button[data-target="rowan"]')
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            value = page.request.get(server.url + '/play/session').json()['view']['snapshot']['meta']['self']
            if value['movement']:
                break
            page.wait_for_timeout(50)
        else:
            raise AssertionError('movement never began')
        page.screenshot(path=str(output / 'accepted-motion.png'), full_page=True)
        server.restart()
        page.reload(wait_until='domcontentloaded')
        expect(page.locator('#welcome')).to_be_hidden(timeout=20000)
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            recovered = page.request.get(server.url + '/play/session').json()
            if recovered['view']['snapshot']['meta']['self']['movement'] is None:
                break
            page.wait_for_timeout(150)
        assert recovered['role_id'] == role
        assert recovered['view']['snapshot']['meta']['self']['position'] == [11, 19]
        report['real_server_restart_completes_accepted_motion'] = True
        readonly = runtime.issue_identity_token('lantern-hollow', role, access_mode='observe')['token']
        observer = browser.new_context(viewport={'width': 1280, 'height': 900})
        observer.add_cookies([{'name': 'lantern_identity', 'value': readonly, 'url': server.url, 'httpOnly': True, 'sameSite': 'Strict'}])
        read_page = observer.new_page()
        read_page.on('pageerror', lambda error: errors.append(str(error)))
        read_page.goto(server.url, wait_until='domcontentloaded')
        expect(read_page.locator('#welcome')).to_be_hidden(timeout=20000)
        expect(read_page.locator('#say')).to_be_disabled()
        expect(read_page.locator('#agent')).to_be_disabled()
        report['readonly_browser_has_no_control_buttons'] = True
        tid = runtime.resolve_identity_token(readonly)['token_id']
        runtime.revoke_identity_token(tid)
        expect(read_page.locator('#welcome')).to_be_visible(timeout=20000)
        expect(read_page.locator('#say')).to_be_disabled()
        assert read_page.locator('#bubbles .bubble').count() == 0
        assert read_page.locator('#traveler-name').inner_text() != '独立验收旅人'
        report['revocation_clears_observer_view'] = True
        assert not errors, errors
        report['page_errors'] = errors
        observer.close()
        context.close()
        browser.close()
    (output / 'independent-edges.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
