// Bounded local layout helpers. These positions never become world coordinates.
export function placeBubble(anchor,width,height,bounds,occupied,margin=8){
 if(width>bounds.width-2*margin||height>bounds.height-2*margin)return null;
 const clamp=(v,lo,hi)=>Math.max(lo,Math.min(hi,v));
 const xs=[clamp(anchor.x-width/2,margin,bounds.width-width-margin),margin,bounds.width-width-margin];
 const ys=[anchor.y-height-margin,...occupied.flatMap(r=>[r.y-height-margin,r.y+r.h+margin]),margin,bounds.height-height-margin];
 for(const x of xs)for(const candidate of ys){const y=clamp(candidate,margin,bounds.height-height-margin);
  if(occupied.every(r=>x+width+margin<=r.x||x>=r.x+r.w+margin||y+height+margin<=r.y||y>=r.y+r.h+margin))return {x,y,w:width,h:height};
 }
 return null;
}
export function travelerLayout(actors,positionAt,width){
 const placed=actors.map(actor=>({actor,...positionAt(actor)}));
 return placed.map(item=>{
  const group=placed.filter(p=>Math.abs(p.x-item.x)<.15&&Math.abs(p.y-item.y)<.15).sort((a,b)=>a.actor.role_id.localeCompare(b.actor.role_id));
  const index=group.findIndex(p=>p.actor.role_id===item.actor.role_id);
  return {...item,x:Math.max(.25,Math.min(width-.75,item.x+(index-(group.length-1)/2)*.55)),group:group.map(p=>p.actor.role_id)};
 });
}
export function hitTraveler(layout,point){
 return layout.filter(p=>Math.abs(point.x-p.x-.5)<.65&&point.y>p.y-.82&&point.y<p.y+1.1)
  .sort((a,b)=>Math.hypot(point.x-a.x-.5,point.y-a.y-.15)-Math.hypot(point.x-b.x-.5,point.y-b.y-.15))[0]?.actor||null;
}
