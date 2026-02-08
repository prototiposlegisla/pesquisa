# -*- coding: utf-8 -*-
"""
Teste de download automatizado de ISO 2709 do iAH/wxis da Câmara Municipal de SP.
Replica exatamente o POST que o browser faz ao clicar "enviar" no formulário de exportação.
"""
import requests
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

URL = "https://www.saopaulo.sp.leg.br/cgi-bin/wxis.bin/iah/scripts/"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
    'Referer': 'https://www.saopaulo.sp.leg.br/cgi-bin/wxis.bin/iah/scripts/',
    'Origin': 'https://www.saopaulo.sp.leg.br',
    'Content-Type': 'application/x-www-form-urlencoded',
}

# Exatamente os campos que o browser envia, na ordem correta
# Usando lista de tuplas para permitir campos repetidos
FORM_DATA = [
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
    ('exprSearch', '"DECRETO LEGISLATIVO"'),
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
]


def test_download():
    session = requests.Session()
    session.headers.update(HEADERS)

    # Primeiro, fazer uma busca GET para inicializar a sessão (como o browser faz)
    print("1. Inicializando sessão com busca GET...")
    search_params = {
        'IsisScript': 'iah.xis',
        'form': 'A',
        'format': 'detalhado.pft',
        'navBar': 'OFF',
        'hits': '10',
        'lang': 'pt',
        'nextAction': 'search',
        'base': 'legis',
        'conectSearch': 'init',
        'exprSearch': '"LEI"',
        'indexSearch': '^nTn^LTipo de norma^x/5^yDATABASE',
        'isisFrom': '1',
    }
    r1 = session.get(URL, params=search_params, timeout=60)
    print(f"   Status: {r1.status_code}, Length: {len(r1.content)}")
    print(f"   Cookies: {dict(session.cookies)}")

    # Agora, tentar o POST de exportação
    print("\n2. POST para exportação ISO...")
    r2 = session.post(URL, data=FORM_DATA, timeout=120, allow_redirects=True)
    print(f"   Status: {r2.status_code}")
    print(f"   Content-Type: {r2.headers.get('Content-Type', 'N/A')}")
    print(f"   Content-Disposition: {r2.headers.get('Content-Disposition', 'N/A')}")
    print(f"   Content-Length header: {r2.headers.get('Content-Length', 'N/A')}")
    print(f"   Actual length: {len(r2.content)}")
    print(f"   First 100 bytes (hex): {r2.content[:100].hex(' ')}")
    print(f"   First 100 bytes (raw): {r2.content[:100]}")

    # Verificar se é ISO 2709 (começa com 5 dígitos de tamanho de registro)
    first_5 = r2.content[:5]
    is_iso = first_5.isdigit()
    print(f"\n   Parece ISO 2709? {is_iso} (primeiros 5 bytes: {first_5})")

    if is_iso:
        output = os.path.join(os.path.dirname(__file__), 'test_output.iso')
        with open(output, 'wb') as f:
            f.write(r2.content)
        print(f"   Salvo em: {output} ({len(r2.content):,} bytes)")
    else:
        # Provavelmente HTML
        text = r2.content.decode('utf-8', errors='replace')[:500]
        print(f"\n   Conteúdo (primeiros 500 chars):\n{text}")


if __name__ == '__main__':
    test_download()
