"""Frontend fault injection against real temporary-server responses; no kernel edits."""
from pathlib import Path
import argparse,sys,json,time,hashlib,traceback
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tests.live import LiveServer
from tools.check_sample_assets import Fixture
from tools.frontend_test_support import launch_browser,static_client

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',default='test-results/fault-gate');args=p.parse_args();out=ROOT/args.output;out.mkdir(parents=True,exist_ok=True);cases={};errors=[]
 def record(name,value=True):cases[name]=value;(out/'report.json').write_text(json.dumps({'cases':cases,'page_errors':errors,'status':'running'},ensure_ascii=False,indent=2),encoding='utf-8');print(name,json.dumps(value),flush=True)
 with static_client(ROOT/'examples/protocol-client') as other,LiveServer(observer_origins=(other,)) as server,sync_playwright() as p:
  browser=launch_browser(p);ctx=browser.new_context(viewport={'width':1280,'height':900});page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)));a=Fixture(server.url,'Fault fixture','traveler')
  try:
   page.route('**/play/map',lambda rt:rt.fulfill(status=503,content_type='text/html',body='Temporary HTML outage'))
   page.goto(server.url+'/watch');expect(page.locator('#connection-problem')).to_be_visible();page.unroute('**/play/map');page.click('#retry-world');expect(page.locator('#asset-status')).to_have_attribute('data-state','ready');record('html_initial_failure_recovers')
   # A corrupt delta cannot replace the displayed public scope, and is reset.
   bad=[True];sentinel='DO_NOT_DISPLAY_PRIVATE';snapshots=[]
   page.on('request',lambda r:snapshots.append(r.url) if r.url.endswith('/watch/session') else None)
   def corrupt(rt):
    if not bad[0]:rt.continue_();return
    result=rt.fetch();body=result.json();key='snapshot' if body['view']['kind']=='snapshot' else 'delta';body['view'][key]['meta']['self']={'role_id':sentinel,'name':sentinel};bad[0]=False;rt.fulfill(response=result,json=body)
   page.route('**/watch/sync',corrupt);page.wait_for_timeout(2500);page.unroute('**/watch/sync');expect(page.locator('#connection')).not_to_have_class('connection offline');assert sentinel not in page.locator('body').inner_text();assert snapshots;record('invalid_public_scope_rejected_and_snapshot_reset')
   def cursor(rt):
    response=rt.fetch();body=response.json()
    if body['view']['kind']=='delta':body['view']['base_cursor']='not-the-current-cursor'
    rt.fulfill(response=response,json=body);page.unroute('**/watch/sync')
   page.route('**/watch/sync',cursor);page.wait_for_timeout(2500);expect(page.locator('#travelers [data-role]')).to_have_count(1);record('mismatched_delta_recovers')
   # Supported view version is explicit; future shapes must not render by accident.
   def version(rt):
    response=rt.fetch();body=response.json();body['view']['view_version']=999;rt.fulfill(response=response,json=body);page.unroute('**/watch/sync')
   page.route('**/watch/sync',version);page.wait_for_timeout(2500);expect(page.locator('#travelers [data-role]')).to_have_count(1);record('unknown_view_version_requires_reset')
   # Commit once, lose the Action response: the UI must recover the receipt.
   page.click('#join-mode');page.fill('#name','Fault UI');page.click('#join');expect(page.locator('#say')).to_be_enabled();assert page.url.endswith('/')
   actions=[]
   def lost(rt):actions.append(rt.request.post_data_json);rt.fetch();rt.abort()
   page.route('**/play/action',lost);page.click('#say');page.fill('#modal textarea','Committed once despite lost response');page.locator('#modal form button[type=submit]').click();expect(page.locator('#modal')).not_to_be_visible(timeout=15000);page.unroute('**/play/action');expect(page.locator('#timeline')).to_contain_text('Committed once despite lost response')
   assert len(actions)==1;assert page.locator('#timeline .event-text').filter(has_text='Committed once despite lost response').count()==1
   page.reload();expect(page.locator('#say')).to_be_enabled();expect(page.locator('#bubbles .bubble')).to_have_count(0);record('lost_response_single_action_receipt_and_reload')
   # Delayed reply after switching to a read-only route cannot restore control.
   held=[]
   def hold(rt):held.append((rt,rt.fetch()))
   page.route('**/play/sync',hold);page.wait_for_timeout(2000);assert held;page.click('#watch-mode');expect(page.locator('body')).to_have_class('spectating');assert page.url.endswith('/watch')
   for rt,res in held:rt.fulfill(response=res)
   page.unroute('**/play/sync');page.wait_for_timeout(200);expect(page.locator('#say')).not_to_be_visible();record('late_private_response_cannot_change_observer_mode')
   # Brief then longer real offline intervals; expired speech must not replay.
   for seconds in (5,30):
    ctx.set_offline(True);page.wait_for_timeout(200);expect(page.locator('#connection')).to_have_class('connection offline');a.act('town.say',{'text':'Offline-'+str(seconds)});page.wait_for_timeout(seconds*1000);ctx.set_offline(False);expect(page.locator('#connection')).not_to_have_class('connection offline',timeout=15000);expect(page.locator('#timeline')).to_contain_text('Offline-'+str(seconds))
    if seconds==30:expect(page.locator('#bubbles .bubble').filter(has_text='Offline-30')).to_have_count(0)
   record('real_5s_30s_offline_and_expired_speech')
   server.restart();expect(page.locator('#connection')).not_to_have_class('connection offline',timeout=15000);a.act('town.say',{'text':'After actual server restart'});expect(page.locator('#timeline')).to_contain_text('After actual server restart',timeout=15000);record('same_fixture_server_restart_recovers')
   # Fault resources never force creation of a replacement role.
   for name,route_url,handler in (
    ('manifest404','**/sample-assets.json',lambda rt:rt.fulfill(status=404)),
    ('png404','**/sample-atlas.png*',lambda rt:rt.fulfill(status=404)),
    ('pngCorrupt','**/sample-atlas.png*',lambda rt:rt.fulfill(status=200,content_type='image/png',body=b'not a PNG')),
    ('unknownManifest','**/sample-assets.json',lambda rt:rt.fulfill(json={'schema':'unknown/9'}))):
    broken=ctx.new_page();broken.on('pageerror',lambda e:errors.append(str(e)));broken.route(route_url,handler);broken.goto(server.url+'/watch');expect(broken.locator('#asset-status')).to_have_attribute('data-state','fallback');expect(broken.locator('#travelers [data-role]')).to_have_count(2);broken.close();record(name+'_declared_fallback')
   invalid=ctx.new_page()
   def unknown_map(rt):response=rt.fetch();body=response.json();body['presentation_version']=999;rt.fulfill(response=response,json=body)
   invalid.route('**/play/map',unknown_map);invalid.goto(server.url+'/watch');expect(invalid.locator('#connection-problem')).to_be_visible();expect(invalid.locator('#join-mode')).to_be_disabled();invalid.close();record('unknown_world_contract_not_rendered')
   denied=browser.new_context();denied.add_init_script("for(const name of ['localStorage','sessionStorage'])Object.defineProperty(window,name,{get(){throw new DOMException('Denied','SecurityError')}})");dp=denied.new_page();dp.on('pageerror',lambda e:errors.append(str(e)));dp.goto(server.url+'/watch');expect(dp.locator('#asset-status')).to_have_attribute('data-state','ready');expect(dp.locator('#travelers [data-role]')).to_have_count(2);denied.close();record('denied_optional_storage_does_not_break_public_client')
   # Independent implementation actually applies deltas and pages events.
   remote=browser.new_context();viewer=remote.new_page();traffic=[];viewer.on('pageerror',lambda e:errors.append(str(e)));viewer.on('request',lambda q:traffic.append((q.url,q.headers)));viewer.goto(other);viewer.fill('#origin',server.url);viewer.locator('#connect button').click();expect(viewer.locator('#health')).to_have_attribute('data-state','ready');expect(viewer.locator('#art')).to_have_attribute('data-state','ready');expect(viewer.locator('#health')).to_have_attribute('data-kind','delta',timeout=10000)
   a.act('town.say',{'text':'Independent delta client sees this'});expect(viewer.locator('#events')).to_contain_text('Independent delta client sees this',timeout=10000);assert remote.cookies()==[];assert all('authorization' not in h and 'cookie' not in h for url,h in traffic if url.startswith(server.url));assert all('/bridge/' not in url and '/static/app.js' not in url and '/static/render.js' not in url for url,_ in traffic)
   remote.set_offline(True);viewer.wait_for_timeout(200);remote.set_offline(False);expect(viewer.locator('#health')).to_have_attribute('data-state','ready',timeout=15000);viewer.screenshot(path=str(out/'independent-protocol.png'),full_page=True);remote.close();record('independent_delta_feed_materials_reconnect_no_internal_import')
   assert not errors,errors;(out/'report.json').write_text(json.dumps({'status':'passed','cases':cases,'page_errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
  except Exception:
   page.screenshot(path=str(out/'failure.png'),full_page=True);raise
  finally:a.close();ctx.close();browser.close()
if __name__=='__main__':main()
