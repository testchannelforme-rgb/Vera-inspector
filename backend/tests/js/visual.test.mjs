import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
import {el,environment} from './synthetic-dom.mjs';
const visual=readFileSync(new URL('../../app/prompts/visual.js',import.meta.url),'utf8');
const boundary=readFileSync(new URL('../../app/prompts/boundary.js',import.meta.url),'utf8');
const source=readFileSync(new URL('../../app/prompts/collect.js',import.meta.url),'utf8').replace('__VEYRA_VISUAL_FUNCTION__',visual).replace('__VEYRA_BOUNDARY_FUNCTION__','('+boundary+')');
const run=(n,scope='element',clock={now:()=>0})=>vm.runInNewContext('('+source+')',environment(clock))(n,scope);
const gradient='linear-gradient(135deg, rgb(10, 30, 90) 12%, rgba(20, 80, 160, 0.5) 88%)';

for(const image of [gradient,'radial-gradient(circle at 10% 20%, red 0%, blue 100%)','conic-gradient(from 45deg at 30% 40%, red, blue)','repeating-linear-gradient(45deg, red 0px, blue 12px)']) {
 test('preserves computed gradient '+image.split('(')[0],()=>{
  const n=run(el('section',{styles:{'background-image':image}})).nodes[0];assert.equal(n.styles['background-image'],image);
 });
}
test('mixed background layers preserve order/gradient parameters and omit asset URLs',()=>{
 const n=run(el('section',{styles:{'background-image':gradient+', url("https://example.com/signed?token=secret"), radial-gradient(red, blue)','background-size':'cover, 80% auto, auto','background-position':'center, right top, left bottom'}})).nodes[0];
 assert.equal(n.styles['background-image'],gradient+', [asset reference omitted], radial-gradient(red, blue)');
 assert.equal(n.styles['background-size'],'cover, 80% auto, auto');assert.ok(!JSON.stringify(n).includes('token=secret'));
});
test('transparent target retains its own paint and a separate painted ancestor owner',()=>{
 const target=el('h1',{text:'Heading',styles:{'background-color':'rgba(0, 0, 0, 0)'}});
 const owner=el('section',{styles:{'background-image':gradient,'overflow':'hidden','opacity':'0.8'}}).add(target);
 const r=run(target);assert.equal(r.nodes[0].styles['background-color'],'rgba(0, 0, 0, 0)');
 assert.equal(r.visualContext.owners[0].owner,'ancestor:1');assert.equal(r.visualContext.owners[0].styles['background-image'],gradient);
 assert.equal(owner.children[0],target);
});
test('pseudo-elements are attributed and carry computed dimensions, not fabricated rectangles',()=>{
 const n=el('section');n.pseudos={'::before':{content:'""',position:'absolute',width:'300px',height:'100px','background-image':gradient,opacity:'0.5',filter:'blur(12px)'}};
 const raw=run(n),pseudo=raw.nodes[0].visual.pseudoElements[0];assert.equal(pseudo.pseudo,'::before');assert.equal(pseudo.styles.width,'300px');
 assert.equal(pseudo.styles['background-image'],gradient);assert.equal(pseudo.styles.filter,'blur(12px)');assert.equal(pseudo.box,undefined);
 assert.match(pseudo.geometry,/not measured/);
});
test('no generated content means no fabricated pseudo-element',()=>{
 const n=el('button');assert.equal(run(n).nodes[0].visual,undefined);
 n.pseudos={'::after':{content:'none',width:'10px','background-image':gradient}};
 assert.equal(run(n).nodes[0].visual,undefined);
});
test('gradient text, stroke, shadow, masks, blend modes and stacking indicators are observed separately',()=>{
 const n=run(el('h1',{text:'Painted heading',styles:{'background-image':gradient,'background-clip':'text','-webkit-text-fill-color':'rgba(0, 0, 0, 0)',color:'rgb(0, 0, 0)','-webkit-text-stroke-width':'1px','text-shadow':'0 1px 2px rgb(1, 2, 3)','mix-blend-mode':'screen','mask-image':'radial-gradient(white, transparent)','z-index':'3',position:'absolute',transform:'matrix(1, 0, 0, 1, 5, 10)','clip-path':'inset(5%)'}})).nodes[0];
 for(const key of ['background-clip','-webkit-text-fill-color','-webkit-text-stroke-width','text-shadow','mix-blend-mode','mask-image','z-index','transform','clip-path'])assert.ok(n.styles[key],key);
 assert.equal(n.styles.color,'rgb(0, 0, 0)');
});
test('nearby positioned text alternatives and decoration keep external owner attribution',()=>{
 const target=el('h1',{text:'Layered title',box:[0,0,300,60]}),overlay=el('h1',{text:'Layered title',box:[0,0,300,60],styles:{position:'absolute',color:'red'},attrs:{'aria-hidden':'true'}});
 el('section').add(target,overlay);
 const raw=run(target);const owner=raw.visualContext.owners.find(o=>o.relation==='nearby-text-layer');
 assert.ok(owner);assert.equal(owner.sameDirectText,true);assert.equal(owner.hiddenFromAT,true);assert.equal(owner.styles.color,'red');assert.equal(owner.text,undefined);
});
test('unrelated and nonoverlapping decoration is not imported into target scope',()=>{
 const target=el('button',{box:[0,0,100,40]}),other=el('div',{box:[900,600,100,80],styles:{position:'absolute','background-image':gradient}});
 el('section').add(target,other);assert.ok(!run(target).visualContext.owners.some(o=>o.relation.startsWith('nearby')));
});
test('unsafe CSS forms and pseudo content never export signed references',()=>{
 const n=el('div',{styles:{'mask-image':'url(//169.254.169.254/latest?token=secret)'}});
 n.pseudos={'::after':{content:'url("data:image/svg+xml,private")'}};
 const raw=JSON.stringify(run(n));assert.ok(!raw.includes('169.254'));assert.ok(!raw.includes('data:image'));assert.ok(!raw.includes('token=secret'));
});
test('long or deeply nested CSS returns bounded explicit omission markers',()=>{
 const n=run(el('section',{styles:{'background-image':'linear-gradient('+('red, '.repeat(5000))+')'}})).nodes[0];
 assert.ok(n.styles['background-image'].length<1025);assert.ok(n.styleTruncatedProperties.includes('background-image'));
 assert.match(n.styles['background-image'],/omitted/);
});

