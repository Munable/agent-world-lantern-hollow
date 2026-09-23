"""Local-first reference product. No copied kernel and no public account-system claim."""
from __future__ import annotations

import argparse
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit
import json
import os
import uuid
import time

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from starlette.applications import Starlette
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount
from agent_world.http_app import create_app as create_world_http
from agent_world.mcp_app import create_mcp_app, BearerIdentityMiddleware
from agent_world.transport_contracts import WorldGateway, error_response
from agent_world.timer_worker import timer_lifespan
from agent_world.maintenance import retention_lifespan
from agent_world.world_sdk import install_world
from agent_world.errors import AuthenticationRequired, InvalidArguments, IdentityScopeMismatch, CursorExpired, PermissionDenied
from agent_world.world_views import ViewResetRequired
from agent_world.world_streams import StreamResetRequired
from agent_world.diagnostics import SafeRequestTrace
from .onboarding import checked_origin, invitation_prompt, resume_prompt, connection_guide, GUIDE_VERSION
from . import __version__
from .world import WORLD
from .map import manifest

COOKIE="lantern_identity"
WEB=Path(__file__).parent/"web"
CORE_PIN="7d3609853db34f3402754bd0860fee96115a9de1"


def create_app(db_path, *, public_url="http://127.0.0.1:8840", universe="lantern-hollow", agent_public_url=None, observer_origins=()):
    public_url=checked_origin(public_url)
    parsed=urlsplit(public_url)
    agent_origin=checked_origin(agent_public_url or public_url)
    agent_host=urlsplit(agent_origin).hostname
    observer_origins=tuple(checked_origin(origin) for origin in observer_origins)
    public_reads={"/play/map","/watch/session","/watch/sync","/watch/history","/static/sample-assets.json","/static/sample-atlas.png"}
    installer=lambda runtime,u:install_world(runtime,u,WORLD)
    mcp,_,runtime=create_mcp_app(db_path,universe,auth_required=True,installer=installer,host=agent_host)
    api=create_world_http(db_path,universe,auth_required=True,installer=installer)
    gateway=WorldGateway(runtime,universe,auth_required=True)
    ui=FastAPI(docs_url=None,redoc_url=None,openapi_url=None)
    ui.state.runtime=runtime

    def identity(request):
        token=request.cookies.get(COOKIE)
        if not token: raise AuthenticationRequired("Enter the village to continue")
        info=runtime.resolve_identity_token(token)
        if info["universe"]!=universe: raise IdentityScopeMismatch("This identity belongs to another world")
        return token,info

    async def body(request):
        data=await request.body()
        if len(data)>65536: raise InvalidArguments("Request exceeds reference-world limit")
        try: value=json.loads(data or b"{}")
        except (ValueError,UnicodeError): raise InvalidArguments("Invalid JSON") from None
        if not isinstance(value,dict): raise InvalidArguments("Expected an object")
        return value

    @ui.middleware("http")
    async def safety(request,call_next):
        if request.method not in ("GET","HEAD","OPTIONS"):
            allowed=(None,public_url)+observer_origins if request.url.path in public_reads else (None,public_url)
            if request.headers.get("origin") not in allowed or request.headers.get("x-lantern-client")!="1":
                return JSONResponse({"error":"ForbiddenOrigin","message":"Same-origin game request required"},status_code=403)
        response=await call_next(request)
        response.headers["Cache-Control"]="no-store" if not request.url.path.startswith("/static/") else "no-cache, max-age=0"
        response.headers["X-Content-Type-Options"]="nosniff"
        response.headers["Referrer-Policy"]="same-origin"
        response.headers["Content-Security-Policy"]="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; media-src 'self' blob:; frame-ancestors 'none'; base-uri 'self'"
        return response

    def failure(exc):
        status,result=error_response(exc)
        return JSONResponse(result,status_code=status)

    @ui.get("/")
    @ui.get("/watch")
    def index(): return FileResponse(WEB/"index.html")

    def observation(role_id=None, token=None, data=None):
        data=data or {}
        view_name='spectator' if role_id is None else 'village'
        try:
            view=runtime.view_sync(universe,role_id,data['cursor'],identity_token=token) if data.get('cursor') else runtime.view_snapshot(universe,role_id,view_name,identity_token=token)
        except ViewResetRequired:
            view=runtime.view_snapshot(universe,role_id,view_name,identity_token=token)
        first=not data.get('stream_cursor')
        anchor=view.get('streams',{}).get('village')
        if anchor is None:raise PermissionDenied('World does not expose an observation stream')
        stream_cursor=data.get('stream_cursor') or anchor['history_cursor']
        gap=False
        try:
            events=runtime.read_stream(universe,'village',role_id,identity_token=token,cursor=stream_cursor,limit=100)
        except StreamResetRequired:
            events=runtime.read_stream(universe,'village',role_id,identity_token=token,limit=100)
            first=True; gap=True
        return {'view':view,'events':events['events'],'stream_cursor':anchor['cursor'] if not data.get('stream_cursor') else events['cursor'],
                'history_cursor':events['history_cursor'],'has_older':events['has_older'],'has_more':events['has_more'],
                'history_truncated':events['history_truncated'],'history':first,'gap':gap,
                'server_time':time.time(),'mode':'spectate' if role_id is None else 'play'}

    def history_page(data, role_id=None, token=None):
        if set(data)-{'history_cursor'}:raise InvalidArguments('Unexpected history arguments')
        if not data.get('history_cursor'):raise InvalidArguments('A history cursor is required')
        result=runtime.read_stream(universe,'village',role_id,identity_token=token,cursor=data['history_cursor'],limit=100)
        if result['mode']!='history':raise InvalidArguments('Expected a history cursor')
        return result

    @ui.get('/watch/session')
    async def watch_session():
        try:return await asyncio.to_thread(observation)
        except Exception as exc:return failure(exc)

    @ui.post('/watch/sync')
    async def watch_sync(request:Request):
        try:
            data=await body(request)
            if set(data)-{'cursor','stream_cursor'}:raise InvalidArguments('Observer requests cannot choose a role')
            return await asyncio.to_thread(observation,data=data)
        except Exception as exc:return failure(exc)

    @ui.post('/watch/history')
    async def watch_history(request:Request):
        try:return await asyncio.to_thread(history_page,await body(request))
        except Exception as exc:return failure(exc)

    @ui.post('/play/history')
    async def play_history(request:Request):
        try:
            token,info=identity(request)
            return await asyncio.to_thread(history_page,await body(request),info['role_id'],token)
        except Exception as exc:return failure(exc)

    @ui.get('/bridge/stream-client.js')
    def stream_client():
        from importlib.resources import files
        return FileResponse(str(files('agent_world').joinpath('web','stream-client.js')),media_type='text/javascript')

    @ui.get("/play/map")
    def get_map(): return {**manifest(),"core_pin":CORE_PIN,"version":__version__,"world_id":WORLD.world_id,
                               "universe":universe,"world_version":WORLD.version,"presentation_version":1,"assets":{"manifest":"/static/sample-assets.json","schema":"lantern-sample-assets/1"}}

    @ui.post("/play/join")
    async def join(request:Request):
        try:
            data=await body(request)
            name=data.get("name","")
            if not isinstance(name,str) or not 1<=len(name.strip())<=24: raise InvalidArguments("Please use a name of 1–24 characters")
            appearance=data.get("appearance","traveler")
            if appearance not in ("traveler","sage","rose"):raise InvalidArguments("Unknown traveler appearance")
            # Reopening the game never silently replaces a valid identity.
            old=request.cookies.get(COOKIE)
            if old:
                try:
                    info=runtime.resolve_identity_token(old)
                    if info["universe"]==universe: return JSONResponse({"entered":True})
                except Exception: pass
            def create():
                profile=runtime.create_role(name.strip())
                token=runtime.issue_identity_token(universe,profile["role_id"],ttl_seconds=2592000)["token"]
                gateway.call("town.enter",{"operation_id":"enter-"+uuid.uuid4().hex,"arguments":{"appearance":appearance}},"Bearer "+token)
                return token
            token=await asyncio.to_thread(create)
            response=JSONResponse({"entered":True})
            response.set_cookie(COOKIE,token,max_age=2592000,httponly=True,secure=parsed.scheme=="https",samesite="strict",path="/")
            return response
        except Exception as exc: return failure(exc)

    @ui.get("/play/session")
    async def session(request:Request):
        try:
            def read():
                token,info=identity(request)
                boot=runtime.bootstrap(universe,info["role_id"],identity_token=token,record_presence=True)
                # Current snapshot is authoritative; only new cues are played on a fresh page.
                observed=observation(info["role_id"],token)
                return {**observed,"role_id":info["role_id"],"event_cursor":boot["latest_event_seq"],"access_mode":info["access_mode"]}
            return await asyncio.to_thread(read)
        except Exception as exc:return failure(exc)

    @ui.post("/play/sync")
    async def sync(request:Request):
        try:
            data=await body(request)
            def read():
                token,info=identity(request)
                if data.get("stream_cursor"):
                    return observation(info["role_id"],token,data)
                try: view=runtime.view_sync(universe,info["role_id"],data.get("cursor"),identity_token=token)
                except ViewResetRequired: view=runtime.view_snapshot(universe,info["role_id"],"village",identity_token=token)
                try: events=runtime.read_changes_page(universe,info["role_id"],data.get("after",0),limit=100,identity_token=token)
                except CursorExpired:
                    events={"events":[],"next_cursor":runtime.read_changes_page(universe,info["role_id"],runtime.event_floor(universe),identity_token=token)["latest_event_seq"],"has_more":False,"reset":True}
                return {"view":view,**events}
            return await asyncio.to_thread(read)
        except Exception as exc:return failure(exc)

    @ui.post("/play/action")
    async def action(request:Request):
        try:
            data=await body(request)
            name=data.get("function")
            if not isinstance(name,str) or name not in {f.name for f in WORLD.functions}:raise InvalidArguments("Unknown village action")
            def invoke():
                token,info=identity(request)
                if data.get("role_id",info["role_id"])!=info["role_id"]:raise IdentityScopeMismatch("Action does not match this traveler")
                return gateway.call(name,{"arguments":data.get("arguments",{}),"operation_id":data.get("operation_id")},"Bearer "+token)
            return await asyncio.to_thread(invoke)
        except Exception as exc:return failure(exc)

    @ui.get("/play/receipt/{operation_id}")
    async def receipt(operation_id:str,request:Request):
        try:
            def read():
                token,info=identity(request)
                return runtime.get_receipt(universe,info["role_id"],operation_id,identity_token=token)
            return await asyncio.to_thread(read)
        except Exception as exc:return failure(exc)

    @ui.post("/play/agent")
    async def agent(request:Request):
        try:
            data=await body(request)
            if set(data)-{"name","language"}:raise InvalidArguments("Unexpected invitation arguments")
            name=data.get("name","访客 Agent")
            language=data.get("language","zh")
            if language not in ("zh","en"):raise InvalidArguments("Unsupported invitation language")
            if not isinstance(name,str) or not 1<=len(name.strip())<=24:raise InvalidArguments("Invalid Agent name")
            def issue():
                _,info=identity(request)
                if info["access_mode"]=="observe":raise PermissionDenied("Observers cannot create control invitations")
                role=runtime.create_role(name.strip())
                ticket=runtime.issue_join_ticket(universe,role["role_id"],ttl_seconds=600)
                # Exchange once on behalf of the website so the user can save the
                # exact long-lived role key. The Agent may exchange the same ticket
                # later and will receive this same deterministic token, not a second key.
                claimed=runtime.exchange_join_ticket(ticket["ticket"],expected_universe=universe)
                return {"role_id":role["role_id"],"expires_at":ticket["expires_at"],"ticket":ticket["ticket"],
                        "identity_token":claimed["token"],
                        "mcp_url":agent_origin+"/mcp","exchange_url":agent_origin+"/v1/join/exchange",
                        "guide_url":agent_origin+"/agent","guide_version":GUIDE_VERSION,
                        "instructions":invitation_prompt(agent_origin,ticket["ticket"],language=language)}
            return await asyncio.to_thread(issue)
        except Exception as exc:return failure(exc)

    @ui.post("/play/agent/resume")
    async def agent_resume(request:Request):
        try:
            data=await body(request)
            if set(data)-{"language"}:raise InvalidArguments("Resume helper accepts language only, never a token")
            language=data.get("language","zh")
            if language not in ("zh","en"):raise InvalidArguments("Unsupported invitation language")
            # Public text helper, not an authentication or control endpoint.
            return {"mode":"resume","guide_url":agent_origin+"/agent","guide_version":GUIDE_VERSION,
                    "instructions":resume_prompt(agent_origin,language=language)}
        except Exception as exc:return failure(exc)

    @ui.post("/play/logout")
    async def logout(request:Request):
        response=JSONResponse({"signed_out":True})
        response.delete_cookie(COOKIE)
        return response

    # Static world code and optional browser helper are data-only assets, never kernel copies.
    ui.mount("/static",StaticFiles(directory=WEB),name="static")

    @api.get("/agent")
    def agent_guide():
        return PlainTextResponse(connection_guide(agent_origin),headers={"Cache-Control":"no-store","X-Content-Type-Options":"nosniff"})

    @api.post("/v1/join/exchange")
    async def exchange(request:Request):
        try:
            data=await body(request)
            def do_exchange():
                result=runtime.exchange_join_ticket(data.get("ticket"),expected_universe=universe)
                return {"identity":{k:result[k] for k in ("token_id","token","role_id","universe","expires_at")},
                        "next":{"tool":"town.enter","arguments":{"arguments":{},"operation_id":"enter-"+result["token_id"]}}}
            return await asyncio.to_thread(do_exchange)
        except Exception as exc:return failure(exc)

    # Cross-origin support is opt-in and only wraps anonymous observation routes.
    public_ui=CORSMiddleware(ui,allow_origins=list(observer_origins),allow_methods=["GET","POST"],
                            allow_headers=["Content-Type","X-Lantern-Client"],allow_credentials=False)

    class Dispatch:
        async def __call__(self,scope,receive,send):
            path=scope.get("path","")
            target=public_ui if path in public_reads else mcp if path=="/mcp" or path.startswith("/mcp/") else ui if path=="/" or path.startswith(("/static/","/play/","/watch","/bridge/")) else api
            await target(scope,receive,send)

    base=mcp.app if isinstance(mcp,BearerIdentityMiddleware) else mcp
    @asynccontextmanager
    async def lifespan(app):
        async with base.router.lifespan_context(base):
            async with retention_lifespan(runtime,universe):
                async with timer_lifespan(runtime,universe,interval=0.10):yield
    app=Starlette(routes=[Mount("/",app=Dispatch())],lifespan=lifespan)
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=[parsed.hostname,agent_host,"127.0.0.1","localhost","testserver"])
    app.state.runtime=runtime
    trace_dir=os.getenv('LANTERN_TRACE_DIR')
    app.add_middleware(SafeRequestTrace,path=Path(trace_dir)/('requests-'+str(os.getpid())+'.jsonl') if trace_dir else None,
                       functions={f.name for f in WORLD.functions})
    return app


def main():
    parser=argparse.ArgumentParser(description="Visit Lantern Hollow")
    parser.add_argument("--db",default="data/lantern-hollow.sqlite3")
    parser.add_argument("--port",type=int,default=8840)
    parser.add_argument("--host",default="127.0.0.1")
    parser.add_argument("--public-url")
    parser.add_argument("--agent-public-url",help="Trusted externally reachable origin for Agent invitations; does not change browser Origin policy")
    parser.add_argument("--observer-origin",action="append",default=[],help="Allow this exact origin to read public observation; repeatable; never grants control")
    args=parser.parse_args()
    import uvicorn
    uvicorn.run(create_app(args.db,public_url=args.public_url or f"http://127.0.0.1:{args.port}",agent_public_url=args.agent_public_url,observer_origins=args.observer_origin),host=args.host,port=args.port,log_level="warning")

if __name__=="__main__":main()
