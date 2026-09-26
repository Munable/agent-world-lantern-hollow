import {createProductShell,goalFor,sameArguments} from './product-shell.js';
import {validateMap,nextView,ViewContractError} from './view-contract.js';
import {localPrefs,tabState} from './browser-storage.js';
import {placeBubble} from './ui-layout.js';
import {loadSampleAssets} from './assets.js';
import {VillageRenderer} from './render.js?v=0.6.0rc1';
import {bindCameraInput} from './camera.js?v=0.6.0rc1';
import {bubbleFromEvent,cueSource} from './presentation.js';
import {EventLedger,BubbleQueue} from '/bridge/stream-client.js?v=0.13.1';
const $=q=>document.querySelector(q), $$=q=>[...document.querySelectorAll(q)];
let productShell=null;
const words={
 title:['灯溪镇','Lantern Hollow'],chapter:['序章 · 归途有光','PROLOGUE · THE HOMEWARD LIGHT'],sound:['声音','Sound'],help:['怎么玩','Guide'],location:['灯溪镇 · 溪岸','LANTERN HOLLOW · RIVERSIDE'],evening:['一个缓慢的黄昏','An unhurried evening'],connecting:['连接世界','Connecting'],online:['已与世界同步','World synchronized'],offline:['连接中断，正在重连','Disconnected · reconnecting'],guest:['世界正在等你','A world awaits'],welcomeTitle:['黄昏还在，<br>等一盏归航的灯。','A quiet dusk.<br>A light to bring home.'],welcomeBody:['沿着溪流散步，和居民聊聊。你留下的光，会在下次回来时继续亮着。','Wander by the river. Meet its people. The light you leave will still be here when you return.'],yourName:['旅人的名字','Traveler’s name'],enter:['进入小镇','Enter the village'],welcomeFoot:['无需模型账号 · 浏览器存档 · 原创像素场景','No AI account needed · Persistent save · Original pixel art'],chapterComplete:['序章完成','CHAPTER COMPLETE'],completeTitle:['归途有光','A light for home'],completeBody:['一盏灯，替这座小镇记住了你的到来。沿着溪岸再走走，或给下一位旅人留句话。','One light will remember your arrival. Take another walk along the river, or leave a note for the next traveler.'],leaveTrace:['去留下足迹 ↗','Leave a trace ↗'],keepWalking:['再散散步','Keep wandering'],visitor:['远道而来的旅人','A traveler from afar'],ready:['世界正在等你','A world awaits'],say:['说句话','Speak'],intent:['公开打算','Intention'],stop:['停下','Stop'],journalTitle:['今晚的小事','A little light'],journalIntro:['让一束光，重新照向溪流。','Bring a homeward glow back to the river.'],q1:['问候守灯人','Meet the lightkeeper'],q1Hint:['艾莉娅在东边的桥头等候。','Elia is waiting by the eastern bridge.'],q2:['寻回三枚星片','Gather three star shards'],q2Hint:['苔间、风里，还有溪畔。','Among moss, in the wind, by the stream.'],q3:['点亮归航灯塔','Relight the beacon'],q3Hint:['星片会记得你的光。','Let your little stars guide someone home.'],moss:['苔间','Moss'],sky:['风里','Sky'],river:['溪畔','River'],findKeeper:['去找艾莉娅','Find Elia'],findShard:['去找下一枚星片','Find the next shard'],repair:['去点亮灯塔','Relight the beacon'],neighbors:['小镇里的熟面孔','Familiar faces'],scripted:['规则驱动居民','Scripted residents'],elia:['艾莉娅','Elia'],rowan:['罗温','Rowan'],fern:['芙恩','Fern'],keeper:['守灯人','Lightkeeper'],smith:['匠人','Artisan'],gardener:['花匠','Gardener'],notesTitle:['后来的人会看见','For the next traveler'],visitBoard:['留言板 ↗','Board ↗'],emptyNotes:['这里还很安静。第一句话，留给你。','Quiet here, for now. The first words could be yours.'],inviteAgent:['邀请一个外部 Agent','Invite an external Agent'],footer:['世界留住足迹，旅人带走故事。','The world keeps our traces. We carry its stories.'],serverTruth:['服务器保存 · 不止于此刻','Server-saved · beyond this moment'],showJournal:['旅人手记','Journal'],walking:['沿着小路前行…','Following the path…'],working:['修复灯座中…','Mending the beacon…'],idle:['静听溪流 · 已保存','By the river · saved'],enterFirst:['先取个名字，进入小镇吧。','Choose a name and enter the village first.'],failed:['操作没有完成，请重试。','The action did not complete. Please retry.'],uncertain:['结果待确认，请勿重复点击。','Confirming the result. Please do not repeat the action.'],recovered:['已恢复上次的操作结果。','Recovered the previous action result.'],saved:['已保存到世界。','Saved to the world.'],unreachable:['那里暂时无法到达，试试小路。','That spot is not reachable. Try the path.'],writeNote:['给后来的旅人留句话','Leave a note for a later traveler'],writeNoteHint:['留言将保存在这个世界，其他旅人也能看见。不要写入隐私或密钥。','Your note stays in this world for other travelers. Do not include secrets or private information.'],publicSpeech:['公开说句话','Say something publicly'],publicIntent:['公开表达打算','Share a public intention'],intentHint:['这是你主动说出的打算，不是读取 AI 的内部思考。','This is an intention you choose to share, not access to an AI’s private reasoning.'],send:['留下这句话','Share these words'],helpTitle:['慢一点，也没关系','No need to hurry'],helpBody:['点击地面就能走过去，点击居民或发光物会自动寻路并互动。','Click the ground to walk. Click a resident or a glowing object to walk over and interact.'],keysMove:['WASD / 方向键','WASD / arrows'],moveHelp:['移动，目标位置由服务器裁定。','Move, with server-authoritative positions.'],interactHelp:['与最近的人或物互动。','Interact with someone or something nearby.'],stopHelp:['取消行走或修灯动作。','Cancel walking or beacon repair.'],helpSave:['刷新、关掉页面再回来，位置和进度仍会保留。若清除浏览器凭据，就不能自动找回原角色。此版本是本地优先的参考作品，不是公开账号服务。','Reload or close the page: position and progress persist. Clearing browser credentials loses automatic access to that role. This is a local-first reference, not a public account service.'],helpNpc:['居民有编写好的性格和对话；不是后台偷偷调用的大模型。外部 Agent 可以通过独立的 MCP 入口真正参与。','Residents have authored personalities and dialogue; they are not hidden LLM calls. External Agents can participate through the separate MCP entrance.'],agentTitle:['让你的 Agent 来散散步','Bring your Agent along'],agentHint:['第一次创建角色会同时生成一张 10 分钟邀请和一枚长期身份令牌。身份令牌就是这个角色的钥匙，请由你自己妥善保存。','Creating a role produces both a 10-minute invitation and a long-lived identity token. The identity token is the key to this role; keep it yourself and store it safely.'],resumeAgent:['继续已有 Agent','Continue an existing Agent'],resumeHint:['已有角色时，使用你自己保存的身份令牌继续。网页不会替你保存令牌，也不会新建角色。','To continue an existing role, use the identity token you saved. This page does not store the token or create another role.'],agentLocal:['本地地址只适合同一电脑上的 Agent；其他设备接入需要你自行部署可达的 HTTPS 地址。','A loopback address works only on this computer. Other devices need a reachable HTTPS deployment.'],generate:['创建角色与邀请','Create role and invitation'],copy:['复制接入说明','Copy connection instructions'],copied:['已复制，请私下交给信任的 Agent。','Copied. Share privately with an Agent you trust.'],identityKeyTitle:['长期身份令牌 · 只交给你信任的人','Long-lived identity token · share only with people or Agents you trust'],identityKeyWarning:['请像保管钱包恢复密钥一样保存它。任何拿到这枚令牌的人都能控制这个角色；网页不会替你长期保存。','Store this like a wallet recovery key. Anyone holding it can control this role; the website will not keep a long-term copy for you.'],copyKey:['复制身份令牌','Copy identity token'],keyCopied:['身份令牌已复制，请妥善保存。','Identity token copied. Store it safely.'],resumeKeyHint:['粘贴你自己保存的身份令牌。它只在当前页面里用于生成接入说明，不会发送到服务器或保存到浏览器存储。','Paste the identity token you saved. It is used only in this page to build the connection instructions; it is not sent to the server or stored in browser storage.'],resumeKeyPlaceholder:['粘贴 awid_… 身份令牌','Paste the awid_… identity token'],buildResume:['生成续接说明','Build resume instructions'],noteWalk:['先走到留言板旁，再留下故事。','Walk over to the board before leaving a story.'],timerAttention:['世界仍在处理这个动作…','The world is still processing this action…'],loggedOut:['原凭据已失效，请重新进入。','Your previous credential expired. Please enter again.']
};
words.welcomeFoot=['进度存于服务器 · 请保留浏览器凭据','Progress saved on the server · keep your browser credential'];
words.resumeAccess=['角色续接','Resume Agent'];
words.observer=['只读观察 · 不能控制角色','Observer · control disabled'];
words.speechHint=['这句话会显示在公开频道，所有获准旁观者都可以读取。它不是永久留言，也不要包含隐私或密钥。','This is public speech, not a permanent note. Do not include private information or keys.'];
let lang=localPrefs.getItem('lh.lang')||'zh';
function tr(key){return words[key]?.[lang==='zh'?0:1]||key;}
function text(el,value){if(el.textContent!==String(value))el.textContent=value;}
function translate(){document.documentElement.lang=lang==='zh'?'zh-CN':'en';$$('[data-i18n]').forEach(el=>{const key=el.dataset.i18n;if(key==='welcomeTitle'){el.replaceChildren(...tr(key).split('<br>').flatMap((s,i)=>i?[document.createElement('br'),document.createTextNode(s)]:[document.createTextNode(s)]));}else text(el,tr(key));});$('#name').placeholder=tr('yourName');$('#language').textContent=lang==='zh'?'EN':'中文';updateUI(true);}
let renderer,map,view=null,roleId=null,eventCursor=0,working=false,polling=false,pollTimer=null,lastSuccess=0,selected=null,toastTimer,notedAt=0,dialogueStamp='',completionShown=false;
let generation=0,canControl=false,appearance='traveler';
let mode='spectate',streamCursor=null,historyCursor=null,historyAvailable=false,focusedRole=null,feedGap=false;
const ledger=new EventLedger(600),bubbleQueue=new BubbleQueue();
let rosterSignature='',timelineSignature='',filterKind='all';
const focusKey='lh.public-focus';
const validRole=id=>typeof id==='string'&&/^awr_[A-Za-z0-9_-]{1,120}$/.test(id);
let preferredRole=localPrefs.getItem(focusKey)||null;
if(!validRole(preferredRole))preferredRole=null;
const linkedRole=new URLSearchParams(location.search).get('role');
if(validRole(linkedRole)){
 preferredRole=linkedRole;localPrefs.setItem(focusKey,linkedRole);
 const clean=new URL(location.href);clean.searchParams.delete('role');
 history.replaceState(null,'',clean.pathname+clean.search+clean.hash);
}
focusedRole=preferredRole;
function followCameraRole(id){const overview=renderer.camera.zoom===1;renderer.camera.follow(id);if(id&&overview&&renderer.canvas.getBoundingClientRect().width<600){renderer.camera.zoom=2.6;renderer.camera.constrain();}}
function followHome(){
 const id=mode==='play'?roleId:preferredRole;
 followCameraRole(id);renderer.focusRole=id;focusedRole=id;updateLiveUI(true);
}
function updateFocusStatus(){
 if(!renderer)return;const id=mode==='play'?roleId:preferredRole;const a=view?.snapshot.entities?.[id];
 const zh=lang==='zh',follow=!!id&&renderer.camera.followId===id;
 text($('#return-role'),zh?'回到关注角色':'Return to role');$('#return-role').disabled=!id;
 $('#return-role').setAttribute('aria-pressed',String(follow));
 text($('#follow-agent'),zh?'关注角色':'Watch a role');text($('#overview'),zh?'全图':'Overview');
 text($('#camera-status'),id?(a?(zh?(follow?'跟随：':'自由镜头 · '):(follow?'Following: ':'Free camera · '))+a.name:(zh?'关注角色尚未入场':'Watched role has not entered')):(zh?'自由观察':'Free observation'));
 if(mode==='spectate'){
  text($('#traveler-name'),a?.name||(id?(zh?'等待关注角色入场':'Waiting for watched role'):(zh?'公开观察':'Public observation')));
  text($('#activity-label'),a?(zh?'只读关注 · ':'Read-only · ')+(a.movement?(zh?'行走中':'Walking'):a.busy?(zh?'活动中':'Working'):(zh?'空闲':'Idle')):(zh?'仅公开数据，不授予控制权':'Public data only; no control granted'));
  renderer.portrait($('#portrait'),a?.appearance||'traveler');
 }
}
function rememberRole(id){if(!validRole(id))return false;preferredRole=id;localPrefs.setItem(focusKey,id);if(!localPrefs.persistent)toast(lang==='zh'?'浏览器未保存偏好，本页暂时关注；刷新后请重新选择。':'Preferences are unavailable; focus lasts for this page only.');return true;}
function watchRoleDialog(){
 modal(lang==='zh'?'关注已有角色':'Watch an existing role');
 paragraph(lang==='zh'?'只需要公开角色 ID，不要填写身份令牌。关注不会取得控制权或私人任务。':'Use a public role ID, never an identity token. Watching grants no control or private data.');
 const input=document.createElement('input');input.id='watch-role-id';input.maxLength=128;input.autocomplete='off';input.value=preferredRole||'';input.setAttribute('aria-label','Public role ID');
 const go=document.createElement('button');go.className='gold';go.id='watch-role-confirm';go.textContent=lang==='zh'?'记住并关注':'Remember and watch';
 const error=document.createElement('p');error.className='error';
 go.onclick=()=>{if(!rememberRole(input.value.trim())){error.textContent=lang==='zh'?'请输入公开角色 ID，而不是令牌。':'Enter a public role ID, not a token.';return;}$('#modal').close();openWatch().catch(e=>toast(e.message));};
 const clear=document.createElement('button');clear.id='watch-role-forget';clear.className='text-button';clear.textContent=lang==='zh'?'取消记住此角色':'Forget watched role';clear.onclick=()=>{focusPublicRole(null);renderer.camera.overview();$('#modal').close();updateLiveUI(true);};
 $('#modal-body').append(input,go,clear,error);input.focus();
}


