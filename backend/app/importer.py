from urllib.request import Request, urlopen
from urllib.parse import urlparse
from html.parser import HTMLParser
import ipaddress, socket

class MetaParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.meta={}; self.title=''; self._title=False
    def handle_starttag(self, tag, attrs):
        data=dict(attrs)
        if tag.lower()=='meta':
            key=data.get('property') or data.get('name')
            if key and data.get('content'): self.meta[key.lower()]=data['content'].strip()
        if tag.lower()=='title': self._title=True
    def handle_endtag(self, tag):
        if tag.lower()=='title': self._title=False
    def handle_data(self,data):
        if self._title: self.title+=data

def safe_url(url):
    p=urlparse(url)
    if p.scheme not in ('http','https') or not p.hostname: raise ValueError('URL inválida')
    for info in socket.getaddrinfo(p.hostname, p.port or (443 if p.scheme=='https' else 80)):
        ip=ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local: raise ValueError('Host privado não permitido')

def extract(url):
    safe_url(url)
    req=Request(url,headers={'User-Agent':'Mozilla/5.0 OrigonStudioAI/1.0'})
    with urlopen(req,timeout=12) as response: html=response.read(800000).decode('utf-8','ignore')
    parser=MetaParser(); parser.feed(html)
    name=parser.meta.get('og:title') or parser.title.strip() or 'Produto importado'
    return {'name':name[:160],'description':parser.meta.get('og:description') or parser.meta.get('description',''),'image':parser.meta.get('og:image',''),'source_url':url,'requiresReview':True,'notice':'Importação assistida: confirme os dados e os direitos de uso das mídias.'}
