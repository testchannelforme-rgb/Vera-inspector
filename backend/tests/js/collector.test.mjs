import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {el,environment} from './synthetic-dom.mjs';
const boundary=readFileSync(new URL('../../app/prompts/boundary.js',import.meta.url),'utf8');
const visual=readFileSync(new URL('../../app/prompts/visual.js',import.meta.url),'utf8');
const collector=readFileSync(new URL('../../app/prompts/collect.js',import.meta.url),'utf8').replace('__VEYRA_BOUNDARY_FUNCTION__','('+boundary+')').replace('__VEYRA_VISUAL_FUNCTION__',visual);
const choose=(n)=>vm.runInNewContext('('+boundary+')',environment())(n);
const collect=(n,scope='section',clock)=>vm.runInNewContext('('+collector+')',environment(clock||{now:()=>0}))(n,scope);
const main=()=>el('main',{box:[0,0,1280,2400]});

test('hero heading resolves to local section, not main',()=>{
  const heading=el('h1',{box:[40,60,480,60],text:'Build together'});
  const hero=el('section',{box:[0,0,1200,540],styles:{paddingTop:'32px'}}).add(el('div').add(heading,el('p',{text:'Subtitle'})),el('img'));
  main().add(hero,el('section',{box:[0,600,1200,800]}));
  const result=choose(heading);assert.equal(result.element,hero);assert.match(result.decision.reasons.join(),/semantic/);
  assert.ok(result.decision.candidates.some(c=>c.tag==='main'&&c.rejected));
});
test('card article wins over surrounding pricing section',()=>{
  const title=el('h2',{box:[24,80,200,30],text:'Starter'});
  const card=el('article',{box:[0,50,300,320],styles:{'border-radius':'12px','box-shadow':'0 2px 8px #000'}}).add(title,el('button',{text:'Choose'}));
  const pricing=el('section',{box:[0,0,1200,600],styles:{display:'grid'}}).add(card,el('article'),el('article'));
  main().add(pricing);assert.equal(choose(title).element,card);
});
test('navigation link stays inside nav, excluding unrelated header/body content',()=>{
  const link=el('a',{box:[20,20,100,24],text:'Products'}),nav=el('nav',{box:[0,0,800,64],styles:{display:'flex'}}).add(link,el('a',{text:'Pricing'}));
  el('body').add(el('header',{box:[0,0,1280,200]}).add(nav,el('div')),main());
  assert.equal(choose(link).element,nav);
});
test('painted nonsemantic card is a local boundary',()=>{
  const heading=el('h3',{box:[16,16,260,30]}),card=el('div',{box:[0,0,320,260],styles:{'box-shadow':'0 2px 8px #333','padding-top':'16px'}}).add(heading,el('button'));
  main().add(el('div',{box:[0,0,1200,600],styles:{display:'grid'}}).add(card,el('div')));
  const result=choose(heading);assert.equal(result.element,card);assert.ok(result.decision.reasons.includes('painted component boundary'));
});
test('direct main heading falls back to heading instead of broad main',()=>{
  const h=el('h1');main().add(h);const result=choose(h);
  assert.equal(result.element,h);assert.equal(result.decision.method,'local-fallback');
});
test('tall semantic wrapper is rejected, local parent fallback remains predictable',()=>{
  const h=el('h1',{box:[0,0,300,50]}),parent=el('div',{box:[0,0,400,100]}).add(h);
  const large=el('section',{box:[0,0,1280,2300]}).add(parent,el('div'));
  main().add(large);const result=choose(h);assert.equal(result.element,parent);
  assert.ok(result.decision.candidates.some(c=>c.rejected==='disproportionately tall ancestor'));
});
test('ancestor wrapper with multiple unrelated landmarks is rejected',()=>{
  const h=el('h2',{box:[0,0,200,30]}),wrapper=el('div',{box:[0,0,1200,700]}).add(h,el('section'),el('nav'));
  main().add(wrapper);assert.equal(choose(h).element,h);
});
test('later CTA and image survive a long sequence of generic nodes',()=>{
  const body=el('body',{box:[0,0,1280,800]});
  for(let i=0;i<100;i++)body.add(el('div',{text:'Repeated item '+i}));
  body.add(el('button',{text:'Critical late CTA'}),el('img',{attrs:{alt:'Hero visual'}}));
  const result=collect(body,'page');assert.ok(result.nodes.some(n=>n.text==='Critical late CTA'));
  assert.ok(result.nodes.some(n=>n.tag==='img'));assert.ok(result.nodes.length<=55);assert.equal(result.truncated,true);
  const ids=new Set(result.nodes.map(n=>n.id));assert.ok(result.nodes.every(n=>n.parent===null||ids.has(n.parent)));
});
test('selected path is pinned, IDs and true sibling order remain available',()=>{
  const selected=el('h2',{text:'Selected'}),last=el('div').add(el('div').add(selected));
  const body=el('body',{box:[0,0,1280,800]}).add(el('div',{text:'First'}),last);
  // Section boundary may be local, but element/page scopes retain the same collector path.
  const result=collect(body,'page');const child=result.nodes.find(n=>n.parent===0&&n.siblingIndex===1);
  assert.ok(child);assert.ok(result.nodes.some(n=>n.text==='Selected'));
});
test('collector does not copy private values, editable text, signed URLs or arbitrary attributes',()=>{
  const body=el('body').add(el('input',{attrs:{value:'password-secret'}}),el('div',{text:'editable-secret',attrs:{contenteditable:'true'}}),el('img',{attrs:{src:'https://example.com/?token=secret',alt:'Visual'}}));
  const serialized=JSON.stringify(collect(body,'page'));
  assert.ok(!serialized.includes('password-secret'));assert.ok(!serialized.includes('editable-secret'));assert.ok(!serialized.includes('?token='));
});
test('computed spacing, CSS whitespace, geometry and truncation markers are retained',()=>{
  const button=el('button',{box:[40,80,160,48],styles:{'margin-left':'17px','font-family':'"Two  Spaces", sans-serif','grid-template-columns':'20px '.repeat(80)}});
  const n=collect(button,'element').nodes[0];
  assert.equal(n.styles['margin-left'],'17px');assert.equal(n.styles['font-family'],'"Two  Spaces", sans-serif');
  assert.deepEqual(JSON.parse(JSON.stringify(n.box)),{x:40,y:80,width:160,height:48});
  assert.ok(n.styleTruncatedProperties.includes('grid-template-columns'));
});
test('node/queue bounds are enforced for wide DOMs',()=>{
  const body=el('body');for(let i=0;i<2000;i++)body.add(el('div'));
  const result=collect(body,'page');assert.ok(result.collection.visited<=1500);assert.ok(result.nodes.length<=55);assert.equal(result.truncated,true);
});
test('time budget stops collection and reports incomplete coverage',()=>{
  let t=0;const body=el('body').add(...Array.from({length:100},()=>el('p')));
  const result=collect(body,'page',{now:()=>t+=15});assert.equal(result.truncated,true);assert.ok(result.nodes.length<55);
});

