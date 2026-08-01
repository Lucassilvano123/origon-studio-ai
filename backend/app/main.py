from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import json, shutil, subprocess, platform
from .db import init_db, init_media_db, rows, one, execute, log, now, connect
from .schemas import ProductIn, ProjectIn, BatchIn, ImportUrlIn, GenerateIn, SettingIn
from .creative import generate_versions, claim_guard
from .importer import extract
from .config import STORAGE

app=FastAPI(title='Origon Studio AI API',version='0.1.0')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_methods=['*'],allow_headers=['*'])
@app.on_event('startup')
def startup(): init_db(); init_media_db()
@app.get('/health')
def health(): return {'status':'healthy','service':'origon-studio-ai'}
@app.get('/api/dashboard')
def dashboard():
    return {'products':one('SELECT COUNT(*) n FROM products WHERE status="active"')['n'],'projects':one('SELECT COUNT(*) n FROM projects')['n'],'batches':one('SELECT COUNT(*) n FROM batches')['n'],'jobs':one('SELECT COUNT(*) n FROM jobs')['n'],'recent':rows('SELECT * FROM history ORDER BY id DESC LIMIT 10')}
@app.get('/api/products')
def list_products(): return rows('SELECT * FROM products WHERE status="active" ORDER BY id DESC')
@app.post('/api/products')
def create_product(body:ProductIn):
    i=execute('INSERT INTO products(name,category,description,benefits,audience,source_url,price,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,"active",?,?)',(body.name,body.category,body.description,body.benefits,body.audience,body.source_url,body.price,now(),now())); log('product',i,'created'); return one('SELECT * FROM products WHERE id=?',(i,))
@app.get('/api/products/{pid}')
def get_product(pid:int):
    x=one('SELECT * FROM products WHERE id=?',(pid,));
    if not x: raise HTTPException(404,'Produto não encontrado')
    return x
@app.put('/api/products/{pid}')
def update_product(pid:int,body:ProductIn):
    execute('UPDATE products SET name=?,category=?,description=?,benefits=?,audience=?,source_url=?,price=?,updated_at=? WHERE id=?',(body.name,body.category,body.description,body.benefits,body.audience,body.source_url,body.price,now(),pid)); log('product',pid,'updated'); return get_product(pid)
@app.delete('/api/products/{pid}')
def delete_product(pid:int):
    x=get_product(pid); execute('INSERT INTO trash(entity_type,entity_id,payload_json,deleted_at) VALUES("product",?,?,?)',(pid,json.dumps(x,ensure_ascii=False),now())); execute('UPDATE products SET status="trash" WHERE id=?',(pid,)); log('product',pid,'trashed'); return {'ok':True}
@app.post('/api/import/url')
def import_url(body:ImportUrlIn):
    try:return extract(str(body.url))
    except Exception as e: raise HTTPException(422,f'Não foi possível importar automaticamente: {e}')
@app.get('/api/projects')
def projects(): return rows('SELECT p.*,pr.name product_name FROM projects p JOIN products pr ON pr.id=p.product_id ORDER BY p.id DESC')
@app.post('/api/projects')
def create_project(body:ProjectIn):
    if not one('SELECT id FROM products WHERE id=?',(body.product_id,)): raise HTTPException(404,'Produto não encontrado')
    i=execute('INSERT INTO projects(product_id,name,platform,mode,duration,versions,language,status,created_at,updated_at) VALUES(?,?,?,?,?,?,?,"draft",?,?)',(body.product_id,body.name,body.platform,body.mode,body.duration,body.versions,body.language,now(),now())); log('project',i,'created'); return one('SELECT * FROM projects WHERE id=?',(i,))
@app.get('/api/projects/{pid}')
def get_project(pid:int):
    x=one('SELECT p.*,pr.name product_name,pr.description,pr.benefits,pr.audience FROM projects p JOIN products pr ON pr.id=p.product_id WHERE p.id=?',(pid,));
    if not x: raise HTTPException(404,'Projeto não encontrado')
    x['versions_data']=rows('SELECT * FROM versions WHERE project_id=? ORDER BY ordinal',(pid,)); return x
