# -*- coding: utf-8 -*-
"""
Distribuição temporal final com os filtros corretos de tipo.
"""
import sys, os, tempfile
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parse_iso import parse_iso2709_isis
from collections import Counter
import requests

URL = "https://www.saopaulo.sp.leg.br/cgi-bin/wxis.bin/iah/scripts/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0', 'Referer': URL, 'Origin': 'https://www.saopaulo.sp.leg.br',
    'Content-Type': 'application/x-www-form-urlencoded',
}
BASE_FORM = [
    ('IsisScript', 'iah.xis'),
    ('environment', '^d/iah/^c/u01/data/www/html/iah/scripts/^b/u01/data/www/html/bases/iah/^p/u01/data/www/html/bases/iah/par/^siah.xis^v3.1.1'),
    ('avaibleFormats', '^nstandard.pft^1Resumido^2Resumido^3Resumed'),
    ('avaibleFormats', '^ndetalhado.pft^1Detalhado^2Datallado^3Detailed'),
    ('avaibleFormats', '^nDEFAULT^fdetalhado.pft'),
    ('apperance', '^eportal.cti3@camara.sp.gov.br^rON^m^apt'),
    ('helpInfo', '^nHELP FORM^vhelp_form_legis.htm'),
    ('helpInfo', '^nNOTE FORM F^vnote_form_legis.htm'),
    ('helpInfo', '^nNOTE FORM A^vnote_form_legis-a.htm'),
    ('gizmoDecod', ''), ('avaibleForms', 'F,A'),
    ('logoImage', ''), ('logoURL', ''), ('headerImage', ''), ('headerURL', ''),
    ('form', 'A'), ('pathImages', '/iah/pt/image/'), ('navBar', 'ON'),
    ('hits', '10'), ('format', 'standard.pft'), ('lang', 'pt'), ('base', 'legis'),
    ('conectSearch', 'init'), ('conectSearch', 'and'), ('conectSearch', 'and'),
]

def download_and_parse(expr):
    form_data = list(BASE_FORM)
    form_data.append(('exprSearch', expr))
    form_data.extend([
        ('indexSearch', '^nTn^LTipo de norma^x/5^yDATABASE'),
        ('indexSearch', '^nTw^LTodos os campos^2Todos los campos^3All fields^xALL ^yDATABASE'),
        ('indexSearch', '^nTw^LTodos os campos^2Todos los campos^3All fields^xALL ^yDATABASE'),
        ('user', 'GUEST'), ('baseFeatures', '^e^f'), ('related', ''),
        ('nextAction', 'list'), ('listOption', 'list_all'),
        ('listHit', '1'), ('listHit', '3'),
        ('sendOption', 'export-iso'), ('saveFileType', 'export-iso'),
    ])
    session = requests.Session()
    session.headers.update(HEADERS)
    r = session.post(URL, data=form_data, timeout=300)
    tmp = os.path.join(tempfile.gettempdir(), f'tmp_final.iso')
    with open(tmp, 'wb') as f:
        f.write(r.content)
    return parse_iso2709_isis(tmp)

# Tipos aceitos (valor exato do campo 005)
TIPOS_ACEITOS = {
    'Lei',
    'Resolução da CMSP',
    'Resolução',         # grafía antiga (pré-1930), mesma coisa
    'Ato da CMSP',
    'Decreto Legislativo',
    'Emenda',
}

PESQUISAS = {
    '"LEI"': r'C:\Users\kauen\Downloads\teste_grande.iso',
    '"RESOLUCAO"': None,
    '"ATO"': None,
    '"DECRETO LEGISLATIVO"': None,
    '"EMENDA"': None,
}

all_records = []

for expr, local_path in PESQUISAS.items():
    print(f"--- {expr} ---")
    if local_path and os.path.exists(local_path):
        records = parse_iso2709_isis(local_path)
    else:
        print("  Baixando...")
        records = download_and_parse(expr)

    before = len(records)
    filtered = []
    for rec in records:
        t = rec.get('005', '')
        if isinstance(t, list):
            t = t[0]
        if t in TIPOS_ACEITOS:
            filtered.append(rec)
    print(f"  {before} brutos → {len(filtered)} filtrados (descartados: {before - len(filtered)})")
    all_records.extend(filtered)

print(f"\nTOTAL FILTRADO: {len(all_records)}")

# Extrair ano
def get_ano(rec):
    data = rec.get('010', '')
    if data and '/' in data:
        try:
            ano = int(data.split('/')[-1])
            if 1800 <= ano <= 2030:
                return ano
        except:
            pass
    return None

# Distribuição por década com tipos
decadas = Counter()
tipo_decada = Counter()
for rec in all_records:
    ano = get_ano(rec)
    if ano:
        dec = (ano // 10) * 10
        decadas[dec] += 1
        t = rec.get('005', '')
        if isinstance(t, list):
            t = t[0]
        tipo_decada[(dec, t)] += 1

# Layer proposta: atual = ano corrente, resto = décadas
print(f"\n=== LAYERS PROPOSTAS ===")
print(f"{'Layer':<20} {'Período':<12} {'Normas':>7}  Detalhes")

# Calcular tamanho estimado em KB (aprox 600 bytes por norma em JSON compacto)
BYTES_PER_NORMA = 600

ano_corrente = 2026
atual_count = sum(1 for rec in all_records if get_ano(rec) == ano_corrente)
print(f"{'normas-atual.json':<20} {ano_corrente:<12} {atual_count:>7}  ~{atual_count * BYTES_PER_NORMA // 1024} KB")

# Década corrente exceto ano corrente
dec_corrente = (ano_corrente // 10) * 10
dec_count = sum(1 for rec in all_records if get_ano(rec) and dec_corrente <= get_ano(rec) < ano_corrente)
if dec_count > 0:
    nome = f"normas-{dec_corrente}.json"
    print(f"{nome:<20} {dec_corrente}-{ano_corrente-1:<6} {dec_count:>7}  ~{dec_count * BYTES_PER_NORMA // 1024} KB")

for dec in sorted(decadas.keys(), reverse=True):
    if dec == dec_corrente:
        continue  # já contou acima
    nome = f"normas-{dec}.json"
    qtd = decadas[dec]
    detail_parts = []
    for t in ['Lei', 'Resolução da CMSP', 'Resolução', 'Ato da CMSP', 'Decreto Legislativo', 'Emenda']:
        c = tipo_decada.get((dec, t), 0)
        if c > 0:
            short = {'Lei':'LEI','Resolução da CMSP':'RES','Resolução':'RES','Ato da CMSP':'ATO','Decreto Legislativo':'DL','Emenda':'EM'}
            detail_parts.append(f"{short[t]}:{c}")
    detail = ", ".join(detail_parts)
    print(f"{nome:<20} {dec}-{dec+9:<6} {qtd:>7}  ~{qtd * BYTES_PER_NORMA // 1024} KB  [{detail}]")

outliers = sum(1 for rec in all_records if get_ano(rec) is None)
print(f"\nSem data válida: {outliers}")
