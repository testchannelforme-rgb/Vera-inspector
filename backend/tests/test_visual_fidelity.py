import json
import math
import pytest
from app.prompts.css_safety import background_layers,sanitize_css,ASSET
from app.prompts.evidence import sanitize,REDACTIONS,clean_text,MAX_EVIDENCE_BYTES
from app.prompts.visual_evidence import sanitize_context,sanitize_visual,safe_box
from app.prompts.composition import relationships,summary_lines
from app.prompts.deterministic import render_prompt
from app.prompts.schemas import PromptRequest
from app.prompts.service import PromptService
from app.prompts.provider import ProviderConfig
from app.prompts.style_groups import factor_styles,reconstruct

G='linear-gradient(135deg, rgb(1, 2, 3) 12%, rgba(4, 5, 6, 0.5) 88%)'


def node(i=0,parent=None,text='Heading',styles=None,**extra):
    return {'id':i,'parent':parent,'tag':'h1','depth':0 if parent is None else 1,'visible':True,'text':text,'role':'',
            'box':{'x':10,'y':20,'width':300,'height':60},'styles':styles or {'color':'rgb(0, 0, 0)','background-color':'rgba(0, 0, 0, 0)'},'image':None,'behavior':{},**extra}


def raw(nodes=None,context=None):
    return {'schemaVersion':'0.3-evidence','scope':'element','boundary':'selected element','viewport':{'width':1280,'height':800},'scroll':{'x':0,'y':0},'nodes':nodes or [node()],
            'truncated':False,'excluded':0,**({'visualContext':context} if context is not None else {})}


def req(**kwargs):return PromptRequest(sessionId='s',frameId='f',referenceId='r',**kwargs)


def context(styles=None,**extra):
    return {'owners':[{'owner':'ancestor:1','relation':'ancestor','distance':1,'tag':'section','box':{'x':0,'y':0,'width':900,'height':500},'styles':styles or {'background-image':G},**extra}],
            'coverage':{'contextOmitted':False},'method':'untrusted method must not pass through'}


@pytest.mark.parametrize('value',[G,'radial-gradient(circle at 10% 20%, red, blue)','conic-gradient(from 45deg, red, blue)','repeating-linear-gradient(90deg, red 0px, blue 10px)',G+', radial-gradient(red, blue)'])
def test_gradient_parameters_and_layers_preserved(value):
    assert background_layers(value)==(value,False,False)
    clean,changed,cut=sanitize_css('background-image',value,REDACTIONS)
    assert clean==value and not changed and not cut


def test_mixed_layers_preserve_gradient_order_and_remove_assets():
    result,changed,_=background_layers(G+', url("https://example.com/signed?token=secret"), conic-gradient(red, blue)')
    assert result==G+', [asset reference omitted], conic-gradient(red, blue)' and changed
    assert 'token=secret' not in result


@pytest.mark.parametrize('value',[
    'url(//169.254.169.254/latest?token=secret)','url("data:image/svg+xml,SECRET")','u\\72l(https://example.com/SECRET)',
    'image-set("/private/SECRET.png" 1x)','linear-gradient(red, url(https://example.com/SECRET))',
    'url/*comment*/(https://example.com/SECRET)','url(file:///etc/SECRET)'])
def test_url_bearing_css_never_leaks(value):
    result,_,_=sanitize_css('background-image',value,REDACTIONS)
    assert 'SECRET' not in result and '169.254' not in result
    for key in ('mask-image','-webkit-mask-image','filter','text-shadow'):
        cleaned,_,_=sanitize_css(key,value,REDACTIONS)
        assert cleaned is None or 'SECRET' not in cleaned


@pytest.mark.parametrize('value',[None,42,{},'linear-gradient(red, "SECRET")','linear-gradient('+('('*20)+'red'+(')'*20)+')','linear-gradient(red, blue','linear-gradient(red, blue)'*500])
def test_malformed_or_large_css_is_bounded(value):
    result,changed,limited=sanitize_css('background-image',value,REDACTIONS)
    assert result is None or len(result)<=1024
    assert changed


def test_long_gradient_has_explicit_incompleteness_and_preserves_more_than_180_characters():
    value='linear-gradient(90deg, '+', '.join(f'rgb({i}, 2, 3) {i}%' for i in range(20))+')'
    assert 180<len(value)<1024
    assert sanitize_css('background-image',value,REDACTIONS)[0]==value


def test_own_transparency_and_background_owner_stay_distinct():
    evidence=sanitize(raw(context=context()),'https://example.com')
    prompt,warnings=render_prompt(evidence,req())
    assert evidence['nodes'][0]['styles']['background-color']=='rgba(0, 0, 0, 0)'
    assert evidence['visualContext']['owners'][0]['styles']['background-image']==G
    assert 'Do not assign its background to the selected child' in prompt
    assert 'no pixel color' in prompt and G in prompt


