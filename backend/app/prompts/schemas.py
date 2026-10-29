from typing import Literal
from pydantic import Field
from ..schemas import StrictModel


class PromptRequest(StrictModel):
    sessionId: str = Field(min_length=1, max_length=64, pattern=r'^[A-Za-z0-9_-]+$')
    frameId: str = Field(min_length=1, max_length=64)
    referenceId: str | None = Field(default=None, min_length=1, max_length=64)
    scope: Literal['element', 'section', 'page'] = 'element'
    target: Literal['html-css', 'html-css-js', 'react'] = 'react'
    detail: Literal['concise', 'detailed', 'highly-detailed'] = 'detailed'
    style: Literal['faithful', 'responsive', 'accessible'] = 'faithful'
    mode: Literal['auto', 'local'] = 'local'
    preset: Literal['faithful', 'responsive-first', 'accessible-implementation', 'clean-production-code', 'maximum-visual-detail'] = 'faithful'


class PromptResponse(StrictModel):
    schemaVersion: Literal['0.3'] = '0.3'
    generationId: str
    prompt: str = Field(max_length=60000)
    mode: Literal['ai', 'fallback']
    provider: str | None = None
    model: str | None = None
    warnings: list[str]
    evidenceSummary: dict
