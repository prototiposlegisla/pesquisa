# -*- coding: utf-8 -*-
"""
Analisa distribuição temporal de TODAS as normas (5 tipos).
Baixa cada tipo e agrupa para ter panorama completo.
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parse_iso import parse_iso2709_isis, transform_record
from collections import Counter
import requests

URL = "https://www.saopaulo.sp.leg.br/cgi-bin/wxis.bin/iah/scripts/"

TIPOS = {
    'LEI': '"LEI"',
    'RESOLUCAO': '"RESOLUCAO"',
    'ATO': '"ATO"',
    'DECRETO_LEG': '"DECRETO LEGISLATIVO"',
    'EMENDA': '"EMENDA"',
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
    ('gizmoDecod', ''),
    ('avaibleForms', 'F,A'),
    ('logoImage', ''),
    ('logoURL', ''),
    ('headerImage', ''),
    ('headerURL', ''),
    ('form', 'A'),
    ('pathImages', '/iah/pt/image/'),
    ('navBar', 'ON'),
    ('hits', '10'),
    ('format', 'standard.pft'),
    ('lang', 'pt'),
    ('base', 'legis'),
    ('conectSearch', 'init'),
    ('conectSearch', 'and'),
    ('conectSearch', 'and'),
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.saopaulo.sp.leg.br/cgi-bin/wxis.bin/iah/scripts/',
    'Origin': 'https://www.saopaulo.sp.leg.br',
    'Content-Type': 'application/x-www-form-urlencoded',
}

def download_iso(expr_search):
    form_data = list(BASE_FORM)
    form_data.append(('exprSearch', expr_search))
    form_data.extend([
        ('indexSearch', '^nTn^LTipo de norma^x/5^yDATABASE'),
        ('indexSearch', '^nTw^LTodos os campos^2Todos los campos^3All fields^xALL ^yDATABASE'),
        ('indexSearch', '^nTw^LTodos os campos^2Todos los campos^3All fields^xALL ^yDATABASE'),
        ('user', 'GUEST'),
        ('baseFeatures', '^e^f'),
        ('related', ''),
        ('nextAction', 'list'),
        ('listOption', 'list_all'),
        ('listHit', '1'),
        ('listHit', '3'),
        ('sendOption', 'export-iso'),
        ('saveFileType', 'export-iso'),
    ])

    session = requests.Session()
    session.headers.update(HEADERS)
    r = session.post(URL, data=form_data, timeout=300)
    return r.content


# Usar os arquivos já baixados se existirem, senão baixar
import tempfile

all_records = []

for nome, expr in TIPOS.items():
    print(f"\n--- {nome} ({expr}) ---")

    # Tentar arquivo local primeiro
    local_paths = {
        'LEI': r'C:\Users\kauen\Downloads\teste_grande.iso',
    }

    if nome in local_paths and os.path.exists(local_paths[nome]):
        print(f"  Usando arquivo local: {local_paths[nome]}")
        records = parse_iso2709_isis(local_paths[nome])
    else:
        print(f"  Baixando...")
        content = download_iso(expr)
        print(f"  Recebido: {len(content):,} bytes")
        tmp = os.path.join(tempfile.gettempdir(), f'norma_{nome}.iso')
        with open(tmp, 'wb') as f:
            f.write(content)
        records = parse_iso2709_isis(tmp)

    transformed = [transform_record(r) for r in records]
    print(f"  Registros: {len(transformed)}")
    all_records.extend(transformed)

print(f"\n{'='*60}")
print(f"TOTAL: {len(all_records)} normas de todos os tipos")

# Análise temporal
anos = []
for r in all_records:
    data = r['data']
    if data and '/' in data:
        try:
            ano = int(data.split('/')[-1])
            if 1800 <= ano <= 2030:  # filtrar outliers
                anos.append(ano)
        except ValueError:
            pass

counter = Counter(anos)
print(f"Com data válida: {len(anos)}")
print(f"Outliers descartados: {len(all_records) - len(anos)}")
print(f"Range: {min(anos)} a {max(anos)}")

# Distribuição por quinquênio
print(f"\n=== LAYERS DE 5 ANOS (todas as normas) ===")
quinquenios = Counter()
for ano, qtd in counter.items():
    bloco = (ano // 5) * 5
    quinquenios[bloco] += qtd

acum = 0
for bloco in sorted(quinquenios.keys(), reverse=True):
    fim = bloco + 4
    qtd = quinquenios[bloco]
    acum += qtd
    bar = '#' * (qtd // 40)
    print(f"  {bloco}-{fim}: {qtd:>5}  acum={acum:>6}  {bar}")

# Distribuição por década
print(f"\n=== LAYERS DE 10 ANOS (todas as normas) ===")
decadas = Counter()
for ano, qtd in counter.items():
    decada = (ano // 10) * 10
    decadas[decada] += qtd

acum = 0
for dec in sorted(decadas.keys(), reverse=True):
    fim = dec + 9
    qtd = decadas[dec]
    acum += qtd
    bar = '#' * (qtd // 60)
    print(f"  {dec}-{fim}: {qtd:>5}  acum={acum:>6}  {bar}")

# Tipos por década
print(f"\n=== TIPOS POR DÉCADA ===")
tipo_decada = {}
for r in all_records:
    data = r['data']
    if data and '/' in data:
        try:
            ano = int(data.split('/')[-1])
            if 1800 <= ano <= 2030:
                dec = (ano // 10) * 10
                key = (dec, r['tipo'])
                tipo_decada[key] = tipo_decada.get(key, 0) + 1
        except ValueError:
            pass

all_tipos = sorted(set(r['tipo'] for r in all_records))
header = f"{'Década':>12}" + "".join(f"{t:>10}" for t in all_tipos) + f"{'TOTAL':>10}"
print(header)
for dec in sorted(decadas.keys(), reverse=True):
    row = f"  {dec}-{dec+9:>4}"
    total = 0
    for t in all_tipos:
        v = tipo_decada.get((dec, t), 0)
        total += v
        row += f"{v:>10}"
    row += f"{total:>10}"
    print(row)
