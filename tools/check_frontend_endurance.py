"""Bounded real-time client endurance. Explicitly not a server capacity benchmark."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse,json,sys,time,hashlib,statistics,traceback
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tests.live import LiveServer
from tools.check_sample_assets import Fixture
from tools.frontend_test_support import launch_browser,static_client

def hashes():
 return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in (ROOT/'lantern_hollow/web',ROOT/'examples/protocol-client') for p in folder.rglob('*') if p.is_file() and p.suffix in ('.js','.html','.css','.json','.png')}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=['quiet','active','dual'],required=True);parser.add_argument('--seconds',type=int,required=True);parser.add_argument('--output',required=True);args=parser.parse_args()
 if not 10<=args.seconds<=7200:parser.error('Bounded duration must be 10..7200 real seconds')
 out=ROOT/args.output;out.mkdir(parents=True,exist_ok=True);before=hashes();report={'mode':args.mode,'requested_seconds':args.seconds,'status':'running','samples':[],'page_errors':[],'model_calls':0,'scope':'Local browser client endurance on isolated fixtures; not cloud/server capacity or physical phones'}
 def save(): (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 with static_client(ROOT/'examples/protocol-client') as other,LiveServer(observer_origins=(other,)) as server,sync_playwright() as p:
  browser=launch_browser(p);report['browser']=browser.version;ctx=browser.new_context(viewport={'width':1280,'height':900});page=ctx.new_page();page.on('pageerror',lambda e:report['page_errors'].append(str(e)));actors=[];remote=None;requests={'official':0,'independent':0}
  try:
   count=2 if args.mode=='quiet' else 12;actors=[Fixture(server.url,'Endurance '+str(i),['traveler','sage','rose'][i%3]) for i in range(count)];page.goto(server.url+'/watch?role='+actors[0].role);expect(page.locator('#asset-status')).to_have_attribute('data-state','ready');expect(page.locator('#travelers [data-role]')).to_have_count(count)
   page.on('request',lambda q:requests.update(official=requests['official']+1) if q.url.endswith(('/watch/sync','/watch/session')) else None)
   pages=[('official',page)];sessions={}
   if args.mode=='dual':
    remote=browser.new_context(viewport={'width':1024,'height':800});viewer=remote.new_page();viewer.on('pageerror',lambda e:report['page_errors'].append(str(e)));viewer.goto(other);viewer.fill('#origin',server.url);viewer.locator('#connect button').click();expect(viewer.locator('#health')).to_have_attribute('data-state','ready');expect(viewer.locator('#art')).to_have_attribute('data-state','ready');viewer.on('request',lambda q:requests.update(independent=requests['independent']+1) if q.url.endswith(('/watch/sync','/watch/session')) else None);pages.append(('independent',viewer))
   for name,pg in pages:
    sessions[name]=pg.context.new_cdp_session(pg);sessions[name].send('Performance.enable');sessions[name].send('HeapProfiler.enable')
    pg.evaluate('()=>{window.__enduranceFrames=[];let previous=performance.now();const next=t=>{const d=t-previous;previous=t;if(d>0&&d<1000){__enduranceFrames.push(d);if(__enduranceFrames.length>512)__enduranceFrames.shift();}requestAnimationFrame(next);};requestAnimationFrame(next);}')
   world_map=actors[0].http.get('/play/map').json();blocked={tuple(t) for t in world_map['blocked']};targets=[(x,y) for y in range(15,22) for x in range(12,24) if (x,y) not in blocked];started=time.monotonic();cycle=0;next_sample=0;report.update(roles=count,clients=len(pages),started_at=time.time());save()
   while time.monotonic()-started<args.seconds:
    tick=time.monotonic();elapsed=tick-started
    if args.mode!='quiet':
     actor=actors[cycle%count];actor.act('town.say',{'text':'Controlled endurance cycle '+str(cycle)});target=targets[(cycle*7)%len(targets)];actor.act('town.move',dict(zip(('x','y'),target)))
     if cycle%9==0:actor.act('town.stop',{})
     if cycle%30==0:actor.act('town.interact',{'target':'bench'})
     if cycle%20==0:page.set_viewport_size({'width':390 if cycle%40==0 else 1280,'height':844 if cycle%40==0 else 900});page.locator('#return-role').click()
     if cycle%20==10:page.locator('#overview').click()
    if elapsed>=next_sample:
     sample={'elapsed_seconds':elapsed,'cycle':cycle,'requests':dict(requests),'clients':{}}
     for name,pg in pages:
      natural={m['name']:m['value'] for m in sessions[name].send('Performance.getMetrics')['metrics']};sessions[name].send('HeapProfiler.collectGarbage');metrics={m['name']:m['value'] for m in sessions[name].send('Performance.getMetrics')['metrics']}
      diag=pg.evaluate("async(name)=>{const url=name==='official'?document.querySelector('script[type=module]').src:new URL('./client.js',location.href).href;const module=await import(url);return name==='official'?module.frontendDiagnostics():module.diagnostics();}",name)
      state=pg.evaluate('()=>({nodes:document.querySelectorAll("*").length,frames:[...__enduranceFrames].sort((a,b)=>a-b),visibility:document.visibilityState})');frames=state.pop('frames');state.update(diag);state.update(natural_heap_bytes=natural.get('JSHeapUsedSize'),documents=metrics.get('Documents'),js_event_listeners=metrics.get('JSEventListeners'),task_duration_seconds=metrics.get('TaskDuration'),heap_bytes=metrics.get('JSHeapUsedSize'),frame_p95_ms=frames[int(.95*(len(frames)-1))] if frames else None)
      assert state['events']<=600,state;assert state['nodes']<8000,state;assert (state['heap_bytes'] or 0)<64*1024*1024,state
      if name=='official':assert state['pending']<=80 and state['showing']<=4 and state['seen']<=1200 and state['assetFrames']<=384 and state['particles']<=512,state
      sample['clients'][name]=state
     assert not report['page_errors'],report['page_errors'];report['samples'].append(sample);save();print(json.dumps({'mode':args.mode,'elapsed':round(elapsed),'cycles':cycle,'events':sample['clients']['official']['events'],'heap_mb':round(sample['clients']['official']['heap_bytes']/1048576,2)}),flush=True);next_sample=elapsed+30
     if int(elapsed)//300>=(len(report.get('screenshots',[]))):
      filename='phase-'+str(int(elapsed))+'.png';page.screenshot(path=str(out/filename),full_page=True);report.setdefault('screenshots',[]).append(filename)
    cycle+=1;page.wait_for_timeout(max(5,int((3-(time.monotonic()-tick))*1000)))
   growth={}
   if len(report['samples'])>=10:
    for name,_ in pages:
     early=report['samples'][2:7];late=report['samples'][-5:]
     early_heap=statistics.median(x['clients'][name]['heap_bytes'] for x in early);late_heap=statistics.median(x['clients'][name]['heap_bytes'] for x in late)
     frames=[x['clients'][name]['frame_p95_ms'] for x in late if x['clients'][name]['frame_p95_ms'] is not None];late_frames=statistics.median(frames) if frames else None
     growth[name]={'warmup_heap_bytes':early_heap,'final_heap_bytes':late_heap,'retained_heap_growth_bytes':late_heap-early_heap,'late_frame_p95_ms_median':late_frames}
     assert late_heap-early_heap<=8*1024*1024,growth
     assert late_frames is not None and late_frames<=80,growth
   report['growth_checks']=growth
   for name,_ in pages:assert requests[name]<args.seconds*3+30,requests
   report['requests']=requests
   report['sampling_note']='Every 30 seconds records natural heap before diagnostic GC and retained heap afterwards; not an uninstrumented memory benchmark'
   report.update(actual_seconds=time.monotonic()-started,cycles=cycle,final_at=time.time(),source_hashes=before,source_unchanged=before==hashes(),status='passed');assert report['source_unchanged'],'Source changed during endurance';assert not report['page_errors'];save();page.screenshot(path=str(out/'final.png'),full_page=True);print(json.dumps({k:v for k,v in report.items() if k not in ('samples','source_hashes','screenshots')}),flush=True)
  except Exception as exc:report.update(status='failed',error=str(exc),traceback=traceback.format_exc());save();raise
  finally:
   for a in actors:a.close()
   if remote:remote.close()
   ctx.close();browser.close()
if __name__=='__main__':main()
