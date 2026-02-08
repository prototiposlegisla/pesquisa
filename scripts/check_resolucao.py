# -*- coding: utf-8 -*-
import sys, os, tempfile
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_iso import parse_iso2709_isis, transform_record
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

form_data = list(BASE_FORM)
form_data.append(('exprSearch', '"RESOLUCAO"'))
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
tmp = os.path.join(tempfile.gettempdir(), 'resolucoes.iso')
with open(tmp, 'wb') as f:
    f.write(r.content)
records = parse_iso2709_isis(tmp)

# Analisar os registros com tipo "Resolução" (sem "da CMSP")
print("=== 'Resolução' (sem 'da CMSP') - Distribuição por década ===")
decadas = Counter()
exemplos = []
for rec in records:
    t = rec.get('005', '')
    if isinstance(t, list):
        t = t[0]
    if t == 'Resolução':
        data = rec.get('010', '')
        if data and '/' in data:
            try:
                ano = int(data.split('/')[-1])
                dec = (ano // 10) * 10
                decadas[dec] += 1
                if len(exemplos) < 5:
                    exemplos.append(f"  {rec.get('001','')} | {data} | {rec.get('025','')[:80]}")
            except:
                pass

for dec in sorted(decadas.keys(), reverse=True):
    print(f"  {dec}s: {decadas[dec]}")

print(f"\nExemplos:")
for e in exemplos:
    print(e)

print(f"\n=== 'Resolução AMC' ===")
for rec in records:
    t = rec.get('005', '')
    if isinstance(t, list):
        t = t[0]
    if t == 'Resolução AMC':
        print(f"  {rec.get('001','')} | {rec.get('010','')} | {rec.get('025','')[:80]}")