function selectRole(id){focusedRole=id;renderer.focusRole=id||roleId;followCameraRole(id||roleId);updateLiveUI(true);}
function focusPublicRole(id){
 if(id){if(!rememberRole(id))return;}else{preferredRole=null;localPrefs.removeItem(focusKey);}
 selectRole(id);
}

const pendingKey='lh.pending';
function closeCompletion(){const dialog=$('#completion');if(dialog.open)dialog.close();dialog.hidden=true;}
function showCompletion(){const dialog=$('#completion');dialog.hidden=false;if(!dialog.open)dialog.showModal();}
$('#completion').addEventListener('cancel',event=>{event.preventDefault();closeCompletion();});
$('#completion').addEventListener('close',()=>{$('#completion').hidden=true;});
function clearSession(){$('#speech-overflow').hidden=true;++generation;ledger.clear();bubbleQueue.clear();streamCursor=null;historyCursor=null;$('#timeline').replaceChildren();$('#travelers').replaceChildren();$('#public-notes').replaceChildren();delete $('#public-notes').dataset.signature;text($('#traveler-count'),'0');rosterSignature=timelineSignature='';clearTimeout(pollTimer);roleId=null;view=null;canControl=false;selected=null;held.clear();renderer?.update(null,null);$('#bubbles').replaceChildren();dialogueStamp='';$('#welcome').hidden=false;closeCompletion();completionShown=false;$$('#say,#intent,#stop,#quest-action,#agent').forEach(x=>x.disabled=true);updateUI(true);}
function toast(message){text($('#toast'),message);$('#toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').hidden=true,4200);}
class RequestError extends Error{constructor(status,body){super(body.message||tr('failed'));this.status=status;this.code=body.error;}}
async function request(path,{method='GET',data}={}){
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),10000);
 try{const response=await fetch(path,{method,headers:{'Content-Type':'application/json','X-Lantern-Client':'1'},body:data===undefined?undefined:JSON.stringify(data),signal:controller.signal});const body=await response.json();if(!response.ok)throw new RequestError(response.status,body);return body;}finally{clearTimeout(timer);}
}
function connected(value){$('#connection').classList.toggle('offline',!value);text($('#connection span'),(view?(value?(lang==='zh'?'已同步世界 · '+(mode==='spectate'?'只读观战':'玩家'):'World synchronized · '+mode):tr('offline')):(value?tr('connecting'):(lang==='zh'?'连接失败 · 请重试':'Connection failed · retry'))));if(renderer)renderer.connected=value;if(value)$('#connection-problem').hidden=true;refreshProduct();}
function apply(update){
 view=nextView(view,update,roleId,map);
 renderer.update(view.snapshot,roleId,update.observed_at);renderer.focusRole=focusedRole||roleId;lastSuccess=Date.now();connected(true);updateUI();updateLiveUI();
}
let localHistoryLimited=false;
function absorbFeed(result, initial=false){
 if(initial)localHistoryLimited=false;
 if(ledger.byId.size+result.events.filter(e=>!ledger.byId.has(e.event_id)).length>ledger.limit)localHistoryLimited=true;
 streamCursor=result.stream_cursor;
 if(initial||!historyCursor){historyCursor=result.history_cursor;historyAvailable=result.has_older;}
 feedGap=feedGap||!!result.gap||!!result.history_truncated;
 const fresh=ledger.ingest(result.events,{historical:initial||result.history||result.gap});
 for(const event of fresh){
  const p=event.payload;
  if(event.kind!=='world.presentation'||!p)continue;
  const recent=!event.historical&&renderer.now()-event.occurred_at<30;
  if(recent){
   renderer.event(event);
   if(p.name==='collect')sound('collect');
   if(p.name==='repair'&&p.phase==='finish')sound('finish');
   const bubble=bubbleFromEvent(event);
   if(bubble&&(view.snapshot.entities[bubble.subject]||map.targets.some(t=>t.id===bubble.subject))){
    bubbleQueue.push(bubble,renderer.now());
   }
  }
 }
 updateLiveUI();
}
function setMode(next){
 mode=next;document.body.classList.toggle('spectating',next==='spectate');
 $('#join-mode').hidden=next!=='spectate';$('#watch-mode').hidden=next==='spectate';
 rosterSignature='';timelineSignature='';$('#world').setAttribute('aria-label',next==='spectate'?(lang==='zh'?'公开场景，只读。可通过名单选择角色。':'Read-only world. Use the roster to select a role.'):(lang==='zh'?'游戏场景。方向键移动，E 互动；任务和角色也可通过按钮选择。':'Game scene. Arrow keys move and E interacts; tasks and roles also have buttons.'));
}
async function openSession(){
 const g=++generation;clearTimeout(pollTimer);
 const result=await request('/play/session');if(g!==generation)return;
 ledger.clear();bubbleQueue.clear();historyCursor=null;feedGap=false;
 setMode('play');if(location.pathname!=='/')history.replaceState(null,'','/');roleId=result.role_id;canControl=result.access_mode!=='observe';eventCursor=result.event_cursor;
 apply(result.view);absorbFeed(result,true);$('#welcome').hidden=true;
 $$('#say,#intent,#stop,#quest-action,#agent').forEach(x=>x.disabled=!canControl);
 followHome();if(canControl)await recoverPending();else text($('#activity-label'),tr('observer'));schedulePoll(150);
}
async function openWatch(){
 const g=++generation;clearTimeout(pollTimer);
 const result=await request('/watch/session');if(g!==generation)return;
 ledger.clear();bubbleQueue.clear();historyCursor=null;feedGap=false;
 setMode('spectate');if(location.pathname!=='/watch')history.replaceState(null,'','/watch');roleId=null;canControl=false;
 apply(result.view);absorbFeed(result,true);$('#welcome').hidden=true;closeCompletion();
 $$('#say,#intent,#stop,#quest-action,#agent').forEach(x=>x.disabled=true);followHome();schedulePoll(150);
}
function schedulePoll(ms=650){clearTimeout(pollTimer);pollTimer=setTimeout(poll,ms);}
async function poll(){
 if(!view)return;if(document.hidden){schedulePoll(10000);return;}if(polling){schedulePoll(100);return;}polling=true;const g=generation;
 try{
  const r=await request(mode==='spectate'?'/watch/sync':'/play/sync',{method:'POST',data:{cursor:view.cursor,stream_cursor:streamCursor}});
  if(g!==generation)return;apply(r.view);absorbFeed(r);schedulePoll(r.has_more?80:Object.values(view.snapshot.entities).some(a=>a.movement||a.busy)?500:1500);
 }catch(err){
  if(g!==generation)return;connected(false);updateLiveUI();
  if(err.status===401||err.status===403){clearSession();toast(tr('loggedOut'));}
  else if(err instanceof ViewContractError){try{if(mode==='play')await openSession();else await openWatch();}catch{showConnectionProblem(err);schedulePoll(1500);}}
  else schedulePoll(1500);
 }finally{polling=false;}
}
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function confirmReceipt(operationId,attempts=4){
 let lastError=null;
 for(let attempt=0;attempt<attempts;attempt++){
  try{return await request('/play/receipt/'+encodeURIComponent(operationId));}
  catch(err){
   lastError=err;
   if(err instanceof RequestError&&err.status!==404&&err.status<500)throw err;
   if(attempt+1<attempts)await pause(120*(attempt+1));
  }
 }
 throw lastError;
}
async function recoverPending(){
 let pending;try{pending=JSON.parse(tabState.getItem(pendingKey)||'null');}catch{tabState.removeItem(pendingKey);return;}
 if(!pending||pending.role_id!==roleId){tabState.removeItem(pendingKey);return;}
 try{const result=await confirmReceipt(pending.operation_id);tabState.removeItem(pendingKey);toast(tr('recovered'));return {intent:pending,result};}
 catch(e){if(e instanceof RequestError&&e.status===404){return {intent:pending,result:await sendIntent(pending)};}else throw e;}
}
async function sendIntent(intent){
 try{const result=await request('/play/action',{method:'POST',data:intent});tabState.removeItem(pendingKey);return result;}
 catch(err){if(err instanceof RequestError&&err.status<500){tabState.removeItem(pendingKey);throw err;}
  toast(tr('uncertain'));
  try{const result=await confirmReceipt(intent.operation_id);tabState.removeItem(pendingKey);return result;}catch{}
  throw err;
 }
}
async function act(name,args={}){
 if(!roleId){toast(tr('enterFirst'));$('#name').focus();return null;}
 if(!canControl){toast(tr('observer'));return null;}
 if(working)return null;
 working=true;refreshProduct();const g=generation;
 try{
  if(tabState.getItem(pendingKey)){try{const recovered=await recoverPending();if(g!==generation)return null;if(recovered&&recovered.intent.function===name&&sameArguments(recovered.intent.arguments,args))return recovered.result;}catch{toast(tr('uncertain'));return null;}}
  if(g!==generation)return null;
  const intent={function:name,arguments:args,operation_id:'ui-'+crypto.randomUUID(),role_id:roleId};
  tabState.setItem(pendingKey,JSON.stringify(intent));if(!tabState.persistent)toast(lang==='zh'?'待确认操作只保存在本页，结果明确前请勿关闭。':'The pending action is held in this page only. Keep it open until confirmed.');
  const result=await sendIntent(intent);if(g===generation)schedulePoll(50);return result;
 }catch(e){toast(tabState.getItem(pendingKey)?tr('uncertain'):e instanceof RequestError?e.message:tr('failed'));return null;}finally{working=false;refreshProduct();}
}
function refreshProduct(){
 const self=mode==='play'?view?.snapshot.meta.self:null;
 productShell?.update({mode,roleId,self,canControl,working,pending:!!tabState.getItem(pendingKey),connected:!!renderer?.connected});
 if(renderer)renderer.goalId=canControl?goalFor(self,lang)?.target:null;
}
function targetName(t){return lang==='zh'?t.name:t.en;}
async function goTo(id){selected=id;renderer.target=id;if(id==='board')notedAt=Date.now();return act('town.interact',{target:id});}
let uiSignature='';
function updateUI(force=false){
 if(!renderer)return;refreshProduct();
 const me=view?.snapshot.meta.self,meta=view?.snapshot.meta;
 const signature=JSON.stringify([me?.quest,me?.shards,me?.movement?.id,me?.busy?.id,meta?.notes,me?.name,lang]);
 if(force||signature!==uiSignature){
  uiSignature=signature;text($('#traveler-name'),me?.name||(mode==='spectate'?(lang==='zh'?'观察世界，不控制角色':'Observe without controlling a role'):tr('visitor')));
  text($('#activity-label'),tr(mode==='spectate'||me&&!canControl?'observer':me?.movement?'walking':me?.busy?'working':me?'idle':'ready'));if(me)renderer.portrait($('#portrait'),me.appearance);
  const stage=me?.quest||'arrival';const n=me?.shards?.length||0;
  for(const [i,done]of [[1,stage!=='arrival'],[2,n===3],[3,stage==='complete']]){$('#q'+i).classList.toggle('done',done);$('#q'+i+' .quest-icon').textContent=done?'✓':String(i);}
  $('#q1').classList.toggle('active',stage==='arrival');$('#q2').classList.toggle('active',stage==='collect');$('#q3').classList.toggle('active',stage==='repair');
  $$('#inventory button').forEach(b=>b.classList.toggle('collected',!!me?.shards?.includes(b.dataset.target)));
  text($('#quest-action-text'),tr(stage==='arrival'?'findKeeper':stage==='collect'?'findShard':stage==='repair'?'repair':'visitBoard'));
  const notes=meta?.notes||[];$('#notes').replaceChildren();if(!notes.length){const p=document.createElement('p');p.textContent=tr('emptyNotes');$('#notes').append(p);}else for(const item of notes.slice(-3).reverse()){const p=document.createElement('p'),cite=document.createElement('cite');p.textContent=item.text;cite.textContent='— '+item.name;p.append(cite);$('#notes').append(p);}
 }
 if(me?.quest==='complete'&&!completionShown&&!$('#modal').open){completionShown=true;const flag='lh.complete.'+roleId;if(!localPrefs.getItem(flag)){showCompletion();localPrefs.setItem(flag,'1');sound('finish');}}
 if(me&&!me.movement&&!me.busy&&selected&&Date.now()-notedAt<20000&&selected==='board'&&distance(me.position,map.targets.find(t=>t.id==='board').approach)<=1){notedAt=0;showComposer('note');}
}