test('selected descendant survives broad sibling discovery and retains its real ancestry',()=>{
  const heading=el('h1',{box:[0,0,300,50],text:'Chosen heading'});
  const branch=el('div').add(el('div').add(el('div').add(heading)));
  const hero=el('section',{box:[0,0,1200,600]});
  for(let i=0;i<1400;i++)hero.add(el('div'));
  hero.add(branch);main().add(hero);
  const result=collect(heading,'section');
  assert.equal(result.nodes[0].tag,'section');
  const selected=result.nodes.find(n=>n.selected);assert.ok(selected);assert.equal(selected.text,'Chosen heading');
  const indexed=new Map(result.nodes.map(n=>[n.id,n]));
  let n=selected,count=0;while(n.parent!==null){n=indexed.get(n.parent);assert.ok(n);count++;}
  assert.equal(count,4);assert.equal(result.nodes.find(n=>n.parent===0&&n.siblingIndex===1400)?.tag,'div');
});

test('private composed ancestor also blocks selected open-shadow copy',()=>{
  const privateHost=el('div',{attrs:{'data-veyra-private':''}}),selected=el('span',{text:'private-shadow-copy'});
  selected.getRootNode=()=>({host:privateHost});privateHost.shadowRoot={children:[selected]};
  const result=collect(selected,'element');assert.equal(result.nodes.length,0);
  assert.ok(!JSON.stringify(result).includes('private-shadow-copy'));
});

test('explicit page wrapper in section mode asks for a local selection; element/page still work',()=>{
  for(const tag of ['main','body','html']) {
    const root=el(tag).add(el('h1',{text:'Local heading'}));
    const result=collect(root,'section');assert.equal(result.boundaryDecision.method,'selection-required');assert.equal(result.nodes.length,0);
    assert.ok(collect(root,'page').nodes.length);assert.ok(collect(root,'element').nodes.length);
  }
});

test('computed URL-free gradients are retained; signed background asset URLs remain omitted',()=>{
  const gradient='linear-gradient(90deg, rgb(1, 2, 3), rgb(4, 5, 6))';
  assert.equal(collect(el('section',{styles:{'background-image':gradient}}),'element').nodes[0].styles['background-image'],gradient);
  const image=collect(el('section',{styles:{'background-image':'url("https://example.com/signed?token=secret")'}}),'element');
  assert.equal(image.nodes[0].styles['background-image'],'present; asset URL omitted');
  assert.ok(!JSON.stringify(image).includes('token=secret'));
});

test('CSS materialization time cutoff preserves late high-priority CTA before generic nodes',()=>{
  const body=el('body');for(let i=0;i<100;i++)body.add(el('div',{text:'generic'}));
  body.add(el('button',{text:'Late important CTA'}));
  let materialized=0;
  for(const n of [body,...body.children])Object.defineProperty(n.styles,'font-family',{get(){materialized++;return 'Arial';}});
  const clock={now:()=>materialized>=2?130:0};
  const result=collect(body,'page',clock);
  assert.equal(result.truncated,true);assert.ok(result.nodes.some(n=>n.text==='Late important CTA'));
  assert.equal(result.nodes.length,2);assert.equal(result.nodes[0].id,0);
});

test('open shadow ancestry is marked as a host relationship with its own sibling indices',()=>{
  const host=el('div'),light=el('p',{text:'Light child'}),shadow=el('button',{text:'Shadow child'});
  host.add(light);shadow.getRootNode=()=>({host});host.shadowRoot={children:[shadow]};
  const result=collect(host,'element');
  const a=result.nodes.find(n=>n.text==='Light child'),b=result.nodes.find(n=>n.text==='Shadow child');
  assert.equal(a.parentRelationship,'dom-child');assert.equal(b.parentRelationship,'shadow-host');
  assert.equal(a.siblingIndex,0);assert.equal(b.siblingIndex,0);assert.equal(b.parent,0);
});
