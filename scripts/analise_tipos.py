# -*- coding: utf-8 -*-
"""
Lista todos os valores distintos do campo 005 (tipo) em cada download ISO,
para saber exatamente quais filtrar.
"""
import sys, os, tempfile
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parse_iso import parse_iso2709_isis
from collections import Counter
import requests

URL = "https://www.saopaulo.sp.leg.br/cgi-bin/wxis.bin/iah/scripts/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.saopaulo.sp.leg.br/cgi-bin/wxis.bin/iah/scripts/',
    'Origin': 'https://www.saopaulo.sp.leg.br',
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
    ('gizmoDecod', ''),
    ('avaibleForms', 'F,A'),
    ('logoImage', ''), ('logoURL', ''), ('headerImage', ''), ('headerURL', ''),
    ('form', 'A'),
    ('pathImages', '/iah/pt/image/'),
    ('navBar', 'ON'),
    ('hits', '10'),
    ('format', 'standard.pft'),
    ('lang', 'pt'),
    ('base', 'legis'),
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
    tmp = os.path.join(tempfile.gettempdir(), 'tmp_tipos.iso')
    with open(tmp, 'wb') as f:
        f.write(r.content)
    return parse_iso2709_isis(tmp)

PESQUISAS = {
    '"LEI"': r'C:\Users\kauen\Downloads\teste_grande.iso',
    '"RESOLUCAO"': None,
    '"ATO"': None,
    '"DECRETO LEGISLATIVO"': None,
    '"EMENDA"': None,
}

for expr, local_path in PESQUISAS.items():
    print(f"\n=== Pesquisa: {expr} ===")
    if local_path and os.path.exists(local_path):
        records = parse_iso2709_isis(local_path)
    else:
        print("  Baixando...")
        records = download_and_parse(expr)

    print(f"  Total registros: {len(records)}")

    # Contar valores distintos do campo 005 (primeiro valor se for lista)
    tipos = Counter()
    for rec in records:
        t = rec.get('005', '???')
        if isinstance(t, list):
            t = t[0]  # primeiro valor = tipo por extenso
        tipos[t] += 1

    for t, count in tipos.most_common():
        print(f"  005 = {repr(t):40s}  → {count:>5}")
