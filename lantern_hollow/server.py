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

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.applications import Starlette
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.routing import Mount
from agent_world.http_app import create_app as create_world_http
from agent_world.mcp_app import create_mcp_app, BearerIdentityMiddleware
from agent_world.transport_contracts import WorldGateway, error_response
from agent_world.timer_worker import timer_lifespan
from agent_world.maintenance import retention_lifespan
from agent_world.world_sdk import install_world
from agent_world.errors import AuthenticationRequired, InvalidArguments, IdentityScopeMismatch, CursorExpired, PermissionDenied
from agent_world.world_views import ViewResetRequired
from .world import WORLD
from .map import manifest

COOKIE="lantern_identity"
WEB=Path(__file__).parent/"web"
CORE_PIN="314bd38b774516af198d039de5bc3e036c17b19d"


def create_app(db_path, *, public_url="http://127.0.0.1:8840", universe="lantern-hollow"):
    parsed=urlsplit(public_url)
    if parsed.scheme not in ("http","https") or not parsed.hostname or parsed.username or parsed.password or parsed.path not in ("","/") or parsed.query or parsed.fragment:
        raise ValueError("public_url must be a credential-free origin")
    if parsed.scheme!="https" and parsed.hostname not in ("127.0.0.1","localhost","::1"):
        raise ValueError("Public deployments require HTTPS")
    public_url=public_url.rstrip("/")
    installer=lambda runtime,u:install_world(runtime,u,WORLD)
    mcp,_,runtime=create_mcp_app(db_path,universe,auth_required=True,installer=installer,host=parsed.hostname)
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
            if request.headers.get("origin") not in (None,public_url) or request.headers.get("x-lantern-client")!="1":
                return JSONResponse({"error":"ForbiddenOrigin","message":"Same-origin game request required"},status_code=403)
        response=await call_next(request)
        response.headers["Cache-Control"]="no-store" if not request.url.path.startswith("/static/") else "public, max-age=3600"
        response.headers["X-Content-Type-Options"]="nosniff"
        response.headers["Referrer-Policy"]="same-origin"
        response.headers["Content-Security-Policy"]="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; media-src 'self' blob:; frame-ancestors 'none'; base-uri 'self'"
        return response

    def failure(exc):
        status,result=error_response(exc)
        return JSONResponse(result,status_code=status)

    @ui.get("/")
    def index(): return FileResponse(WEB/"index.html")

    @ui.get("/play/map")
    def get_map(): return {**manifest(),"core_pin":CORE_PIN,"version":"0.1.0"}

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
                snap=runtime.view_snapshot(universe,info["role_id"],"village",identity_token=token)
                # Current snapshot is authoritative; only new cues are played on a fresh page.
                page=runtime.read_changes_page(universe,info["role_id"],runtime.event_floor(universe),identity_token=token)
                return {"view":snap,"role_id":info["role_id"],"event_cursor":page["latest_event_seq"],"access_mode":info["access_mode"]}
            return await asyncio.to_thread(read)
        except Exception as exc:return failure(exc)

    @ui.post("/play/sync")
    async def sync(request:Request):
        try:
            data=await body(request)
            def read():
                token,info=identity(request)
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
            if name not in {f.name for f in WORLD.functions}:raise InvalidArguments("Unknown village action")
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
            name=data.get("name","访客 Agent")
            if not isinstance(name,str) or not 1<=len(name.strip())<=24:raise InvalidArguments("Invalid Agent name")
            def issue():
                _,info=identity(request)
                if info["access_mode"]=="observe":raise PermissionDenied("Observers cannot create control invitations")
                role=runtime.create_role(name.strip())
                ticket=runtime.issue_join_ticket(universe,role["role_id"],ttl_seconds=600)
                return {"role_id":role["role_id"],"expires_at":ticket["expires_at"],"ticket":ticket["ticket"],
                        "mcp_url":public_url+"/mcp","exchange_url":public_url+"/v1/join/exchange"}
            return await asyncio.to_thread(issue)
        except Exception as exc:return failure(exc)

    @ui.post("/play/logout")
    async def logout(request:Request):
        response=JSONResponse({"signed_out":True})
        response.delete_cookie(COOKIE)
        return response

    # Static world code and optional browser helper are data-only assets, never kernel copies.
    ui.mount("/static",StaticFiles(directory=WEB),name="static")

    @api.post("/v1/join/exchange")
    async def exchange(request:Request):
        try:
            data=await body(request)
            def do_exchange():
                result=runtime.exchange_join_ticket(data.get("ticket"),expected_universe=universe)
                if result["universe"]!=universe:raise IdentityScopeMismatch("Wrong world invitation")
                return {"identity":{k:result[k] for k in ("token_id","token","role_id","universe","expires_at")},
                        "next":{"tool":"town.enter","arguments":{"arguments":{},"operation_id":"enter-"+result["token_id"]}}}
            return await asyncio.to_thread(do_exchange)
        except Exception as exc:return failure(exc)

    class Dispatch:
        async def __call__(self,scope,receive,send):
            path=scope.get("path","")
            target=mcp if path=="/mcp" or path.startswith("/mcp/") else ui if path=="/" or path.startswith(("/static/","/play/")) else api
            await target(scope,receive,send)

    base=mcp.app if isinstance(mcp,BearerIdentityMiddleware) else mcp
    @asynccontextmanager
    async def lifespan(app):
        async with base.router.lifespan_context(base):
            async with retention_lifespan(runtime,universe):
                async with timer_lifespan(runtime,universe,interval=0.10):yield
    app=Starlette(routes=[Mount("/",app=Dispatch())],lifespan=lifespan)
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=[parsed.hostname,"127.0.0.1","localhost","testserver"])
    app.state.runtime=runtime
    return app


def main():
    parser=argparse.ArgumentParser(description="Visit Lantern Hollow")
    parser.add_argument("--db",default="data/lantern-hollow.sqlite3")
    parser.add_argument("--port",type=int,default=8840)
    parser.add_argument("--host",default="127.0.0.1")
    parser.add_argument("--public-url")
    args=parser.parse_args()
    import uvicorn
    uvicorn.run(create_app(args.db,public_url=args.public_url or f"http://127.0.0.1:{args.port}"),host=args.host,port=args.port,log_level="warning")

if __name__=="__main__":main()
