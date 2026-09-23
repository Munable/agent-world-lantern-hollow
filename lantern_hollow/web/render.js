// Original pixel-art renderer. World positions and actions always come from the server.
import {ServerClock} from './presentation.js';
const T=16;
const C={grass:['#4d674c','#4f6a4f','#516d51','#536e51'],deep:'#233d3b',leaf:'#345547',light:'#8ca56c',water:'#294e58',ink:'#202c35',gold:'#e9b76a'};
function rand(n){let x=Math.sin(n*127.1+311.7)*43758.5453;return x-Math.floor(x);}
function rect(c,x,y,w,h,color){c.fillStyle=color;c.fillRect(Math.round(x),Math.round(y),Math.round(w),Math.round(h));}
function poly(c,p,color){c.fillStyle=color;c.beginPath();p.forEach(([x,y],i)=>i?c.lineTo(Math.round(x),Math.round(y)):c.moveTo(Math.round(x),Math.round(y)));c.closePath();c.fill();}
function ellipse(c,x,y,rx,ry,color){c.fillStyle=color;c.beginPath();c.ellipse(x,y,rx,ry,0,0,Math.PI*2);c.fill();}
function line(c,a,b,color,width=1){c.strokeStyle=color;c.lineWidth=width;c.beginPath();c.moveTo(...a);c.lineTo(...b);c.stroke();}

function sprite(kind,dir,frame){
 const canvas=document.createElement('canvas');canvas.width=24;canvas.height=32;const c=canvas.getContext('2d');
 const palettes={traveler:['#44677b','#81a6a0','#583f36','#e6b780'],sage:['#646284','#b7b1cc','#cbc5b8','#e1b994'],rose:['#8c576a','#c494a0','#49382e','#e4b392'],keeper:['#777e70','#c4b59b','#cfb98b','#deb391'],smith:['#785849','#ba8660','#453836','#dba780'],gardener:['#516f54','#9daa77','#775541','#ecc197']};
 const [coat,trim,hair,skin]=palettes[kind]||palettes.traveler;
 const step=[0,1,0,-1][frame%4],back=dir==='up',side=dir==='left'||dir==='right',left=dir==='left';
 if(left){c.translate(24,0);c.scale(-1,1);}
 // Boots, moving legs, coat outline, shoulder silhouette.
 rect(c,8,25+Math.max(0,step),4,4,'#202c35');rect(c,14,25+Math.max(0,-step),4,4,'#202c35');
 rect(c,8,26+Math.max(0,step),4,2,'#6a5043');rect(c,14,26+Math.max(0,-step),4,2,'#6a5043');
 rect(c,7,16,12,10,'#27333b');rect(c,8,16,10,10,coat);rect(c,9,17,8,7,trim);rect(c,10,18,7,8,coat);
 rect(c,5,17+step,3,7,'#28323a');rect(c,6,18+step,2,4,coat);rect(c,6,22+step,2,2,skin);
 rect(c,18,17-step,3,7,'#28323a');rect(c,18,18-step,2,4,coat);rect(c,18,22-step,2,2,skin);
 rect(c,8,23,10,2,'#4d4138');rect(c,13,23,2,2,'#d1ad72');
 // Head with stepped silhouette and directional face.
 rect(c,7,6,11,2,'#26333a');rect(c,5,8,15,7,'#26333a');rect(c,7,15,11,2,'#26333a');
 rect(c,7,8,11,7,skin);rect(c,8,14,9,2,'#c6926d');
 rect(c,6,7,13,5,hair);rect(c,8,5,9,3,hair);rect(c,5,9,3,5,hair);rect(c,17,8,3,6,hair);
 rect(c,8,7,9,1,'#ebcf9d');
 if(back){rect(c,7,8,11,7,hair);rect(c,8,13,9,2,'#65533e');rect(c,9,17,7,6,'#6d5945');rect(c,10,18,5,4,'#b59867');}
 else if(side){rect(c,14,11,2,2,'#26333a');rect(c,18,12,2,2,skin);rect(c,9,7,7,2,hair);}
 else{rect(c,9,11,2,2,'#26333a');rect(c,15,11,2,2,'#26333a');rect(c,9,13,2,1,'#e0a38b');rect(c,15,13,2,1,'#e0a38b');}
 if(kind==='traveler'||kind==='sage'||kind==='rose'){rect(c,8,16,10,2,'#c17e50');rect(c,9,17,3,4,'#e1b16d');}
 if(kind==='gardener'){rect(c,4,7,18,2,'#b29d6e');rect(c,7,4,11,3,'#c8b581');rect(c,14,5,3,2,'#9c715b');}
 if(kind==='keeper'){rect(c,7,5,11,2,'#789190');rect(c,9,3,7,2,'#668580');rect(c,18,21-step,3,5,'#f1c783');}
 if(kind==='smith'){rect(c,10,18,6,7,'#55413b');rect(c,13,18,1,5,'#9a7860');}
 return canvas;
}