def test_pseudo_owner_and_computed_geometry_are_not_invented_boxes():
    p={'pseudo':'::before','contentKind':'empty','content':'""','styles':{'background-image':G,'width':'300px','position':'absolute','filter':'blur(12px)'},'box':{'x':999}}
    n=node(visual={'pseudoElements':[p]})
    evidence=sanitize(raw([n]),'https://example.com')
    pseudo=evidence['nodes'][0]['visual']['pseudoElements'][0]
    assert 'box' not in pseudo and pseudo['styles']['width']=='300px'
    prompt,_=render_prompt(evidence,req());assert 'Node 0::before' in prompt and 'not measured' in prompt


def test_pseudo_content_is_redacted_and_extra_fields_are_not_forwarded():
    p={'pseudo':'::after','contentKind':'text','content':'password=SECRET me@example.com','styles':{'color':'red','unknown':'secret'},'cookies':'private','html':'<script>SECRET</script>'}
    result=sanitize_visual({'pseudoElements':[p]},clean_text,REDACTIONS)
    serialized=json.dumps(result)
    assert 'SECRET' not in serialized and 'me@example.com' not in serialized and 'cookies' not in serialized and 'unknown' not in serialized


def test_context_does_not_forward_unvalidated_owner_metadata_or_private_image_fields():
    ctx=context();ctx['owners'].append({'owner':'http://internal/SECRET','relation':'ancestor','distance':1,'box':{'x':0}})
    n=node(image={'naturalWidth':0,'naturalHeight':0,'complete':True,'src':'https://private/SECRET','alt':'sample'})
    e=sanitize(raw([n],ctx),'https://example.com')
    assert e['nodes'][0]['image']['assetStatus']=='unavailable'
    assert 'SECRET' not in json.dumps(e) and 'untrusted method' not in json.dumps(e)


@pytest.mark.parametrize('bad',[None,[],{'x':math.nan,'y':0,'width':1,'height':1},{'x':0,'y':0,'width':math.inf,'height':1}])
def test_context_boxes_require_finite_geometry(bad):assert safe_box(bad) is None


def test_overlapping_text_is_a_hypothesis_not_blind_duplication_or_dom_merging():
    nodes=[node(0,styles={'display':'block'}),node(1,0,styles={'position':'absolute','color':'red'}),node(2,0,styles={'position':'absolute','color':'blue'},accessibility={'hiddenFromAT':True})]
    relations=relationships(nodes[1:]);assert len(relations)==1 and relations[0]['nodes']==[1,2]
    e=sanitize(raw(nodes),'https://example.com');prompt,_=render_prompt(e,req(scope='section'))
    assert 'Inferred shared display-copy composition' in prompt and 'state variants or accessibility alternatives' in prompt
    assert 'Node 1, parent 0' in prompt and 'Node 2, parent 0' in prompt
    assert 'independent flow headings' in prompt and 'Both DOM nodes and exact styles remain separate' in prompt
    for n in e['nodes']:assert reconstruct(factor_styles(e['nodes']),n['id'])==n['styles']


def test_matching_text_alone_does_not_group_separate_content():
    a=node(1,0);b=node(2,0);b['box']={**b['box'],'y':500}
    assert not relationships([a,b])
    b['box']=a['box'];assert not relationships([a,b]) # no layering CSS


def test_multiple_layers_coalesce_only_connected_geometry_candidates():
    nodes=[node(i,99,styles={'position':'absolute','color':str(i)}) for i in (1,2,3)]
    assert len(relationships(nodes))==1 and set(relationships(nodes)[0]['nodes'])=={1,2,3}


@pytest.mark.parametrize('scope',['element','section','page'])
@pytest.mark.parametrize('detail',['concise','detailed','highly-detailed'])
@pytest.mark.parametrize('target',['html-css','html-css-js','react'])
def test_visual_prompt_all_existing_options(scope,detail,target):
    e=sanitize(raw([node(styles={'background-image':G,'background-clip':'text','-webkit-text-fill-color':'transparent','color':'black','text-shadow':'0 1px 2px red'})]),'https://example.com')
    prompt,_=render_prompt(e,req(scope=scope,detail=detail,target=target))
    assert all(f'## {i}.' in prompt for i in range(1,9)) and 'Visual Composition Summary' in prompt
    assert G in prompt and 'transparent text fill' in prompt and 'not render its computed color as an additional opaque text layer' in prompt


def test_unknown_visual_fields_do_not_change_request_contract():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):req(visualContext={'secret':'untrusted client data'})


def test_visual_metadata_and_size_budgets_remain_bounded():
    pseudo={'pseudo':'::before','contentKind':'text','content':'public','styles':{'background-image':G,'text-shadow':'0px 1px '+('x'*7000)}}
    nodes=[node(i,None if i==0 else 0,visual={'pseudoElements':[pseudo]}) for i in range(55)]
    ctx=context();ctx['owners']=ctx['owners']*100
    e=sanitize(raw(nodes,ctx),'https://example.com')
    assert len(json.dumps(e,ensure_ascii=True).encode())<=MAX_EVIDENCE_BYTES
    assert sum(len(n.get('visual',{}).get('pseudoElements',[])) for n in e['nodes'])<=8
    assert len(json.dumps(e.get('visualContext',{})).encode())<6000


