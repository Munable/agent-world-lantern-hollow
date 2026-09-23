"""Actual MCP calls observed by the game and an independent cross-origin SVG client.
This is a deterministic protocol/browser test, not a model autonomy benchmark.
"""
from __future__ import annotations
import asyncio
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import json
import os
from pathlib import Path
import sys
from threading import Thread
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tests.live import LiveServer

@contextmanager
def static_viewer():
    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
    # Use a bounded, browser-safe test port range rather than OS-assigned unsafe ports.
    for port in range(24100,24120):
        try:
            server=ThreadingHTTPServer(('127.0.0.1',port),partial(Quiet,directory=str(ROOT/'examples/observer')));break
        except OSError:continue
    else:raise RuntimeError('No free browser-safe static test port')
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try:yield 'http://127.0.0.1:'+str(server.server_port)
    finally:server.shutdown();server.server_close();thread.join(timeout=5)

async def mcp_call(origin,token,name,args,*,error=False):
    async with httpx.AsyncClient(trust_env=False,timeout=15,headers={'Authorization':'Bearer '+token}) as http:
        async with streamable_http_client(origin+'/mcp',http_client=http) as (read,write):
            async with ClientSession(read,write) as session:
                await session.initialize()
                if name=='town.enter':
                    tools={tool.name:tool for tool in (await session.list_tools()).tools}
                    assert all(t in tools for t in ('town.move','town.look','town.say','town.interact'))
                    # Actual schema is the contract, not an invented animation API.
                    for t in ('town.move','town.look','town.say','town.interact'):
                        assert 'presentation' not in json.dumps(tools[t].input_schema)
                result=await session.call_tool(name,arguments=args)
                assert bool(result.is_error)==error,(name,result.structured_content)
                return result.structured_content

