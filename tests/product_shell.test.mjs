import assert from 'node:assert/strict';
import {goalFor,activityProgress,sameArguments} from '../lantern_hollow/web/product-shell.js';
import {SceneCamera} from '../lantern_hollow/web/camera.js';
assert.equal(sameArguments({x:1,y:[2,3]},{y:[2,3],x:1}),true);
assert.equal(sameArguments({x:[1,2]},{x:[2,1]}),false);
assert.equal(goalFor(null),null);
assert.equal(goalFor({quest:'arrival'}).target,'elia');
assert.equal(goalFor({quest:'collect',shards:['shard_moss']}).target,'shard_sky');
assert.match(goalFor({quest:'collect',shards:['shard_moss']},'en').title,/1\/3/);
assert.equal(goalFor({quest:'repair'}).target,'beacon');
assert.equal(goalFor({quest:'complete'}).target,'board');
const actor={movement:{start_at:10,step_seconds:1,path:[[0,0],[1,0],[2,0]]}};
assert.deepEqual(activityProgress(actor,9),{fraction:0,awaiting:false});
assert.deepEqual(activityProgress(actor,11),{fraction:.5,awaiting:false});
assert.deepEqual(activityProgress(actor,13),{fraction:1,awaiting:true});
assert.equal(activityProgress({},20),null);
assert.equal(activityProgress({busy:{start_at:10,end_at:10}},20),null);
assert.equal(activityProgress(actor,NaN),null);
for(const width of [160,290,364,640,1100]) {
  const camera=new SceneCamera(640,416);camera.setViewport(width,416);camera.overview();
  assert.equal(camera.zoom,Math.min(1,width/640));
  for(const point of [[0,0],[320,208],[640,416]]) {
    const screen=camera.project(...point),back=camera.unproject(screen.x,screen.y);
    assert.ok(Math.abs(back.x-point[0])<1e-9 && Math.abs(back.y-point[1])<1e-9);
  }
  camera.follow('role');camera.track(630,400);
  assert.ok(camera.x<=640 && camera.y<=416);
  const zoom=camera.zoom;camera.setViewport(width,416);assert.equal(camera.zoom,zoom);
}
console.log('Product goals, authoritative progress and portrait camera invariants PASS');
