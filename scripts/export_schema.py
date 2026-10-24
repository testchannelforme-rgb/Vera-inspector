import json
from pathlib import Path
from app.schemas import Inspection

if __name__=='__main__':
    target=Path('docs/inspection.schema.json')
    target.parent.mkdir(exist_ok=True)
    schema=Inspection.model_json_schema()
    schema['$schema']='https://json-schema.org/draft/2020-12/schema'
    schema['$id']='urn:veyra:inspection:0.1'
    target.write_text(json.dumps(schema,indent=2)+'\n')
    print(target)
