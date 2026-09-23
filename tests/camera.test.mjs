import assert from 'node:assert/strict';
import {SceneCamera} from '../lantern_hollow/web/camera.js';
const c=new SceneCamera(640,416);
assert.deepEqual(c.project(100,200),{x:100,y:200});
c.follow('role-a');assert.equal(c.followId,'role-a');c.track(250,200);
for(const point of [[0,0],[99,211],[640,416]]){const p=c.project(...point),q=c.unproject(p.x,p.y);assert.ok(Math.abs(q.x-point[0])<1e-8);assert.ok(Math.abs(q.y-point[1])<1e-8);}
c.pan(20,5);assert.equal(c.followId,null);
c.scale(100);assert.equal(c.zoom,4);c.pan(1e6,1e6);assert.equal(c.x,80);assert.equal(c.y,52);
c.scale(.0001);assert.equal(c.zoom,1);assert.equal(c.x,320);assert.equal(c.y,208);
c.follow('role-b');c.track(-1000,10000);assert.ok(c.x>0&&c.y<416);
c.overview();assert.equal(c.zoom,1);assert.equal(c.followId,null);
console.log('camera inverse, bounds, pan/follow and zoom PASS');
