"""Product-flow gate for the scene-first frontend; uses isolated test roles only."""
from pathlib import Path
import argparse,json,sys
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tests.live import LiveServer
from tools.frontend_test_support import launch_browser

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--browser',default='chromium');parser.add_argument('--output',default='test-results/product-polish');args=parser.parse_args()
    out=ROOT/args.output;out.mkdir(parents=True,exist_ok=True);report={'status':'running','browser':args.browser,'checks':{},'page_errors':[]};checks=report['checks']
    with LiveServer() as server,sync_playwright() as p:
        browser=launch_browser(p,args.browser);report['version']=browser.version
        context=browser.new_context(viewport={'width':1440,'height':960},device_scale_factor=2)
        page=context.new_page();page.set_default_timeout(12000);page.on('pageerror',lambda e:report['page_errors'].append(str(e)))
        def shot(name):page.screenshot(path=str(out/(name+'.png')),full_page=True)
        try:
            page.goto(server.url,wait_until='domcontentloaded');expect(page.locator('#asset-status')).to_have_attribute('data-state','ready')
            expect(page.locator('#arrival-card')).to_be_visible();shot('01-public-entry')
            page.click('#agent-entry');expect(page.locator('#access-watch')).to_be_visible();expect(page.locator('#access-resume')).to_be_visible()
            assert page.locator('#modal input').count()==0;page.keyboard.press('Escape');checks['agent_entry_no_implicit_key_or_role_creation']=True
            page.click('#join-mode');expect(page.locator('#entry-boundary')).to_be_visible();shot('02-new-traveler')
            page.fill('#name','晨灯旅人 / Dawn');page.click('#join');expect(page.locator('#welcome')).to_be_hidden()
            expect(page.locator('#panel-journey')).to_be_visible();expect(page.locator('#panel-live')).to_be_hidden();expect(page.locator('#goal-title')).to_contain_text('守灯人');shot('03-player-goal-first')
            page.click('#tab-live');expect(page.locator('#panel-live')).to_be_visible();page.click('#tab-journey');checks['goal_first_with_separate_live_panel']=True
            page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(300)
            expect(page.locator('#journal')).to_be_hidden();role=page.locator('.world-bottom').bounding_box();dock=page.locator('.mobile-dock').bounding_box()
            assert role['y']+role['height']<=dock['y'],(role,dock)
            shot('04-mobile-scene');checks['mobile_hud_above_navigation']=True
            page.click('#dock-journey');expect(page.locator('#panel-journey')).to_be_visible();expect(page.locator('#tab-journey')).to_be_focused();shot('05-mobile-journal')
            page.keyboard.press('Escape');expect(page.locator('#journal')).to_be_hidden();expect(page.locator('#world')).to_be_focused()
            page.click('#dock-live');expect(page.locator('#panel-live')).to_be_visible();page.click('#panel-close');checks['mobile_panels_keyboard_and_focus_return']=True
            measurements=[]
            for width,height in [(320,640),(390,844),(768,480),(1024,768),(1440,960)]:
                page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(250)
                metrics=page.evaluate('''()=>{const c=document.querySelector('#world'),r=c.getBoundingClientRect(),labels=document.querySelector('.world-labels');return {width:innerWidth,overflow:document.documentElement.scrollWidth-innerWidth,aspectError:Math.abs(c.width/c.height-r.width/r.height),labelScale:labels.width/r.width}}''')
                assert metrics['overflow']<=1,metrics;assert metrics['aspectError']<.012,metrics;assert metrics['labelScale']>=1.9,metrics
                measurements.append(metrics)
            checks['aspect_correct_high_dpi_matrix']=measurements
            page.set_viewport_size({'width':390,'height':844});page.click('#language');page.wait_for_timeout(200);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');shot('06-mobile-english');page.click('#language')
            page.click('#goal-action');expect(page.locator('#activity-meter')).to_be_visible();shot('07-accepted-movement');expect(page.locator('#q1')).to_have_class('done',timeout=25000)
            for i in range(3):
                page.click('#goal-action');expect(page.locator('#inventory button.collected')).to_have_count(i+1,timeout=30000)
            expect(page.locator('#q2')).to_have_class('done',timeout=25000);page.click('#goal-action');expect(page.locator('#completion')).to_be_visible(timeout=25000)
            assert page.locator('#completion').evaluate('(el)=>el.open && el.tagName==="DIALOG"');shot('08-confirmed-result')
            page.keyboard.press('Escape');expect(page.locator('#completion')).to_be_hidden();checks['full_gameplay_and_native_result_dialog']=True
            page.reload(wait_until='domcontentloaded');expect(page.locator('#goal-step')).to_have_text('✓');expect(page.locator('#completion')).to_be_hidden();checks['authoritative_result_survives_refresh']=True
            assert not report['page_errors'],report['page_errors'];report['status']='passed'
        except Exception as error:
            report.update(status='failed',error=str(error));shot('failure')
        finally:context.close();browser.close()
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False),flush=True)
    if report['status']!='passed':raise SystemExit(1)
if __name__=='__main__':main()
