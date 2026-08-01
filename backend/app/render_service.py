from pathlib import Path
import subprocess, json, uuid, shutil, textwrap, zipfile
from .config import STORAGE
from .db import one, rows, execute, now

def run(cmd,msg):
    p=subprocess.run(cmd,capture_output=True,text=True,check=False)
    if p.returncode: raise RuntimeError((p.stderr or msg)[-4000:])

def render_scene(source:Path,out:Path,duration:float,media_type:str,text:str):
    textfile=STORAGE/'renders'/f'text-{uuid.uuid4().hex}.txt'; textfile.write_text('\n'.join(textwrap.wrap(text or 'Confira o produto',26)[:3]))
    vf=f"scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,fps=30,drawtext=textfile='{textfile}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=h-text_h-150:box=1:boxcolor=black@0.6:boxborderw=24,format=yuv420p"
    try:
        inp=['-stream_loop','-1','-i',str(source)] if media_type=='video' else ['-loop','1','-i',str(source)]
        run(['ffmpeg','-y',*inp,'-vf',vf,'-t',str(max(1,duration)),'-an','-c:v','libx264','-preset','fast','-crf','22','-movflags','+faststart',str(out)],'Falha na cena')
    finally:textfile.unlink(missing_ok=True)

def render_version(version_id:int):
    v=one('SELECT v.*,p.name project_name,p.product_id,pr.name product_name FROM versions v JOIN projects p ON p.id=v.project_id JOIN products pr ON pr.id=p.product_id WHERE v.id=?',(version_id,))
    if not v: raise ValueError('Versão não encontrada')
    script=json.loads(v['script_json']); scenes=script.get('scenes',[])
    media=rows('SELECT * FROM media WHERE product_id=? AND blocked=0 ORDER BY favorite DESC,id',(v['product_id'],))
    if not media: raise ValueError('Adicione pelo menos uma mídia ao produto')
    assignments={x['scene_order']:x for x in rows('SELECT sm.*,m.* FROM scene_media sm JOIN media m ON m.id=sm.media_id WHERE sm.version_id=?',(version_id,))}
    tmp=STORAGE/'renders'/f'tmp-{uuid.uuid4().hex}';tmp.mkdir(parents=True)
    clips=[]
    try:
        for i,scene in enumerate(scenes,1):
            m=assignments.get(i) or media[(i-1)%len(media)]
            source=STORAGE/'media'/str(v['product_id'])/m['stored_name'];clip=tmp/f'{i:03}.mp4'
            render_scene(source,clip,float(scene.get('duration',3)),m['media_type'],scene.get('screenText','')); clips.append(clip)
        concat=tmp/'concat.txt';concat.write_text('\n'.join(f"file '{x}'" for x in clips))
        outdir=STORAGE/'renders'/str(v['project_id']);outdir.mkdir(parents=True,exist_ok=True)
        output=outdir/f'version-{v["ordinal"]}-{uuid.uuid4().hex[:8]}.mp4'
        run(['ffmpeg','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy','-movflags','+faststart',str(output)],'Falha ao concatenar')
        quality={'exists':output.exists(),'size':output.stat().st_size if output.exists() else 0,'resolution':'720x1280','video':'h264','status':'approved' if output.exists() and output.stat().st_size>1000 else 'rejected'}
        execute('UPDATE versions SET status="rendered",output_path=?,updated_at=? WHERE id=?',(str(output),now(),version_id))
        return output,quality
    finally: shutil.rmtree(tmp,ignore_errors=True)

def editorial(version_id:int):
    v=one('SELECT v.*,pr.name product_name,pr.benefits FROM versions v JOIN projects p ON p.id=v.project_id JOIN products pr ON pr.id=p.product_id WHERE v.id=?',(version_id,))
    strategy=v['strategy'];name=v['product_name']
    return {'title':f'{name}: veja os detalhes','caption':f'{v["hook"]} Confira as informações e condições diretamente no anúncio.','hashtags':['#ShopeeVideo','#Produto','#Dica',f'#{name.replace(" ","")}'],'keywords':[name,strategy,v.get('benefits') or 'praticidade'],'pinnedComment':'Qual detalhe deste produto chamou mais sua atenção?'}

def export_package(version_id:int):
    v=one('SELECT * FROM versions WHERE id=?',(version_id,)); data=editorial(version_id)
    folder=STORAGE/'exports'/f'version-{version_id}';folder.mkdir(parents=True,exist_ok=True)
    for key,val in data.items(): (folder/f'{key}.txt').write_text('\n'.join(val) if isinstance(val,list) else str(val))
    (folder/'manifest.json').write_text(json.dumps({'version':v,'editorial':data},ensure_ascii=False,indent=2),encoding='utf-8')
    if v.get('output_path') and Path(v['output_path']).exists(): shutil.copy2(v['output_path'],folder/'video.mp4')
    z=STORAGE/'exports'/f'origon-version-{version_id}.zip'
    with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as out:
        for p in folder.iterdir():out.write(p,p.name)
    return z