test('private owners do not export generated pseudo content',()=>{
 const n=el('input',{attrs:{type:'password'}});n.pseudos={'::before':{content:'"private-generated-secret"'}};
 assert.ok(!JSON.stringify(run(n)).includes('private-generated-secret'));
});
test('oversized scalar CSS and pseudo content have bounded explicit markers',()=>{
 const n=el('div',{styles:{filter:'x'.repeat(20000)}});
 n.pseudos={'::before':{content:'"'+'x'.repeat(20000)+'"',width:'x'.repeat(20000)}};
 const r=run(n).nodes[0];assert.match(r.styles.filter,/omitted/);
 assert.ok(r.visual.pseudoElements[0].content.length<170);
 assert.match(r.visual.pseudoElements[0].styles.width,/omitted/);
});

test('bounded paint records prioritize text fill/clip and gradient over long placement strings',()=>{
 const s={'background-image':gradient,'-webkit-text-fill-color':'transparent','background-clip':'text',
  'background-position':'x'.repeat(1000),'background-size':'y'.repeat(1000),'background-origin':'z'.repeat(1000),
  'mask-image':'radial-gradient(white, transparent)','text-shadow':'v'.repeat(1000)};
 const n=run(el('h1',{text:'Layered',styles:s})).nodes[0];
 assert.equal(n.styles['background-image'],gradient);assert.equal(n.styles['-webkit-text-fill-color'],'transparent');
 assert.equal(n.styles['background-clip'],'text');assert.ok(n.visual.omittedProperties.length>0);
});
