// Static sample art only. This module cannot submit world actions.
const KINDS=['traveler','sage','rose','keeper','smith','gardener'];
export const CLIPS={idle:{frames:4,fps:2},walk:{frames:4,fps:9},talk:{frames:4,fps:6},work:{frames:4,fps:7}};
export function actionClip(actor,speaking=false){return actor?.moving?'walk':actor?.busy?'work':speaking?'talk':'idle';}
export function validatePack(m){
  if(!m||m.schema!=='lantern-sample-assets/1'||m.tile_size!==16||m.atlas!=='sample-atlas.png'||!Number.isInteger(m.width)||!Number.isInteger(m.height)||m.width<1||m.height<1||m.width>2048||m.height>2048)throw new Error('Unsupported sample asset pack');
  if(!m.frames||Array.isArray(m.frames)||typeof m.frames!=='object'||Object.keys(m.frames).length>600)throw new Error('Invalid asset frames');
  for(const [key,f]of Object.entries(m.frames)){
    if(!/^[a-z0-9_/-]+$/.test(key)||!f||![f.x,f.y,f.w,f.h].every(Number.isInteger)||f.x<0||f.y<0||f.w<1||f.h<1||f.x+f.w>m.width||f.y+f.h>m.height||!Array.isArray(f.anchor)||f.anchor.length!==2||!f.anchor.every(Number.isFinite)||f.anchor[0]<0||f.anchor[1]<0||f.anchor[0]>f.w||f.anchor[1]>f.h)throw new Error('Invalid asset frame bounds');
  }
  for(const kind of KINDS)for(const dir of ['up','down','left','right'])for(const clip of Object.keys(CLIPS))for(let i=0;i<4;i++)if(!m.frames[`${kind}/${dir}/${clip}/${i}`])throw new Error('Incomplete character clip');
  return m;
}
export class SampleAssets{
  constructor(manifest,image){this.manifest=validatePack(manifest);this.image=image;this.cache=new Map();this.draws=0;if(image.width!==manifest.width||image.height!==manifest.height)throw new Error('Atlas dimensions do not match');}
  frame(kind,dir,clip,index){const key=`${kind}/${dir}/${clip}/${index%4}`,f=this.manifest.frames[key];if(!f)return null;if(!this.cache.has(key)){const c=document.createElement('canvas');c.width=f.w;c.height=f.h;c.getContext('2d').drawImage(this.image,f.x,f.y,f.w,f.h,0,0,f.w,f.h);this.cache.set(key,c);}this.draws++;return this.cache.get(key);}
  draw(c,key,x,y){const f=this.manifest.frames[key];if(!f)return false;c.drawImage(this.image,f.x,f.y,f.w,f.h,Math.round(x-f.anchor[0]),Math.round(y-f.anchor[1]),f.w,f.h);this.draws++;return true;}
}
export async function loadSampleAssets(url=new URL('./sample-assets.json',import.meta.url),fetcher=fetch){
  const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),5000);
  try{
    const response=await fetcher(url,{credentials:'omit',signal:controller.signal});if(!response.ok)throw new Error('Asset manifest HTTP '+response.status);
    const text=await response.text();if(text.length>131072)throw new Error('Asset manifest too large');const manifest=validatePack(JSON.parse(text));
    const imageUrl=new URL(manifest.atlas,new URL(url,location.href));imageUrl.search='v='+encodeURIComponent(manifest.version);
    const source=await fetcher(imageUrl,{credentials:'omit',signal:controller.signal});if(!source.ok)throw new Error('Atlas HTTP '+source.status);
    const blob=await source.blob();if(blob.size>1048576)throw new Error('Atlas too large');const image=await createImageBitmap(blob);
    try{return new SampleAssets(manifest,image);}catch(error){image.close();throw error;}
  }finally{clearTimeout(timeout);}
}