@pytest.mark.parametrize('value',[None,[],{'pseudoElements':None},{'pseudoElements':[None,{'pseudo':'::not-real'}]},{'pseudoElements':[{'pseudo':'::before','styles':None,'sanitizedProperties':None,'styleTruncatedProperties':None}]}])
def test_missing_visual_properties_do_not_break_generation(value):
    assert isinstance(sanitize_visual(value,clean_text,REDACTIONS),dict)


@pytest.mark.asyncio
async def test_older_v031_evidence_and_no_key_generation_remain_useful():
    e=sanitize(raw(),'https://example.com')
    result=await PromptService(ProviderConfig()).generate(e,req())
    assert result.mode=='fallback' and result.schemaVersion=='0.3' and 'Heading' in result.prompt


def test_api_rejects_client_supplied_visual_evidence_before_browser_use():
    from unittest.mock import AsyncMock
    from fastapi.testclient import TestClient
    from app.main import create_app
    from app.browser_manager import BrowserManager
    from app.config import Settings
    manager=BrowserManager(Settings());manager.start=AsyncMock();manager.stop=AsyncMock()
    with TestClient(create_app(Settings(),manager)) as client:
        r=client.post('/api/prompts/generate',json={'sessionId':'s','frameId':'f','visualContext':{'owners':[]}},headers={'X-Veyra-Client':'inspector-v0.1'})
        assert r.status_code==422 and not manager.sessions


@pytest.mark.asyncio
async def test_dense_visual_evidence_stays_in_input_and_prompt_limits():
    pseudos=[{'pseudo':pseudo,'content':'""','contentKind':'empty','styles':{'background-image':G,'text-shadow':'0px 1px '+('x'*1400),'mask-image':'radial-gradient(white, transparent)'}} for pseudo in ('::before','::after')]
    nodes=[node(i,None if i==0 else 0,text='Copy '+str(i),styles={**{f'property-{k}':str(i)+'x'*150 for k in range(45)},'background-image':G},visual={'pseudoElements':pseudos}) for i in range(55)]
    e=sanitize(raw(nodes,context()),'https://example.com')
    assert len(json.dumps(e,ensure_ascii=True).encode())<=48000
    result=await PromptService(ProviderConfig()).generate(e,req(detail='highly-detailed'))
    assert result.mode=='fallback' and len(result.prompt)<60000


def test_context_style_budget_omissions_survive_pseudo_metadata_merge():
    from app.prompts.visual_evidence import sanitize_context
    from app.prompts.evidence import clean_text, REDACTIONS
    raw={'owners':[{'owner':'ancestor:1','relation':'ancestor','distance':1,'tag':'section',
         'box':{'x':0,'y':0,'width':100,'height':100},
         'styles':{k:'x'*1000 for k in ('background-position','background-size','background-clip','mask-size')},
         'omittedProperties':['box-shadow']}]}
    owner=sanitize_context(raw,clean_text,REDACTIONS)['owners'][0]
    assert 'box-shadow' in owner['omittedProperties']
    assert len(owner['omittedProperties'])>1


@pytest.mark.parametrize('key',['background-image','mask-image','filter'])
def test_control_byte_url_obfuscation_is_removed_before_safety_check(key):
    value='linear-gradient(red, ur\x00l(/private/SECRET))' if key!='filter' else 'ur\x00l(/private/SECRET)'
    cleaned,_,_=sanitize_css(key,value,REDACTIONS)
    assert cleaned is None or 'SECRET' not in cleaned


def test_malformed_omitted_keys_and_negative_geometry_are_rejected_safely():
    assert sanitize_visual({'omittedProperties':[[],{},None,'box-shadow']},clean_text,REDACTIONS)['omittedProperties']==['box-shadow']
    assert safe_box({'x':0,'y':0,'width':-1,'height':1}) is None


def test_new_visual_styles_factor_and_reconstruct_exactly_with_attribution():
    styles={'background-image':G,'mask-image':'radial-gradient(white, transparent)',
            'background-clip':'text','-webkit-text-fill-color':'transparent','mix-blend-mode':'screen','background-size':'200% 100%'}
    e=sanitize(raw([node(0,styles=styles),node(1,0,styles={**styles,'opacity':'0.5'})]),'https://example.com')
    factored=factor_styles(e['nodes'])
    for n in e['nodes']:assert reconstruct(factored,n['id'])==n['styles']
    assert e['nodes'][0]['styles']['background-image']==G
    assert 'opacity' not in reconstruct(factored,0) and reconstruct(factored,1)['opacity']=='0.5'
