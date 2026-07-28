import tempfile, os
from pathlib import Path
os.environ['ORIGON_STORAGE']=tempfile.mkdtemp()
from app.db import init_db, one
from app.creative import generate_versions, claim_guard

def test_database():
    init_db(); assert one('SELECT COUNT(*) n FROM products')['n']==0

def test_versions():
    p={'id':1,'name':'Produto teste','description':'','benefits':'praticidade','audience':'pessoas'}
    project={'id':1,'versions':3,'duration':15}
    assert len(generate_versions(p,project))==3

def test_claim_guard():
    c=claim_guard({'name':'X','description':'','benefits':'','price':''})
    assert c['blocked']
