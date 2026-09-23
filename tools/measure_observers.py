"""Bounded loopback-only HTTP observer measurement, not a production load claim."""
import argparse
import asyncio
import json
import sqlite3
import time
from pathlib import Path
from urllib.parse import urlsplit
import httpx
try:
    import psutil
except ImportError:
    psutil=None

def database(path):
    if not path:return {}
    path=Path(path).resolve()
    with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as db:
        tables=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        rows={t:db.execute('SELECT count(*) FROM "'+t.replace('"','""')+'"').fetchone()[0] for t in tables}
    size=sum(p.stat().st_size for p in [path,Path(str(path)+'-wal'),Path(str(path)+'-shm')] if p.exists())
    return {'rows':rows,'allocated_bytes_including_wal':size}

def process(pid):
    if not pid or not psutil:return None
    root=psutil.Process(pid);processes=[root]+root.children(recursive=True)
    return {'cpu_seconds':sum(p.cpu_times().user+p.cpu_times().system for p in processes),
            'rss_bytes_sum':sum(p.memory_info().rss for p in processes)}

async def stage(args,n):
    before=database(args.db);metrics=[];errors=[];kinds={}
    async with httpx.AsyncClient(base_url=args.url,trust_env=False,timeout=10,limits=httpx.Limits(max_connections=n+2,max_keepalive_connections=n+2),headers={'X-Lantern-Client':'1','Origin':args.url}) as client:
        async def initialize():
            r=await client.get('/watch/session');r.raise_for_status();return r.json()
        states=await asyncio.gather(*(initialize() for _ in range(n)))
        cpu0=process(args.pid);started=time.monotonic()
        async def observer(i):
            state=states[i]
            await asyncio.sleep(i*args.interval/n)
            while time.monotonic()-started<args.seconds:
                t=time.monotonic()
                try:
                    r=await client.post('/watch/sync',json={'cursor':state['view']['cursor'],'stream_cursor':state['stream_cursor']})
                    r.raise_for_status();state=r.json();v=state['view']
                    meta=v['snapshot']['meta'] if v['kind']=='snapshot' else v['delta']['meta']
                    if meta.get('self') is not None:raise AssertionError('Public observer received private self state')
                    metrics.append((time.monotonic()-t,len(r.content)));kinds[v['kind']]=kinds.get(v['kind'],0)+1
                except Exception as exc:
                    errors.append(type(exc).__name__)
                await asyncio.sleep(max(0,args.interval-(time.monotonic()-t)))
        await asyncio.gather(*(observer(i) for i in range(n)))
        elapsed=time.monotonic()-started;cpu1=process(args.pid)
    after=database(args.db);latencies=sorted(x[0]*1000 for x in metrics)
    percentile=lambda p:latencies[min(len(latencies)-1,int((len(latencies)-1)*p))] if latencies else None
    return {'virtual_observers':n,'elapsed_seconds':elapsed,'interval_seconds':args.interval,
        'successful_requests':len(metrics),'error_count':len(errors),'error_types':sorted(set(errors)),
        'requests_per_second':len(metrics)/elapsed,'response_body_bytes':sum(x[1] for x in metrics),
        'p50_ms':percentile(.5),'p95_ms':percentile(.95),'max_ms':max(latencies) if latencies else None,
        'view_kinds':kinds,'server_cpu_percent_of_one_core':((cpu1['cpu_seconds']-cpu0['cpu_seconds'])/elapsed*100 if cpu0 and cpu1 else None),
        'server_rss_bytes_sum':cpu1['rss_bytes_sum'] if cpu1 else None,
        'database_before':before,'database_after':after}

async def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--url',required=True);p.add_argument('--db');p.add_argument('--pid',type=int);p.add_argument('--seconds',type=float,default=10);p.add_argument('--interval',type=float,default=1.5);p.add_argument('--output',required=True);args=p.parse_args()
    u=urlsplit(args.url)
    if u.scheme!='http' or u.hostname not in ('127.0.0.1','localhost','::1') or u.username or u.password or u.path not in ('','/') or u.query or u.fragment:p.error('Only a credential-free loopback HTTP origin is allowed')
    if not 2<=args.seconds<=60 or not .5<=args.interval<=10:p.error('Use a bounded duration/interval')
    args.url=args.url.rstrip('/')
    results=[]
    for n in (10,50,100):
        result=await stage(args,n);results.append(result);print(json.dumps({k:v for k,v in result.items() if not k.startswith('database_')}),flush=True)
        if result['error_count']:break
    report={'scope':'Local short-duration HTTP virtual observers; not rendered browser concurrency, internet capacity, sustained traffic, or a model workload','model_calls':0,'results':results}
    Path(args.output).write_text(json.dumps(report,indent=2),encoding='utf-8')
    if any(r['error_count'] for r in results):raise SystemExit(1)

if __name__=='__main__':asyncio.run(main())
