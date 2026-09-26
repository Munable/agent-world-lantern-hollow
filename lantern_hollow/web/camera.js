// Local presentation only. Coordinates here never change world state.
const clamp=(value,min,max)=>Math.max(min,Math.min(max,value));
export class SceneCamera {
  constructor(width,height) {this.width=width;this.height=height;this.viewportWidth=width;this.viewportHeight=height;this.zoom=1;this.x=width/2;this.y=height/2;this.followId=null;}
  get overviewZoom(){return Math.min(1,this.viewportWidth/this.width,this.viewportHeight/this.height);}
  setViewport(width,height){
    if(!Number.isFinite(width)||!Number.isFinite(height)||width<=0||height<=0)return;
    const overview=!this.followId && Math.abs(this.zoom-this.overviewZoom)<.001;
    this.viewportWidth=width;this.viewportHeight=height;
    if(overview)this.overview();else this.constrain();
  }
  constrain() {
    const hx=this.viewportWidth/(2*this.zoom),hy=this.viewportHeight/(2*this.zoom);
    this.x=hx>=this.width/2?this.width/2:clamp(this.x,hx,this.width-hx);this.y=hy>=this.height/2?this.height/2:clamp(this.y,hy,this.height-hy);
  }
  get tx(){return this.viewportWidth/2-this.x*this.zoom;}
  get ty(){return this.viewportHeight/2-this.y*this.zoom;}
  project(x,y){return {x:x*this.zoom+this.tx,y:y*this.zoom+this.ty};}
  unproject(x,y){return {x:(x-this.tx)/this.zoom,y:(y-this.ty)/this.zoom};}
  follow(id){this.followId=id||null;if(id&&this.zoom<=this.overviewZoom+.001)this.zoom=1.8;this.constrain();}
  track(x,y){if(!this.followId)return;this.x=x;this.y=y;this.constrain();}
  pan(dx,dy){this.followId=null;this.x-=dx/this.zoom;this.y-=dy/this.zoom;this.constrain();}
  scale(factor,sx=this.viewportWidth/2,sy=this.viewportHeight/2){
    if(!Number.isFinite(factor)||factor<=0)return;
    const anchor=this.unproject(sx,sy);this.followId=null;this.zoom=clamp(this.zoom*factor,this.overviewZoom,4);
    this.x=anchor.x-(sx-this.viewportWidth/2)/this.zoom;this.y=anchor.y-(sy-this.viewportHeight/2)/this.zoom;this.constrain();
  }
  overview(){this.followId=null;this.zoom=this.overviewZoom;this.x=this.width/2;this.y=this.height/2;}
}
// Pointer gestures are local. Dragging/pinching must never become a game click.
export function bindCameraInput(canvas,camera,onChange=()=>{}) {
  const points=new Map();let start=null,dragged=false,suppressUntil=0;
  const point=e=>{const r=canvas.getBoundingClientRect();return {x:(e.clientX-r.left)*canvas.width/r.width,y:(e.clientY-r.top)*canvas.height/r.height};};
  const midpoint=ps=>({x:(ps[0].x+ps[1].x)/2,y:(ps[0].y+ps[1].y)/2});
  const distance=ps=>Math.hypot(ps[0].x-ps[1].x,ps[0].y-ps[1].y);
  canvas.addEventListener('pointerdown',e=>{
    if(e.button!==0)return;points.set(e.pointerId,point(e));
    if(points.size===1){start={x:e.clientX,y:e.clientY};dragged=false;}else dragged=true;
    canvas.setPointerCapture(e.pointerId);
  });
  canvas.addEventListener('pointermove',e=>{
    if(!points.has(e.pointerId))return;
    const old=[...points.values()],previous=points.get(e.pointerId),current=point(e);points.set(e.pointerId,current);
    const now=[...points.values()];
    if(points.size>=2){
      dragged=true;const a=midpoint(old),b=midpoint(now);camera.pan(b.x-a.x,b.y-a.y);
      if(distance(old)>1)camera.scale(distance(now)/distance(old),b.x,b.y);
    }else if(dragged||Math.hypot(e.clientX-start.x,e.clientY-start.y)>6){
      dragged=true;camera.pan(current.x-previous.x,current.y-previous.y);
    }
    if(dragged){e.preventDefault();onChange();}
  });
  const end=e=>{
    if(dragged||e.type==='pointercancel')suppressUntil=performance.now()+500;
    points.delete(e.pointerId);if(canvas.hasPointerCapture(e.pointerId))canvas.releasePointerCapture(e.pointerId);
    if(!points.size){start=null;dragged=false;}
  };
  canvas.addEventListener('pointerup',end);canvas.addEventListener('pointercancel',end);
  canvas.addEventListener('click',e=>{if(performance.now()<suppressUntil){e.preventDefault();e.stopImmediatePropagation();}},{capture:true});
  canvas.addEventListener('wheel',e=>{
    if(!e.ctrlKey&&!e.metaKey)return;const p=point(e);e.preventDefault();camera.scale(Math.exp(-e.deltaY*.002),p.x,p.y);onChange();
  },{passive:false});
}
