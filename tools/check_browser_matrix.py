"""Four-engine frontend gate; fixed browser binaries are reported, never inferred."""
from pathlib import Path
import argparse,json,sys,time,traceback,os
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tests.live import LiveServer
from tools.check_sample_assets import Fixture,clip
from tools.frontend_test_support import launch_browser,static_client

def inspect_labels(page):
    labels=page.locator('#world').get_attribute('data-nameplates');items=json.loads(labels or '[]')
    for i,a in enumerate(items):
        for b in items[i+1:]:assert a['x']+a['w']<=b['x'] or b['x']+b['w']<=a['x'] or a['y']+a['h']<=b['y'] or b['y']+b['h']<=a['y'],items
    return len(items)

def run_browser(name,out,axe):
    result={'browser':name,'status':'running','checks':{},'page_errors':[]};checks=result['checks']
    with static_client(ROOT/'examples/observer') as other,static_client(ROOT/'examples/protocol-client') as protocol,LiveServer(observer_origins=(other,protocol)) as server,sync_playwright() as p:
        browser=launch_browser(p,name);result['version']=browser.version
        context=browser.new_context(viewport={'width':1280,'height':900});page=context.new_page();page.on('pageerror',lambda e:result['page_errors'].append(str(e)))
        a=Fixture(server.url,'长名字的旅人甲abcdefghij','sage');b=Fixture(server.url,'A neighboring long name','rose')
        try:
            page.goto(server.url+'/watch?role='+a.role);expect(page.locator('#asset-status')).to_have_attribute('data-state','ready');expect(page.locator('#travelers [data-role]')).to_have_count(2)
            for f,target in ((a,[16,21]),(b,[18,21])):f.act('town.move',dict(zip(('x','y'),target)));f.idle()
            page.wait_for_timeout(1700);page.click('#overview');checks['adjacent_nameplates_nonoverlap']=inspect_labels(page);page.screenshot(path=str(out/(name+'-names.png')),full_page=True)
            a.act('town.say',{'text':'甲向乙公开说话 <b>not HTML</b>','to_role_id':b.role});clip(page,a.role,'talk');expect(page.locator('#timeline')).to_contain_text('not HTML');assert page.locator('#timeline b').count()==0
            checks['authored_speech_safe_text']=True
            # Use the real player interface, not only the HTTP fixture, to join and submit.
            page.click('#join-mode');page.fill('#name','UI '+name);page.click('#join');expect(page.locator('#say')).to_be_enabled()
            page.click('#say');page.fill('#modal textarea','Typed from '+name);page.locator('#modal form button[type=submit]').click();expect(page.locator('#modal')).not_to_be_visible();expect(page.locator('#timeline')).to_contain_text('Typed from '+name)
            checks['player_join_and_composer']=True
            page.goto(server.url+'/');expect(page.locator('#say')).to_be_enabled();expect(page.locator('#bubbles .bubble')).to_have_count(0);checks['player_refresh_and_no_old_bubbles']=True
            # Complete the reference gameplay through visible UI controls.
            page.click('#quest-action');expect(page.locator('#q1')).to_have_class('done',timeout=25000)
            for i in range(3):page.click('#quest-action');expect(page.locator('#inventory button.collected')).to_have_count(i+1,timeout=30000)
            expect(page.locator('#q2')).to_have_class('done',timeout=25000);page.click('#quest-action');expect(page.locator('#completion')).to_be_visible(timeout=25000);page.click('#complete-close');checks['visible_quest_and_result']=True
            page.click('#help');expect(page.locator('#modal')).to_be_visible();page.keyboard.press('Escape');expect(page.locator('#modal')).not_to_be_visible();checks['native_dialog_keyboard']=True
            page.click('#watch-mode');expect(page.locator('body')).to_have_class('spectating');expect(page.locator('#say')).not_to_be_visible()
            for width in (320,390,768,1024,1440,1920):
                page.set_viewport_size({'width':width,'height':900});page.wait_for_timeout(100);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),width;inspect_labels(page)
            page.set_viewport_size({'width':390,'height':844});page.click('#language');page.wait_for_timeout(100);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');page.screenshot(path=str(out/(name+'-mobile-en.png')),full_page=True);page.click('#language');checks['responsive_and_language']=True
            page.set_viewport_size({'width':1280,'height':900})
            for zoom in (1.25,1.5,2):
                page.evaluate('(z)=>document.documentElement.style.zoom=z',zoom);page.wait_for_timeout(150);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+2'),zoom
            page.evaluate('document.documentElement.style.zoom="1"');checks['css_zoom_reflow_125_150_200']=True
            if axe:
                audits={}
                for state in ('watch','help'):
                    if state=='help':page.click('#help')
                    page.evaluate(axe.read_text(encoding='utf-8'))
                    audits[state]=page.evaluate('async()=>{const r=await axe.run(document,{runOnly:{type:"tag",values:["wcag2a","wcag2aa","wcag21aa"]}});return {violations:r.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))})),incomplete:r.incomplete.map(v=>({id:v.id,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary,checks:[...n.any,...n.all,...n.none].map(c=>({id:c.id,message:c.message,data:c.data}))}))}))}}')
                (out/(name+'-axe.json')).write_text(json.dumps(audits,ensure_ascii=False,indent=2),encoding='utf-8');checks['axe_violations']={k:len(v['violations']) for k,v in audits.items()};page.keyboard.press('Escape');assert not any(v['violations'] for v in audits.values()),audits
            gallery=context.new_page();gallery.on('pageerror',lambda e:result['page_errors'].append(str(e)));gallery.goto(server.url+'/static/art-gallery.html');expect(gallery.locator('#status')).to_have_attribute('data-state','ready');gallery.click('[data-clip=walk]');gallery.emulate_media(reduced_motion='reduce');gallery.wait_for_timeout(150);data=[gallery.locator('#characters canvas').first.evaluate('(c)=>c.toDataURL()') for _ in range(3)];assert len(set(data))==1;checks['gallery_reduced_motion']=True;gallery.close()
            remote=browser.new_context();viewer=remote.new_page();viewer.goto(other);viewer.fill('#origin',server.url);viewer.click('#connect button');expect(viewer.locator('#health')).to_have_attribute('data-assets','ready');assert remote.cookies()==[];checks['independent_material_read']=True;remote.close()
            independent=browser.new_context();ip=independent.new_page();ip.on('pageerror',lambda e:result['page_errors'].append(str(e)));ip.goto(protocol);ip.fill('#origin',server.url);ip.locator('#connect button').click();expect(ip.locator('#art')).to_have_attribute('data-state','ready');expect(ip.locator('#health')).to_have_attribute('data-kind','delta',timeout=12000);a.act('town.say',{'text':'Protocol delta '+name});expect(ip.locator('#events')).to_contain_text('Protocol delta '+name);assert independent.cookies()==[];checks['independent_protocol_delta_feed']=True;independent.close()
            assert not result['page_errors'],result['page_errors'];result['status']='passed'
        except Exception as e:result['status']='failed';result['error']=str(e);result['traceback']=traceback.format_exc();page.screenshot(path=str(out/(name+'-failure.png')),full_page=True)
        finally:a.close();b.close();context.close();browser.close()
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--browsers',default='chromium,edge,firefox,webkit');parser.add_argument('--axe');parser.add_argument('--output',default='test-results/browser-matrix');args=parser.parse_args();out=ROOT/args.output;out.mkdir(parents=True,exist_ok=True);results=[]
    for name in args.browsers.split(','):
        print('START',name,flush=True)
        try:r=run_browser(name,out,Path(args.axe) if args.axe else None)
        except Exception as e:r={'browser':name,'status':'failed','error':str(e),'traceback':traceback.format_exc()}
        results.append(r);(out/'report.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(r,ensure_ascii=False),flush=True)
    if any(r['status']!='passed' for r in results):raise SystemExit(1)
if __name__=='__main__':main()
