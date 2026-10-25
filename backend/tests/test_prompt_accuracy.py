from copy import deepcopy
import json
from types import SimpleNamespace
import pytest
from app.prompts.deterministic import render_prompt, hierarchy
from app.prompts.evidence import sanitize, MAX_EVIDENCE_BYTES
from app.prompts.selection import selection_plan
from app.prompts.style_groups import factor_styles, reconstruct
from app.prompts.schemas import PromptRequest
from app.prompts.service import PromptService
from app.prompts.provider import ProviderConfig


def node(ident=0,parent=None,tag='div',text='',styles=None,**extra):
    return {'id':ident,'parent':parent,'tag':tag,'depth':0 if parent is None else 1,'visible':True,'text':text,'role':'',
        'box':{'x':20+ident,'y':40+ident,'width':160,'height':48},'styles':styles if styles is not None else {'display':'block','font-size':'16px','color':'rgb(0, 0, 0)','margin-left':'17px'},
        'behavior':{},'image':None,**extra}


def evidence(nodes,**extra):
    return {'schemaVersion':'0.3-evidence','scope':'section','boundary':'local container','viewport':{'width':1280,'height':800},
        'scroll':{'x':0,'y':0},'source':{'origin':'https://example.com','capturedAt':'2026-10-25T12:00:00Z'},
        'nodes':nodes,'truncated':False,'excluded':0,**extra}


def request(**extra):return PromptRequest(sessionId='s',frameId='f',referenceId='r',**extra)


def assert_parent_closure(chosen):
    ids={n['id'] for n in chosen}
    assert all(n['parent'] is None or n['parent'] in ids for n in chosen)


def test_late_meaningful_nodes_outweigh_early_generic_copy():
    nodes=[node()]+[node(i,0,text='ordinary copy') for i in range(1,35)]+[
        node(35,0,tag='h1',text='Important title'),node(36,0,tag='button',text='Start'),node(37,0,tag='img',image={'naturalWidth':800,'naturalHeight':400,'alt':'Hero'})]
    chosen,sample=selection_plan(nodes,4)
    assert [n['id'] for n in chosen]==[0,35,36,37]
    assert_parent_closure(chosen);assert sample['omitted']==34


def test_complete_ancestor_paths_and_selected_context_can_exceed_concise_count():
    nodes=[node()]+[node(i,i-1) for i in range(1,7)]+[node(7,6,'button',selected=True)]
    chosen,sample=selection_plan(nodes,4)
    assert len(chosen)==8 and sample['contextExpanded'] and not sample['selectedOmitted']
    assert_parent_closure(chosen)
    prompt,warnings=render_prompt(evidence(nodes),request(detail='concise'))
    assert 'Node 7, parent 6' in prompt and '[selected]' in prompt
    assert any('ancestor context' in w for w in warnings)


def test_no_isolated_priority_nodes_when_parent_chain_does_not_fit():
    nodes=[node(),node(1,0),node(2,1),node(3,2,'h1'),node(4,0,'button')]
    chosen,_=selection_plan(nodes,3)
    assert 3 not in {n['id'] for n in chosen}
    assert_parent_closure(chosen)


def test_invalid_cycles_orphans_and_duplicate_ids_do_not_change_parent_relationships():
    nodes=[node(),node(10,99,'button'),node(20,21),node(21,20),node(0,None)]
    chosen,sample=selection_plan(nodes,20)
    assert [n['id'] for n in chosen]==[0] and sample['invalid']==4
    assert all(n['parent'] is None for n in chosen)


def test_hierarchy_uses_captured_dom_sibling_order_and_keeps_ids():
    nodes=[node(),node(90,0,'button',siblingIndex=2),node(2,0,'h1',siblingIndex=0),node(45,0,'p',siblingIndex=1)]
    lines='\n'.join(hierarchy(nodes))
    assert lines.index('Node 2,')<lines.index('Node 45,')<lines.index('Node 90,')
    nodes.append(node(99,0,'button',siblingIndex=0,parentRelationship='shadow-host'))
    shadow='\n'.join(hierarchy(nodes))
    assert shadow.index('Node 90,')<shadow.index('Node 99,') and 'parent reference is its host' in shadow


def test_lossless_shared_style_groups_include_every_property_and_difference():
    common={'font-family':'"Two  Spaces", serif','font-size':'17.5px','padding-left':'19px','transition-duration':'0.23s','--arbitrary-measure':'observed'}
    nodes=[node(0,styles={**common,'color':'rgb(1, 2, 3)','display':'grid'}),
           node(5,0,styles={**common,'color':'rgb(1, 2, 3)','display':'flex'}),
           node(9,0,styles={**common,'color':'rgb(4, 5, 6)','display':'block'})]
    factored=factor_styles(nodes)
    for n in nodes:assert reconstruct(factored,n['id'])==n['styles']
    assert any(g['nodes']==[0,5] for g in factored['groups'].values())
    prompt,_=render_prompt(evidence(nodes),request(detail='concise'))
    assert prompt.count('"font-size": "17.5px"')==1
    assert '19px' in prompt and '0.23s' in prompt and '--arbitrary-measure' in prompt
    assert 'not proven CSS inheritance' in prompt


