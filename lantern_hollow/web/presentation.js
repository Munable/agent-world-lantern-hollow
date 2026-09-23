// Local presentation only. No network, model calls, authority or world writes.
export class ServerClock {
  constructor(monotonic=()=>performance.now()/1000, initial=Date.now()/1000) {
    this.monotonic=monotonic;this.anchor=monotonic();this.server=initial;
  }
  sync(serverTime) {
    if(!Number.isFinite(serverTime))return false;
    this.server=serverTime;this.anchor=this.monotonic();return true;
  }
  now(){return this.server+Math.max(0,this.monotonic()-this.anchor);}
}

export function cueSource(cue) {
  if(cue?.name==='public_expression')return 'authored';
  if(cue?.name==='dialogue')return 'scripted';
  return 'system';
}

// Deadlines are enforced once, by the shared BubbleQueue, not by a second scheduler.
export function bubbleFromEvent(event) {
  const p=event?.payload,d=p?.data;
  if(event?.kind!=='world.presentation'||event.historical||p?.phase!=='start'||
     !['speech','intent'].includes(p.channel)||typeof d?.text!=='string'||!d.text||
     typeof p.subject_id!=='string'||!Number.isFinite(d.at)||!Number.isFinite(d.expires_at)||
     d.expires_at<=d.at)return null;
  return {id:event.event_id,subject:p.subject_id,channel:p.channel,text:d.text,en:d.en,
          at:d.at,expires_at:d.expires_at,source:cueSource(p)};
}