export class VillageRenderer{
 constructor(canvas,map){
  this.canvas=canvas;this.ctx=canvas.getContext('2d',{alpha:false});this.map=map;canvas.width=map.width*T;canvas.height=map.height*T;
  this.ctx.imageSmoothingEnabled=false;this.bg=document.createElement('canvas');this.bg.width=canvas.width;this.bg.height=canvas.height;
  this.atlas=new Map();this.scene=null;this.selfId=null;this.clock=new ServerClock();this.hover=null;this.destination=null;this.target=null;this.particles=[];this.last=0;this.reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;this.connected=true;
  this.drawBase();
 }
 update(scene,selfId,serverTime){this.scene=scene;this.selfId=selfId;this.clock.sync(serverTime);}
 now(){return this.clock.now();}
 getFrame(kind,dir,frame){const key=`${kind}:${dir}:${frame}`;if(!this.atlas.has(key))this.atlas.set(key,sprite(kind,dir,frame));return this.atlas.get(key);}
 actorPosition(a,now=this.now()){
  const m=a?.movement;if(!m)return {x:a?.position?.[0]??18,y:a?.position?.[1]??21,dir:a?.facing||'up',moving:false};
  const s=Math.max(0,Math.min((now-m.start_at)/m.step_seconds,m.path.length-1)),i=Math.floor(s),j=Math.min(i+1,m.path.length-1),f=s-i;
  const p=m.path[i],q=m.path[j],previous=m.path[Math.max(0,i-1)];
  const dx=j===i?p[0]-previous[0]:q[0]-p[0],dy=j===i?p[1]-previous[1]:q[1]-p[1];
  return {x:p[0]+(q[0]-p[0])*f,y:p[1]+(q[1]-p[1])*f,dir:dx>0?'right':dx<0?'left':dy>0?'down':dy<0?'up':a.facing||'down',moving:s<m.path.length-1};
 }
 project(x,y){return {x:(x*T+T/2)/this.canvas.width*100,y:((y+1)*T-30)/this.canvas.height*100};}
 event(e){
  if(e.kind!=='world.presentation')return;const p=e.payload;
  if(p.name==='collect'||p.name==='repair'&&p.phase==='finish'){
   if(this.reduced)return;
   const a=this.scene?.entities?.[p.subject_id],pos=this.actorPosition(a);
   for(let i=0;i<(p.name==='repair'?50:18);i++)this.particles.push({x:pos.x*T+8,y:pos.y*T-8,vx:(rand(i+e.seq)-.5)*45,vy:-20-rand(i*2+e.seq)*35,life:1.8,age:0,color:i%3?'#f2c97f':'#ffefba'});
  }
 }
 drawBase(){
  const c=this.bg.getContext('2d');c.imageSmoothingEnabled=false;
  for(let y=0;y<this.map.height;y++)for(let x=0;x<this.map.width;x++){
   const k=this.map.tiles[y][x],px=x*T,py=y*T,n=x+y*77,r=rand(n);
   if(k==='water'){rect(c,px,py,T,T,['#294e58','#2c535d','#305b62'][n%3]);for(let i=0;i<3;i++)rect(c,px+Math.floor(rand(n+i*3)*12),py+i*5,4,1,'#48767a');}
   else if(k==='cliff'){
    rect(c,px,py,T,T,'#293f3e');rect(c,px,py+2,T,3,'#3b534a');rect(c,px+2,py+7,9,5,'#344940');rect(c,px+1,py+13,6,2,'#24383a');
   }else if(k==='bridge'){
    rect(c,px,py,T,T,'#343e3e');for(let i=0;i<4;i++){rect(c,px,py+i*4,16,3,i%2?'#a78059':'#b28e65');rect(c,px+3,py+i*4,1,1,'#604e43');rect(c,px+13,py+i*4,1,1,'#604e43');}
   }else if(k==='path'||k==='stone'){
    rect(c,px,py,T,T,k==='stone'?'#777c6b':'#8f846b');
    for(let i=0;i<3;i++){const xx=Math.floor(rand(n+i+1)*11),yy=i*5;rect(c,px+xx,py+yy,5,3,r>.5?'#aaa18a':'#9a927d');rect(c,px+xx,py+yy+3,5,1,'#746f5c');}
    if(k==='path'){for(let i=0;i<3;i++)rect(c,px+Math.floor(rand(n+i*11)*15),py+Math.floor(rand(n+i*5)*15),1,1,'#b6a487');}
   }else{
    rect(c,px,py,T,T,C.grass[n%4]);for(let i=0;i<5;i++){const xx=Math.floor(rand(n+i*9)*14),yy=Math.floor(rand(n+i*3)*15);rect(c,px+xx,py+yy,1,2,'#65805a');rect(c,px+xx+1,py+yy+1,1,1,'#708963');}
    if(r>.86){rect(c,px+6,py+8,1,3,'#718b61');rect(c,px+5,py+7,3,2,n%2?'#c6ae77':'#9eb08c');}
   }
   if(k==='grass'||k==='path'){if(x+1<this.map.width&&this.map.tiles[y][x+1]==='water'){rect(c,px+13,py,3,16,'#294b40');rect(c,px+12,py,1,16,'#84947a');}if(x>0&&this.map.tiles[y][x-1]==='water'){rect(c,px,py,3,16,'#294b40');rect(c,px+3,py,1,16,'#84947a');}}
  }
  // Flower beds, courtyard paving, timber fences and border stones.
  for(const [x,y,w] of [[4,20,4],[12,8,3],[22,14,3]]){rect(c,x*T,y*T,w*T,10,'#3b4435');for(let i=0;i<w*6;i++){let xx=x*T+i*2.5;rect(c,xx,y*T+4+rand(i)*4,1,4,'#7d9867');rect(c,xx-1,y*T+3+rand(i)*4,3,2,i%3?'#d5b388':'#ae8191');}}
  for(let x=3;x<14;x++){if(x===10||x===11)continue;rect(c,x*T,22*T,3,11,'#534b3b');rect(c,x*T+1,22*T,2,2,'#d1b47e');rect(c,x*T,22*T+4,16,2,'#9c875d');rect(c,x*T,22*T+8,16,2,'#9c875d');}
  for(let x=30;x<38;x++){rect(c,x*T,21*T,3,11,'#4b4b40');rect(c,x*T,21*T+3,16,2,'#9a8662');}
  for(const [x,y] of [[26,11],[31,11],[26,12],[31,12]]){rect(c,x*T,y*T+2,3,12,'#483d34');rect(c,x*T,y*T,4,3,'#c1a076');}
  // Subtle stepping stones and grasses, outside paths only.
  for(const [x,y] of [[15,17],[23,9],[33,14],[8,13],[15,12]]){ellipse(c,x*T+5,y*T+9,7,3,'#3b5147');rect(c,x*T,y*T+6,11,4,'#92957a');rect(c,x*T+2,y*T+5,7,1,'#b1b59a');}
 }
 tree(c,x,y,seed,big=false){
  x=x*T+8;y=(y+1)*T;const scale=big?1.65:1;
  c.save();c.translate(Math.round(x),Math.round(y));c.scale(scale,scale);
  ellipse(c,0,-1,17,6,'#344c40');rect(c,-4,-27,8,25,'#3d3b30');rect(c,-2,-28,3,26,'#76654b');rect(c,1,-19,2,16,'#544d3a');
  const layers=[[-18,-45,35,15,'#263f3b'],[-23,-36,45,19,'#2c4a3f'],[-20,-46,38,16,'#3a5b45'],[-16,-55,30,17,'#496947'],[-9,-60,18,13,'#56734d']];
  for(const [a,b,w,h,color] of layers){rect(c,a+3,b,w-6,h,color);rect(c,a,b+4,w,h-8,color);}
  for(let i=0;i<27;i++){const a=Math.floor(rand(seed+i)*36)-18,b=-51+Math.floor(rand(seed+i*2+19)*26);rect(c,a,b,4+Math.floor(rand(i)*3),2,i%3?'#5e7c51':'#7b915d');}
  for(let i=0;i<5;i++){const a=-17+i*8;rect(c,a,-26,2,9+Math.floor(rand(seed+i)*11),'#3c5943');rect(c,a+1,-22,1,5,'#6c8053');}
  c.restore();
 }
 building(c,b,now,lit){
  const x=b.x*T,y=b.y*T,w=b.w*T,h=b.h*T;
  ellipse(c,x+w/2,y+h,w*.6,9,'#374738');
  if(b.kind==='tower'){
   rect(c,x+9,y-6,w-18,h+6,'#414e51');rect(c,x+12,y-8,w-24,h+8,'#919386');rect(c,x+17,y-8,w-34,h+8,'#b3afa0');
   for(let yy=y;yy<y+h-2;yy+=9){rect(c,x+12,yy,w-24,1,'#747b72');for(let xx=x+13+(yy%2)*7;xx<x+w-12;xx+=15)rect(c,xx,yy,1,9,'#7e867c');}
   rect(c,x+8,y-19,w-16,13,'#34494b');rect(c,x+15,y-38,w-30,20,'#283d46');
   rect(c,x+19,y-36,w-38,15,lit?'#f7d286':'#839b91');rect(c,x+w/2-1,y-36,2,16,'#384b47');
   poly(c,[[x+5,y-39],[x+w/2,y-62],[x+w-5,y-39]],'#334e54');poly(c,[[x+11,y-40],[x+w/2,y-57],[x+w/2,y-40]],'#618080');
   rect(c,x+5,y-40,w-10,4,'#243a43');rect(c,x+w/2-1,y-68,2,9,'#c8a676');
   rect(c,x+w/2-7,y+h-21,14,21,'#354143');rect(c,x+w/2-5,y+h-19,10,19,'#645347');rect(c,x+w/2+2,y+h-10,2,2,'#e5be78');
   rect(c,x+6,y+h-1,w-12,5,'#bec0a5');
   for(const yy of [y+13,y+39]){rect(c,x+w/2-4,yy,8,10,'#38494b');rect(c,x+w/2-2,yy+2,4,6,lit?'#d2b46b':'#7f9690');}
   return;
  }
  rect(c,x,y+19,w,h-19,'#534638');rect(c,x+3,y+20,w-6,h-24,'#c3ad82');rect(c,x+5,y+21,w-10,h-25,'#d3bc8e');
  for(let xx=x+6;xx<x+w;xx+=24)rect(c,xx,y+20,3,h-23,'#7b5d45');rect(c,x,y+h-10,w,4,'#82644b');
  const ridge=y-21;
  poly(c,[[x-7,y+25],[x+10,ridge],[x+w-10,ridge],[x+w+7,y+25]],'#633e37');
  for(let yy=ridge+3;yy<y+25;yy+=5){let d=(yy-ridge)/(y+25-ridge)*16;rect(c,x+9-d,yy,w-18+2*d,4,['#895145','#9c6150','#a56c52'][(yy+100)%3]);for(let xx=x+10-d;xx<x+w-8+d;xx+=10){rect(c,xx+(yy%2)*3,yy+1,6,1,'#bb7a5b');rect(c,xx+7,yy+1,1,3,'#754b40');}}
  rect(c,x-7,y+24,w+14,4,'#443d34');rect(c,x-6,y+25,w+12,1,'#c18b5a');
  // Chimney and warm windows.
  rect(c,x+w-27,ridge-13,11,18,'#696a5a');rect(c,x+w-29,ridge-15,15,4,'#9b9782');
  const doorx=x+w*.55;
  rect(c,doorx,y+h-27,15,27,'#594736');rect(c,doorx+2,y+h-25,11,25,'#8e6847');rect(c,doorx+10,y+h-13,2,2,'#e9c782');
  for(const xx of [x+13,x+w-27]){rect(c,xx-2,y+38,17,16,'#634d38');rect(c,xx,y+40,13,12,'#dfb06b');rect(c,xx+2,y+41,9,8,'#f1cc87');rect(c,xx+6,y+40,1,13,'#816042');rect(c,xx,y+46,13,1,'#816042');rect(c,xx-3,y+55,20,3,'#7d603f');}
  // Hanging sign, flower box, entrance step.
  rect(c,doorx-3,y+h,21,3,'#b9ab86');rect(c,x+w-5,y+32,2,11,'#756044');rect(c,x+w-4,y+34,16,2,'#756044');rect(c,x+w+4,y+35,14,11,'#b8a37a');rect(c,x+w+6,y+37,10,7,'#586647');
  if(b.kind==='inn'){rect(c,x+20,y+59,20,4,'#795644');for(let i=0;i<6;i++)rect(c,x+21+i*3,y+56,2,3,i%2?'#be9b80':'#899a6e');}
  else {rect(c,x+w-12,y+h-22,19,22,'#4e5146');rect(c,x+w-9,y+h-15,13,10,'#d78b4d');rect(c,x+w-6,y+h-13,6,7,'#f9c777');}
  if(!this.reduced)for(let i=0;i<3;i++){let p=(now*.23+i*.3)%1;ellipse(c,x+w-21+p*11,ridge-18-p*26,3+p*4,2+p*3,`rgba(197,185,162,${.16*(1-p)})`);}
 }
 lamp(c,x,y,now){
  x=x*T+8;y=y*T+15;rect(c,x-1,y-24,3,26,'#3a3d34');rect(c,x-5,y-30,11,2,'#493e35');rect(c,x-4,y-28,9,10,'#463e36');rect(c,x-3,y-27,7,7,'#d49d56');rect(c,x-2,y-26,5,5,'#ffdc8f');rect(c,x-4,y-19,9,2,'#493e35');rect(c,x-3,y-1,7,2,'#6e6850');
 }
 targetObject(c,t,now){
  const x=t.x*T+8,y=(t.y+1)*T;
  if(t.kind==='npc'){this.character(c,{kind:t.portrait,name:t.name,x:t.x,y:t.y,dir:t.id==='elia'?'left':'down',moving:false},now);return;}
  if(t.kind==='shard'){
   if(this.scene?.meta.self?.shards?.includes(t.id))return;
   const bob=this.reduced?0:Math.sin(now*2+t.x)*2;
   ellipse(c,x,y-2,7,3,'#354a42');poly(c,[[x,y-16+bob],[x+5,y-9+bob],[x,y-3+bob],[x-4,y-9+bob]],'#e1b167');poly(c,[[x,y-16+bob],[x+2,y-9+bob],[x,y-4+bob],[x-3,y-9+bob]],'#ffe8a8');rect(c,x-7,y-17+bob,2,2,'#cabb80');return;
  }
  if(t.kind==='board'){
   rect(c,x-7,y-12,3,13,'#684c36');rect(c,x+6,y-12,3,13,'#684c36');rect(c,x-12,y-28,26,17,'#4a4036');rect(c,x-10,y-26,22,13,'#a98253');rect(c,x-7,y-23,7,8,'#e6d2a2');rect(c,x+2,y-22,6,6,'#d5b383');rect(c,x-12,y-30,26,3,'#706847');return;
  }
  if(t.kind==='bench'){
   rect(c,x-13,y-17,29,3,'#b2a076');rect(c,x-13,y-12,29,3,'#b2a076');rect(c,x-15,y-5,33,4,'#988059');rect(c,x-12,y-2,3,5,'#4c4837');rect(c,x+12,y-2,3,5,'#4c4837');return;
  }
 }
 character(c,a,now){
  const x=Math.round(a.x*T+8),y=Math.round((a.y+1)*T),frame=a.moving&&!this.reduced?Math.floor(now*9)%4:0;
  ellipse(c,x,y-1,6,2,'#30483d');
  const bob=this.reduced?0:a.moving?(frame%2):Math.floor(now*.7)%4===0?1:0;c.drawImage(this.getFrame(a.kind||'traveler',a.dir,frame),x-12,y-29-bob);
  if(a.self){rect(c,x-2,y-34,5,1,'#efd59a');rect(c,x-1,y-33,3,1,'#efd59a');rect(c,x,y-32,1,1,'#efd59a');}
  if(a.busy){
   const lift=this.reduced?0:[0,3,6,2][Math.floor(now*7)%4];
   rect(c,x+8,y-15-lift,2,8,'#aa8358');rect(c,x+5,y-18-lift,8,4,'#adb8b0');
   rect(c,x+5,y-18-lift,8,1,'#e1ddbf');
  }
  if(a.busy){const progress=Math.max(0,Math.min(1,(now-a.busy.start_at)/(a.busy.end_at-a.busy.start_at)));rect(c,x-10,y-39,20,3,'#263937');rect(c,x-9,y-38,18*progress,1,'#e4c37f');}
 }
 glow(c,x,y,r,alpha=.22){const grad=c.createRadialGradient(x,y,0,x,y,r);grad.addColorStop(0,`rgba(255,208,110,${alpha})`);grad.addColorStop(.3,`rgba(236,160,68,${alpha*.6})`);grad.addColorStop(1,'rgba(224,146,58,0)');c.fillStyle=grad;c.fillRect(x-r,y-r,r*2,r*2);}
 draw(nowMillis){
  const now=this.now(),c=this.ctx,dt=Math.min(.05,(nowMillis-this.last)/1000||.016);this.last=nowMillis;
  c.drawImage(this.bg,0,0);
  if(!this.reduced){for(let i=0;i<36;i++){let y=(i*31+now*7)%this.canvas.height,x=(y/16<16?29:y/16<21?28:27)*16+rand(i)*23;rect(c,x,y,4+rand(i)*7,1,'#6b9891');}}
  const self=this.scene?.meta.self;
  const walking=self?.movement;
  if(walking){c.globalAlpha=.42;for(const p of walking.path)rect(c,p[0]*T+7,p[1]*T+9,2,2,'#f8dfa0');c.globalAlpha=1;}
  const pointed=this.target?this.map.targets.find(t=>t.id===this.target):null;
  const highlight=pointed?pointed.approach:this.hover;
  if(highlight){const [hx,hy]=highlight;const p=now*3;poly(c,[[hx*T+1,hy*T+9],[hx*T+8,hy*T+5],[hx*T+15,hy*T+9],[hx*T+8,hy*T+13]],'rgba(235,211,154,.28)');line(c,[hx*T+2,hy*T+9],[hx*T+8,hy*T+13],'#e8d19a');line(c,[hx*T+8,hy*T+13],[hx*T+14,hy*T+9],'#e8d19a');}
  // Fountain behind characters, distinct from the stream.
  ellipse(c,21*T,12*T+4,18,9,'#394b47');ellipse(c,21*T,12*T,17,9,'#a6aa94');ellipse(c,21*T,12*T-2,13,6,'#4b7575');rect(c,21*T-3,12*T-16,6,16,'#a1a896');ellipse(c,21*T,12*T-16,9,4,'#c1c0a4');rect(c,21*T-1,12*T-26,2,11,'#91b1a0');
  const drawables=[];
  for(const b of this.map.buildings)drawables.push({y:(b.y+b.h)*T,draw:()=>this.building(c,b,now,this.scene?.meta.beacon?.lit)});
  for(const [i,p] of this.map.trees.entries())drawables.push({y:(p[1]+1)*T,draw:()=>this.tree(c,p[0],p[1],i*13)});
  drawables.push({y:8.5*T,draw:()=>this.tree(c,17.5,7,22,true)});
  for(const t of this.map.targets)drawables.push({y:(t.y+1)*T,draw:()=>this.targetObject(c,t,now)});
  const actors=Object.values(this.scene?.entities||{}).filter(a=>a.kind==='traveler');
  for(const a of actors){const p=this.actorPosition(a);const colocated=actors.filter(other=>{const o=this.actorPosition(other);return Math.abs(o.x-p.x)<.15&&Math.abs(o.y-p.y)<.15;}).sort((x,y)=>x.role_id.localeCompare(y.role_id));
   const visualOffset=(colocated.findIndex(x=>x.role_id===a.role_id)-(colocated.length-1)/2)*.55;
   drawables.push({y:(p.y+1)*T,draw:()=>this.character(c,{...p,x:p.x+visualOffset,kind:a.appearance,self:a.role_id===this.selfId,busy:a.busy},now)});
  }
  for(const [x,y] of [[15,12],[23,12],[26,11],[31,12],[10,21],[20,21]])drawables.push({y:(y+1)*T,draw:()=>this.lamp(c,x,y,now)});
  drawables.sort((a,b)=>a.y-b.y);drawables.forEach(d=>d.draw());
  // Nameplates identify real entered travelers; emphasis does not imply a model is online.
  for(const a of actors){const p=this.actorPosition(a);const stack=actors.filter(other=>{const o=this.actorPosition(other);return Math.abs(o.x-p.x)<.15&&Math.abs(o.y-p.y)<.15;}).sort((x,y)=>x.role_id.localeCompare(y.role_id));const index=stack.findIndex(other=>other.role_id===a.role_id);const x=p.x*T+8+(index-(stack.length-1)/2)*T*.55,y=(p.y+1)*T-43-index*11;
   const label=[...a.name].slice(0,14).join('');c.save();c.font='7px monospace';c.textAlign='center';
   const w=Math.ceil(c.measureText(label).width)+8;rect(c,x-w/2,y-7,w,10,'rgba(15,30,31,.86)');
   c.fillStyle=a.role_id===this.focusRole?'#ffe2a0':'#e1e6ce';c.fillText(label,Math.round(x),Math.round(y));
   if(a.role_id===this.focusRole){c.strokeStyle='#f1ce80';c.strokeRect(Math.round(x-9),Math.round(p.y*T-18),18,35);}
   c.restore();
  }
  // Warm hanging lights, high enough not to imply collision.
  const lights=[];
  for(let i=0;i<11;i++){const x=195+i*18,y=121+Math.sin(i/10*Math.PI)*14;lights.push([x,y]);if(i)line(c,lights[i-1],[x,y],'#65694d');rect(c,x-1,y,3,4,i%2?'#dbae69':'#e3c88a');}
  c.save();c.globalCompositeOperation='screen';for(const [x,y] of lights)this.glow(c,x,y+2,15,.12);
  for(const [x,y] of [[15,12],[23,12],[26,11],[31,12],[10,21],[20,21]])this.glow(c,x*T+8,y*T-10,28,.20);
  this.glow(c,5*T+30,5*T+47,22,.14);this.glow(c,4*T+90,15*T+45,23,.19);
  if(this.scene?.meta.beacon?.lit){this.glow(c,34*T,5*T-29,75,.5);poly(c,[[34*T-7,5*T-30],[3*T,16*T],[7*T,20*T],[34*T+6,5*T-30]],'rgba(238,211,136,.075)');}
  if(!this.reduced)for(let i=0;i<22;i++){const x=rand(i*13)*600+20+Math.sin(now*.6+i)*8,y=140+rand(i*23)*210+Math.cos(now*.4+i)*5;const bright=.3+Math.sin(now*1.5+i)*.25;c.globalAlpha=Math.max(.05,bright);rect(c,x,y,1,1,'#f5d996');}c.globalAlpha=1;c.restore();
  for(const p of this.particles){p.age+=dt;p.x+=p.vx*dt;p.y+=p.vy*dt;p.vy+=14*dt;c.globalAlpha=Math.max(0,1-p.age/p.life);rect(c,p.x,p.y,2,2,p.color);}c.globalAlpha=1;this.particles=this.particles.filter(p=>p.age<p.life);
  // Foreground vignette and soft evening haze. Pixel textures remain nearest-neighbor.
  const g=c.createRadialGradient(320,210,110,320,200,390);g.addColorStop(0,'rgba(14,25,31,0)');g.addColorStop(1,'rgba(11,24,29,.35)');c.fillStyle=g;c.fillRect(0,0,640,416);
  if(this.target){const t=this.map.targets.find(a=>a.id===this.target);if(t){const yy=t.y*T-28+(this.reduced?0:Math.sin(now*4)*2);poly(c,[[t.x*T+4,yy],[t.x*T+12,yy],[t.x*T+8,yy+4]],'#ffe1a0');}}
 }
 portrait(canvas,kind){canvas.width=48;canvas.height=48;const c=canvas.getContext('2d');c.imageSmoothingEnabled=false;rect(c,0,0,48,48,'#304440');c.drawImage(this.getFrame(kind,'down',0),0,0,24,23,0,0,48,46);}
}
