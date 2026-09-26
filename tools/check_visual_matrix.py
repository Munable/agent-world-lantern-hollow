"""Real-browser layout matrix using only accepted fixture coordinates."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import sys,json,argparse
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tests.live import LiveServer
from tools.check_sample_assets import Fixture
from tools.frontend_test_support import launch_browser

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',default='test-results/visual-matrix');args=parser.parse_args();out=ROOT/args.output;out.mkdir(parents=True,exist_ok=True);results=[]
 with sync_playwright() as p:
  browser=launch_browser(p)
  for n in (1,2,6,12):
   with LiveServer() as server:
    actors=[Fixture(server.url,('长中文名字旅人'+str(i)+'abcdefghijk')[:24] if i%2==0 else ('Long neighboring name '+str(i))[:24],['traveler','sage','rose'][i%3]) for i in range(n)];ctx=browser.new_context();page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(server.url+'/watch?role='+actors[0].role);expect(page.locator('#asset-status')).to_have_attribute('data-state','ready');expect(page.locator('#travelers [data-role]')).to_have_count(n)
    m=actors[0].http.get('/play/map').json();blocked={tuple(x) for x in m['blocked']};free=[(x,y) for y in range(17,22) for x in range(12,25) if (x,y) not in blocked]
    for mode in ('same','adjacent','spread'):
     targets=[(18,21)]*n if mode=='same' else sorted(free,key=lambda p:abs(p[0]-18)+abs(p[1]-21))[:n] if mode=='adjacent' else free[::max(1,len(free)//n)][:n]
     with ThreadPoolExecutor(max_workers=12) as pool:list(pool.map(lambda pair:pair[0].act('town.move',dict(zip(('x','y'),pair[1]))),zip(actors,targets)))
     for a in actors:a.idle()
     page.wait_for_timeout(1700)
     for width in (320,390,768,1280,1920):
      page.set_viewport_size({'width':width,'height':900})
      for camera in ('overview','follow','max'):
       page.click('#overview')
       if camera=='follow':page.click('#return-role')
       if camera=='max':
        for _ in range(7):page.click('#zoom-in')
       page.wait_for_timeout(80);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
       boxes=json.loads(page.locator('#world').get_attribute('data-nameplates') or '[]');viewport=page.locator('#world').evaluate('(c)=>({width:c.width,height:c.height})')
       for i,a in enumerate(boxes):
        assert 0<=a['x'] and a['x']+a['w']<=viewport['width']+.001 and 0<=a['y'] and a['y']+a['h']<=viewport['height']+.001
        for b in boxes[i+1:]:assert a['x']+a['w']<=b['x'] or b['x']+b['w']<=a['x'] or a['y']+a['h']<=b['y'] or b['y']+b['h']<=a['y'],(n,mode,width,camera,boxes)
       results.append({'roles':n,'distribution':mode,'width':width,'camera':camera,'labels':len(boxes)})
       if n in (2,12) and mode=='adjacent' and width in (390,1280) and camera in ('overview','follow'):page.screenshot(path=str(out/f'{n}-{mode}-{width}-{camera}.png'),full_page=True)
    assert not errors;ctx.close()
    for a in actors:a.close()
  browser.close()
 (out/'report.json').write_text(json.dumps({'status':'passed','cases':results,'count':len(results),'scope':'Real fixture positions, browser layouts; hidden names remain accessible in roster'},indent=2),encoding='utf-8');print('Visual matrix PASS',len(results),flush=True)
if __name__=='__main__':main()
