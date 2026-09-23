"""Reproduce the bounded two-traveler observer experiment on a disposable server."""
import argparse
import asyncio
import json
import platform
import sys
from pathlib import Path
from types import SimpleNamespace
import httpx
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests.live import LiveServer
from tools.measure_observers import stage

async def measure(server, seconds):
    args=SimpleNamespace(url=server.url,db=str(server.db),pid=server.proc.pid,seconds=seconds,interval=1.5)
    for name in ('Alpha','Beta'):
        with httpx.Client(base_url=server.url,trust_env=False,headers={'X-Lantern-Client':'1'}) as client:
            response=client.post('/play/join',json={'name':name})
            response.raise_for_status()
    results=[]
    for count in (10,50,100):
        result=await stage(args,count);results.append(result)
        print(json.dumps({k:v for k,v in result.items() if not k.startswith('database_')}),flush=True)
    return results

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    parser.add_argument('--seconds',type=float,default=10)
    args=parser.parse_args()
    if not 2<=args.seconds<=60:parser.error('Use a bounded duration of 2 to 60 seconds')
    with LiveServer() as server:
        results=asyncio.run(measure(server,args.seconds))
    report={'scope':'Two synthetic travelers, loopback, 1.5s polling; not rendered browser concurrency or production capacity',
            'model_calls':0,'seconds_per_stage':args.seconds,'python':sys.version,
            'platform':platform.platform(),'results':results}
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2),encoding='utf-8')
    if any(result['error_count'] for result in results):raise SystemExit(1)

if __name__=='__main__':main()
