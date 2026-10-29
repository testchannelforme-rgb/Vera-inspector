"""Candidate behavior: evidence inventory, distinct presets and unchanged contracts."""
from copy import deepcopy
import re
import pytest
from pydantic import ValidationError
from app.prompts.schemas import PromptRequest
from app.prompts.presets import PRESETS
from app.prompts.deterministic import render_prompt
from app.prompts.report import quality_report
from app.prompts.service import PromptService
from app.prompts.provider import ProviderConfig
from test_prompts import evidence, node, request

@pytest.mark.parametrize('preset', PRESETS)
def test_presets_retain_eight_sections_and_exact_css_without_new_measurements(preset):
    e=evidence();q=request(preset=preset)
    text,warnings=render_prompt(e,q)
    assert re.findall(r'^## ([1-8])\.',text,re.M)==list('12345678')
    assert '160px' in text and 'rgb(37, 99, 235)' in text
    assert PRESETS[preset][0] in text and PRESETS[preset][1] in text
    assert 'No exact CSS breakpoints' in text and 'No hover capture' in text
    assert 'No links, buttons' in text and warnings


def test_all_presets_produce_distinct_testable_implementation_priorities():
    texts={p:render_prompt(evidence(),request(preset=p))[0] for p in PRESETS}
    assert len(set(texts.values()))==5
    assert 'intrinsic grid/flex' in texts['responsive-first']
    assert 'contrast ratio' in texts['accessible-implementation']
    assert 'file/component map' in texts['clean-production-code']
    assert 'Do not flatten compositing' in texts['maximum-visual-detail']


def test_maximum_detail_coverage_matches_report():
    e=evidence([node(id=i,parent=0 if i else None) for i in range(35)])
    a=quality_report(e,request(detail='concise'),[])
    b=quality_report(e,request(detail='concise',preset='maximum-visual-detail'),[])
    assert a['coverage']['describedNodes']==4
    assert b['coverage']['describedNodes']==28
    assert b['coverage']['rendererOmittedNodes']==7 and b['coverage']['truncated']


def test_report_never_equates_indicators_with_observation_or_accuracy():
    e=evidence();r=quality_report(e,request(),['One warning','One warning'])
    assert r['coverage']['computedStyleEntries']==len(e['nodes'][0]['styles'])
    assert r['warnings']==['One warning']
    assert any('Hover endpoints' in x for x in r['missing'])
    assert any('Navigation destinations' in x for x in r['missing'])
    assert not any('accuracy' in k.lower() for k in r)
    empty=quality_report({**e,'nodes':[]},request(),[])
    assert empty['coverage']['describedNodes']==0
    assert 'Usable connected' in empty['missing'][0]


def test_flagged_styles_assets_and_hover_baseline_are_attributed():
    e=evidence();e['nodes'][0]['sanitizedProperties']=['background-image'];e['nodes'][0]['styleTruncatedProperties']=['background-image','mask-image']
    e['nodes'][0]['image']={'alt':'Image','naturalWidth':80,'naturalHeight':60}
    e['hover']={'baselineWasAlreadyHovered':True}
    r=quality_report(e,request(),[])
    assert r['coverage']['flaggedProperties']==2
    assert 'Node 0' in r['assetChecklist'][0]
    assert any('resting hover baseline' in s for s in r['missing'])
    assert any('prior hover capture' in s for s in r['observed'])


async def test_service_adds_report_without_changing_schema_or_calling_provider():
    from unittest.mock import AsyncMock
    provider=AsyncMock();provider.generate.side_effect=AssertionError('No provider call')
    response=await PromptService(ProviderConfig(),provider).generate(evidence(),request(preset='clean-production-code'))
    assert response.schemaVersion=='0.3' and response.mode=='fallback'
    r=response.evidenceSummary['qualityReport'];assert r['preset']=='clean-production-code'
    assert r['coverage']['describedNodes']==1
    provider.generate.assert_not_called()
    with pytest.raises(ValidationError):PromptRequest(sessionId='s',frameId='f',preset='invent-measurements')
