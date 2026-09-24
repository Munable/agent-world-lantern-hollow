// Independent implementation of docs/PUBLIC_CLIENT_CONTRACT.md. No game imports.
const record=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
export function applyView(current,next){
 if(!record(next)||next.viewer_role_id!==null||next.view!=='spectator'||!['snapshot','delta'].includes(next.kind)||typeof next.cursor!=='string'||next.view_version!==1||!Number.isInteger(next.world_version))throw new Error('Expected an anonymous spectator view');
 let body;
 if(next.kind==='snapshot')body=structuredClone(next.snapshot);
 else{
  if(!current||next.base_cursor!==current.cursor||next.world_version!==current.world_version||next.view_version!==current.view_version)throw new Error('RESET_VIEW');
  body=structuredClone(current.snapshot);
  for(const key of ['entities','resources']){
   const changes=next.delta?.[key];if(!record(changes)||!record(changes.upsert)||!Array.isArray(changes.remove))throw new Error('Invalid delta');
   for(const id of changes.remove)delete body[key][id];
   for(const [id,value]of Object.entries(changes.upsert))Object.defineProperty(body[key],id,{value:structuredClone(value),enumerable:true,writable:true,configurable:true});
  }body.meta=structuredClone(next.delta.meta);
 }
 if(!record(body)||!record(body.entities)||!record(body.resources)||!record(body.meta)||body.meta.self!==null||Object.keys(body.entities).length>256)throw new Error('Invalid public snapshot');
 for(const a of Object.values(body.entities)){
  if(!record(a))throw new Error('Invalid entity');if(a.kind!=='traveler')continue;
  if(!Array.isArray(a.position)||a.position.length!==2||!a.position.every(Number.isFinite))throw new Error('Invalid position');
  const m=a.movement;if(m&&(!Array.isArray(m.path)||!m.path.length||m.path.length>4096||!m.path.every(p=>Array.isArray(p)&&p.length===2&&p.every(Number.isFinite))||!Number.isFinite(m.start_at)||!Number.isFinite(m.end_at)||!Number.isFinite(m.step_seconds)||m.step_seconds<=0))throw new Error('Invalid motion');
 }
 return {...next,snapshot:body};
}
export function position(actor,now){
 const m=actor.movement;if(!m||!Array.isArray(m.path)||m.path.length<1||!Number.isFinite(m.step_seconds)||m.step_seconds<=0)return actor.position;
 const progress=Math.min(m.path.length-1,Math.max(0,(now-m.start_at)/m.step_seconds)),i=Math.floor(progress),j=Math.min(i+1,m.path.length-1),f=progress-i;
 return [m.path[i][0]+(m.path[j][0]-m.path[i][0])*f,m.path[i][1]+(m.path[j][1]-m.path[i][1])*f];
}
export class Feed{
 constructor(limit=600){this.limit=limit;this.items=new Map();}
 ingest(events,historical=false){const fresh=[];for(const e of events){if(typeof e.event_id!=='string'||this.items.has(e.event_id))continue;const entry={...e,historical};this.items.set(e.event_id,entry);fresh.push(entry);}const sorted=this.values();while(sorted.length>this.limit)this.items.delete(sorted.shift().event_id);return fresh;}
 values(){return [...this.items.values()].sort((a,b)=>a.seq-b.seq);}
}
