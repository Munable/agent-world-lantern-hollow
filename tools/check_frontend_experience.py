"""Experience regressions plus bounded sustained frontend exercise on disposable data.
This tests UI with controlled actors, never autonomous models or a production DB.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from time import monotonic,sleep
import argparse,json,os,sys
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tests.live import LiveServer
from tools.check_sample_assets import Fixture
from tools.check_semantic_presentation import static_viewer

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--soak-seconds',type=int,default=120);parser.add_argument('--output',default='test-results/experience-audit');args=parser.parse_args()
    if not 0<=args.soak_seconds<=300:parser.error('Use a bounded 0..300-second soak')
    out=ROOT/args.output;out.mkdir(parents=True,exist_ok=True);report={'scope':'Frontend-only controlled fixtures; mobile/zoom are browser emulation, not physical devices','cases':{},'page_errors':[],'screenshots':[]};started=monotonic()
    def record(name,data=True):
        report['cases'][name]=data;(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(name,json.dumps(data,ensure_ascii=False),flush=True)
    def shot(page,name):
        page.screenshot(path=str(out/(name+'.png')),full_page=True);report['screenshots'].append(name+'.png')
    def watch(page):page.on('pageerror',lambda e:report['page_errors'].append(str(e)))
    def bubbles(page):
        data=page.locator('#bubbles .bubble:visible').evaluate_all('(els)=>els.map(e=>({text:e.querySelector(".sr-only").textContent,...Object.fromEntries(["left","top","right","bottom"].map(k=>[k,e.getBoundingClientRect()[k]]))}))')
        bounds=page.locator('#world').bounding_box();assert bounds
        for a in data:assert a['left']>=bounds['x']-1 and a['right']<=bounds['x']+bounds['width']+1 and a['top']>=bounds['y']-1 and a['bottom']<=bounds['y']+bounds['height']+1,data
        for i,a in enumerate(data):
            for b in data[i+1:]:assert a['right']<=b['left'] or b['right']<=a['left'] or a['bottom']<=b['top'] or b['bottom']<=a['top'],data
        return len(data)
    with static_viewer() as other,LiveServer(observer_origins=(other,)) as server,sync_playwright() as p:
        try:browser=p.chromium.launch(headless=True)
        except Exception:
            if os.name!='nt':raise
            browser=p.chromium.launch(channel='msedge',headless=True)
        context=browser.new_context(viewport={'width':1280,'height':850});page=context.new_page();watch(page)
        actors=[];remote=None
        try:
            page.route('**/play/map',lambda route:route.fulfill(status=503,content_type='application/json',body='{"message":"test outage"}'))
            page.goto(server.url+'/watch');expect(page.locator('#connection-problem')).to_be_visible();expect(page.locator('#retry-world')).to_be_enabled();shot(page,'01-initial-outage')
            page.unroute('**/play/map');page.click('#retry-world');expect(page.locator('#world')).to_have_attribute('data-assets','ready');expect(page.locator('#connection-problem')).to_be_hidden();record('first_load_outage_user_retry')
            actors=[Fixture(server.url,'Crowded traveler name '+str(i),['traveler','sage','rose'][i%3]) for i in range(6)]
            page.goto(server.url+'/watch?role='+actors[0].role);expect(page.locator('#travelers [data-role]')).to_have_count(6)
            expect(page.locator('#world')).to_have_attribute('data-assets','ready');shot(page,'02-crowd-idle')
            snapshot=actors[0].http.get('/watch/session').json()['view']['snapshot'];world_map=actors[0].http.get('/play/map').json()
            page.wait_for_timeout(700)  # Allow the local follow-camera easing to settle before hit geometry.
            positions=page.evaluate("""async ({entities,map,role})=>{
             const {travelerLayout}=await import('/static/ui-layout.js');const {SceneCamera}=await import('/static/camera.js');
             const canvas=document.querySelector('#world'),r=canvas.getBoundingClientRect();
             const camera=new SceneCamera(map.width*16,map.height*16);camera.setViewport(canvas.width,canvas.height);camera.follow(role);camera.track(18*16+8,21*16+2);
             return travelerLayout(Object.values(entities),a=>({x:a.position[0],y:a.position[1]}),map.width).map(p=>{const q=camera.project((p.x+.5)*16,(p.y+.1)*16);return {role:p.actor.role_id,name:p.actor.name,x:r.x+q.x*r.width/canvas.width,y:r.y+q.y*r.height/canvas.height};});
            }""",{'entities':snapshot['entities'],'map':world_map,'role':actors[0].role})
            for target in positions:
                page.mouse.click(target['x'],target['y']);expect(page.locator('#modal-title')).to_have_text(target['name']);page.click('#modal-close')
            record('all_six_colocated_sprites_hit_correct_identity',len(positions))
            page.locator('#travelers [data-role]').nth(3).dblclick();expect(page.locator('#modal')).to_be_visible();page.click('#modal-close');record('roster_double_click_survives_selection_update')
            # Six long simultaneous messages; full text remains in retained history.
            def burst(prefix):
                with ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(lambda pair:pair[1].act('town.say',{'text':prefix+str(pair[0])+' '+('Readable public message. '*7)[:145]}),enumerate(actors)))
            burst('desktop-');page.wait_for_timeout(1900);count=bubbles(page);assert count>0;shot(page,'03-crowd-speech');record('desktop_bubbles_bounded_nonoverlap',count)
            page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(100);assert bubbles(page)<=2;expect(page.locator('#speech-overflow')).to_be_visible();shot(page,'04-mobile-speech')
            page.click('#speech-overflow');expect(page.locator('#event-filter')).to_have_value('speech');record('crowd_overflow_has_full_history_entry')
            page.click('#dock-scene');page.click('#join-mode');expect(page.locator('#name')).to_be_visible();expect(page.locator('#bubbles .bubble:visible')).to_have_count(0);shot(page,'05-entry_form_not_obscured');page.click('#join-mode');record('entry_form_not_covered_by_speech')
            page.set_viewport_size({'width':1280,'height':850});page.select_option('#event-filter','all')
            row=page.locator('#travelers [data-role]').nth(2);row.focus();active=row.get_attribute('data-role');actors[0].act('town.say',{'text':'Focus must survive a different actor update'});page.wait_for_timeout(1700)
            assert page.evaluate('document.activeElement.dataset.role')==active;record('keyboard_focus_survives_live_roster_update')
            for i in range(12):actors[i%6].act('town.say',{'text':'History '+str(i)+' '+('long public text '*5)});page.wait_for_timeout(220)
            page.wait_for_timeout(1700);page.locator('#timeline').evaluate('(el)=>el.scrollTop=20');before=page.locator('#timeline').evaluate('(el)=>el.scrollTop')
            actors[1].act('town.say',{'text':'An appended message must not scroll someone reading older entries'});page.wait_for_timeout(1700)
            after=page.locator('#timeline').evaluate('(el)=>el.scrollTop');assert abs(after-before)<2,(before,after);expect(page.locator('#timeline-new')).to_be_visible();shot(page,'06-reading_position');record('appended_history_preserves_reader_position',{'before':before,'after':after})
            page.click('#timeline-new');assert page.locator('#timeline').evaluate('(e)=>e.scrollHeight-e.clientHeight-e.scrollTop<3');expect(page.locator('#timeline-new')).to_be_hidden();record('new_records_badge_returns_to_latest')
            # Real input, not direct calls: a delayed submission must not close a newer dialog.
            page.click('#join-mode');page.fill('#name','UI keyboard tester');page.click('[data-appearance="sage"]');page.click('#join');expect(page.locator('#say')).to_be_enabled()
            page.click('#say');expect(page.locator('#modal textarea')).to_be_focused();page.locator('#modal textarea').fill('Typed once, with a delayed response. <b>not markup</b>')
            typing=[];page.on('request',lambda req:typing.append(req.url) if req.url.endswith('/play/action') else None);page.locator('#modal textarea').press_sequentially(' wasd e',delay=60);assert not typing;record('typing_movement_letters_does_not_control_world')
            paused=[]
            def delay_response(route):paused.append((route,route.fetch()))
            page.route('**/play/action',delay_response);page.locator('#modal form button[type=submit]').click()
            deadline=monotonic()+10
            while not paused and monotonic()<deadline:page.wait_for_timeout(50)
            assert len(paused)==1,'Expected exactly one completed interception before releasing the delayed response'
            page.click('#modal-close');page.click('#help');title=page.locator('#modal-title').inner_text();paused[0][0].fulfill(response=paused[0][1]);page.unroute('**/play/action');page.wait_for_timeout(500)
            expect(page.locator('#modal')).to_be_visible();expect(page.locator('#modal-title')).to_have_text(title);page.click('#modal-close');record('late_action_response_does_not_close_new_dialog')
            expect(page.locator('#timeline')).to_contain_text('Typed once, with a delayed response.');assert page.locator('#timeline b').count()==0
            # Pausing the network never creates a fake reply; reconnect uses current state.
            page.click('#watch-mode');expect(page.locator('body')).to_have_class('spectating')
            context.set_offline(True);page.wait_for_timeout(300);expect(page.locator('#connection')).to_have_class('connection offline');shot(page,'07-offline')
            actors[0].act('town.interact',{'target':'bench'});actors[0].idle();context.set_offline(False)
            expect(page.locator('#connection')).not_to_have_class('connection offline',timeout=15000);expect(page.locator('#timeline')).to_contain_text('歇一会儿',timeout=15000);shot(page,'08-reconnected');record('offline_world_change_and_reconnect')
            # Different sizes and language without horizontal page overflow.
            widths=[(320,640),(390,844),(768,600),(1024,768),(1920,1080)]
            for width,height in widths:
                page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(120)
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(width,page.evaluate('document.documentElement.scrollWidth'))
                shot(page,'viewport-'+str(width))
            page.set_viewport_size({'width':390,'height':844});page.click('#language');page.wait_for_timeout(150);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');shot(page,'09-mobile-english');page.click('#language')
            record('responsive_sizes_and_english',widths)
            # A single long utterance offers access to its full text, not only crowd overflow.
            page.click('#dock-live');page.locator('#travelers [data-role="'+actors[2].role+'"]').click();page.click('#dock-scene')
            page.wait_for_timeout(8500);actors[2].act('town.say',{'text':'Single long utterance '+('read the complete text. '*7)[:137]})
            page.wait_for_timeout(1800);expect(page.locator('#speech-overflow')).to_be_visible();page.click('#speech-overflow');expect(page.locator('#timeline')).to_contain_text('Single long utterance');record('single_truncated_bubble_has_full_text_entry')
            # Broken decoration is explicit without abandoning the world connection.
            bad=browser.new_page();watch(bad);bad.route('**/sample-assets.json',lambda route:route.fulfill(status=200,content_type='application/json',body='{"schema":"unknown/999"}'))
            bad.goto(server.url+'/watch');expect(bad.locator('#asset-status')).to_have_attribute('data-state','fallback');expect(bad.locator('#travelers [data-role]')).to_have_count(7);shot(bad,'10-invalid-art');bad.close();record('invalid_asset_manifest_safe_fallback')
            remote=browser.new_context(viewport={'width':1000,'height':780});viewer=remote.new_page();watch(viewer);viewer.goto(other);viewer.fill('#origin',server.url);viewer.click('#connect button');expect(viewer.locator('#health')).to_have_attribute('data-assets','ready');assert not remote.cookies();record('independent_viewer_still_connected')
            page.set_viewport_size({'width':1280,'height':850});page.reload();expect(page.locator('#world')).to_have_attribute('data-assets','ready')
            # Bounded extended exercise: many ordinary cycles, not a server capacity test.
            soak_start=monotonic();cycles=0;shots=0
            while monotonic()-soak_start<args.soak_seconds:
                actor=actors[cycles%6]
                actor.act('town.say',{'text':'Sustained UI cycle '+str(cycles)+'; this is a controlled test message.'})
                actor.act('town.interact',{'target':['bench','fern','rowan'][cycles%3]})
                if cycles%3==0:actor.act('town.stop',{})
                if cycles%5==0:
                    page.click('#overview');page.click('#return-role');page.set_viewport_size({'width':390 if cycles%10==0 else 1280,'height':844})
                page.wait_for_timeout(2200);assert len(report['page_errors'])==0;assert page.locator('#bubbles .bubble').count()<=4;assert page.locator('#timeline li').count()<=600
                if cycles in (0,20,40):shot(page,'soak-'+str(cycles));shots+=1
                cycles+=1
            record('sustained_frontend_exercise',{'elapsed_seconds':monotonic()-soak_start,'cycles':cycles,'roles':7,'simultaneous_clients':2,'timeline_rows':page.locator('#timeline li').count(),'page_errors':len(report['page_errors'])})
            if args.soak_seconds>=90:
                page.reload();
                if page.locator('#dock-live').is_visible():page.click('#dock-live')
                expect(page.locator('#load-history')).to_be_visible();page.locator('#timeline').evaluate('(el)=>el.scrollTop=20')
                old=page.locator('#timeline').evaluate('(el)=>{const t=el.getBoundingClientRect().top,c=[...el.children].find(c=>c.getBoundingClientRect().bottom>t);return {id:c.dataset.eventId,offset:c.getBoundingClientRect().top-t};}')
                page.click('#load-history');page.wait_for_timeout(500)
                new=page.locator('#timeline').evaluate('(el,id)=>{const c=[...el.children].find(c=>c.dataset.eventId===id);return c.getBoundingClientRect().top-el.getBoundingClientRect().top;}',old['id'])
                assert abs(new-old['offset'])<2,(old,new);record('prepending_older_history_preserves_visible_anchor')
            gallery=browser.new_page();watch(gallery);gallery.goto(server.url+'/static/art-gallery.html');expect(gallery.locator('#status')).to_have_attribute('data-state','ready');gallery.click('[data-clip=walk]');gallery.emulate_media(reduced_motion='reduce');expect(gallery.locator('#pause')).to_have_attribute('aria-pressed','true')
            first=gallery.locator('#characters canvas').first.evaluate('(c)=>c.toDataURL()');gallery.wait_for_timeout(350);assert first==gallery.locator('#characters canvas').first.evaluate('(c)=>c.toDataURL()');gallery.screenshot(path=str(out/'11-reduced-motion-gallery.png'),full_page=True);gallery.close();record('changing_reduced_motion_freezes_gallery_pixels')
            assert not report['page_errors'],report['page_errors'];record('overall_completed',True)
        finally:
            report['total_seconds']=monotonic()-started;(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
            for a in actors:a.close()
            if remote:remote.close()
            context.close();browser.close()

if __name__=='__main__':main()
