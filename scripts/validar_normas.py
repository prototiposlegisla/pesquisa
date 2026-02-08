# -*- coding: utf-8 -*-
"""Valida os JSONs gerados: estrutura, ordenação, amostragem de dados."""
import json, os, sys
sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dados", "normas")

# Carregar version
with open(os.path.join(DATA_DIR, "normas-version.json"), 'r', encoding='utf-8') as f:
    version = json.load(f)

print(f"=== normas-version.json ===")
print(f"  lastUpdate: {version['lastUpdate']}")
print(f"  totalNormas: {version['totalNormas']}")
print(f"  Camadas: {len(version['camadas'])}")
print()

total_check = 0
all_tipos = set()

for key in sorted(version['camadas'].keys()):
    info = version['camadas'][key]
    filename = info['arquivo']
    filepath = os.path.join(DATA_DIR, filename)

    with open(filepath, 'r', encoding='utf-8') as f:
        layer = json.load(f)

    cols = layer['columns']
    rows = layer['data']
    total_check += len(rows)

    print(f"--- {filename} ({info['anos']}) ---")
    print(f"  Normas: {len(rows)} (version diz: {info['normas']})")
    assert len(rows) == info['normas'], f"MISMATCH: {len(rows)} != {info['normas']}"

    # Verificar colunas
    expected_cols = ["tipo", "numero", "data", "ementa", "autores", "publicacao",
                     "projeto", "palavras-chave", "notas", "revogacao", "searchable"]
    assert cols == expected_cols, f"Colunas erradas: {cols}"

    # Verificar ordenação (data decrescente)
    order_ok = True
    for i in range(1, len(rows)):
        d_prev = rows[i-1][2]  # data
        d_curr = rows[i][2]
        # Converter DD/MM/YYYY para tuple comparável
        def to_tuple(d):
            try:
                parts = d.split('/')
                return (int(parts[2]), int(parts[1]), int(parts[0]))
            except:
                return (0, 0, 0)
        if to_tuple(d_prev) < to_tuple(d_curr):
            if order_ok:
                print(f"  ⚠️ Ordenação quebrada em row {i}: {d_prev} < {d_curr}")
                order_ok = False

    if order_ok:
        print(f"  ✅ Ordenação OK (decrescente)")

    # Tipos presentes
    tipos = {}
    for row in rows:
        t = row[0]
        tipos[t] = tipos.get(t, 0) + 1
        all_tipos.add(t)
    detail = ", ".join(f"{t}:{c}" for t, c in sorted(tipos.items()))
    print(f"  Tipos: {detail}")

    # Amostra: primeiro e último
    first = rows[0]
    last = rows[-1]
    print(f"  Primeiro: {first[0]} {first[1]} | {first[2]} | {first[3][:60]}...")
    print(f"  Último:   {last[0]} {last[1]} | {last[2]} | {last[3][:60]}...")

    # Verificar searchable
    for row in rows:
        s = row[10]
        if any(c in s for c in "áéíóúãõçÁÉÍÓÚÃÕÇ"):
            print(f"  ❌ Searchable com acentos: {s[:60]}")
            break
    else:
        print(f"  ✅ Searchable OK (sem acentos)")

    print()

print(f"=== RESUMO ===")
print(f"Total normas nos arquivos: {total_check}")
print(f"Total no version.json:     {version['totalNormas']}")
assert total_check == version['totalNormas'], f"MISMATCH total!"
print(f"✅ Totais batem!")
print(f"Tipos encontrados: {sorted(all_tipos)}")
