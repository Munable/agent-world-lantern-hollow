import assert from 'node:assert/strict';
import {placeNameplates,travelerLayout,hitTraveler} from '../lantern_hollow/web/ui-layout.js';
let scenarios=0;
for(const n of [1,2,6,12])for(const distribution of ['same','adjacent','spread'])for(const width of [320,390,768,1280,1920])for(const zoom of [1,1.8,4]){
 const actors=Array.from({length:n},(_,i)=>({role_id:'a'+String(i).padStart(2,'0'),x:distribution==='same'?10:distribution==='adjacent'?10+i*.8:4+i*2,y:10}));
 const layout=travelerLayout(actors,a=>a,40);
 const candidates=layout.map((p,i)=>({id:p.actor.role_id,ax:width/2+(p.x-layout[0].x)*16*zoom,ay:150,w:Math.min(width*.4,160),h:16,priority:i===0?2:0}));
 const placed=placeNameplates(candidates,{width,height:300});assert.ok(placed.some(p=>p.id==='a00'));
 for(let i=0;i<placed.length;i++){const a=placed[i];assert.ok(a.x>=0&&a.x+a.w<=width&&a.y>=0&&a.y+a.h<=300);for(const b of placed.slice(i+1))assert.ok(a.x+a.w<=b.x||b.x+b.w<=a.x||a.y+a.h<=b.y||b.y+b.h<=a.y);}
 scenarios++;
}
for(const x of [0,18,39]){const a=Array.from({length:12},(_,i)=>({role_id:'r'+i,position:[x,10]}));const layout=travelerLayout(a,a=>({x:a.position[0],y:10}),40);assert.equal(new Set(layout.map(p=>p.x)).size,12);for(const p of layout)assert.equal(hitTraveler(layout,{x:p.x+.5,y:p.y+.1}).role_id,p.actor.role_id);}
console.log(`Nameplate bounds/nonoverlap/priority matrix PASS: ${scenarios}; 12-role edge hit mapping PASS`);
