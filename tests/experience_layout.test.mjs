import assert from 'node:assert/strict';
import {placeBubble,travelerLayout,hitTraveler} from '../lantern_hollow/web/ui-layout.js';
const actors=Array.from({length:6},(_,i)=>({role_id:'role-'+i,position:[18,21]}));
const layout=travelerLayout(actors,a=>({x:a.position[0],y:a.position[1]}),40);
assert.equal(new Set(layout.map(p=>p.x)).size,6);
for(const p of layout)assert.equal(hitTraveler(layout,{x:p.x+.5,y:p.y+.1}).role_id,p.actor.role_id);
assert.deepEqual(actors.map(a=>a.position),actors.map(()=>[18,21]));
for(const width of [280,365,640,1280])for(const height of [170,235,416]){
 const occupied=[];for(let i=0;i<8;i++){
  const rect=placeBubble({x:width/2,y:height/2},Math.min(240,width-20),75,{width,height},occupied);
  if(!rect)continue;assert.ok(rect.x>=0&&rect.y>=0&&rect.x+rect.w<=width&&rect.y+rect.h<=height);
  for(const old of occupied)assert.ok(rect.x+rect.w<=old.x||old.x+old.w<=rect.x||rect.y+rect.h<=old.y||old.y+old.h<=rect.y);
  occupied.push(rect);
 }
}
assert.equal(placeBubble({x:0,y:0},500,300,{width:200,height:200},[]),null);
console.log('shared sprite layout/hit and bounded nonoverlap bubble placement PASS');