@pytest.mark.parametrize('scope',['element','section','page'])
@pytest.mark.parametrize('detail',['concise','detailed','highly-detailed'])
@pytest.mark.parametrize('target',['html-css','html-css-js','react'])
def test_all_existing_preferences_preserve_precision(scope,detail,target):
    nodes=[node(0,tag='section',styles={'display':'grid','grid-template-columns':'220px 480px','gap':'23px','background-color':'rgb(3, 4, 5)'}),
           node(8,0,'h1','Observed heading',styles={'font-size':'37px','line-height':'43px','font-family':'Inter'}),
           node(12,0,'button','Explore',styles={'width':'163px','border-radius':'9px','box-shadow':'0px 3px 7px rgb(0, 0, 0)'})]
    prompt,warnings=render_prompt(evidence(nodes,scope=scope),request(scope=scope,detail=detail,target=target))
    assert all(f'## {i}.' in prompt for i in range(1,9))
    assert all(v in prompt for v in ('220px 480px','23px','37px','43px','163px','9px','Node 12, parent 0'))
    assert 'No exact CSS breakpoints' in prompt and 'not verified behavior' in prompt
    assert warnings and len(prompt)<60000


@pytest.mark.parametrize('nodes',[[],[node(styles={})],[node(),node(1,999)]])
def test_empty_partial_and_truncated_evidence_is_honest(nodes):
    prompt,warnings=render_prompt(evidence(nodes,truncated=True),request())
    assert 'unavailable' in prompt and any('bounded' in w for w in warnings)
    assert 'not inspected' in prompt
    if not nodes:assert 'No usable' in ' '.join(warnings)


def test_byte_budget_prioritizes_late_cta_and_preserves_ancestor_paths():
    huge={f'property-{i}':'x'*180 for i in range(25)}
    nodes=[node()]+[node(i,0,text='generic',styles=huge) for i in range(1,50)]+[node(54,0,'button','Late CTA')]
    raw=evidence(nodes);raw.pop('source')
    result=sanitize(raw,'https://example.com/path?token=private')
    assert len(json.dumps(result,ensure_ascii=True).encode())<=MAX_EVIDENCE_BYTES
    assert result['truncated'] and any(n['id']==54 for n in result['nodes'])
    assert_parent_closure(result['nodes'])
    assert 'token=private' not in json.dumps(result)


def test_css_internal_whitespace_and_measured_strings_survive_sanitization():
    original={'font-family':'"Two  Spaces", sans-serif','grid-template-columns':'10px  20px','margin-left':'17px'}
    raw=evidence([node(styles=original)])
    cleaned=sanitize(raw,'https://example.com')['nodes'][0]
    assert cleaned['styles']==original


def test_boundary_decision_truncation_and_privacy_are_reported():
    n=node(styles={'grid-template-columns':'100px','background-image':'url(https://a.test/?token=secret)'},
           styleTruncatedProperties=['grid-template-columns'],accessibility={'label':'me@example.com','disabled':False})
    raw=evidence([n],boundaryDecision={'method':'scored-local-container','rootTag':'section','distance':2,'score':42,
        'reasons':['local semantic container'],'candidates':[{'tag':'main','distance':3,'rejected':'page-level landmark'}]})
    cleaned=sanitize(raw,'https://example.com')
    prompt,warnings=render_prompt(cleaned,request(scope='section'))
    assert 'Boundary decision' in prompt and 'page-level landmark' in prompt
    assert 'me@example.com' not in prompt and 'token=secret' not in prompt
    assert 'length-bounded properties' in prompt and any('privacy-sanitized' in w for w in warnings)


@pytest.mark.asyncio
async def test_no_key_generation_with_prioritized_evidence():
    service=PromptService(ProviderConfig())
    result=await service.generate(evidence([node(),node(42,0,'button','Start')]),request(mode='auto'))
    assert result.mode=='fallback' and 'Node 42, parent 0' in result.prompt and result.schemaVersion=='0.3'


@pytest.mark.parametrize('shared',[True,False])
@pytest.mark.asyncio
async def test_maximum_sanitized_sample_stays_inside_prompt_limit(shared):
    nodes=[]
    for i in range(55):
        styles={f'property-{k}':(('shared' if shared else str(i))+':'+str(k)+'x'*150) for k in range(70)}
        nodes.append(node(i,None if i==0 else 0,'button' if i%3==0 else 'div',styles=styles))
    bounded=sanitize(evidence(nodes),'https://example.com')
    result=await PromptService(ProviderConfig()).generate(bounded,request(detail='highly-detailed'))
    assert result.mode=='fallback' and len(result.prompt)<60000
    assert len(json.dumps(bounded,ensure_ascii=True).encode())<=MAX_EVIDENCE_BYTES


def test_byte_budget_does_not_reparent_unaffordable_selected_paths():
    nodes=[node()]+[node(i,i-1) for i in range(1,8)]+[node(8,7,'button',selected=True)]
    chosen,sample=selection_plan(nodes,55,cost=lambda n:100,budget=500)
    assert 8 not in {n['id'] for n in chosen} and sample['selectedOmitted']
    assert_parent_closure(chosen)
    prompt,warnings=render_prompt(evidence(chosen,sampling=sample),request())
    assert any('selected node did not fit' in w for w in warnings)


@pytest.mark.asyncio
async def test_page_wrapper_section_error_is_explicit_and_preserves_api_conventions():
    from unittest.mock import AsyncMock
    from app.browser_manager import Session,SessionError
    from app.prompts.evidence import collect_evidence
    root=AsyncMock();root.evaluate.return_value={'boundaryDecision':{'method':'selection-required'}}
    session=Session('s',AsyncMock(),AsyncMock(),element=root,reference_id='r',frame_id='f')
    with pytest.raises(SessionError) as exc:await collect_evidence(session,request(scope='section'))
    assert exc.value.code=='prompt-section-too-broad' and exc.value.status==422
