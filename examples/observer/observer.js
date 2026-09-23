// Independent read-only implementation: no imports from the game client or kernel.
const $=s=>document.querySelector(s),NS='http://www.w3.org/2000/svg';
let generation=0,timer=null,frame=null,base='',scene=null,map=null,serverTime=0,localTime=0;
function element(name,attrs={},text){const el=document.createElementNS(NS,name);for(const [k,v]of Object.entries(attrs))el.setAttribute(k,v);if(text!==undefined)el.textContent=text;return el;}
function now(){return serverTime+(performance.now()-localTime)/1000;}
function position(actor,time){
 const m=actor.movement;if(!m)return actor.position;
 const progress=Math.max(0,Math.min(m.path.length-1,(time-m.start_at)/m.step_seconds));
 const i=Math.floor(progress),j=Math.min(i+1,m.path.length-1),f=progress-i;
 return [m.path[i][0]+(m.path[j][0]-m.path[i][0])*f,m.path[i][1]+(m.path[j][1]-m.path[i][1])*f];
}
async function read(path,signal){
 const response=await fetch(base+path,{credentials:'omit',signal});
 if(!response.ok)throw new Error('HTTP '+response.status);
 return response.json();
}
function drawMap(){
 const svg=$('#scene');svg.replaceChildren();svg.setAttribute('viewBox',`0 0 ${map.width} ${map.height}`);
 const colors={grass:'#bfd3b9',path:'#c8b79d',water:'#8eb6c3',bridge:'#a78962',cliff:'#637866',stone:'#a1a595'};
 for(let y=0;y<map.height;y++)for(let x=0;x<map.width;x++)svg.append(element('rect',{x,y,width:1,height:1,fill:colors[map.tiles[y][x]]||'#bbb'}));
 for(const b of map.buildings)svg.append(element('rect',{x:b.x,y:b.y,width:b.w,height:b.h,fill:'#7c7067','data-building':b.kind}));
 for(const t of map.targets){const g=element('g',{'data-target':t.id});g.append(element('circle',{cx:t.x+.5,cy:t.y+.5,r:.3,fill:'#766542'}),element('text',{x:t.x+.8,y:t.y+.5},t.name||t.id));svg.append(g);}
 svg.append(element('g',{id:'travelers'}));
}
function showSnapshot(result){
 if(result.mode!=='spectate'||result.view.kind!=='snapshot'||result.view.snapshot.meta.self!==null)throw new Error('Expected public spectator snapshot');
 scene=result.view.snapshot;serverTime=result.server_time;localTime=performance.now();
 $('#roles').replaceChildren();$('#travelers').replaceChildren();
 for(const a of Object.values(scene.entities)){
  const card=document.createElement('article');card.className='role';card.dataset.role=a.role_id;
  const name=document.createElement('strong'),state=document.createElement('p');name.textContent=a.name;
  state.textContent=(a.movement?'行走中':a.busy?'活动中':'无进行中的动作')+' · ['+a.position.join(', ')+']';
  card.append(name,state);$('#roles').append(card);
  const group=element('g',{'data-role':a.role_id});group.append(element('circle',{r:.35,fill:'#285c67'}),element('text',{x:.45,y:0},a.name));$('#travelers').append(group);
 }
 $('#events').replaceChildren();
 for(const event of result.events){
  const p=event.payload,d=p?.data;if(!p)continue;
  const line=document.createElement('li');line.dataset.eventId=event.event_id;
  line.dataset.source=p.name==='dialogue'?'scripted':p.name==='public_expression'?'authored':'system';
  const source={scripted:'游戏脚本',authored:p.channel==='intent'?'公开打算':'公开发言',system:'世界事件'}[line.dataset.source];
  line.textContent=source+' · '+(scene.entities[p.subject_id]?.name||p.subject_id)+' · '+(d?.text||p.name+' / '+p.phase);
  $('#events').append(line);
 }
 $('#health').dataset.state='ready';$('#health').textContent='公开快照已同步 · '+scene.meta.world_name+' · 灯塔'+(scene.meta.beacon.lit?'已点亮':'未点亮');
 $('#health').dataset.lit=String(scene.meta.beacon.lit);
 $('#health').dataset.historyTruncated=String(!!result.history_truncated||!!result.has_older);
 if(result.history_truncated||result.has_older)$('#health').textContent+=' · 仅显示有限近期记录';
}
function draw(){
 if(scene)for(const a of Object.values(scene.entities)){
  const node=[...$('#travelers').children].find(n=>n.dataset.role===a.role_id),[x,y]=position(a,now());
  if(node)node.setAttribute('transform',`translate(${x+.5} ${y+.5})`);
 }
 frame=requestAnimationFrame(draw);
}
$('#connect').onsubmit=async event=>{
 event.preventDefault();const g=++generation;clearTimeout(timer);cancelAnimationFrame(frame);scene=null;
 $('#roles').replaceChildren();$('#events').replaceChildren();$('#scene').replaceChildren();
 try{
  const url=new URL($('#origin').value);if(!['http:','https:'].includes(url.protocol)||url.username||url.password||url.search||url.hash||!['','/'].includes(url.pathname))throw new Error('请输入不含凭据的世界 origin');
  base=url.origin;const controller=new AbortController(),deadline=setTimeout(()=>controller.abort(),10000);
  let loaded;try{loaded=await read('/play/map',controller.signal);}finally{clearTimeout(deadline);}
  if(g!==generation)return;map=loaded;
  if(map.world_id!=='lantern-hollow'||map.presentation_version!==1)throw new Error('不兼容的世界表现版本');
  drawMap();draw();
 }catch(error){if(g===generation){$('#health').dataset.state='error';$('#health').textContent=error.message;}return;}
 async function sync(){
  const controller=new AbortController(),deadline=setTimeout(()=>controller.abort(),10000);
  try{const result=await read('/watch/session',controller.signal);if(g===generation)showSnapshot(result);}
  catch(error){if(g===generation){$('#health').dataset.state='error';$('#health').textContent='数据可能陈旧：'+error.message;}}
  finally{clearTimeout(deadline);if(g===generation)timer=setTimeout(sync,document.hidden?5000:1000);}
 }
 await sync();
};
