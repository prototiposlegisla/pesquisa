# -*- coding: utf-8 -*-
"""
Teste de scraping do iAH/wxis da Camara Municipal de Sao Paulo.
Objetivo: entender como paginar e extrair dados da base legis.
"""
import requests
import re
import time
import sys

# Force UTF-8 output on Windows
sys.stdout.reconfigure(encoding='utf-8')

URL = "https://www.saopaulo.sp.leg.br/cgi-bin/wxis.bin/iah/scripts/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

def fetch_page(expr_search, isis_from=1, hits=200):
    params = {
        'IsisScript': 'iah.xis',
        'form': 'A',
        'format': 'detalhado.pft',
        'navBar': 'OFF',
        'hits': str(hits),
        'lang': 'pt',
        'nextAction': 'search',
        'base': 'legis',
        'conectSearch': 'init',
        'exprSearch': expr_search,
        'indexSearch': '^nTn^LTipo de norma^x/5^yDATABASE',
        'isisFrom': str(isis_from),
    }
    r = requests.get(URL, params=params, headers=HEADERS, timeout=120)
    # The server says charset=utf-8 in detalhado format
    return r.text

def count_records(html):
    # Use the checkbox pattern which is unique per record
    return len(re.findall(r'name="listChecked"', html))

def extract_total(html):
    m = re.search(r'encontradas.*?<b>(\d+)</b>', html, re.DOTALL)
    return int(m.group(1)) if m else 0

def extract_showing(html):
    m = re.search(r'Mostrando.*?(\d+)\s*\.\.\s*(\d+)', html, re.DOTALL)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None

def extract_records(html):
    """Extract all records from the detailed format HTML."""
    records = []
    # Split by record markers (the checkbox with listChecked)
    parts = re.split(r'<!-- begin display of record -->', html)

    for part in parts[1:]:  # Skip the first part (before any record)
        record = {}
        # Extract field values from table rows
        for m in re.finditer(
            r'<td[^>]*align="right">(.*?)</td>\s*<td[^>]*>[^<]*</td>\s*<td[^>]*>(.*?)</td>',
            part, re.DOTALL
        ):
            label = re.sub(r'<[^>]+>', '', m.group(1)).replace('\xa0', '').strip()
            value = m.group(2)
            # Clean HTML from value but preserve link hrefs
            value_clean = re.sub(r'<[^>]+>', '', value).replace('\xa0', ' ').strip()
            value_clean = re.sub(r'\s+', ' ', value_clean)
            if label.endswith(':'):
                label = label[:-1]
            if label and value_clean:
                if label in record:
                    record[label] += ' | ' + value_clean
                else:
                    record[label] = value_clean

        # Extract MFN from checkbox value
        mfn_match = re.search(r'value="\^m(\d+)\^h', part)
        if mfn_match:
            record['_mfn'] = mfn_match.group(1)

        if record:
            records.append(record)

    return records

# === TESTE 1: Quantidade por tipo ===
print("=" * 60)
print("TESTE 1: Quantidade de normas por tipo")
print("=" * 60)
tipos = {
    'LEI': '"LEI"',
    'RESOLUCAO': '"RESOLUCAO"',
    'ATO': '"ATO"',
    'DECRETO LEGISLATIVO': '"DECRETO LEGISLATIVO"',
    'EMENDA': '"EMENDA"',
}
total_geral = 0
for nome, expr in tipos.items():
    html = fetch_page(expr, hits=10)
    total = extract_total(html)
    n_recs = count_records(html)
    show_from, show_to = extract_showing(html)
    print(f"  {nome}: {total} total, {n_recs} nesta pagina, mostrando {show_from}-{show_to}")
    total_geral += total
    time.sleep(2)
print(f"  TOTAL GERAL: {total_geral}")

# === TESTE 2: Paginacao ===
print("\n" + "=" * 60)
print("TESTE 2: Paginacao (LEI, paginas 1-3)")
print("=" * 60)
for page_start in [1, 11, 21]:
    html = fetch_page('"LEI"', isis_from=page_start, hits=10)
    records = extract_records(html)
    show_from, show_to = extract_showing(html)
    print(f"  isisFrom={page_start}: {len(records)} registros, mostrando {show_from}-{show_to}")
    if records:
        print(f"    Primeiro: {records[0].get('Titulo', records[0])}")
        print(f"    Ultimo:   {records[-1].get('Titulo', records[-1])}")
    time.sleep(2)

# === TESTE 3: hits maximo ===
print("\n" + "=" * 60)
print("TESTE 3: Limite de hits (tentando 200 com EMENDA que tem 44)")
print("=" * 60)
html = fetch_page('"EMENDA"', isis_from=1, hits=200)
n = count_records(html)
total = extract_total(html)
show_from, show_to = extract_showing(html)
print(f"  EMENDA ({total} total): {n} registros retornados, mostrando {show_from}-{show_to}")

# === TESTE 4: Estrutura de um registro completo ===
print("\n" + "=" * 60)
print("TESTE 4: Exemplo de registro LEI completo")
print("=" * 60)
html = fetch_page('"LEI"', isis_from=1, hits=10)
records = extract_records(html)
if records:
    for key, value in records[0].items():
        print(f"  {key}: {value[:120]}")

# === TESTE 5: Velocidade estimada ===
print("\n" + "=" * 60)
print("TESTE 5: Estimativa de tempo")
print("=" * 60)
pages_needed = total_geral // 10 + 1
print(f"  Total de normas: {total_geral}")
print(f"  Paginas necessarias (10 por pagina): {pages_needed}")
print(f"  Com delay de 2s entre requests: ~{pages_needed * 2 / 60:.0f} minutos")
print(f"  Com delay de 1s entre requests: ~{pages_needed * 1 / 60:.0f} minutos")

print("\nTeste completo!")
