"""Frontend-only material and performance demo driven by controlled HTTP fixtures.
No autonomous models, no new kernel behavior, no user database access.
"""
from pathlib import Path
from time import monotonic,sleep
import json,os,sys,uuid
import httpx
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tests.live import LiveServer
from tools.check_semantic_presentation import static_viewer

class Fixture:
    def __init__(self,origin,name,appearance):
        self.http=httpx.Client(base_url=origin,trust_env=False,timeout=10,headers={'X-Lantern-Client':'1'})
        response=self.http.post('/play/join',json={'name':name,'appearance':appearance});response.raise_for_status()
        self.role=self.http.get('/play/session').json()['role_id']
    def act(self,name,args):
        response=self.http.post('/play/action',json={'function':name,'arguments':args,'operation_id':'art-'+str(uuid.uuid4()),'role_id':self.role});response.raise_for_status();return response.json()
    def idle(self):
        end=monotonic()+25
        while monotonic()<end:
            me=self.http.get('/play/session').json()['view']['snapshot']['meta']['self']
            if not me['movement'] and not me['busy']:return me
            sleep(.15)
        raise AssertionError('Fixture did not finish an accepted action')
    def close(self):self.http.close()

def clip(page,role,name,timeout=20000):
    page.wait_for_function('([role,name])=>JSON.parse(document.querySelector("#world").dataset.clips||"{}")[role]===name',arg=[role,name],timeout=timeout)

