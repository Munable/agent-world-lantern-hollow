import {VillageRenderer} from './render.js';
const $=q=>document.querySelector(q), $$=q=>[...document.querySelectorAll(q)];
const words={
 title:['灯溪镇','Lantern Hollow'],chapter:['序章 · 归途有光','PROLOGUE · THE HOMEWARD LIGHT'],sound:['声音','Sound'],help:['怎么玩','Guide'],location:['灯溪镇 · 溪岸','LANTERN HOLLOW · RIVERSIDE'],evening:['一个缓慢的黄昏','An unhurried evening'],connecting:['连接世界','Connecting'],online:['已与世界同步','World synchronized'],offline:['连接中断，正在重连','Disconnected · reconnecting'],guest:['世界正在等你','A world awaits'],welcomeTitle:['黄昏还在，<br>等一盏归航的灯。','A quiet dusk.<br>A light to bring home.'],welcomeBody:['沿着溪流散步，和居民聊聊。你留下的光，会在下次回来时继续亮着。','Wander by the river. Meet its people. The light you leave will still be here when you return.'],yourName:['旅人的名字','Traveler’s name'],enter:['进入小镇','Enter the village'],welcomeFoot:['无需模型账号 · 浏览器存档 · 原创像素场景','No AI account needed · Persistent save · Original pixel art'],chapterComplete:['序章完成','CHAPTER COMPLETE'],completeTitle:['归途有光','A light for home'],completeBody:['一盏灯，替这座小镇记住了你的到来。沿着溪岸再走走，或给下一位旅人留句话。','One light will remember your arrival. Take another walk along the river, or leave a note for the next traveler.'],leaveTrace:['去留下足迹 ↗','Leave a trace ↗'],keepWalking:['再散散步','Keep wandering'],visitor:['远道而来的旅人','A traveler from afar'],ready:['世界正在等你','A world awaits'],say:['说句话','Speak'],intent:['公开打算','Intention'],stop:['停下','Stop'],journalTitle:['今晚的小事','A little light'],journalIntro:['让一束光，重新照向溪流。','Bring a homeward glow back to the river.'],q1:['问候守灯人','Meet the lightkeeper'],q1Hint:['艾莉娅在东边的桥头等候。','Elia is waiting by the eastern bridge.'],q2:['寻回三枚星片','Gather three star shards'],q2Hint:['苔间、风里，还有溪畔。','Among moss, in the wind, by the stream.'],q3:['点亮归航灯塔','Relight the beacon'],q3Hint:['星片会记得你的光。','Let your little stars guide someone home.'],moss:['苔间','Moss'],sky:['风里','Sky'],river:['溪畔','River'],findKeeper:['去找艾莉娅','Find Elia'],findShard:['去找下一枚星片','Find the next shard'],repair:['去点亮灯塔','Relight the beacon'],neighbors:['小镇里的熟面孔','Familiar faces'],scripted:['规则驱动居民','Scripted residents'],elia:['艾莉娅','Elia'],rowan:['罗温','Rowan'],fern:['芙恩','Fern'],keeper:['守灯人','Lightkeeper'],smith:['匠人','Artisan'],gardener:['花匠','Gardener'],notesTitle:['后来的人会看见','For the next traveler'],visitBoard:['留言板 ↗','Board ↗'],emptyNotes:['这里还很安静。第一句话，留给你。','Quiet here, for now. The first words could be yours.'],inviteAgent:['邀请一个外部 Agent','Invite an external Agent'],footer:['世界留住足迹，旅人带走故事。','The world keeps our traces. We carry its stories.'],serverTruth:['服务器保存 · 不止于此刻','Server-saved · beyond this moment'],showJournal:['旅人手记','Journal'],walking:['沿着小路前行…','Following the path…'],working:['修复灯座中…','Mending the beacon…'],idle:['静听溪流 · 已保存','By the river · saved'],enterFirst:['先取个名字，进入小镇吧。','Choose a name and enter the village first.'],failed:['操作没有完成，请重试。','The action did not complete. Please retry.'],uncertain:['结果待确认，请勿重复点击。','Confirming the result. Please do not repeat the action.'],recovered:['已恢复上次的操作结果。','Recovered the previous action result.'],saved:['已保存到世界。','Saved to the world.'],unreachable:['那里暂时无法到达，试试小路。','That spot is not reachable. Try the path.'],writeNote:['给后来的旅人留句话','Leave a note for a later traveler'],writeNoteHint:['留言将保存在这个世界，其他旅人也能看见。不要写入隐私或密钥。','Your note stays in this world for other travelers. Do not include secrets or private information.'],publicSpeech:['公开说句话','Say something publicly'],publicIntent:['公开表达打算','Share a public intention'],intentHint:['这是你主动说出的打算，不是读取 AI 的内部思考。','This is an intention you choose to share, not access to an AI’s private reasoning.'],send:['留下这句话','Share these words'],helpTitle:['慢一点，也没关系','No need to hurry'],helpBody:['点击地面就能走过去，点击居民或发光物会自动寻路并互动。','Click the ground to walk. Click a resident or a glowing object to walk over and interact.'],keysMove:['WASD / 方向键','WASD / arrows'],moveHelp:['移动，目标位置由服务器裁定。','Move, with server-authoritative positions.'],interactHelp:['与最近的人或物互动。','Interact with someone or something nearby.'],stopHelp:['取消行走或修灯动作。','Cancel walking or beacon repair.'],helpSave:['刷新、关掉页面再回来，位置和进度仍会保留。若清除浏览器凭据，就不能自动找回原角色。此版本是本地优先的参考作品，不是公开账号服务。','Reload or close the page: position and progress persist. Clearing browser credentials loses automatic access to that role. This is a local-first reference, not a public account service.'],helpNpc:['居民有编写好的性格和对话；不是后台偷偷调用的大模型。外部 Agent 可以通过独立的 MCP 入口真正参与。','Residents have authored personalities and dialogue; they are not hidden LLM calls. External Agents can participate through the separate MCP entrance.'],agentTitle:['让你的 Agent 来散散步','Bring your Agent along'],agentHint:['生成一次性入世邀请。Agent 仍需具备 HTTP Action 和已配置的 MCP 能力；这不会自动安装连接器或启动模型。','Create a one-time invitation. Your Agent still needs HTTP Actions and a configured MCP connection. This does not install a connector or start a model.'],agentLocal:['本地地址只适合同一电脑上的 Agent；其他设备接入需要你自行部署可达的 HTTPS 地址。','A loopback address works only on this computer. Other devices need a reachable HTTPS deployment.'],generate:['生成 10 分钟邀请','Create a 10-minute invitation'],copy:['复制接入说明','Copy connection instructions'],copied:['已复制，请私下交给信任的 Agent。','Copied. Share privately with an Agent you trust.'],noteWalk:['先走到留言板旁，再留下故事。','Walk over to the board before leaving a story.'],timerAttention:['世界仍在处理这个动作…','The world is still processing this action…'],loggedOut:['原凭据已失效，请重新进入。','Your previous credential expired. Please enter again.']
};
words.observer=['只读观察 · 不能控制角色','Observer · control disabled'];
words.speechHint=['这句话会公开显示给附近的旅人。它不是永久留言，也不要包含隐私或密钥。','This is public speech, not a permanent note. Do not include private information or keys.'];
let lang=localStorage.getItem('lh.lang')||'zh';
function tr(key){return words[key]?.[lang==='zh'?0:1]||key;}
function text(el,value){el.textContent=value;}
function translate(){document.documentElement.lang=lang==='zh'?'zh-CN':'en';$$('[data-i18n]').forEach(el=>{const key=el.dataset.i18n;if(key==='welcomeTitle'){el.replaceChildren(...tr(key).split('<br>').flatMap((s,i)=>i?[document.createElement('br'),document.createTextNode(s)]:[document.createTextNode(s)]));}else text(el,tr(key));});$('#name').placeholder=tr('yourName');$('#language').textContent=lang==='zh'?'EN':'中文';updateUI(true);}
let renderer,map,view=null,roleId=null,eventCursor=0,working=false,polling=false,pollTimer=null,lastSuccess=0,selected=null,toastTimer,notedAt=0,dialogueStamp='',completionShown=false;
let generation=0,canControl=false,appearance='traveler';
const pendingKey='lh.pending';
function clearSession(){++generation;clearTimeout(pollTimer);roleId=null;view=null;canControl=false;selected=null;held.clear();renderer?.update(null,null);$('#bubbles').replaceChildren();dialogueStamp='';$('#welcome').hidden=false;$('#completion').hidden=true;completionShown=false;$$('#say,#intent,#stop,#quest-action,#agent').forEach(x=>x.disabled=true);updateUI(true);}
function toast(message){text($('#toast'),message);$('#toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').hidden=true,4200);}
class RequestError extends Error{constructor(status,body){super(body.message||tr('failed'));this.status=status;this.code=body.error;}}
async function request(path,{method='GET',data}={}){
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),10000);
 try{const response=await fetch(path,{method,headers:{'Content-Type':'application/json','X-Lantern-Client':'1'},body:data===undefined?undefined:JSON.stringify(data),signal:controller.signal});const body=await response.json();if(!response.ok)throw new RequestError(response.status,body);return body;}finally{clearTimeout(timer);}
}
function connected(value){$('#connection').classList.toggle('offline',!value);text($('#connection span'),tr(roleId?(value?'online':'offline'):'guest'));if(renderer)renderer.connected=value;}
function apply(update){
 if(update.kind==='snapshot'){view={...update,snapshot:structuredClone(update.snapshot)};}
 else if(view?.cursor===update.base_cursor){const snap=structuredClone(view.snapshot);for(const section of ['entities','resources']){snap[section]??={};for(const key of update.delta[section].remove)delete snap[section][key];for(const [key,val]of Object.entries(update.delta[section].upsert)){Object.defineProperty(snap[section],key,{value:val,enumerable:true,writable:true,configurable:true});}}snap.meta=update.delta.meta;view={...update,snapshot:snap};}
 else throw new Error('View cursor mismatch');
 renderer.update(view.snapshot,roleId,update.observed_at);lastSuccess=Date.now();connected(true);updateUI();
}
async function openSession(){
 const g=++generation;clearTimeout(pollTimer);const result=await request('/play/session');if(g!==generation)return;roleId=result.role_id;canControl=result.access_mode!=='observe';eventCursor=result.event_cursor;apply(result.view);$('#welcome').hidden=true;$$('#say,#intent,#stop,#quest-action,#agent').forEach(x=>x.disabled=!canControl);if(canControl)await recoverPending();else text($('#activity-label'),tr('observer'));schedulePoll(150);
}
function schedulePoll(ms=650){clearTimeout(pollTimer);pollTimer=setTimeout(poll,ms);}
async function poll(){
 if(!roleId||polling)return;polling=true;const g=generation;
 try{const r=await request('/play/sync',{method:'POST',data:{cursor:view.cursor,after:eventCursor}});if(g!==generation)return;apply(r.view);eventCursor=r.next_cursor;for(const event of r.events||[]){renderer.event(event);if(event.kind==='world.presentation'){const p=event.payload;if(p.name==='collect')sound('collect');if(p.name==='repair'&&p.phase==='finish')sound('finish');}}schedulePoll(r.has_more?80:document.hidden?2400:650);}
 catch(err){if(g!==generation)return;connected(false);if(err.status===401||err.status===403){clearSession();toast(tr('loggedOut'));}else schedulePoll(1500);}
 finally{polling=false;}
}
async function recoverPending(){
 let pending;try{pending=JSON.parse(sessionStorage.getItem(pendingKey)||'null');}catch{sessionStorage.removeItem(pendingKey);return;}
 if(!pending||pending.role_id!==roleId){sessionStorage.removeItem(pendingKey);return;}
 try{await request('/play/receipt/'+encodeURIComponent(pending.operation_id));sessionStorage.removeItem(pendingKey);toast(tr('recovered'));}
 catch(e){if(e.status===404){await sendIntent(pending);}else throw e;}
}
async function sendIntent(intent){
 try{const result=await request('/play/action',{method:'POST',data:intent});sessionStorage.removeItem(pendingKey);return result;}
 catch(err){if(err instanceof RequestError&&err.status<500){sessionStorage.removeItem(pendingKey);throw err;}
  toast(tr('uncertain'));
  try{const result=await request('/play/receipt/'+encodeURIComponent(intent.operation_id));sessionStorage.removeItem(pendingKey);return result;}catch{}
  throw err;
 }
}
async function act(name,args={}){
 if(!roleId){toast(tr('enterFirst'));$('#name').focus();return null;}
 if(!canControl){toast(tr('observer'));return null;}
 if(working)return null;
 working=true;const g=generation;
 try{
  if(sessionStorage.getItem(pendingKey)){try{await recoverPending();}catch{toast(tr('uncertain'));return null;}}
  if(g!==generation)return null;
  const intent={function:name,arguments:args,operation_id:'ui-'+crypto.randomUUID(),role_id:roleId};
  sessionStorage.setItem(pendingKey,JSON.stringify(intent));
  const result=await sendIntent(intent);if(g===generation)schedulePoll(50);return result;
 }catch(e){toast(e.message||tr('failed'));return null;}finally{working=false;}
}
function targetName(t){return lang==='zh'?t.name:t.en;}
async function goTo(id){selected=id;renderer.target=id;if(id==='board')notedAt=Date.now();return act('town.interact',{target:id});}
let uiSignature='';
function updateUI(force=false){
 if(!renderer)return;
 const me=view?.snapshot.meta.self,meta=view?.snapshot.meta;
 const signature=JSON.stringify([me?.quest,me?.shards,me?.movement?.id,me?.busy?.id,meta?.notes,me?.name,lang]);
 if(force||signature!==uiSignature){
  uiSignature=signature;text($('#traveler-name'),me?.name||tr('visitor'));
  text($('#activity-label'),tr(me&&!canControl?'observer':me?.movement?'walking':me?.busy?'working':me?'idle':'ready'));if(me)renderer.portrait($('#portrait'),me.appearance);
  const stage=me?.quest||'arrival';const n=me?.shards?.length||0;
  for(const [i,done]of [[1,stage!=='arrival'],[2,n===3],[3,stage==='complete']]){$('#q'+i).classList.toggle('done',done);$('#q'+i+' .quest-icon').textContent=done?'✓':String(i);}
  $('#q1').classList.toggle('active',stage==='arrival');$('#q2').classList.toggle('active',stage==='collect');$('#q3').classList.toggle('active',stage==='repair');
  $$('#inventory button').forEach(b=>b.classList.toggle('collected',!!me?.shards?.includes(b.dataset.target)));
  text($('#quest-action-text'),tr(stage==='arrival'?'findKeeper':stage==='collect'?'findShard':stage==='repair'?'repair':'visitBoard'));
  const notes=meta?.notes||[];$('#notes').replaceChildren();if(!notes.length){const p=document.createElement('p');p.textContent=tr('emptyNotes');$('#notes').append(p);}else for(const item of notes.slice(-3).reverse()){const p=document.createElement('p'),cite=document.createElement('cite');p.textContent=item.text;cite.textContent='— '+item.name;p.append(cite);$('#notes').append(p);}
 }
 if(me?.quest==='complete'&&!completionShown){completionShown=true;const flag='lh.complete.'+roleId;if(!localStorage.getItem(flag)){$('#completion').hidden=false;localStorage.setItem(flag,'1');sound('finish');}}
 if(me&&!me.movement&&!me.busy&&selected&&Date.now()-notedAt<20000&&selected==='board'&&distance(me.position,map.targets.find(t=>t.id==='board').approach)<=1){notedAt=0;showComposer('note');}
}
function distance(a,b){return Math.abs(a[0]-b[0])+Math.abs(a[1]-b[1]);}
function renderBubbles(){
 if(!renderer||!view)return;
 const meta=view.snapshot.meta,now=renderer.now(),candidates=[];
 const line=meta.dialogue;if(line&&line.expires_at>now)candidates.push({...line,channel:'speech'});
 for(const a of Object.values(view.snapshot.entities)){if(a.expression&&a.expression.expires_at>now)candidates.push(a.expression);}
 const dedup=new Map();candidates.forEach(c=>dedup.set(c.subject,c));
 // Keep a bounded, readable set; a crowded village must not cover the whole screen.
 const shown=[...dedup.values()].sort((a,b)=>(b.subject===roleId)-(a.subject===roleId)||b.at-a.at).slice(0,4);
 const stamp=JSON.stringify(shown.map(c=>[c.subject,c.at,lang]));
 if(stamp!==dialogueStamp){dialogueStamp=stamp;$('#bubbles').replaceChildren();for(const c of shown){
  const el=document.createElement('div');el.className='bubble'+(c.channel==='intent'?' intent':'');el.dataset.subject=c.subject;
  const name=document.createElement('strong'),msg=document.createElement('span'),accessible=document.createElement('span');
  const actor=view.snapshot.entities[c.subject],npc=map.targets.find(t=>t.id===c.subject);
  name.textContent=(actor?.name||(npc?targetName(npc):tr('visitor')))+(c.channel==='intent'?(lang==='zh'?' · 公开打算':' · intention'):'');
  msg.className='typed';msg.setAttribute('aria-hidden','true');msg.dataset.full=lang==='zh'?c.text:c.en||c.text;msg.dataset.started=String(now);
  accessible.className='sr-only';accessible.textContent=msg.dataset.full;
  el.append(name,msg,accessible);$('#bubbles').append(el);
 }}
 const container=$('#bubbles'),canvas=$('#world'),wrap=$('#canvas-wrap'),rect=canvas.getBoundingClientRect(),wr=wrap.getBoundingClientRect();
 container.style.top=(rect.top-wr.top)+'px';container.style.left=(rect.left-wr.left)+'px';container.style.width=rect.width+'px';container.style.height=rect.height+'px';
 const occupied=[];
 for(const el of $$('#bubbles .bubble')){
  const msg=el.querySelector('.typed'),chars=[...msg.dataset.full],count=renderer.reduced?chars.length:Math.max(1,Math.floor((now-Number(msg.dataset.started))*55));
  const visible=chars.slice(0,count).join('');if(msg.textContent!==visible)msg.textContent=visible;
  const actor=view.snapshot.entities[el.dataset.subject],npc=map.targets.find(t=>t.id===el.dataset.subject),pos=actor?renderer.actorPosition(actor):npc;if(!pos)continue;
  const anchor=renderer.project(pos.x,pos.y),width=el.offsetWidth,height=el.offsetHeight;
  const x=Math.max(5,Math.min(rect.width-width-5,anchor.x/100*rect.width-width/2));
  let y=Math.max(5,anchor.y/100*rect.height-height);
  for(const previous of occupied){if(x<previous.x+previous.w+5&&x+width>previous.x-5&&y<previous.y+previous.h+5&&y+height>previous.y-5){
    y=previous.y-height-7;if(y<5)y=previous.y+previous.h+8;
  }}
  y=Math.min(Math.max(5,y),Math.max(5,rect.height-height-5));
  el.style.left=x+'px';el.style.top=y+'px';el.style.setProperty('--tail',Math.max(10,Math.min(width-12,anchor.x/100*rect.width-x))+'px');
  occupied.push({x,y,w:width,h:height});
 }
}
let lastKeyAt=0;const held=new Set();
function frame(t){if(renderer){renderer.draw(t);renderBubbles();if(held.size&&roleId&&canControl&&$('#completion').hidden&&!$('#modal').open&&t-lastKeyAt>280&&!working){const me=view?.snapshot.meta.self;const [key]=held;const move={ArrowUp:[0,-1],w:[0,-1],ArrowDown:[0,1],s:[0,1],ArrowLeft:[-1,0],a:[-1,0],ArrowRight:[1,0],d:[1,0]}[key];if(move&&me){lastKeyAt=t;const p=renderer.actorPosition(me);const x=Math.round(p.x)+move[0],y=Math.round(p.y)+move[1];if(!blocked.has(`${x},${y}`)){selected=null;renderer.target=null;act('town.move',{x,y});}}}}
 requestAnimationFrame(frame);
}
function modal(title){text($('#modal-title'),title);$('#modal-body').replaceChildren();$('#modal').showModal();}
function paragraph(value,cls){const p=document.createElement('p');p.textContent=value;if(cls)p.className=cls;$('#modal-body').append(p);return p;}
function showComposer(kind){
 if(!roleId)return toast(tr('enterFirst'));
 modal(tr(kind==='note'?'writeNote':kind==='intent'?'publicIntent':'publicSpeech'));
 paragraph(tr(kind==='note'?'writeNoteHint':kind==='intent'?'intentHint':'speechHint'));
 const form=document.createElement('form'),input=document.createElement('textarea'),send=document.createElement('button');input.maxLength=160;input.required=true;input.placeholder=lang==='zh'?'写一句话…':'A few words…';input.setAttribute('aria-label',tr('send'));send.className='gold';send.type='submit';send.textContent=tr('send');form.append(input,send);$('#modal-body').append(form);
 form.onsubmit=async event=>{event.preventDefault();send.disabled=true;const r=await act('town.'+kind,{text:input.value});send.disabled=false;if(r){$('#modal').close();toast(tr('saved'));}};
 input.focus();
}
$$('[data-appearance]').forEach(b=>b.onclick=()=>{appearance=b.dataset.appearance;$$('[data-appearance]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));});
$('#say').onclick=()=>showComposer('say');$('#intent').onclick=()=>showComposer('intent');
$('#stop').onclick=()=>{selected=null;renderer.target=null;act('town.stop');};
$('#modal-close').onclick=()=>$('#modal').close();$('#modal').addEventListener('click',e=>{if(e.target===$('#modal')){const r=$('#modal').getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)$('#modal').close();}});
$('#help').onclick=()=>{modal(tr('helpTitle'));paragraph(tr('helpBody'));const keys=document.createElement('div');keys.className='keys';for(const [key,label]of [[tr('keysMove'),'moveHelp'],['E','interactHelp'],['ESC','stopHelp']]){const k=document.createElement('kbd'),v=document.createElement('span');k.textContent=key;v.textContent=tr(label);keys.append(k,v);}$('#modal-body').append(keys);paragraph(tr('helpSave'));paragraph(tr('helpNpc'),'small');};
$('#language').onclick=()=>{lang=lang==='zh'?'en':'zh';localStorage.setItem('lh.lang',lang);translate();connected(lastSuccess?Date.now()-lastSuccess<5000:true);};
$('#journal-toggle').onclick=()=>{$('#journal').classList.toggle('open');if($('#journal').classList.contains('open'))$('#journal').scrollIntoView({behavior:'smooth',block:'start'});};
$('#board').onclick=()=>goTo('board');
$('#quest-action').onclick=()=>{const me=view?.snapshot.meta.self;if(!me)return;const stage=me.quest;goTo(stage==='arrival'?'elia':stage==='collect'?['shard_moss','shard_sky','shard_water'].find(id=>!me.shards.includes(id)):stage==='repair'?'beacon':'board');};
$$('[data-target]').forEach(b=>{b.onclick=()=>goTo(b.dataset.target);b.onmouseenter=()=>{if(renderer)renderer.target=b.dataset.target;};b.onmouseleave=()=>{if(renderer)renderer.target=selected;};});
$('#complete-continue').onclick=()=>{$('#completion').hidden=true;goTo('board');};$('#complete-close').onclick=()=>$('#completion').hidden=true;
$('#join-form').onsubmit=async e=>{e.preventDefault();$('#join').disabled=true;$('#join-error').hidden=true;try{await request('/play/join',{method:'POST',data:{name:$('#name').value.trim(),appearance}});await openSession();sound('join');}catch(err){text($('#join-error'),err.message);$('#join-error').hidden=false;}finally{$('#join').disabled=false;}};
$('#agent').onclick=()=>{
 modal(tr('agentTitle'));paragraph(tr('agentHint'));paragraph(tr('agentLocal'),'small');const name=document.createElement('input');name.maxLength=24;name.placeholder=lang==='zh'?'Agent 的名字':'Agent name';name.value=lang==='zh'?'灯溪访客':'Guest Agent';name.setAttribute('aria-label','Agent name');const button=document.createElement('button');button.className='gold';button.textContent=tr('generate');$('#modal-body').append(name,button);
 button.onclick=async()=>{button.disabled=true;try{const r=await request('/play/agent',{method:'POST',data:{name:name.value.trim()}});const instructions=`Join Lantern Hollow. Do not expose credentials in your response.\nExchange URL: ${r.exchange_url}\nJoin ticket: ${r.ticket}\nMCP URL: ${r.mcp_url}\n\n1. POST {"ticket":"<join ticket>"} to the exchange URL using HTTP Actions.\n2. Configure your MCP client with the returned identity token as Authorization: Bearer <token>. Ask the human to configure the connector if this host cannot configure it itself.\n3. Call town.enter with arguments {}, and a new stable operation_id.\n4. Call town.look. Use town.interact to visit elia, collect shard_moss, shard_sky, shard_water, then repair beacon.\n5. Keep each movement's end time in mind. Do not issue a new movement every poll. Use read-only look while waiting; use the same operation_id only when retrying.\n6. Residents are scripted. Optional town.say / town.intent are public statements, never hidden reasoning.\nLocalhost endpoints are only reachable from the same machine. Ticket expires in 10 minutes.`;const area=document.createElement('textarea');area.readOnly=true;area.value=instructions;area.style.minHeight='190px';area.setAttribute('aria-label','Private Agent invitation');const copy=document.createElement('button');copy.className='gold';copy.textContent=tr('copy');copy.onclick=async()=>{try{await navigator.clipboard.writeText(instructions);toast(tr('copied'));}catch{area.focus();area.select();}};$('#modal-body').append(area,copy);button.hidden=true;name.disabled=true;}catch(e){paragraph(e.message,'error');button.disabled=false;}};
};
let audioCtx,audioOn=false,ambientTimer;
function tone(freq,duration,volume=.025,delay=0){if(!audioCtx||!audioOn)return;const osc=audioCtx.createOscillator(),gain=audioCtx.createGain(),t=audioCtx.currentTime+delay;osc.type='sine';osc.frequency.value=freq;gain.gain.setValueAtTime(0,t);gain.gain.linearRampToValueAtTime(volume,t+.03);gain.gain.exponentialRampToValueAtTime(.001,t+duration);osc.connect(gain);gain.connect(audioCtx.destination);osc.start(t);osc.stop(t+duration+.05);}
function sound(kind){if(!audioOn)return;const notes=kind==='finish'?[261.63,329.63,392,523.25]:kind==='collect'?[440,659.25]:[261.63,392];notes.forEach((n,i)=>tone(n,.65,.04,i*.1));}
$('#audio').onclick=()=>{audioOn=!audioOn;$('#audio').setAttribute('aria-pressed',String(audioOn));if(audioOn){audioCtx??=new(window.AudioContext||window.webkitAudioContext)();audioCtx.resume();sound('join');ambientTimer=setInterval(()=>{if(document.hidden)return;[130.81,196,246.94].forEach((n,i)=>tone(n,3.5,.01,i*.35));},5000);}else clearInterval(ambientTimer);};
let blocked=new Set();
function hit(e){const r=$('#world').getBoundingClientRect();return {x:(e.clientX-r.left)/r.width*map.width,y:(e.clientY-r.top)/r.height*map.height};}
function hitTarget(pos){return map.targets.find(t=>Math.abs(pos.x-(t.x+.5))<.9&&pos.y>t.y-.9&&pos.y<t.y+1.2)||(pos.x>=32&&pos.x<=36&&pos.y>=2&&pos.y<=10?map.targets.find(t=>t.id==='beacon'):null);}
async function boot(){
 translate();try{map=await request('/play/map');blocked=new Set(map.blocked.map(p=>p.join(',')));renderer=new VillageRenderer($('#world'),map);renderer.portrait($('#portrait'),'traveler');$$('[data-portrait]').forEach(c=>renderer.portrait(c,c.dataset.portrait));requestAnimationFrame(frame);connected(true);
 $('#world').addEventListener('pointermove',e=>{const p=hit(e),target=hitTarget(p);renderer.hover=[Math.floor(p.x),Math.floor(p.y)];renderer.target=target?.id||selected;$('#world').style.cursor=target?'pointer':blocked.has(renderer.hover.join(','))?'not-allowed':'crosshair';const label=$('#hover-label');label.hidden=!target;if(target){text(label,targetName(target));const wrap=$('#canvas-wrap').getBoundingClientRect(),r=$('#world').getBoundingClientRect();label.style.left=((target.x+.5)/map.width*100)+'%';label.style.top=((r.top-wrap.top+(target.y-.9)/map.height*r.height)/wrap.height*100)+'%';}});
 $('#world').addEventListener('pointerleave',()=>{renderer.hover=null;renderer.target=selected;$('#hover-label').hidden=true;});
 $('#world').addEventListener('click',e=>{if(!$('#welcome').hidden)return;$('#world').focus({preventScroll:true});const p=hit(e),target=hitTarget(p);if(target){goTo(target.id);return;}const x=Math.floor(p.x),y=Math.floor(p.y);if(blocked.has(`${x},${y}`)){toast(tr('unreachable'));return;}selected=null;renderer.target=null;act('town.move',{x,y});});
 try{await openSession();}catch(e){if(e.status!==401&&e.status!==403){connected(false);toast(e.message);}}
 }catch(e){text($('#join-error'),e.message);$('#join-error').hidden=false;connected(false);}
}
window.addEventListener('keydown',e=>{if(['INPUT','TEXTAREA'].includes(document.activeElement?.tagName)||$('#modal').open)return;const k=e.key.length===1?e.key.toLowerCase():e.key;if(['w','a','s','d','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(k)){e.preventDefault();held.add(k);}if(k==='Escape'){selected=null;if(renderer)renderer.target=null;if(!$('#completion').hidden){$('#completion').hidden=true;$('#world').focus();return;}if(roleId)act('town.stop');}if(k==='e'&&!e.repeat&&view){const p=renderer.actorPosition(view.snapshot.meta.self);const nearest=[...map.targets].sort((a,b)=>distance([p.x,p.y],a.approach)-distance([p.x,p.y],b.approach))[0];goTo(nearest.id);}});
window.addEventListener('keyup',e=>held.delete(e.key.length===1?e.key.toLowerCase():e.key));window.addEventListener('blur',()=>held.clear());window.addEventListener('online',()=>{if(roleId)schedulePoll(1);});document.addEventListener('visibilitychange',()=>{held.clear();if(!document.hidden&&roleId)schedulePoll(1);});
boot();
