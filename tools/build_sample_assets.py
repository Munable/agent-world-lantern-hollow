"""Build original sample art offline; no world server, database or model calls."""
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from pathlib import Path
import base64, hashlib, json, os, sys, zipfile
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from lantern_hollow.map import manifest

@contextmanager
def source_server():
    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
    worker=Thread(target=server.serve_forever,daemon=True);worker.start()
    try:yield 'http://127.0.0.1:'+str(server.server_port)
    finally:server.shutdown();server.server_close();worker.join(timeout=5)

BUILD=r"""async map=>{
const {sprite,VillageRenderer}=await import('/lantern_hollow/web/render.js');
const make=(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;return c;};
const r=new VillageRenderer(make(map.width*16,map.height*16),map);r.reduced=true;
const items=[];
function add(key,canvas,anchor,crop=false){
 let left=0,top=0,right=canvas.width-1,bottom=canvas.height-1;
 if(crop){const data=canvas.getContext('2d').getImageData(0,0,canvas.width,canvas.height).data;left=canvas.width;top=canvas.height;right=-1;bottom=-1;
  for(let y=0;y<canvas.height;y++)for(let x=0;x<canvas.width;x++)if(data[(y*canvas.width+x)*4+3]){left=Math.min(left,x);top=Math.min(top,y);right=Math.max(right,x);bottom=Math.max(bottom,y);}
  if(right<0)throw new Error('Empty art '+key);
 }
 items.push({key,canvas,left,top,w:right-left+1,h:bottom-top+1,anchor:[anchor[0]-left,anchor[1]-top]});
}
const kinds=['traveler','sage','rose','keeper','smith','gardener'];
for(const kind of kinds)for(const dir of ['up','down','left','right'])for(const clip of ['idle','walk','talk','work'])for(let i=0;i<4;i++)add(`${kind}/${dir}/${clip}/${i}`,sprite(kind,dir,i,clip),[12,29]);
for(const kind of [...new Set(map.tiles.flat())].sort()){
 const y=map.tiles.findIndex(row=>row.includes(kind)),x=map.tiles[y].indexOf(kind),tile=make(16,16);tile.getContext('2d').drawImage(r.bg,x*16,y*16,16,16,0,0,16,16);add('tile/'+kind,tile,[0,0]);
}
for(const kind of ['board','bench','shard','lamp','tree','tree-large']){
 const c=make(256,256),ctx=c.getContext('2d');ctx.translate(120,kind==='lamp'?209:208);
 if(kind==='lamp')r.lamp(ctx,0,0,0);
 else if(kind.startsWith('tree'))r.tree(ctx,0,0,13,kind==='tree-large');
 else r.targetObject(ctx,{id:'sample',kind,x:0,y:0},0);
 add('prop/'+kind,c,[128,224],true);
}
const buildings=new Set();
for(const b of map.buildings)for(const state of b.kind==='tower'?['base','lit']:['base']){
 const key=`building/${b.kind}/${b.w}x${b.h}/${state}`;if(buildings.has(key))continue;buildings.add(key);
 const c=make(256,256),ctx=c.getContext('2d');ctx.translate(128-b.w*8,224-b.h*16);r.building(ctx,{...b,x:0,y:0},0,state==='lit');add(key,c,[128,224],true);
}
const width=1024,frames={};let x=1,y=1,row=0;
for(const item of items){if(x+item.w+1>width){x=1;y+=row+2;row=0;}frames[item.key]={x,y,w:item.w,h:item.h,anchor:item.anchor};x+=item.w+2;row=Math.max(row,item.h);}
const atlas=make(width,y+row+1),ctx=atlas.getContext('2d');ctx.imageSmoothingEnabled=false;
for(const item of items){const f=frames[item.key];ctx.drawImage(item.canvas,item.left,item.top,item.w,item.h,f.x,f.y,f.w,f.h);}
return {png:atlas.toDataURL('image/png').split(',')[1],manifest:{schema:'lantern-sample-assets/1',version:'sample-art-1',atlas:'sample-atlas.png',width:atlas.width,height:atlas.height,tile_size:16,units:'pixels',frames,characters:kinds,directions:['up','down','left','right'],clips:{idle:{frames:4,fps:2},walk:{frames:4,fps:9},talk:{frames:4,fps:6},work:{frames:4,fps:7}},provenance:'Original procedural pixel art from this repository; built locally, no external assets or model calls',license:'MIT',semantic_boundary:'Clips describe display only; they cannot move actors, author speech or complete actions'}};
}"""

def main():
    with source_server() as origin,sync_playwright() as p:
        try:browser=p.chromium.launch(headless=True)
        except Exception:
            if os.name!='nt':raise
            browser=p.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page();page.goto(origin,wait_until='domcontentloaded')
        result=page.evaluate(BUILD,manifest());browser.close()
    raw=base64.b64decode(result['png']);data=result['manifest'];data['sha256']=hashlib.sha256(raw).hexdigest()
    web=ROOT/'lantern_hollow/web';(web/'sample-atlas.png').write_bytes(raw)
    (web/'sample-assets.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    with zipfile.ZipFile(web/'sample-assets.zip','w',compression=zipfile.ZIP_DEFLATED) as archive:
        for name,raw_data in [('sample-atlas.png',raw),('sample-assets.json',(web/'sample-assets.json').read_bytes()),('README.md',(ROOT/'tools/sample-assets-README.md').read_bytes()),('LICENSE',(ROOT/'LICENSE').read_bytes())]:
            info=zipfile.ZipInfo(name,date_time=(2026,9,24,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;archive.writestr(info,raw_data)
    print(json.dumps({'frames':len(data['frames']),'size':[data['width'],data['height']],'png_bytes':len(raw),'sha256':data['sha256']}))

if __name__=='__main__':main()