def main():
    out=ROOT/'test-results';out.mkdir(exist_ok=True);report={};errors=[]
    with static_viewer() as other,LiveServer(observer_origins=(other,)) as server,ThreadPoolExecutor(max_workers=1) as runner,sync_playwright() as p:
        try:browser=p.chromium.launch(headless=True)
        except Exception:
            if os.name!='nt':raise
            browser=p.chromium.launch(channel='msedge',headless=True)
        primary=browser.new_context(viewport={'width':1440,'height':1000})
        remote=browser.new_context(viewport={'width':1100,'height':1000})
        game=primary.new_page();viewer=remote.new_page()
        for page in (game,viewer):page.on('pageerror',lambda e:errors.append(str(e)))
        traffic=[];viewer.on('request',lambda r:traffic.append((r.url,r.post_data or '',r.headers)))
        game.goto(server.url+'/watch',wait_until='domcontentloaded')
        game.click('#join-mode');game.fill('#name','Integration Human');game.click('#join')
        expect(game.locator('#agent')).to_be_enabled()
        player_role=game.request.get(server.url+'/play/session').json()['role_id']
        game.click('#agent')
        with game.expect_response(lambda r:r.url.endswith('/play/agent') and r.request.method=='POST') as created:
            game.click('#agent-generate')
        invite=created.value.json();token=invite['identity_token'];role=invite['role_id']
        game.click('#agent-follow');game.wait_for_selector('body.spectating')
        expect(game.locator('#say')).to_be_disabled()
        assert game.request.get(server.url+'/play/session').json()['role_id']==player_role and player_role!=role
        expect(game.locator('#focus-status')).to_contain_text('尚未公开入场')
        assert game.evaluate('localStorage.getItem("lh.public-focus")')==role
        assert token not in game.evaluate('JSON.stringify([localStorage,sessionStorage])')
        viewer.goto(other,wait_until='domcontentloaded');viewer.fill('#origin',server.url);viewer.click('#connect button')
        expect(viewer.locator('#health')).to_have_attribute('data-state','ready')
        assert remote.cookies()==[]
        def call(name,args,op=None,error=False):
            body={'arguments':args}
            if op:body['operation_id']=op
            return runner.submit(lambda:asyncio.run(mcp_call(server.url,token,name,body,error=error))).result(timeout=30)
        call('town.enter',{},'presentation-entry')
        game_row=game.locator('[data-role="'+role+'"]')
        remote_row=viewer.locator('#roles [data-role="'+role+'"]')
        expect(game_row).to_have_count(1);expect(remote_row).to_have_count(1)
        expect(game_row).to_have_class('traveler-row focused')
        report['public_focus_does_not_change_control']=True
        observed=call('town.look',{})['result']
        assert observed['meta']['self']['role_id']==role
        with httpx.Client(base_url=server.url,trust_env=False,timeout=10) as http:
            world_map=http.get('/play/map').json()
            target=next(t for t in world_map['targets'] if t['id']=='elia')
            motion=call('town.move',dict(zip(('x','y'),target['approach'])),'presentation-move')
            assert motion['result']['walking']
            endpoint=motion['result']['movement']['path'][-1]
            assert endpoint==target['approach']
            # Both implementations display accepted state, not client-written positions.
            expect(game_row).to_contain_text('行走中',timeout=10000)
            expect(remote_row).to_contain_text('行走中',timeout=10000)
            expect(game_row).to_contain_text('无进行中的动作',timeout=20000)
            expect(remote_row).to_contain_text('无进行中的动作',timeout=20000)
            coordinate='['+', '.join(map(str,endpoint))+']'
            expect(game_row).to_contain_text(coordinate);expect(remote_row).to_contain_text(coordinate)
            same=http.get('/watch/session').json()['view']['snapshot']
            assert same['entities'][role]['position']==endpoint and same['meta']['self'] is None
            report['two_renderers_same_movement_result']=True
            text='同一事实，两种画法。<img src=x onerror=alert(1)>'
            speech=call('town.say',{'text':text},'presentation-speech')
            expect(game.locator('#timeline')).to_contain_text(text)
            expect(viewer.locator('#events')).to_contain_text(text)
            expect(game.locator('#bubbles .bubble[data-source="authored"]')).to_have_count(1)
            assert game.locator('#timeline img').count()==0 and viewer.locator('#events img').count()==0
            replay=call('town.say',{'text':text},'presentation-speech')
            assert replay['replayed'] and replay['result']['message_id']==speech['result']['message_id']
            call('town.say',{'text':'changed'},'presentation-speech',error=True)
            call('town.say',{'text':'forged','presentation':{'animation':'wave'}},'forged-decoration',error=True)
            runner.submit(lambda:asyncio.run(mcp_call(server.url,token,'town.say',{'text':'bare payload'},error=True))).result(timeout=30)
            for extra in ({'author':'forged'},{'token':'not-a-credential'}):
                call('town.say',{'text':'invalid',**extra},'rejected-extra',error=True)
            report['semantic_speech_replay_and_schema']=True
            call('town.interact',{'target':'elia'},'presentation-interact-npc')
            expect(game.locator('#timeline [data-source="scripted"]')).not_to_have_count(0)
            expect(viewer.locator('#events [data-source="scripted"]')).not_to_have_count(0)
            call('town.interact',{'target':'bench'},'presentation-interact-feedback')
            expect(game.locator('#timeline')).to_contain_text('歇一会儿',timeout=20000)
            expect(viewer.locator('#events')).to_contain_text('歇一会儿',timeout=20000)
            expect(game.locator('#bubbles .bubble[data-source="scripted"]').filter(has_text='游戏脚本')).not_to_have_count(0)
            report['scripted_first_person_not_agent_speech']=True
            game.reload(wait_until='domcontentloaded')
            expect(game.locator('#focus-status')).to_contain_text('灯溪访客')
            expect(game.locator('#say')).to_be_disabled()
            assert game.locator('#bubbles .bubble').count()==0
            report['refresh_restores_public_focus_without_replay']=True
            assert viewer.locator('#scene [data-target]').count()==len(world_map['targets'])
            assert viewer.locator('#scene [data-building]').count()==len(world_map['buildings'])
            report['static_map_and_objects_exported']=True
        assert all(token not in url+body+json.dumps(headers) for url,body,headers in traffic)
        world_requests=[x for x in traffic if x[0].startswith(server.url)]
        assert world_requests and all('authorization' not in headers and 'cookie' not in headers for _,_,headers in world_requests)
        assert all(url in (server.url+'/play/map',server.url+'/watch/session') for url,_,_ in world_requests)
        report['independent_origin_no_credential_no_control']=True
        unsupported=remote.new_page()
        unsupported.route('**/play/map',lambda route:route.fulfill(status=200,headers={'Content-Type':'application/json','Access-Control-Allow-Origin':other},body=json.dumps({**world_map,'presentation_version':999})))
        unsupported.goto(other,wait_until='domcontentloaded');unsupported.fill('#origin',server.url);unsupported.click('#connect button')
        expect(unsupported.locator('#health')).to_have_attribute('data-state','error')
        expect(unsupported.locator('#health')).to_contain_text('不兼容')
        assert unsupported.locator('#scene > *').count()==0
        unsupported.close();report['unknown_presentation_version_blocked']=True
        viewer.set_viewport_size({'width':390,'height':844})
        assert viewer.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        game.screenshot(path=str(out/'semantic-game.png'),full_page=True)
        viewer.screenshot(path=str(out/'semantic-independent-viewer.png'),full_page=True)
        assert not errors,errors
        report.update(actions=['town.move','town.look','town.say','town.interact'],page_errors=errors,
                      scope='Actual MCP plus two browsers; no LLM/Sub-Agent used; public read-only CORS only')
        primary.close();remote.close();browser.close()
    (out/'semantic-presentation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