function localClock(value){return value?new Date(value*1000).toLocaleTimeString(lang==='zh'?'zh-CN':'en-GB',{hour12:false}):'—';}
function personName(id){return view?.snapshot.entities[id]?.name || map?.targets.find(t=>t.id===id)?.[lang==='zh'?'name':'en'] || (id?.startsWith('system:')?(lang==='zh'?'世界规则':'World rules'):id||'');}
function describeEvent(event){
 const p=event.payload||{},d=p.data||{},who=personName(p.subject_id||event.actor_role_id);
 const names={walk:['行走','walk'],repair:['修灯','repair'],collect:['收集星片','collect'],arrive:['入场','arrive'],note:['留言','leave a note']};
 const phases={start:['开始','started'],finish:['完成','finished'],cancel:['取消','cancelled']};
 if(p.channel==='speech'||p.channel==='intent')return (lang==='zh'?d.text:d.en||d.text)||'';
 if(p.name==='note'&&d.text)return who+' · '+(lang==='zh'?'留言：':'Note: ')+d.text;
 return who+' · '+(names[p.name]?.[lang==='zh'?0:1]||p.name||event.kind)+' · '+(phases[p.phase]?.[lang==='zh'?0:1]||p.phase||'');
}
function updateLiveUI(force=false){
 if(!renderer||!view)return;updateFocusStatus();
 const zh=lang==='zh',actors=Object.values(view.snapshot.entities).filter(a=>a.kind==='traveler');
 const watched=actors.find(a=>a.role_id===focusedRole);
 text($('#focus-status'),focusedRole?(zh?'公开关注：':'Public focus: ')+(watched?.name||(zh?'角色尚未公开入场':'role not present'))+(zh?' · 不改变控制身份':' · does not change control identity'):(zh?'可选择公开关注的角色':'Select a public role to focus'));
 $('#focus-clear').hidden=!focusedRole;$('#focus-clear').textContent=zh?'取消关注':'Clear focus';
 text($('#live-title'),zh?'世界现场':'World observation');text($('#timeline-title'),zh?'事件与对话':'Events & conversation');
 text($('#traveler-count'),String(actors.length));text($('#presence-boundary'),zh?'角色存在不代表模型持续在线；只展示已接受的世界动作。':'Presence is not proof of a running model. Only accepted world actions are shown.');
 text($('#join-mode'),zh?'加入小镇':'Join as a player');text($('#watch-mode'),zh?'只读观战':'Observe');
 text($('#load-history'),zh?'读取更早记录':'Load earlier records');
 text($('#public-notes-title'),zh?'旅人留下的话':'Persistent traveler notes');
 const notes=view.snapshot.meta.notes||[],notesKey=JSON.stringify([notes,lang]);
 if($('#public-notes').dataset.signature!==notesKey){
  $('#public-notes').dataset.signature=notesKey;$('#public-notes').replaceChildren();
  if(!notes.length){const empty=document.createElement('p');empty.textContent=tr('emptyNotes');$('#public-notes').append(empty);}
  for(const note of notes.slice(-10).reverse()){const p=document.createElement('p'),cite=document.createElement('cite');p.textContent=note.text;cite.textContent='— '+note.name;p.append(cite);$('#public-notes').append(p);}
 }

 for(const option of $('#event-filter').options)option.textContent=({all:['全部','All'],speech:['对话','Speech'],action:['动作','Actions']})[option.value][zh?0:1];
 const ok=renderer.connected && Date.now()-lastSuccess<6000;
 $('#watch-health').classList.toggle('stale',!ok);
 text($('#watch-health'),(ok?(zh?'已同步':'Synchronized'):(zh?'连接中断，正在重连':'Disconnected; reconnecting'))+' · '+localClock(lastSuccess/1000));
 text($('#history-notice'),localHistoryLimited?(zh?'本页仅保留最近 600 条记录；更早内容不在当前缓存中。':'This page keeps the latest 600 records; earlier content is not in its buffer.'):feedGap?(zh?'部分早期记录已到保留期限。历史不会伪装成正在发生。':'Some older records expired. History is not played as live activity.'):(zh?'最近记录可回看；公开打算不等于模型内部思考。':'Retained history is available. Public intention is not private reasoning.'));
 $('#load-history').hidden=!historyAvailable||ledger.byId.size>=ledger.limit;
 const signature=JSON.stringify([actors,focusedRole,lang]);
 if(force||signature!==rosterSignature){
  rosterSignature=signature;const container=$('#travelers');
  const activeId=container.contains(document.activeElement)?document.activeElement.dataset.role:null;
  const existing=new Map([...container.querySelectorAll('[data-role]')].map(row=>[row.dataset.role,row]));
  if(!actors.length){container.replaceChildren();const p=document.createElement('p');p.className='empty';p.textContent=zh?'尚无旅人入场。网页已连接，不需要先创建玩家。':'No traveler has entered. Observation is connected without a player.';container.append(p);}
  else container.querySelector('.empty')?.remove();
  for(const [index,a] of actors.entries()){
   let row=existing.get(a.role_id);
   if(!row){row=document.createElement('button');row.dataset.role=a.role_id;row.append(document.createElement('strong'),document.createElement('span'),document.createElement('small'));row.children[1].className='state';row.onclick=()=>selectRole(a.role_id);row.ondblclick=()=>showTraveler(a.role_id);}
   row.className='traveler-row'+(focusedRole===a.role_id?' focused':'');
   row.setAttribute('aria-label',a.name);row.children[0].textContent=a.name;
   row.children[1].textContent=a.movement?(zh?'行走中':'Walking'):a.busy?(zh?'修灯中':'Repairing'):(zh?'无进行中的动作':'No active action');
   row.children[2].textContent=(a.last_action?.source?(zh?'最近保留记录 ':'Last retained record '):(zh?'最后世界动作 ':'Last world action '))+localClock(a.last_action?.at)+' · ['+a.position.join(', ')+']';
   if(container.children[index]!==row)container.insertBefore(row,container.children[index]||null);
   existing.delete(a.role_id);
  }
  for(const row of existing.values())row.remove();
  if(activeId)[...container.children].find(row=>row.dataset.role===activeId)?.focus({preventScroll:true});
 }
 const items=ledger.items().filter(e=>filterKind==='all'||e.payload?.channel===filterKind);
 const sig=JSON.stringify([items.map(e=>e.event_id),lang,filterKind,canControl]);
 if(force||sig!==timelineSignature){
  timelineSignature=sig;const list=$('#timeline');const atBottom=list.scrollHeight-list.clientHeight-list.scrollTop<40;
  const previousLast=list.lastElementChild?.dataset.eventId;const previousTop=list.scrollTop,listTop=list.getBoundingClientRect().top;
  const anchor=[...list.children].find(li=>li.getBoundingClientRect().bottom>listTop);
  const anchorId=anchor?.dataset.eventId,anchorOffset=anchor?anchor.getBoundingClientRect().top-listTop:0;
  const focusId=list.contains(document.activeElement)?document.activeElement.closest('[data-event-id]')?.dataset.eventId:null;list.replaceChildren();
  for(const e of items){
   const p=e.payload||{},d=p.data||{},li=document.createElement('li');li.dataset.eventId=e.event_id;li.dataset.source=cueSource(p);li.className=e.historical?'history':'fresh';
   const top=document.createElement('div'),who=document.createElement('span'),clock=document.createElement('time'),msg=document.createElement('div');
   top.className='event-top';who.textContent=personName(p.subject_id||e.actor_role_id)+(d.to_role_id?' → '+personName(d.to_role_id):'')+sourceLabel(cueSource(p),p.channel);
   clock.textContent=localClock(e.occurred_at)+(e.historical?(zh?' · 历史':' · history'):'');top.append(who,clock);
   msg.className='event-text';msg.textContent=describeEvent(e);li.append(top,msg);
   if(d.reply_to){const link=document.createElement('div');link.className='event-detail';link.textContent=(zh?'回复 ':'Reply to ')+d.reply_to.slice(-8);li.append(link);}
   if(canControl && p.name==='public_expression' && p.channel==='speech' && p.subject_id!==roleId && d.message_id){
    const reply=document.createElement('button');reply.className='reply';reply.textContent=zh?'回复这句话':'Reply';
    reply.onclick=()=>showComposer('say',{to_role_id:p.subject_id,reply_to:d.message_id});li.append(reply);
   }
   list.append(li);
  }
  if(atBottom){list.scrollTop=list.scrollHeight;$('#timeline-new').hidden=true;}
  else if(previousLast&&previousLast!==list.lastElementChild?.dataset.eventId){$('#timeline-new').hidden=false;$('#timeline-new').textContent=zh?'有新记录 · 到最新':'New records · jump to latest';}
  if(!atBottom){const retained=[...list.children].find(li=>li.dataset.eventId===anchorId);list.scrollTop=retained?list.scrollTop+retained.getBoundingClientRect().top-list.getBoundingClientRect().top-anchorOffset:Math.min(previousTop,list.scrollHeight);}
  if(focusId)[...list.children].find(li=>li.dataset.eventId===focusId)?.querySelector('button')?.focus({preventScroll:true});
 }
}
function showTraveler(id){
 const a=view?.snapshot.entities[id];if(!a)return;
 selectRole(id);modal(a.name);
 paragraph(lang==='zh'?'这是已入场的旅人。没有后续动作不代表模型正在思考或离线。':'An entered traveler. No active action does not establish the model’s status.');
 if(canControl&&id!==roleId){
  const walk=document.createElement('button');walk.className='gold';walk.textContent=lang==='zh'?'走到旁边':'Approach';walk.onclick=()=>{$('#modal').close();act('town.approach',{role_id:id});};
  const say=document.createElement('button');say.className='text-button';say.textContent=lang==='zh'?'公开对话':'Speak publicly';say.onclick=()=>{$('#modal').close();showComposer('say',{to_role_id:id});};
  $('#modal-body').append(walk,say);
 }
}
$('#focus-clear').onclick=()=>focusPublicRole(null);
$('#return-role').onclick=followHome;$('#follow-agent').onclick=watchRoleDialog;
$('#zoom-in').onclick=()=>{renderer.camera.scale(1.25);updateFocusStatus();};$('#zoom-out').onclick=()=>{renderer.camera.scale(.8);updateFocusStatus();};$('#overview').onclick=()=>{renderer.camera.overview();updateFocusStatus();};
$('#timeline-new').onclick=()=>{$('#timeline').scrollTop=$('#timeline').scrollHeight;$('#timeline-new').hidden=true;};$('#timeline').addEventListener('scroll',()=>{const list=$('#timeline');if(list.scrollHeight-list.clientHeight-list.scrollTop<40)$('#timeline-new').hidden=true;});
$('#event-filter').onchange=e=>{filterKind=e.target.value;updateLiveUI(true);};
$('#load-history').onclick=async()=>{
 if(!historyCursor)return;const g=generation;const button=$('#load-history');button.disabled=true;
 try{const p=await request(mode==='spectate'?'/watch/history':'/play/history',{method:'POST',data:{history_cursor:historyCursor}});
  if(g!==generation)return;ledger.ingest(p.events,{historical:true});historyCursor=p.history_cursor;historyAvailable=p.has_older;feedGap=feedGap||p.history_truncated;updateLiveUI(true);
 }catch(e){if(g===generation)toast(e.message);}finally{button.disabled=false;}
};
$('#join-mode').onclick=()=>{$('#welcome').hidden=!$('#welcome').hidden;if(!$('#welcome').hidden)$('#name').focus();};
$('#watch-mode').onclick=()=>{openWatch().catch(e=>toast(e.message));};

