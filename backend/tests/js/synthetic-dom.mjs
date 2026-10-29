// Deliberately synthetic DOM/geometry for executing the real collector functions.
// These tests are algorithm tests, never evidence of a rendered website.
export class SyntheticElement {
  constructor(tag,{box=[0,0,600,180],styles={},attrs={},text=''}={}) {
    this.localName=tag;this.attrs=attrs;this.children=[];this.parentElement=null;this.shadowRoot=null;
    this.box=box;this.styles=styles;this.text=text;this.isConnected=true;this.nodeType=1;
    this.naturalWidth=320;this.naturalHeight=180;
  }
  add(...nodes){for(const n of nodes){this.children.push(n);n.parentElement=this;}return this;}
  get childNodes(){return [...(this.text?[{nodeType:3,textContent:this.text,ownerElement:this}]:[]),...this.children];}
  getBoundingClientRect(){const [x,y,width,height]=this.box;return {x,y,width,height,top:y,left:x,right:x+width,bottom:y+height};}
  getAttribute(k){return this.attrs[k]??null;}
  hasAttribute(k){return Object.hasOwn(this.attrs,k);}
  getRootNode(){return {host:null};}
  contains(other){for(let n=other;n;n=n.parentElement)if(n===this)return true;return false;}
  getAnimations(){return [];}
  matches(selector){
    if(selector.includes('[contenteditable]')||selector.includes('contenteditable'))return ['input','textarea','select','option'].includes(this.localName)||this.attrs.contenteditable==='true'||this.hasAttribute('data-veyra-private');
    return selector.split(',').includes(this.localName);
  }
  closest(selector){for(let n=this;n;n=n.parentElement)if(n.matches(selector))return n;return null;}
}
export const el=(tag,options)=>new SyntheticElement(tag,options);
export function computed(el,pseudo=null) {
  if(pseudo)el={styles:{content:'none',...(el.pseudos?.[pseudo]||{})}};
  const defaults={display:'block',visibility:'visible',opacity:'1','background-color':'rgba(0, 0, 0, 0)','background-image':'none','border-radius':'0px','box-shadow':'none','font-size':'16px','font-family':'Arial','animation-name':'none','transition-duration':'0s'};
  return new Proxy({getPropertyValue:key=>el.styles[key]??defaults[key]??''},{get:(target,key)=>key in target?target[key]:el.styles[String(key).replace(/[A-Z]/g,m=>'-'+m.toLowerCase())]??defaults[String(key).replace(/[A-Z]/g,m=>'-'+m.toLowerCase())]??''});
}
export function environment(clock) {
  return {Element:SyntheticElement,Node:{TEXT_NODE:3},getComputedStyle:computed,innerWidth:1280,innerHeight:800,scrollX:0,scrollY:0,
    performance:clock||{now:()=>performance.now()},document:{createRange:()=>({selectNodeContents(n){this.node=n;},getClientRects(){return [this.node.ownerElement.getBoundingClientRect()];}})}};
}
