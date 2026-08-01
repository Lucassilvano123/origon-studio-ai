from pathlib import Path
import json, subprocess, shutil, uuid
from .config import STORAGE

ALLOWED={'.jpg','jpeg','.jpeg','.png','.webp','.mp4','.mov','.webm','.m4v'}

def probe(path:Path):
    cmd=['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]
    p=subprocess.run(cmd,capture_output=True,text=True,check=False)
    if p.returncode: return {'width':0,'height':0,'duration':0,'has_audio':0}
    d=json.loads(p.stdout or '{}'); streams=d.get('streams',[])
    video=next((s for s in streams if s.get('codec_type')=='video'),{})
    return {'width':int(video.get('width') or 0),'height':int(video.get('height') or 0),'duration':float((d.get('format') or {}).get('duration') or 0),'has_audio':int(any(s.get('codec_type')=='audio' for s in streams))}

def save_upload(product_id:int, filename:str, fileobj):
    suffix=Path(filename).suffix.lower()
    if suffix not in ALLOWED: raise ValueError('Formato não suportado')
    folder=STORAGE/'media'/str(product_id);folder.mkdir(parents=True,exist_ok=True)
    stored=f'{uuid.uuid4().hex}{suffix}';path=folder/stored
    with path.open('wb') as out: shutil.copyfileobj(fileobj,out)
    meta=probe(path);meta.update({'path':path,'stored_name':stored,'size_bytes':path.stat().st_size,'media_type':'video' if suffix in {'.mp4','.mov','.webm','.m4v'} else 'image'})
    return meta