@app.post('/api/generate')
def generate(body:GenerateIn):
    project=one('SELECT * FROM projects WHERE id=?',(body.project_id,));
    if not project: raise HTTPException(404,'Projeto não encontrado')
    product=one('SELECT * FROM products WHERE id=?',(project['product_id'],)); execute('DELETE FROM versions WHERE project_id=?',(project['id'],))
    generated=generate_versions(product,project)
    for v in generated: execute('INSERT INTO versions(project_id,ordinal,strategy,hook,script_json,creative_json,status,created_at,updated_at) VALUES(?,?,?,?,?,?,"ready",?,?)',(project['id'],v['ordinal'],v['strategy'],v['hook'],json.dumps(v['script'],ensure_ascii=False),json.dumps(v['creative'],ensure_ascii=False),now(),now()))
    execute('UPDATE projects SET status="ready",updated_at=? WHERE id=?',(now(),project['id'])); log('project',project['id'],'generated',{'versions':len(generated)}); return get_project(project['id'])
@app.get('/api/batches')
def list_batches(): return rows('SELECT * FROM batches ORDER BY id DESC')
@app.post('/api/batches')
def create_batch(body:BatchIn):
    i=execute('INSERT INTO batches(name,status,product_ids_json,versions,progress,created_at,updated_at) VALUES(?,"draft",?,?,0,?,?)',(body.name,json.dumps(body.product_ids),body.versions,now(),now())); log('batch',i,'created'); return one('SELECT * FROM batches WHERE id=?',(i,))
@app.post('/api/batches/{bid}/prepare')
def prepare_batch(bid:int):
    b=one('SELECT * FROM batches WHERE id=?',(bid,));
    if not b: raise HTTPException(404,'Lote não encontrado')
    ids=json.loads(b['product_ids_json']); created=[]
    for product_id in ids:
        product=one('SELECT * FROM products WHERE id=?',(product_id,));
        if not product: continue
        project_id=execute('INSERT INTO projects(product_id,name,platform,mode,duration,versions,language,status,created_at,updated_at) VALUES(?,?,"shopee","assisted",15,?,"pt-BR","draft",?,?)',(product_id,f'Lote {bid} - {product["name"]}',b['versions'],now(),now()))
        generate(GenerateIn(project_id=project_id)); created.append(project_id)
        for v in rows('SELECT id FROM versions WHERE project_id=?',(project_id,)): execute('INSERT INTO jobs(batch_id,project_id,version_id,status,progress,message,created_at,updated_at) VALUES(?,?,?,"ready",0,"Aguardando mídias e render",?,?)',(bid,project_id,v['id'],now(),now()))
    execute('UPDATE batches SET status="ready",progress=25,updated_at=? WHERE id=?',(now(),bid)); log('batch',bid,'prepared',{'projects':created}); return {'batch':one('SELECT * FROM batches WHERE id=?',(bid,)),'projects':created,'jobs':rows('SELECT * FROM jobs WHERE batch_id=?',(bid,))}
@app.get('/api/history')
def history(): return rows('SELECT * FROM history ORDER BY id DESC LIMIT 200')
@app.get('/api/trash')
def trash(): return rows('SELECT * FROM trash ORDER BY id DESC')
@app.post('/api/trash/{tid}/restore')
def restore(tid:int):
    x=one('SELECT * FROM trash WHERE id=?',(tid,));
    if not x: raise HTTPException(404,'Item não encontrado')
    if x['entity_type']=='product': execute('UPDATE products SET status="active",updated_at=? WHERE id=?',(now(),x['entity_id']))
    execute('DELETE FROM trash WHERE id=?',(tid,)); return {'ok':True}
@app.get('/api/settings')
def settings(): return {x['key']:json.loads(x['value_json']) for x in rows('SELECT * FROM settings')}
@app.put('/api/settings/{key}')
def set_setting(key:str,body:SettingIn): execute('INSERT OR REPLACE INTO settings(key,value_json,updated_at) VALUES(?,?,?)',(key,json.dumps(body.value,ensure_ascii=False),now())); return {'ok':True}
@app.get('/api/diagnostics')
def diagnostics():
    def cmd(name):
        path=shutil.which(name); return {'ok':bool(path),'path':path}
    disk=shutil.disk_usage(STORAGE)
    return {'overall':'ready' if cmd('ffmpeg')['ok'] else 'warning','python':platform.python_version(),'ffmpeg':cmd('ffmpeg'),'ffprobe':cmd('ffprobe'),'piper':cmd('piper'),'database':{'ok':STORAGE.joinpath('database','origon.db').exists(),'path':str(STORAGE.joinpath('database','origon.db'))},'storage':{'path':str(STORAGE),'freeGB':round(disk.free/1024**3,2)},'providers':{'externalEnabled':False,'webllm':'browser-check-required','comfyui':'not-configured','huggingface':'not-configured'}}
@app.post('/api/repair')
def repair(): init_db(); return {'ok':True,'message':'Banco e pastas verificados.'}


