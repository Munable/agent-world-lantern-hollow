import {applyView,position,Feed} from './model.js';
const $=s=>document.querySelector(s);let generation=0,base='',map=null,view=null,stream=null,history=null,timer=0,feed=new Feed(),art=null,artImage=null,focus='',offset=0,reading=0,raf=0,selectorSignature='',eventSignature='';
const now=()=>performance.now()/1000+offset;
async function request(path,body,signal){const response=await fetch(base+path,{method:body?'POST':'GET',credentials:'omit',signal,headers:body?{'Content-Type':'application/json','X-Lantern-Client':'1'}:undefined,body:body?JSON.stringify(body):undefined});if(!response.ok)throw new Error('HTTP '+response.status);return response.json();}
function status(text,state='ready'){if($('#health').textContent!==text)$('#health').textContent=text;$('#health').dataset.state=state;}
function renderData(result,initial=false){
 if(result.mode!=='spectate'||result.view?.world_version!==map.world_version||!Array.isArray(result.events)||!Number.isFinite(result.server_time))throw new Error('Invalid public response');
 view=applyView(view,result.view);stream=result.stream_cursor;offset=result.server_time-performance.now()/1000;
 if(initial||!history)history=result.history_cursor;$('#older').hidden=!result.has_older;
 feed.ingest(result.events,initial||result.history||result.gap);$('#roles').replaceChildren();const previous=focus,newSignature=JSON.stringify(Object.values(view.snapshot.entities).map(a=>[a.role_id,a.name])),updateSelector=newSignature!==selectorSignature;if(updateSelector){selectorSignature=newSignature;$('#focus').replaceChildren(new Option('全图',''));}
 for(const a of Object.values(view.snapshot.entities)){const row=document.createElement('p');row.dataset.role=a.role_id;row.textContent=a.name+' · '+(a.movement?'行走':a.busy?'工作':'空闲')+' · ['+a.position.join(', ')+']';$('#roles').append(row);if(updateSelector)$('#focus').append(new Option(a.name,a.role_id));}
 if(view.snapshot.entities[previous])$('#focus').value=previous;else focus='';renderEvents();status('已同步公开世界 · '+(view.snapshot.meta.beacon?.lit?'灯塔已点亮':'灯塔未点亮'));$('#health').dataset.kind=result.view.kind;
}
function renderEvents(){const signature=JSON.stringify(feed.values().map(e=>[e.event_id,e.historical]));if(signature===eventSignature)return;eventSignature=signature;const list=$('#events'),old=list.scrollTop,bottom=list.scrollHeight-list.clientHeight-old<30;list.replaceChildren();for(const e of feed.values()){const item=document.createElement('li'),p=e.payload,d=p?.data||{};item.dataset.event=e.event_id;item.dataset.history=String(e.historical);item.textContent=(e.historical?'历史':'本次收到')+' · '+(view.snapshot.entities[p?.subject_id]?.name||p?.subject_id||'世界')+' · '+(d.text||p?.name||e.kind)+(d.reply_to?'\n回复 '+d.reply_to.slice(-8):'');list.append(item);}list.scrollTop=bottom?list.scrollHeight:old;}
async function loadArt(g){
 if(map.assets?.manifest!=='/static/sample-assets.json')return;
 const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),5000);
 try{const manifest=await request(map.assets.manifest,null,controller.signal);if(manifest.schema!=='lantern-sample-assets/1'||manifest.atlas!=='sample-atlas.png'||!manifest.frames||!Number.isInteger(manifest.width)||!Number.isInteger(manifest.height)||manifest.width<1||manifest.height<1||manifest.width>2048||manifest.height>2048||Object.keys(manifest.frames).length>600||typeof manifest.sha256!=='string')throw new Error('Unsupported artwork');
  for(const f of Object.values(manifest.frames))if(![f.x,f.y,f.w,f.h].every(Number.isInteger)||f.x<0||f.y<0||f.w<1||f.h<1||f.x+f.w>manifest.width||f.y+f.h>manifest.height||!Array.isArray(f.anchor)||f.anchor.length!==2||!f.anchor.every(Number.isFinite))throw new Error('Invalid frame bounds');
  const r=await fetch(base+'/static/'+manifest.atlas,{credentials:'omit',signal:controller.signal});if(!r.ok)throw new Error('PNG unavailable');const blob=await r.blob();if(blob.size>1048576)throw new Error('PNG too large');const digest=await crypto.subtle.digest('SHA-256',await blob.arrayBuffer());if([...new Uint8Array(digest)].map(x=>x.toString(16).padStart(2,'0')).join('')!==manifest.sha256)throw new Error('PNG digest mismatch');const image=await createImageBitmap(blob);
  if(image.width!==manifest.width||image.height!==manifest.height){image.close();throw new Error('PNG dimension mismatch');}
  if(g!==generation){image.close();return;}artImage?.close();art=manifest;artImage=image;$('#art').textContent='公开 PNG / JSON 已载入';$('#art').dataset.state='ready';
 }catch(e){if(g===generation){$('#art').textContent='素材不可用，使用基础图形';$('#art').dataset.state='fallback';}}finally{clearTimeout(timeout);}
}
function frame(t){
 if(view&&map&&!document.hidden){const c=$('#scene').getContext('2d'),sx=800/map.width,sy=520/map.height;c.imageSmoothingEnabled=false;c.clearRect(0,0,800,520);
  const colors={grass:'#729472',path:'#c1b28b',water:'#528396',bridge:'#bc9467',stone:'#a2ac96',cliff:'#405f59'};for(let y=0;y<map.height;y++)for(let x=0;x<map.width;x++){c.fillStyle=colors[map.tiles[y][x]]||'#729472';c.fillRect(x*sx,y*sy,sx,sy);}
  for(const b of map.buildings){c.fillStyle=b.kind==='tower'&&view.snapshot.meta.beacon?.lit?'#ead797':'#616b66';c.fillRect(b.x*sx,b.y*sy,b.w*sx,b.h*sy);}
  for(const a of Object.values(view.snapshot.entities)){const p=position(a,now()),m=a.movement;let direction=a.facing||'down',clip=m&&now()<m.end_at?'walk':a.busy?'work':'idle';
   if(clip==='walk'){const i=Math.min(m.path.length-2,Math.max(0,Math.floor((now()-m.start_at)/m.step_seconds)));if(i>=0){const q=m.path[i],r=m.path[i+1];direction=r[0]>q[0]?'right':r[0]<q[0]?'left':r[1]>q[1]?'down':'up';}}
   const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches,n=reduced?0:Math.floor(now()*(clip==='walk'?9:clip==='work'?7:2))%4,f=art?.frames?.[`${a.appearance}/${direction}/${clip}/${n}`];
   if(f&&artImage)c.drawImage(artImage,f.x,f.y,f.w,f.h,(p[0]+.5)*sx-f.anchor[0]/16*sx,(p[1]+1)*sy-f.anchor[1]/16*sy,f.w/16*sx,f.h/16*sy);else{c.fillStyle='#223b46';c.fillRect(p[0]*sx,p[1]*sy,sx,sy);}
   if(a.role_id===focus){c.strokeStyle='#fff0ab';c.lineWidth=3;c.strokeRect(p[0]*sx-3,p[1]*sy-sy,sx+6,sy*2+4);}
  }
 }raf=requestAnimationFrame(frame);
}
async function sync(g,initial=false){
 if(g!==generation||reading===g)return;if(document.hidden){timer=setTimeout(()=>sync(g),5000);return;}reading=g;const controller=new AbortController(),deadline=setTimeout(()=>controller.abort(),10000);
 try{const result=initial||!view?await request('/watch/session',null,controller.signal):await request('/watch/sync',{cursor:view.cursor,stream_cursor:stream},controller.signal);if(g===generation)renderData(result,initial);}
 catch(e){if(g===generation){status('连接中断或数据不兼容，正在重新读取公开快照','error');view=null;}}
 finally{if(reading===g)reading=0;clearTimeout(deadline);if(g===generation)timer=setTimeout(()=>sync(g),1500);}
}
$('#connect').onsubmit=async e=>{e.preventDefault();const g=++generation;clearTimeout(timer);selectorSignature=eventSignature='';$('#roles').replaceChildren();$('#events').replaceChildren();$('#scene').getContext('2d').clearRect(0,0,800,520);view=null;map=null;stream=history=null;feed=new Feed();art=null;$('#older').hidden=true;$('#art').textContent='正在读取公开素材';$('#art').dataset.state='loading';artImage?.close();artImage=null;status('正在连接…','loading');
 try{const u=new URL($('#origin').value);if(!['http:','https:'].includes(u.protocol)||u.username||u.password||u.search||u.hash||u.pathname!=='/')throw new Error('Use a credential-free origin');base=u.origin;const controller=new AbortController(),deadline=setTimeout(()=>controller.abort(),10000);let m;try{m=await request('/play/map',null,controller.signal);}finally{clearTimeout(deadline);}if(g!==generation)return;
  if(m.world_id!=='lantern-hollow'||m.presentation_version!==1||!Number.isInteger(m.world_version)||!Number.isInteger(m.width)||!Number.isInteger(m.height)||m.width<1||m.height<1||m.width>256||m.height>256||!Array.isArray(m.tiles)||m.tiles.length!==m.height||!m.tiles.every(row=>Array.isArray(row)&&row.length===m.width)||!Array.isArray(m.buildings))throw new Error('Unsupported world');map=m;loadArt(g);await sync(g,true);
 }catch(error){if(g===generation)status('连接失败：'+error.message,'error');}
};
$('#focus').onchange=e=>focus=e.target.value;
$('#older').onclick=async()=>{const g=generation;if(!history)return;$('#older').disabled=true;const controller=new AbortController(),deadline=setTimeout(()=>controller.abort(),10000);try{const r=await request('/watch/history',{history_cursor:history},controller.signal);if(g===generation){feed.ingest(r.events,true);history=r.history_cursor;$('#older').hidden=!r.has_older;renderEvents();}}catch(e){if(g===generation)status('更早记录暂不可用；当前状态不变','error');}finally{clearTimeout(deadline);$('#older').disabled=false;}};
document.addEventListener('visibilitychange',()=>{if(!document.hidden&&base){clearTimeout(timer);sync(generation);}});
window.addEventListener('offline',()=>status('连接中断，显示最后确认的数据','error'));window.addEventListener('online',()=>{if(base){clearTimeout(timer);sync(generation);}});
requestAnimationFrame(frame);
export function diagnostics(){return {events:feed.items.size,roles:view?Object.keys(view.snapshot.entities).length:0,kind:view?.kind||null,generation,reading,art:!!artImage};}
