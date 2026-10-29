import json
from typing import Literal
from pydantic import Field, model_validator
from ..schemas import StrictModel
from ..prompts.schemas import PromptRequest

FILES = {'index.html', 'style.css', 'script.js', 'App.jsx', 'main.jsx', 'package.json', 'vite.config.js', 'README.md'}

class Project(StrictModel):
    format: Literal['vanilla', 'react'] = 'vanilla'
    files: dict[str, str]

    @model_validator(mode='after')
    def validate_files(self):
        required = {'index.html','style.css','script.js'} if self.format == 'vanilla' else {'index.html','style.css','App.jsx','main.jsx','package.json','vite.config.js'}
        if not required <= self.files.keys() or not set(self.files) <= FILES:
            raise ValueError('Project requires the supported file structure; nested paths are not allowed.')
        if any(not isinstance(v,str) or len(v.encode()) > 100000 for v in self.files.values()) or sum(len(v.encode()) for v in self.files.values()) > 180000:
            raise ValueError('Project exceeds the 180 KB budget.')
        if self.format == 'react':
            try:package=json.loads(self.files['package.json'])
            except ValueError:raise ValueError('package.json must contain valid JSON.') from None
            if package.get('scripts') != {'dev':'vite --host 127.0.0.1','build':'vite build','preview':'vite preview --host 127.0.0.1'} or package.get('dependencies') != {'react':'19.1.1','react-dom':'19.1.1'} or package.get('devDependencies') != {'vite':'8.3.5'} or set(package) - {'name','version','private','type','scripts','dependencies','devDependencies'}:
                raise ValueError('React project metadata must retain the supported Vite scripts and pinned dependencies.')
            if self.files['vite.config.js'].strip() != 'export default {};':
                raise ValueError('Custom build configurations are not supported by the preview. Keep export default {};')
        return self

class GenerateRequest(PromptRequest):
    format: Literal['vanilla', 'react'] = 'vanilla'
    consent: bool = False

class RefineRequest(StrictModel):
    generationId: str = Field(pattern=r'^[a-f0-9]{32}$')
    project: Project
    instruction: str = Field(min_length=5, max_length=1200)
    consent: bool = False

class PreviewRequest(StrictModel):
    project: Project