from .media_service import save_upload
from .render_service import render_version, export_package, editorial

app.mount('/storage/media', StaticFiles(directory=STORAGE/'media'), name='media')

@app.get('/api/products/{pid}/media')
def product_media(pid:int):
    return rows('SELECT * FROM media WHERE product_id=? ORDER BY favorite DESC,id DESC',(pid,))

@app.post('/api/products/{pid}/media')
async def upload_media(pid:int, files:list[UploadFile]=File(...)):
    get_product(pid); result=[]
    for item in files:
        try:
            meta=save_upload(pid,item.filename or 'media',item.file)
            mid=execute('INSERT INTO media(product_id,original_name,stored_name,media_type,mime_type,size_bytes,width,height,duration,has_audio,origin,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,"upload",?)',(pid,item.filename,meta['stored_name'],meta['media_type'],item.content_type,meta['size_bytes'],meta['width'],meta['height'],meta['duration'],meta['has_audio'],now()))
            result.append(one('SELECT * FROM media WHERE id=?',(mid,)))
        finally: await item.close()
    log('product',pid,'media_uploaded',{'count':len(result)}); return result

@app.patch('/api/media/{mid}')
def media_update(mid:int, favorite:bool|None=None, blocked:bool|None=None):
    m=one('SELECT * FROM media WHERE id=?',(mid,))
    if not m: raise HTTPException(404,'Mídia não encontrada')
    execute('UPDATE media SET favorite=?,blocked=? WHERE id=?',(int(favorite) if favorite is not None else m['favorite'],int(blocked) if blocked is not None else m['blocked'],mid)); return one('SELECT * FROM media WHERE id=?',(mid,))

@app.delete('/api/media/{mid}')
def media_delete(mid:int):
    m=one('SELECT * FROM media WHERE id=?',(mid,))
    if not m: raise HTTPException(404,'Mídia não encontrada')
    path=STORAGE/'media'/str(m['product_id'])/m['stored_name']; path.unlink(missing_ok=True); execute('DELETE FROM media WHERE id=?',(mid,)); return {'ok':True}

@app.get('/api/versions/{vid}/editor')
def editor_data(vid:int):
    v=one('SELECT v.*,p.product_id,pr.name product_name FROM versions v JOIN projects p ON p.id=v.project_id JOIN products pr ON pr.id=p.product_id WHERE v.id=?',(vid,))
    if not v: raise HTTPException(404,'Versão não encontrada')
    v['script']=json.loads(v['script_json']); v['media']=rows('SELECT * FROM media WHERE product_id=? ORDER BY favorite DESC,id',(v['product_id'],)); v['assignments']=rows('SELECT * FROM scene_media WHERE version_id=?',(vid,)); return v

@app.put('/api/versions/{vid}/scene/{order}/media/{mid}')
def assign_media(vid:int,order:int,mid:int):
    execute('INSERT OR REPLACE INTO scene_media(version_id,scene_order,media_id,created_at) VALUES(?,?,?,?)',(vid,order,mid,now())); return {'ok':True}

@app.post('/api/versions/{vid}/auto-assign')
def auto_assign(vid:int):
    data=editor_data(vid); media=[m for m in data['media'] if not m['blocked']]
    if not media: raise HTTPException(422,'Adicione mídias ao produto')
    execute('DELETE FROM scene_media WHERE version_id=?',(vid,))
    for i,_scene in enumerate(data['script'].get('scenes',[]),1):
        preferred=next((m for m in media if (i<=2 and m['media_type']=='video')),None) or media[(i-1)%len(media)]
        execute('INSERT INTO scene_media(version_id,scene_order,media_id,created_at) VALUES(?,?,?,?)',(vid,i,preferred['id'],now()))
    return editor_data(vid)

@app.post('/api/versions/{vid}/render')
def render(vid:int):
    try:
        output,quality=render_version(vid); return {'ok':True,'download':f'/api/versions/{vid}/video','quality':quality,'editorial':editorial(vid)}
    except Exception as e: raise HTTPException(500,f'Falha na renderização: {e}')

@app.get('/api/versions/{vid}/video')
def download_video(vid:int):
    v=one('SELECT output_path FROM versions WHERE id=?',(vid,)); path=Path(v['output_path']) if v and v['output_path'] else None
    if not path or not path.exists(): raise HTTPException(404,'Vídeo ainda não foi renderizado')
    return FileResponse(path,media_type='video/mp4',filename=path.name)

@app.get('/api/versions/{vid}/export')
def export(vid:int):
    z=export_package(vid); return FileResponse(z,media_type='application/zip',filename=z.name)