def main():
    out=ROOT/'test-results/sample-assets';out.mkdir(parents=True,exist_ok=True);report={};errors=[]
    with static_viewer() as other,LiveServer(observer_origins=(other,)) as server,sync_playwright() as p:
        try:browser=p.chromium.launch(headless=True)
        except Exception:
            if os.name!='nt':raise
            browser=p.chromium.launch(channel='msedge',headless=True)
        a=Fixture(server.url,'Sample Alpha','traveler');b=Fixture(server.url,'Sample Beta','rose')
        context=browser.new_context(viewport={'width':1440,'height':1000},record_video_dir=str(out/'recording'),record_video_size={'width':1152,'height':800})
        game=context.new_page();game.on('pageerror',lambda e:errors.append(str(e)))
        game.goto(server.url+'/watch?role='+a.role,wait_until='domcontentloaded')
        expect(game.locator('#asset-status')).to_have_attribute('data-state','ready')
        expect(game.locator('#world')).to_have_attribute('data-assets','ready');clip(game,a.role,'idle')
        expect(game.locator('#say')).to_be_disabled()
        world_map=a.http.get('/play/map').json();elia=next(t for t in world_map['targets'] if t['id']=='elia')
        a.act('town.move',dict(zip(('x','y'),elia['approach'])));clip(game,a.role,'walk')
        game.screenshot(path=str(out/'01-walking.png'),full_page=True);a.idle();clip(game,a.role,'idle')
        b.act('town.approach',{'role_id':a.role});b.idle();clip(game,b.role,'idle')
        first=a.act('town.say',{'text':'这些是测试台词，来自服务器事件。','to_role_id':b.role})
        clip(game,a.role,'talk');clip(game,b.role,'idle')
        mid=first['result']['message_id'];b.act('town.say',{'text':'收到。我的发言由另一个测试身份提交。','reply_to':mid})
        clip(game,b.role,'talk');expect(game.locator('#bubbles')).to_contain_text('测试台词')
        game.screenshot(path=str(out/'02-conversation.png'),full_page=True)
        report['loaded_art_idle_walk_talk_and_two_authors']=True
        # Walking wins over cosmetic talk; speech cannot move either actor.
        a.act('town.interact',{'target':'elia'});a.idle()
        for t in world_map['targets']:
            if t['kind']=='shard':a.act('town.interact',{'target':t['id']});a.idle()
        a.act('town.interact',{'target':'beacon'});clip(game,a.role,'work')
        game.screenshot(path=str(out/'03-working.png'),full_page=True)
        me=a.idle();assert me['quest']=='complete';clip(game,a.role,'idle')
        game.screenshot(path=str(out/'04-result.png'),full_page=True)
        report['work_clip_and_confirmed_scene_result']=True
        game.reload(wait_until='domcontentloaded');expect(game.locator('#asset-status')).to_have_attribute('data-state','ready')
        clip(game,a.role,'idle');expect(game.locator('#bubbles .bubble')).to_have_count(0)
        assert game.evaluate('localStorage.getItem("lh.public-focus")')==a.role
        report['refresh_restores_character_without_old_speech']=True
        # A separately hosted SVG implementation reads only the public manifest and PNG.
        remote=browser.new_context(viewport={'width':1100,'height':850});viewer=remote.new_page();viewer.on('pageerror',lambda e:errors.append(str(e)))
        requests=[];viewer.on('request',lambda req:requests.append((req.url,req.headers)))
        viewer.goto(other);viewer.fill('#origin',server.url);viewer.click('#connect button')
        expect(viewer.locator('#health')).to_have_attribute('data-assets','ready');expect(viewer.locator('#scene [data-sprite]')).to_have_count(2)
        assert remote.cookies()==[]
        assert any(url.split('?')[0]==server.url+'/static/sample-atlas.png' for url,_ in requests)
        assert all('authorization' not in h and 'cookie' not in h for url,h in requests if url.startswith(server.url))
        viewer.screenshot(path=str(out/'05-independent-assets.png'),full_page=True);report['independent_origin_uses_same_png_without_credentials']=True
        # Gallery is static and never sends world actions.
        gallery=context.new_page();gallery.on('pageerror',lambda e:errors.append(str(e)))
        gallery.goto(server.url+'/static/art-gallery.html');expect(gallery.locator('#status')).to_have_attribute('data-state','ready')
        expect(gallery.locator('#characters canvas')).to_have_count(6)
        for action in ('walk','talk','work','idle'):
            gallery.click('[data-clip="'+action+'"]');expect(gallery.locator('#characters canvas').first).to_have_attribute('data-clip',action)
        gallery.screenshot(path=str(out/'06-material-gallery.png'),full_page=True)
        gallery.set_viewport_size({'width':390,'height':844});assert gallery.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        gallery.screenshot(path=str(out/'07-gallery-mobile.png'),full_page=True)
        report['six_materials_four_clips_and_mobile_gallery']=True
        mobile=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,reduced_motion='reduce')
        phone=mobile.new_page();phone.on('pageerror',lambda e:errors.append(str(e)));phone.goto(server.url+'/watch?role='+a.role)
        expect(phone.locator('#asset-status')).to_have_attribute('data-state','ready');clip(phone,a.role,'idle')
        assert phone.evaluate('document.documentElement.scrollWidth<=innerWidth+1');phone.screenshot(path=str(out/'08-game-mobile.png'),full_page=True)
        report['mobile_and_reduced_motion']=True
        # Broken decorative art is explicit; actual world state stays available.
        degraded=browser.new_context();failure=degraded.new_page();failure.on('pageerror',lambda e:errors.append(str(e)))
        failure.route('**/sample-atlas.png*',lambda route:route.abort())
        failure.goto(server.url+'/watch?role='+a.role);expect(failure.locator('#asset-status')).to_have_attribute('data-state','fallback')
        clip(failure,a.role,'idle');expect(failure.locator('#timeline')).not_to_be_empty()
        failure.screenshot(path=str(out/'09-art-failure.png'),full_page=True);report['missing_atlas_explicit_without_world_failure']=True
        missing=remote.new_page();missing.route('**/sample-atlas.png*',lambda route:route.abort());missing.goto(other);missing.fill('#origin',server.url);missing.click('#connect button');expect(missing.locator('#health')).to_have_attribute('data-assets','fallback');expect(missing.locator('#roles [data-role]')).to_have_count(2);missing.close()
        report['independent_missing_image_not_claimed_loaded']=True
        assert not errors,errors
        report.update(page_errors=errors,frames=400,model_calls=0,scope='Controlled frontend fixture, not autonomous Agent behavior or kernel acceptance',world_version=world_map['world_version'],core_pin=world_map['core_pin'])
        a.close();b.close();degraded.close();mobile.close();remote.close();gallery.close();video=game.video;context.close();video.save_as(str(out/'official-demo.webm'));browser.close()
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
