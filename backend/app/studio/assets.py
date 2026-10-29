"""Embed only already-loaded origin-clean raster images. No new asset requests."""
import base64
from io import BytesIO
import re
from PIL import Image

async def embed_assets(session,evidence):
    images=[{'id':n['id'],'box':n.get('box')} for n in evidence['nodes'] if n['tag']=='img' and n.get('box')]
    if not images:return
    result=await session.page.evaluate('''items=>{
      const output={};let budget=64000;
      for(const n of items.slice(0,8)){
        const b=n.box,e=document.elementFromPoint(b.x+b.width/2,b.y+b.height/2);
        if(!(e instanceof HTMLImageElement)||!e.complete||!e.naturalWidth)continue;
        try{const c=document.createElement('canvas'),scale=Math.min(1,512/e.naturalWidth,512/e.naturalHeight);
          c.width=Math.max(1,Math.round(e.naturalWidth*scale));c.height=Math.max(1,Math.round(e.naturalHeight*scale));
          c.getContext('2d').drawImage(e,0,0,c.width,c.height);const data=c.toDataURL('image/png');
          if(data.length<=budget){output[n.id]=data;budget-=data.length;}
        }catch{} // Tainted/cross-origin images remain unavailable; never bypass CORS.
      }return output;
    }''',images)
    if not isinstance(result,dict):return
    budget=64000
    for n in evidence['nodes']:
        data=result.get(str(n['id']))
        if not isinstance(data,str) or len(data)>budget or not re.fullmatch(r'data:image/png;base64,[A-Za-z0-9+/]+={0,2}',data):continue
        try:
            image=Image.open(BytesIO(base64.b64decode(data.split(',',1)[1],validate=True)))
            if image.format!='PNG' or image.width>512 or image.height>512:continue
            image.verify()
        except Exception:continue
        n['embeddedAsset']=data;budget-=len(data)
