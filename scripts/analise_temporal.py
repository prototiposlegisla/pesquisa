# -*- coding: utf-8 -*-
"""
Analisa a distribuição temporal das normas no ISO grande (LEIs)
para ajudar a definir os cortes das layers.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from parse_iso import parse_iso2709_isis, transform_record
from collections import Counter

# Usar o arquivo grande de LEIs já baixado
filepath = r'C:\Users\kauen\Downloads\teste_grande.iso'
print(f"Parseando {filepath}...")
records = parse_iso2709_isis(filepath)
transformed = [transform_record(r) for r in records]
print(f"Total: {len(transformed)} registros\n")

# Extrair ano de cada registro
anos = []
for r in transformed:
    data = r['data']  # formato DD/MM/YYYY
    if data and '/' in data:
        try:
            ano = int(data.split('/')[-1])
            anos.append(ano)
        except ValueError:
            pass

counter = Counter(anos)

print("=== DISTRIBUIÇÃO POR ANO (LEIs) ===")
print(f"{'Ano':>6} {'Qtd':>6}  {'Acum':>6}")
acum = 0
for ano in sorted(counter.keys(), reverse=True):
    acum += counter[ano]
    bar = '#' * (counter[ano] // 20)
    print(f"{ano:>6} {counter[ano]:>6}  {acum:>6}  {bar}")

# Agrupar por década
print("\n=== DISTRIBUIÇÃO POR DÉCADA ===")
decadas = Counter()
for ano, qtd in counter.items():
    decada = (ano // 10) * 10
    decadas[decada] += qtd

for dec in sorted(decadas.keys(), reverse=True):
    print(f"  {dec}s: {decadas[dec]:>5} normas")

# Sugerir layers com período fixo de 5 anos
print("\n=== SUGESTÃO DE LAYERS (5 anos) ===")
quinquenios = Counter()
for ano, qtd in counter.items():
    bloco = (ano // 5) * 5
    quinquenios[bloco] += qtd

for bloco in sorted(quinquenios.keys(), reverse=True):
    fim = bloco + 4
    print(f"  {bloco}-{fim}: {quinquenios[bloco]:>5} normas")

# Faixas maiores (10 anos)
print("\n=== SUGESTÃO DE LAYERS (10 anos) ===")
for dec in sorted(decadas.keys(), reverse=True):
    fim = dec + 9
    print(f"  {dec}-{fim}: {decadas[dec]:>5} normas")

print(f"\nAnos extremos: {min(anos)} a {max(anos)}")
print(f"Total com data parseada: {len(anos)}/{len(transformed)}")
