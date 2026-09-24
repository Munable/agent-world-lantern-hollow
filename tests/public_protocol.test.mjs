import assert from 'node:assert/strict';
import {applyView,Feed,position} from '../examples/protocol-client/model.js';
const a={kind:'snapshot',view:'spectator',viewer_role_id:null,cursor:'a',world_version:2,view_version:1,snapshot:{entities:{one:{kind:'traveler',position:[1,1]}},resources:{},meta:{self:null}}};
const b={...a,kind:'delta',base_cursor:'a',cursor:'a',delta:{entities:{upsert:{},remove:[]},resources:{upsert:{},remove:[]},meta:{self:null}}};
const first=applyView(null,a);assert.equal(applyView(first,b).cursor,'a');assert.throws(()=>applyView(first,{...b,base_cursor:'old'}));
assert.throws(()=>applyView(null,{...a,viewer_role_id:'private'}));assert.throws(()=>applyView(null,{...a,snapshot:{...a.snapshot,meta:{self:{}}}}));
const feed=new Feed();const events=Array.from({length:800},(_,i)=>({event_id:String(i),seq:i}));feed.ingest(events);feed.ingest(events);assert.equal(feed.items.size,600);assert.equal(feed.values()[0].seq,200);
assert.deepEqual(position({position:[0,0],movement:{path:[[0,0],[2,0]],start_at:10,step_seconds:2}},11),[1,0]);
console.log('Independent public snapshot/delta, dedup, bounded feed and motion PASS');

assert.throws(()=>applyView(null,{...a,view_version:99}));
