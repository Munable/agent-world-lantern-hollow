import assert from 'node:assert/strict';
import {nextView,ViewContractError} from '../lantern_hollow/web/view-contract.js';
import {safeStorage} from '../lantern_hollow/web/browser-storage.js';
const base={view:'spectator',viewer_role_id:null,world_version:2,view_version:1,kind:'snapshot',cursor:'a',observed_at:100,snapshot:{entities:{},resources:{},meta:{self:null}}};
const delta={...base,kind:'delta',base_cursor:'a',delta:{entities:{upsert:{},remove:[]},resources:{upsert:{},remove:[]},meta:{self:null}}};
const current=nextView(null,base,null,{world_version:2});assert.equal(nextView(current,delta,null,{world_version:2}).cursor,'a');
assert.throws(()=>nextView(current,{...delta,base_cursor:'bad'},null,{world_version:2}),ViewContractError);
assert.throws(()=>nextView(null,{...base,viewer_role_id:'other'},null,{world_version:2}),ViewContractError);
assert.throws(()=>nextView(null,{...base,snapshot:{...base.snapshot,meta:{self:{role_id:'secret'}}}},null,{world_version:2}),ViewContractError);
const host={get localStorage(){throw new Error('storage denied');}},store=safeStorage('localStorage',host);assert.equal(store.getItem('x'),null);store.setItem('x','ok');assert.equal(store.getItem('x'),'ok');store.removeItem('x');assert.equal(store.getItem('x'),null);assert.equal(store.persistent,false);
console.log('View scope, matching checkpoint, same cursor and denied browser storage PASS');

assert.throws(()=>nextView(null,{...base,view_version:99},null,{world_version:2}),ViewContractError);
const quota={localStorage:{getItem:()=>null,setItem:()=>{throw new Error('quota')},removeItem:()=>{}}};
const temp=safeStorage('localStorage',quota);temp.setItem('pending','keep');assert.equal(temp.getItem('pending'),'keep');temp.removeItem('pending');assert.equal(temp.getItem('pending'),null);
console.log('Unknown views rejected and write-only storage failure preserves in-page state PASS');

const privateView={...base,view:'village',viewer_role_id:'me',view_version:2,snapshot:{entities:{},resources:{},meta:{self:{role_id:'me'}}}};assert.equal(nextView(null,privateView,'me',{world_version:2}).view_version,2);assert.throws(()=>nextView(null,{...privateView,view_version:1},'me',{world_version:2}),ViewContractError);