function distance(a,b){return Math.abs(a[0]-b[0])+Math.abs(a[1]-b[1]);}
function sourceLabel(source,channel){
 const zh=lang==='zh';
 if(source==='scripted')return zh?' · 游戏脚本':' · scripted game feedback';
 if(source==='authored')return channel==='intent'?(zh?' · 公开打算':' · public intention'):(zh?' · 公开发言':' · public speech');
 return zh?' · 世界事件':' · world event';
}
function renderBubbles(){
 if(!renderer||!view)return;
 const now=renderer.now(),shown=bubbleQueue.active(now);
 renderer.speaking=new Set(shown.filter(c=>c.channel==='speech').map(c=>c.subject));
 const stamp=JSON.stringify(shown.map(c=>[c.id,lang]));
 if(stamp!==dialogueStamp){dialogueStamp=stamp;const keep=new Set(shown.map(c=>c.id));for(const node of $$('#bubbles .bubble'))if(!keep.has(node.dataset.cueId))node.remove();for(const c of shown){
  const retained=$$('#bubbles .bubble').find(node=>node.dataset.cueId===c.id);if(retained&&retained.dataset.language===lang)continue;if(retained)retained.remove();
  const el=document.createElement('div');el.dataset.cueId=c.id;el.dataset.language=lang;el.className='bubble'+(c.channel==='intent'?' intent':'');el.dataset.subject=c.subject;
  const name=document.createElement('strong'),msg=document.createElement('span'),accessible=document.createElement('span');
  const actor=view.snapshot.entities[c.subject],npc=map.targets.find(t=>t.id===c.subject);
  el.dataset.source=c.source;
  name.textContent=(actor?.name||(npc?targetName(npc):tr('visitor')))+sourceLabel(c.source,c.channel);
  msg.className='typed';msg.setAttribute('aria-hidden','true');msg.dataset.full=lang==='zh'?c.text:c.en||c.text;msg.dataset.started=String(c.started);
  accessible.className='sr-only';accessible.textContent=msg.dataset.full;
  const body=document.createElement('span'),measure=document.createElement('span');body.className='bubble-body';measure.className='bubble-measure';measure.setAttribute('aria-hidden','true');measure.textContent=msg.dataset.full;body.append(measure,msg);el.append(name,body,accessible);$('#bubbles').append(el);
 }}
 const container=$('#bubbles'),canvas=$('#world'),wrap=$('#canvas-wrap'),rect=canvas.getBoundingClientRect(),wr=wrap.getBoundingClientRect();
 container.style.top=(rect.top-wr.top)+'px';container.style.left=(rect.left-wr.left)+'px';container.style.width=rect.width+'px';container.style.height=rect.height+'px';
 const occupied=[],obscured=!$('#welcome').hidden||$('#modal').open||!$('#completion').hidden;
 let overflow=0,truncated=false;const maxBubbles=rect.width<600?2:4;
 const elements=$$('#bubbles .bubble').sort((a,b)=>Number(b.dataset.subject===(focusedRole||roleId))-Number(a.dataset.subject===(focusedRole||roleId)));
 for(const el of elements){
  el.hidden=false;
  const msg=el.querySelector('.typed'),chars=[...msg.dataset.full],count=renderer.reduced?chars.length:Math.max(1,Math.floor((now-Number(msg.dataset.started))*55));
  const visible=chars.slice(0,count).join('');if(msg.textContent!==visible)msg.textContent=visible;
  const npc=map.targets.find(t=>t.id===el.dataset.subject),pos=renderer.displayPosition(el.dataset.subject)||npc;
  if(obscured||!pos){el.hidden=true;continue;}
  const anchor=renderer.project(pos.x,pos.y);
  if(anchor.x<0||anchor.x>100||anchor.y<0||anchor.y>100){el.hidden=true;continue;}
  const px=anchor.x/100*rect.width,py=anchor.y/100*rect.height;
  const placed=occupied.length<maxBubbles?placeBubble({x:px,y:py},el.offsetWidth,el.offsetHeight,{width:rect.width,height:rect.height},occupied):null;
  if(!placed){el.hidden=true;overflow++;continue;}
  const measure=el.querySelector('.bubble-measure');truncated=truncated||measure.scrollHeight>measure.clientHeight+1;
  el.style.left=placed.x+'px';el.style.top=placed.y+'px';el.style.setProperty('--tail',Math.max(10,Math.min(placed.w-12,px-placed.x))+'px');occupied.push(placed);
 }
 const more=$('#speech-overflow');more.hidden=obscured||(!overflow&&!truncated);more.textContent=lang==='zh'?'完整发言 · 查看记录':'Full speech · open history';

}
let lastKeyAt=0;const held=new Set();
function frame(t){if(document.hidden){requestAnimationFrame(frame);return;}if(renderer){productShell?.tick(renderer.now(),t);if(lastSuccess&&renderer.connected&&Date.now()-lastSuccess>6000){connected(false);updateLiveUI();}renderer.draw(t);renderBubbles();if(held.size&&roleId&&canControl&&$('#welcome').hidden&&$('#completion').hidden&&!$('#modal').open&&!($('#journal').classList.contains('open')&&matchMedia('(max-width:900px)').matches)&&t-lastKeyAt>280&&!working){const me=view?.snapshot.meta.self;const [key]=held;const move={ArrowUp:[0,-1],w:[0,-1],ArrowDown:[0,1],s:[0,1],ArrowLeft:[-1,0],a:[-1,0],ArrowRight:[1,0],d:[1,0]}[key];if(move&&me){lastKeyAt=t;const p=renderer.actorPosition(me);const x=Math.round(p.x)+move[0],y=Math.round(p.y)+move[1];if(!blocked.has(`${x},${y}`)){selected=null;renderer.target=null;act('town.move',{x,y});}}}}
 requestAnimationFrame(frame);
}
$('#modal').addEventListener('close',()=>{if(!$('#modal').open)$('#modal-body').replaceChildren();});
function modal(title){text($('#modal-title'),title);$('#modal-body').replaceChildren();$('#modal').showModal();}
function paragraph(value,cls){const p=document.createElement('p');p.textContent=value;if(cls)p.className=cls;$('#modal-body').append(p);return p;}
function showComposer(kind,reply={}){
 if(!roleId)return toast(tr('enterFirst'));
 modal(tr(kind==='note'?'writeNote':kind==='intent'?'publicIntent':'publicSpeech'));
 paragraph(tr(kind==='note'?'writeNoteHint':kind==='intent'?'intentHint':'speechHint'));
 const form=document.createElement('form'),input=document.createElement('textarea'),send=document.createElement('button');input.maxLength=160;input.required=true;input.placeholder=lang==='zh'?'写一句话…':'A few words…';input.setAttribute('aria-label',tr('send'));send.className='gold';send.type='submit';send.textContent=tr('send');form.append(input,send);$('#modal-body').append(form);
 const recipients=document.createElement('select');
 if(kind==='say'){
  recipients.setAttribute('aria-label',lang==='zh'?'公开对话对象':'Public recipient');
  const all=document.createElement('option');all.value='';all.textContent=lang==='zh'?'对所有人说':'Everyone';recipients.append(all);
  for(const a of Object.values(view.snapshot.entities)){if(a.kind!=='traveler'||a.role_id===roleId)continue;const opt=document.createElement('option');opt.value=a.role_id;opt.textContent=a.name;recipients.append(opt);}
  recipients.value=reply.to_role_id||focusedRole||'';if(recipients.value===roleId)recipients.value='';
  if(reply.reply_to){recipients.value=reply.to_role_id;recipients.disabled=true;paragraph((lang==='zh'?'回复消息 ':'Reply to message ')+reply.reply_to.slice(-8));}
  form.prepend(recipients);
 }
 form.onsubmit=async event=>{event.preventDefault();send.disabled=true;const args={text:input.value};
  if(kind==='say'){if(recipients.value)args.to_role_id=recipients.value;if(reply.reply_to)args.reply_to=reply.reply_to;}
  const r=await act('town.'+kind,args);send.disabled=false;if(r&&form.isConnected&&$('#modal').open){$('#modal').close();toast(tr('saved'));}};
 input.focus();
}
$$('[data-appearance]').forEach(b=>b.onclick=()=>{appearance=b.dataset.appearance;$$('[data-appearance]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));});
$('#say').onclick=()=>showComposer('say');$('#intent').onclick=()=>showComposer('intent');
$('#stop').onclick=()=>{selected=null;renderer.target=null;act('town.stop');};
$('#modal-close').onclick=()=>$('#modal').close();$('#modal').addEventListener('click',e=>{if(e.target===$('#modal')){const r=$('#modal').getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)$('#modal').close();}});
$('#help').onclick=()=>{modal(tr('helpTitle'));paragraph(tr('helpBody'));const keys=document.createElement('div');keys.className='keys';for(const [key,label]of [[tr('keysMove'),'moveHelp'],['E','interactHelp'],['ESC','stopHelp']]){const k=document.createElement('kbd'),v=document.createElement('span');k.textContent=key;v.textContent=tr(label);keys.append(k,v);}$('#modal-body').append(keys);paragraph(tr('helpSave'));paragraph(tr('helpNpc'),'small');const audio=document.createElement('button');audio.id='guide-audio';audio.className='text-button';audio.textContent=lang==='zh'?(audioOn?'关闭声音':'开启声音'):(audioOn?'Turn sound off':'Turn sound on');audio.onclick=()=>{$('#audio').click();audio.textContent=lang==='zh'?(audioOn?'关闭声音':'开启声音'):(audioOn?'Turn sound off':'Turn sound on');};$('#modal-body').append(audio);};
$('#language').onclick=()=>{lang=lang==='zh'?'en':'zh';localPrefs.setItem('lh.lang',lang);translate();connected(lastSuccess?Date.now()-lastSuccess<5000:true);updateLiveUI(true);};
// Journal navigation is managed by the responsive shell.
$('#board').onclick=()=>goTo('board');
$('#quest-action').onclick=()=>{const me=view?.snapshot.meta.self;if(!me)return;const stage=me.quest;goTo(stage==='arrival'?'elia':stage==='collect'?['shard_moss','shard_sky','shard_water'].find(id=>!me.shards.includes(id)):stage==='repair'?'beacon':'board');};
$$('[data-target]').forEach(b=>{b.onclick=()=>goTo(b.dataset.target);b.onmouseenter=()=>{if(renderer)renderer.target=b.dataset.target;};b.onmouseleave=()=>{if(renderer)renderer.target=selected;};});
$('#complete-continue').onclick=()=>{closeCompletion();goTo('board');};$('#complete-close').onclick=()=>closeCompletion();
$('#join-form').onsubmit=async e=>{e.preventDefault();$('#join').disabled=true;$('#join-error').hidden=true;try{await request('/play/join',{method:'POST',data:{name:$('#name').value.trim(),appearance}});await openSession();sound('join');}catch(err){text($('#join-error'),err.message);$('#join-error').hidden=false;}finally{$('#join').disabled=false;}};
function agentPanel(title){
 modal(title);
 const panel=document.createElement('section');
 $('#modal-body').append(panel);
 return panel;
}
function agentPanelActive(panel){return panel.isConnected&&$('#modal').open;}
function agentParagraph(panel,value,cls='small'){
 const p=document.createElement('p');p.textContent=value;p.className=cls;panel.append(p);
}
function agentCopyField(panel,value,label,id,copyLabel,message){
 const area=document.createElement('textarea');area.readOnly=true;area.value=value;
 area.rows=4;area.setAttribute('aria-label',label);
 const copy=document.createElement('button');copy.id=id;copy.className='gold';copy.textContent=copyLabel;
 copy.onclick=async()=>{
  try{await navigator.clipboard.writeText(area.value);if(agentPanelActive(panel))toast(message);}
  catch{if(agentPanelActive(panel)){area.focus();area.select();}}
 };
 panel.append(area,copy);
}
function showAgentAccess(){
 const en=lang==='en';modal(en?'Bring your Agent':'让你的 Agent 来到小镇');
 paragraph(en?'Already have a role? Watch its public activity without handing over its identity token. Opening this page does not start your Agent.':'已有角色，可以只用公开 ID 关注，不必交出身份令牌。打开网页不会自动启动你的 Agent。');
 const watch=document.createElement('button');watch.className='gold';watch.id='access-watch';watch.textContent=en?'Watch an existing role':'关注已有角色';watch.onclick=watchRoleDialog;
 const resume=document.createElement('button');resume.className='text-button';resume.id='access-resume';resume.textContent=en?'Resume an Agent with a saved key':'用已保存的令牌续接 Agent';resume.onclick=showAgentResume;
 const create=document.createElement('button');create.className='text-button';create.id='access-create';create.textContent=en?(canControl?'Create a separate Agent role':'Enter as a traveler to invite a new Agent'):(canControl?'创建一个独立的 Agent 角色':'先以旅人进入，再邀请新的 Agent');
 create.onclick=()=>{if(canControl)$('#agent').click();else{$('#modal').close();productShell.openPanel('scene');if($('#welcome').hidden)$('#join-mode').click();}};
 $('#modal-body').append(watch,resume,create);
 paragraph(en?'A watched role is not a controlled role. Keep identity keys private and only share them with an Agent you trust.':'关注不等于取得控制权。身份令牌请私下保管，只交给信任的 Agent。','small');
}
function showAgentResume(){
 const panel=agentPanel(tr('resumeAgent'));
 agentParagraph(panel,tr('resumeKeyHint'));
 const key=document.createElement('input');key.type='password';key.autocomplete='off';
 key.spellcheck=false;key.maxLength=256;key.placeholder=tr('resumeKeyPlaceholder');
 key.setAttribute('aria-label','Saved Agent identity token');
 const build=document.createElement('button');build.id='agent-resume-build';
 build.className='gold';build.textContent=tr('buildResume');
 const error=document.createElement('p');error.className='error';error.setAttribute('role','alert');
 panel.append(key,build,error);
 build.onclick=async()=>{
  const token=key.value.trim();
  if(!/^awid_[A-Za-z0-9_-]{1,251}$/.test(token)){
   error.textContent=lang==='zh'?'身份令牌格式不正确。':'Invalid identity token format.';return;
  }
  const language=lang;build.disabled=true;error.textContent='';
  try{
   const r=await request('/play/agent/resume',{method:'POST',data:{language}});
   if(!agentPanelActive(panel))return;
   const instructions=r.instructions+(language==='zh'?' 身份令牌：':' Identity token: ')+token;
   key.value='';panel.replaceChildren();
   agentCopyField(panel,instructions,'Private Agent resume','agent-copy',tr('copy'),tr('copied'));
  }catch(e){if(agentPanelActive(panel)){error.textContent=e.message;build.disabled=false;}}
 };
 key.focus();
}
$('#resume-existing').onclick=showAgentResume;
$('#agent').onclick=()=>{
 const panel=agentPanel(tr('agentTitle'));
 agentParagraph(panel,tr('agentHint'));agentParagraph(panel,tr('agentLocal'));agentParagraph(panel,tr('resumeHint'));
 const name=document.createElement('input');name.maxLength=24;
 name.placeholder=lang==='zh'?'Agent 的名字':'Agent name';name.value=lang==='zh'?'灯溪访客':'Guest Agent';
 name.setAttribute('aria-label','Agent name');
 const button=document.createElement('button');button.id='agent-generate';button.className='gold';button.textContent=tr('generate');
 const resume=document.createElement('button');resume.id='agent-resume';resume.className='text-button';resume.textContent=tr('resumeAgent');
 resume.onclick=showAgentResume;
 const error=document.createElement('p');error.className='error';error.setAttribute('role','alert');
 panel.append(name,button,resume,error);
 button.onclick=async()=>{
  button.disabled=true;resume.disabled=true;error.textContent='';
  try{
   const r=await request('/play/agent',{method:'POST',data:{name:name.value.trim(),language:lang}});
   if(!agentPanelActive(panel))return;
   panel.replaceChildren();
   agentParagraph(panel,tr('identityKeyTitle'));agentParagraph(panel,tr('identityKeyWarning'));
   agentCopyField(panel,r.identity_token,'Private Agent identity token','agent-key-copy',tr('copyKey'),tr('keyCopied'));
   agentCopyField(panel,r.instructions,'Private Agent invitation','agent-copy',tr('copy'),tr('copied'));
   const follow=document.createElement('button');follow.id='agent-follow';follow.className='text-button';
   follow.textContent=lang==='zh'?'已保存令牌，公开关注此角色':'Key saved; observe this role publicly';
   follow.onclick=()=>{focusPublicRole(r.role_id);$('#modal').close();openWatch().catch(e=>toast(e.message));};
   panel.append(follow);
  }catch(e){if(agentPanelActive(panel)){error.textContent=e.message;button.disabled=false;resume.disabled=false;}}
 };
};
let audioCtx,audioOn=false,ambientTimer;
function tone(freq,duration,volume=.025,delay=0){if(!audioCtx||!audioOn)return;const osc=audioCtx.createOscillator(),gain=audioCtx.createGain(),t=audioCtx.currentTime+delay;osc.type='sine';osc.frequency.value=freq;gain.gain.setValueAtTime(0,t);gain.gain.linearRampToValueAtTime(volume,t+.03);gain.gain.exponentialRampToValueAtTime(.001,t+duration);osc.connect(gain);gain.connect(audioCtx.destination);osc.onended=()=>{osc.disconnect();gain.disconnect();};osc.start(t);osc.stop(t+duration+.05);}
function sound(kind){if(!audioOn)return;const notes=kind==='finish'?[261.63,329.63,392,523.25]:kind==='collect'?[440,659.25]:[261.63,392];notes.forEach((n,i)=>tone(n,.65,.04,i*.1));}
$('#audio').onclick=()=>{audioOn=!audioOn;$('#audio').setAttribute('aria-pressed',String(audioOn));if(audioOn){audioCtx??=new(window.AudioContext||window.webkitAudioContext)();audioCtx.resume();sound('join');ambientTimer=setInterval(()=>{if(document.hidden)return;[130.81,196,246.94].forEach((n,i)=>tone(n,3.5,.01,i*.35));},5000);}else clearInterval(ambientTimer);};
let blocked=new Set();
function hit(e){const r=$('#world').getBoundingClientRect(),p=renderer.camera.unproject((e.clientX-r.left)/r.width*renderer.canvas.width,(e.clientY-r.top)/r.height*renderer.canvas.height);return {x:p.x/16,y:p.y/16};}
function hitTarget(pos){return map.targets.find(t=>Math.abs(pos.x-(t.x+.5))<.9&&pos.y>t.y-.9&&pos.y<t.y+1.2)||(pos.x>=32&&pos.x<=36&&pos.y>=2&&pos.y<=10?map.targets.find(t=>t.id==='beacon'):null);}
async function prepareSampleAssets(){
 const status=document.createElement('a');status.href='/static/art-gallery.html';status.target='_blank';status.rel='noopener';status.id='asset-status';status.setAttribute('aria-label','素材预览 / Sample artwork');status.dataset.state='loading';status.textContent='素材加载中 / Loading art';$('#art-tools').append(status);
 try{const pack=await loadSampleAssets();renderer.useAssets(pack);status.dataset.state='ready';status.textContent='示例素材 / Sample art';status.title=pack.manifest.version;renderer.portrait($('#portrait'),view?.snapshot?.entities?.[preferredRole]?.appearance||view?.snapshot?.meta?.self?.appearance||'traveler');$$('[data-portrait]').forEach(c=>renderer.portrait(c,c.dataset.portrait));}
 catch(error){status.dataset.state='fallback';status.textContent='素材不可用，使用基础图形 / Basic art';status.title=String(error.message).slice(0,120);$('#art-tools').open=true;}
}
function showConnectionProblem(error){
 $('#connection-problem').hidden=false;$('#connection-problem h2').textContent=lang==='zh'?'连接暂时中断':'Connection unavailable';$('#watch-health').textContent=lang==='zh'?'尚未连接，请重试':'Not connected; please retry';$('#connection-problem-text').textContent=(lang==='zh'?'暂时无法连接世界。请重试，角色与进度不会因此重建。':'The world is temporarily unavailable. Retry without recreating your role.');
 $('#retry-world').textContent=lang==='zh'?'重新连接':'Reconnect';
}
$('#retry-world').onclick=()=>location.reload();
$('#speech-overflow').onclick=()=>{filterKind='speech';$('#event-filter').value='speech';productShell.openPanel('live',true);updateLiveUI(true);$('#timeline').scrollIntoView({block:'center',behavior:renderer?.reduced?'auto':'smooth'});};
async function boot(){
 setMode('spectate');translate();try{map=validateMap(await request('/play/map'));blocked=new Set(map.blocked.map(p=>p.join(',')));renderer=new VillageRenderer($('#world'),map);prepareSampleAssets();bindCameraInput($('#world'),renderer.camera,()=>{$('#hover-label').hidden=true;updateFocusStatus();});renderer.portrait($('#portrait'),'traveler');$$('[data-portrait]').forEach(c=>renderer.portrait(c,c.dataset.portrait));requestAnimationFrame(frame);connected(true);
 $('#world').addEventListener('pointermove',e=>{const p=hit(e),target=hitTarget(p);renderer.hover=[Math.floor(p.x),Math.floor(p.y)];renderer.target=target?.id||selected;$('#world').style.cursor=target?'pointer':blocked.has(renderer.hover.join(','))?'not-allowed':'crosshair';const label=$('#hover-label');label.hidden=!target;if(target){text(label,targetName(target));const wrap=$('#canvas-wrap').getBoundingClientRect(),r=$('#world').getBoundingClientRect();const anchor=renderer.project(target.x,target.y);label.style.left=((r.left-wrap.left+anchor.x/100*r.width)/wrap.width*100)+'%';label.style.top=((r.top-wrap.top+anchor.y/100*r.height)/wrap.height*100)+'%';}});
 $('#world').addEventListener('pointerleave',()=>{renderer.hover=null;renderer.target=selected;$('#hover-label').hidden=true;});
 $('#world').addEventListener('click',e=>{if(!$('#welcome').hidden)return;$('#world').focus({preventScroll:true});const p=hit(e),target=hitTarget(p);const traveler=renderer.hitTraveler(p);if(mode==='spectate'){if(traveler)showTraveler(traveler.role_id);return;}if(traveler&&traveler.role_id!==roleId){showTraveler(traveler.role_id);return;}if(target){goTo(target.id);return;}const x=Math.floor(p.x),y=Math.floor(p.y);if(blocked.has(`${x},${y}`)){toast(tr('unreachable'));return;}selected=null;renderer.target=null;act('town.move',{x,y});});
 try{if(location.pathname==='/watch')await openWatch();else await openSession();}catch(e){if(e.status===401||e.status===403){await openWatch();}else{connected(false);showConnectionProblem(e);}}
 $$('#join-mode,#follow-agent,#zoom-out,#zoom-in,#overview').forEach(el=>el.disabled=false);
 }catch(e){showConnectionProblem(e);connected(false);}
}
window.addEventListener('keydown',e=>{if(e.isComposing||e.keyCode===229)return;if(!canControl||!view?.snapshot.meta.self||(document.activeElement?.isContentEditable||['INPUT','TEXTAREA','SELECT','BUTTON'].includes(document.activeElement?.tagName))||$('#modal').open||(!$('#welcome').hidden)||(!$('#completion').hidden)||($('#journal').classList.contains('open')&&matchMedia('(max-width:900px)').matches))return;const k=e.key.length===1?e.key.toLowerCase():e.key;if(['w','a','s','d','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(k)){e.preventDefault();held.add(k);}if(k==='Escape'){selected=null;if(renderer)renderer.target=null;if(!$('#completion').hidden){closeCompletion();$('#world').focus();return;}if(roleId)act('town.stop');}if(k==='e'&&!e.repeat&&view){const p=renderer.actorPosition(view.snapshot.meta.self);const nearest=[...map.targets].sort((a,b)=>distance([p.x,p.y],a.approach)-distance([p.x,p.y],b.approach))[0];goTo(nearest.id);}});
window.addEventListener('keyup',e=>held.delete(e.key.length===1?e.key.toLowerCase():e.key));window.addEventListener('blur',()=>held.clear());window.addEventListener('offline',()=>{connected(false);updateLiveUI();});window.addEventListener('online',()=>{if(view)schedulePoll(1);});document.addEventListener('visibilitychange',()=>{held.clear();if(!document.hidden&&view)schedulePoll(1);});
productShell=createProductShell({
 getLanguage:()=>lang,
 onJoin:()=>{if($('#welcome').hidden)$('#join-mode').click();},
 onAgent:showAgentAccess,
 onGoal:()=>$('#quest-action').click()
});
boot();

// Aggregate diagnostics only: no tokens, texts, private state or control surface.
export function frontendDiagnostics(){return {events:ledger.byId.size,pending:bubbleQueue.pending.length,showing:bubbleQueue.showing.size,seen:bubbleQueue.seen.size,particles:renderer?.particles.length||0,assetFrames:renderer?.assets?.cache.size||0,roles:view?Object.keys(view.snapshot.entities).length:0,polling,mode,localPreferencePersistence:localPrefs.persistent,pendingPersistence:tabState.persistent,localHistoryLimited,audioEnabled:audioOn,audioState:audioCtx?.state||'off'};}
