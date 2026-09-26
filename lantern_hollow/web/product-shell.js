// UI state is a projection of authorized snapshots, never a second world model.
export function sameArguments(a,b){
  const stable=value=>Array.isArray(value)?value.map(stable):value&&typeof value==='object'?Object.fromEntries(Object.keys(value).sort().map(k=>[k,stable(value[k])])):value;
  return JSON.stringify(stable(a))===JSON.stringify(stable(b));
}
const clamp = value => Math.max(0, Math.min(1, value));
export function goalFor(self, lang = 'zh') {
  if (!self) return null;
  const en = lang === 'en', count = self.shards?.length || 0;
  const stages = {
    arrival: {step:'01', title:en?'Meet the lightkeeper':'问候守灯人', action:en?'Find Elia ↗':'去找艾莉娅 ↗', target:'elia'},
    collect: {step:'02', title:en?`Star shards · ${count}/3`:`寻找星片 · ${count}/3`, action:en?'Find a shard ↗':'去找下一枚 ↗', target:['shard_moss','shard_sky','shard_water'].find(id=>!self.shards?.includes(id))},
    repair: {step:'03', title:en?'Bring the beacon home':'点亮归航灯塔', action:en?'To the beacon ↗':'前往灯塔 ↗', target:'beacon'},
    complete: {step:'✓', title:en?'A light for the next traveler':'为后来的人留一盏灯', action:en?'Leave a note ↗':'去留句话 ↗', target:'board'}
  };
  return stages[self.quest] || stages.arrival;
}
export function activityProgress(self, now) {
  const activity = self?.busy || self?.movement;
  if (!activity || !Number.isFinite(now)) return null;
  const start = activity.start_at;
  const end = activity.end_at ?? (start + Math.max(0, (activity.path?.length || 1)-1)*activity.step_seconds);
  if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start) return null;
  return {fraction:clamp((now-start)/(end-start)), awaiting:now>=end};
}
const $ = selector => document.querySelector(selector);
const setText = (selector, value) => {const el=$(selector);if(el && el.textContent!==value)el.textContent=value;};
export function createProductShell({onJoin, onAgent, onGoal, getLanguage}) {
  let state = {}, panel = 'live', identity = '', tickAt = 0;
  const mobile = matchMedia('(max-width: 900px)');
  const journal = $('#journal');
  function openPanel(next, focus = false) {
    if (next === 'journey' && !state.self) next = 'live';
    if (next !== 'scene') panel = next;
    journal.classList.toggle('open', next !== 'scene');
    journal.dataset.panel = panel;
    $('#panel-journey').hidden = panel !== 'journey';
    $('#panel-live').hidden = panel !== 'live';
    for (const button of document.querySelectorAll('[data-panel-target]')) {
      const target = button.dataset.panelTarget;
      const active = button.closest('.mobile-dock') ? (journal.classList.contains('open') ? target===panel : target==='scene') : target===panel;
      button.setAttribute('aria-pressed', String(active));
    }
    $('#journal-toggle').setAttribute('aria-expanded', String(journal.classList.contains('open')));
    if (focus) {
      if(next==='scene') $('#world').focus({preventScroll:true});
      else if(mobile.matches) $('#tab-'+panel).focus({preventScroll:true});
    }
  }
  for (const b of document.querySelectorAll('[data-panel-target]')) b.onclick=()=>openPanel(b.dataset.panelTarget,true);
  $('#panel-close').onclick=()=>openPanel('scene',true);
  $('#journal-toggle').onclick=()=>openPanel(journal.classList.contains('open')?'scene':(state.self?'journey':'live'),true);
  $('#arrival-join').onclick=()=>{openPanel('scene');onJoin();};
  $('#arrival-agent').onclick=onAgent;$('#agent-entry').onclick=onAgent;
  $('#goal-action').onclick=()=>{openPanel('scene');if(state.canControl)onGoal();else onAgent();};
  $('#welcome-close').onclick=()=>{$('#welcome').hidden=true;$('#join-mode').focus({preventScroll:true});};
  window.addEventListener('keydown',e=>{if(e.key==='Escape'&&mobile.matches&&journal.classList.contains('open')&&!$('#modal').open){e.preventDefault();e.stopImmediatePropagation();openPanel('scene',true);}},{capture:true});
  mobile.addEventListener('change',()=>openPanel('scene'));
  matchMedia('(max-width:600px)').addEventListener('change',()=>update(state));
  function update(next) {
    state = next;
    const en=getLanguage()==='en', compact=matchMedia('(max-width:600px)').matches, key=`${next.mode}:${next.roleId || ''}`;
    if(key!==identity){identity=key;panel=next.self?'journey':'live';openPanel('scene');}
    const labels={
      '#agent-entry':compact?'Agent ↗':en?'Agent access ↗':'Agent 接入 ↗', '#arrival-agent':en?'Bring my Agent ↗':'带上我的 Agent ↗',
      '#arrival-join':en?'Explore as a new traveler':'我先亲自走走', '#arrival-title':en?'The village is still alight.':'小镇还亮着灯。',
      '#arrival-copy':en?'Bring your Agent, or explore as a traveler yourself. The world remembers what happens here.':'让你的 Agent 来走走，或亲自成为一位旅人。世界会记住已经发生的事。',
      '#tab-journey':en?'Your journal':'旅人手记', '#tab-live':en?'The village':'世界现场',
      '#dock-scene-label':en?'Scene':'场景', '#dock-journey-label':en?'Journal':'手记', '#dock-live-label':en?'Village':'现场',
      '#world-disclosure-label':en?'Roles & public information':'关于角色与公开信息', '#art-tools-label':en?'Artwork':'素材',
      '#goal-caption':en?'YOUR NEXT STEP':'今晚的小事 · 当前目标',
      '#entry-boundary':en?'This creates a new, directly controlled traveler. Already have an Agent role? Use Agent access instead.':'这里会新建一个由你直接操作的旅人。已有 Agent 角色，请用顶部的 Agent 接入。'
    };
    for(const [selector,label] of Object.entries(labels))setText(selector,label);
    $('#tab-journey').hidden=!next.self;
    $('#dock-journey').disabled=!next.self;
    $('#arrival-card').hidden=next.mode!=='spectate';
    $('#scene-objective').hidden=!next.connected && !next.self;
    const goal=next.canControl?goalFor(next.self,getLanguage()):{step:'◌',title:en?'A shared world. Your own traveler.':'共享的小镇，你自己的旅人。',action:en?'Agent access ↗':'Agent 接入 ↗'};
    if(!next.canControl)setText('#goal-caption',en?'WATCH, OR JOIN THE STORY':'可以旁观，也可以参与');
    if(goal){setText('#goal-step',goal.step);setText('#goal-title',goal.title);setText('#goal-action',goal.action);}
    $('#goal-action').disabled=next.canControl && (next.working || !!next.pending);
    $('#goal-action').setAttribute('aria-label',goal?.action || (en?'Current objective':'当前目标'));
    const waiting = next.working ? (en?'Submitting to the world…':'正在提交给世界…') : next.pending ? (en?'Result unconfirmed. Do not repeat the action.':'结果待确认，请勿重复提交。') : !next.connected ? (en?'Connection interrupted. Your progress is not reset.':'连接中断，角色进度不会因此重置。') : '';
    setText('#action-feedback',waiting);$('#action-feedback').hidden=!waiting;
    $('#world').setAttribute('aria-busy',String(!!next.working));
    setText('#help',compact?'?':en?'Guide':'怎么玩');$('#help').setAttribute('aria-label',en?'How to play':'怎么玩');
    $('#welcome-close').setAttribute('aria-label',en?'Cancel joining':'取消进入小镇');
    $('#panel-close').setAttribute('aria-label',en?'Back to the scene':'回到场景');
    $('#zoom-in').setAttribute('aria-label',en?'Zoom in':'放大场景');$('#zoom-out').setAttribute('aria-label',en?'Zoom out':'缩小场景');
    $('#overview').setAttribute('aria-label',en?'Whole map':'查看全图');
    $('#activity-meter').setAttribute('aria-label',en?'Accepted activity progress':'已接受活动的进度');
    $('#scene-objective').setAttribute('aria-label',en?'Current objective':'当前目标');
    $('#journal').setAttribute('aria-label',en?'Your journal and village activity':'旅人手记与世界现场');
  }
  function tick(now, frameTime) {
    if(frameTime-tickAt<200)return;tickAt=frameTime;
    const progress=state.canControl?activityProgress(state.self,now):null;
    const meter=$('#activity-meter');meter.hidden=!progress;
    if(progress){
      meter.setAttribute('aria-valuemin','0');meter.setAttribute('aria-valuemax','100');
      meter.setAttribute('aria-valuenow',String(Math.floor(progress.fraction*100)));
      $('#activity-progress').style.transform=`scaleX(${progress.fraction})`;
      if(progress.awaiting)setText('#activity-label',getLanguage()==='en'?'Waiting for the world to confirm…':'等待世界确认结果…');
    }
  }
  return {update, tick, openPanel};
}
