// Optional non-secret browser preferences; identity credentials never enter this store.
export function safeStorage(name,host=globalThis){
 const memory=new Map();let available=true;
 return {get persistent(){return available;},
  getItem(key){if(!available)return memory.get(key)??null;try{const value=host[name].getItem(key);if(value===null)memory.delete(key);else memory.set(key,value);return value;}catch{available=false;return memory.get(key)??null;}},
  setItem(key,value){memory.set(key,String(value));if(available)try{host[name].setItem(key,String(value));}catch{available=false;}},
  removeItem(key){memory.delete(key);if(available)try{host[name].removeItem(key);}catch{available=false;}}
 };
}
export const localPrefs=safeStorage('localStorage'),tabState=safeStorage('sessionStorage');
