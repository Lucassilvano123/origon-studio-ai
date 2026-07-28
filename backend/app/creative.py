import re, hashlib
STRATEGIES=['Curiosidade','Demonstração','Dor e solução','Review','UGC','Oferta','Tutorial','Comparação','Lista de benefícios','Antes e depois']

def claim_guard(product):
    confirmed=[]
    for label,value in [('Nome',product.get('name')),('Descrição',product.get('description')),('Benefícios',product.get('benefits')),('Preço',product.get('price'))]:
        if value: confirmed.append({'claim':str(value),'source':label,'status':'confirmed'})
    return {'confirmed':confirmed,'requiresApproval':[],'blocked':['preço, desconto, frete ou estoque não informados','afirmações médicas ou resultados garantidos não confirmados']}

def scenes_for(product,strategy,duration):
    name=product['name']; benefit=(product.get('benefits') or 'mais praticidade no dia a dia').split(',')[0]; audience=product.get('audience') or 'quem busca praticidade'
    count=max(4,min(6,round(duration/3)))
    templates=[
      ('Gancho',f'Você já imaginou facilitar sua rotina com {name}?','Olha isso!'),
      ('Problema',f'Para {audience}, tarefas simples não precisam tomar tanto tempo.','Menos complicação'),
      ('Produto',f'{name} foi pensado para tornar o uso mais simples. ',name),
      ('Benefício',f'O principal destaque é {benefit}.',benefit),
      ('Prova','Veja os detalhes e o funcionamento nas imagens do produto.','Veja na prática'),
      ('CTA','Confira as informações do produto antes de decidir.','Confira o produto'),
    ]
    if strategy=='Demonstração': templates[0]=('Gancho',f'Veja {name} funcionando na prática.','Funcionando na prática')
    if strategy=='Dor e solução': templates[0]=('Gancho','Você também enfrenta essa dificuldade no dia a dia?','Isso acontece com você?')
    if strategy=='Review': templates[0]=('Gancho',f'Vale a pena conhecer {name}?','Vale a pena?')
    if strategy=='Oferta': templates[-1]=('CTA','Confira preço, disponibilidade e condições diretamente no anúncio.','Confira as condições')
    chosen=templates[:count-1]+[templates[-1]]
    each=round(duration/len(chosen),2)
    return [{'order':i+1,'purpose':p,'narration':n.strip(),'screenText':t,'duration':each,'mediaRole':'video' if i<2 else 'image','transition':'fade' if i%2==0 else 'cut'} for i,(p,n,t) in enumerate(chosen)]

def generate_versions(product,project):
    n=project['versions']; seed=int(hashlib.sha1((product['name']+str(project['id'])).encode()).hexdigest()[:8],16)
    selected=[STRATEGIES[(seed+i*3)%len(STRATEGIES)] for i in range(n)]
    out=[]
    for i,strategy in enumerate(selected,1):
        scenes=scenes_for(product,strategy,project['duration'])
        out.append({'ordinal':i,'strategy':strategy,'hook':scenes[0]['narration'],'script':{'scenes':scenes},'creative':{'style': 'Automático','captionStyle':'Palavras-chave','musicMood':'Energética' if i%2 else 'Leve','claimGuard':claim_guard(product)}})
    return out
