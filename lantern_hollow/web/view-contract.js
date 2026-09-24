// Reference renderer contract, not a replacement for server authorization.
const object=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
export class ViewContractError extends Error{}
export function validateMap(m){
 if(!object(m)||m.world_id!=='lantern-hollow'||m.presentation_version!==1||!Number.isInteger(m.width)||!Number.isInteger(m.height)||m.width<1||m.width>256||m.height<1||m.height>256||!Array.isArray(m.tiles)||m.tiles.length!==m.height||!m.tiles.every(row=>Array.isArray(row)&&row.length===m.width)||!Array.isArray(m.blocked)||!Array.isArray(m.targets)||!Array.isArray(m.buildings)||!Array.isArray(m.trees))throw new ViewContractError('Unsupported or invalid reference world');
 return m;
}
export function nextView(current,update,viewer,map){
 if(!object(update)||!['snapshot','delta'].includes(update.kind)||update.viewer_role_id!==viewer||update.view!==(viewer===null?'spectator':'village')||typeof update.cursor!=='string'||update.view_version!==(viewer===null?1:2)||!Number.isFinite(update.observed_at)||update.world_version!==map.world_version)throw new ViewContractError('Unexpected observation scope or version');
 let snapshot;
 if(update.kind==='snapshot')snapshot=structuredClone(update.snapshot);
 else{
  if(!current||current.cursor!==update.base_cursor||current.view_version!==update.view_version||current.world_version!==update.world_version)throw new ViewContractError('Mismatched view checkpoint');
  snapshot=structuredClone(current.snapshot);
  for(const part of ['entities','resources']){const d=update.delta?.[part];if(!object(d)||!object(d.upsert)||!Array.isArray(d.remove))throw new ViewContractError('Invalid delta');
   for(const key of d.remove)delete snapshot[part][key];
   for(const [key,value]of Object.entries(d.upsert))Object.defineProperty(snapshot[part],key,{value:structuredClone(value),enumerable:true,writable:true,configurable:true});
  }snapshot.meta=structuredClone(update.delta.meta);
 }
 if(!object(snapshot)||!object(snapshot.entities)||!object(snapshot.resources)||!object(snapshot.meta)||Object.keys(snapshot.entities).length>256||(viewer===null?snapshot.meta.self!==null:snapshot.meta.self?.role_id!==viewer))throw new ViewContractError('Invalid observation body');
 for(const [id,a] of Object.entries(snapshot.entities)){if(!object(a))throw new ViewContractError('Invalid entity');if(a.kind!=='traveler')continue;
  if(typeof a.name!=='string'||a.role_id!==id||!Array.isArray(a.position)||a.position.length!==2||!a.position.every(Number.isFinite))throw new ViewContractError('Invalid traveler');
  const m=a.movement;if(m&&(!Array.isArray(m.path)||m.path.length<1||m.path.length>4096||!m.path.every(p=>Array.isArray(p)&&p.length===2&&p.every(Number.isFinite))||!Number.isFinite(m.start_at)||!Number.isFinite(m.end_at)||m.end_at<m.start_at||!Number.isFinite(m.step_seconds)||m.step_seconds<=0))throw new ViewContractError('Invalid motion');
  if(a.busy&&(!object(a.busy)||!Number.isFinite(a.busy.start_at)||!Number.isFinite(a.busy.end_at)||a.busy.end_at<=a.busy.start_at))throw new ViewContractError('Invalid activity');
 }
 return {...update,snapshot};
}
