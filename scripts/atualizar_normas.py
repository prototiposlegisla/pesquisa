#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
atualizar_normas.py — Coleta e atualiza a base de normas municipais de São Paulo.

Pipeline:
  1. Download: 5 POSTs ao iAH → 5 arquivos ISO 2709
  2. Parse: ISO 2709 → registros Python (via parse_iso.py)
  3. Filtrar: somente tipos aceitos
  4. Merge + Ordenar: por data decrescente
  5. Split: dividir por período fixo (décadas) em layers
  6. Transform: registro → row array compacto + searchable
  7. Hash check: só salva layers que efetivamente mudaram
  8. version.json: atualiza metadados e hashes

Fonte: Biblioteca da Câmara Municipal de São Paulo (iAH/CDS-ISIS)
       https://www.saopaulo.sp.leg.br/cgi-bin/wxis.bin/iah/scripts/

Uso:
  python atualizar_normas.py                  # atualiza tudo
  python atualizar_normas.py --layer atual    # só a layer atual (ano corrente)
  python atualizar_normas.py --layer 2010     # só a layer da década de 2010
  python atualizar_normas.py --layer atual,2020  # múltiplas layers
"""
import json
import os
import sys
import time
import hashlib
import tempfile
import argparse
import unicodedata
import re
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from zoneinfo import ZoneInfo

# Garantir que o parse_iso.py seja importável
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_iso import parse_iso2709_isis

# --- CONFIGURAÇÃO ---

IAH_URL = "https://www.saopaulo.sp.leg.br/cgi-bin/wxis.bin/iah/scripts/"
MAX_RETRIES = 3
TIMEOUT_SECONDS = 300
SP_TZ = ZoneInfo("America/Sao_Paulo")

DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "dados", "normas"
)

# Expressões de busca por tipo de norma (campo indexSearch = Tipo de norma)
PESQUISAS = [
    '"LEI"',
    '"RESOLUCAO"',
    '"ATO"',
    '"DECRETO LEGISLATIVO"',
    '"EMENDA"',
]

# Valores aceitos do campo 005 (tipo por extenso no ISIS).
# Tudo que não estiver aqui é descartado.
TIPOS_ACEITOS = {
    'Lei',
    'Resolução da CMSP',
    'Ato da CMSP',
    'Decreto Legislativo',
    'Emenda',
}

# Mapeamento do tipo extenso (005) para sigla curta usada no JSON final
TIPO_SIGLA = {
    'Lei':                  'LEI',
    'Resolução da CMSP':    'RES',
    'Ato da CMSP':          'ATO',
    'Decreto Legislativo':  'DL',
    'Emenda':               'ELO',
}

# Nomes por extenso para o searchable
TIPO_EXTENSO = {
    'LEI':  'Lei',
    'RES':  'Resolução da CMSP',
    'ATO':  'Ato da CMSP',
    'DL':   'Decreto Legislativo',
    'ELO':  'Emenda à Lei Orgânica',
}

# Campos do JSON final (índices 0..10)
COLUMNS = [
    "tipo",             # 0
    "numero",           # 1
    "data",             # 2
    "ementa",           # 3
    "autores",          # 4
    "publicacao",       # 5
    "projeto",          # 6
    "palavras-chave",   # 7
    "notas",            # 8
    "revogacao",        # 9
    "searchable",       # 10
]

# Definição das layers: (nome_arquivo, ano_inicio, ano_fim)
# ano_fim = None significa "até o ano anterior ao corrente" (calculado em runtime)
# A layer "atual" é tratada à parte.
LAYER_DECADAS = [
    # décadas fixas de 2020 para trás
    ("normas-2020.json", 2020, None),   # 2020 até ano_corrente-1
    ("normas-2010.json", 2010, 2019),
    ("normas-2000.json", 2000, 2009),
    ("normas-1990.json", 1990, 1999),
    ("normas-1980.json", 1980, 1989),
    ("normas-1970.json", 1970, 1979),
    ("normas-1960.json", 1960, 1969),
    ("normas-1950.json", 1950, 1959),
    ("normas-1940.json", 1940, 1949),
    ("normas-1930.json", 1930, 1939),
    ("normas-1920.json", 1920, 1929),
    ("normas-1910.json", 1910, 1919),
    ("normas-1900.json", 1900, 1909),
    ("normas-antigo.json", 1, 1899),    # tudo antes de 1900
]


# --- FORMULÁRIO iAH ---

IAH_BASE_FORM = [
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

IAH_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
    'Referer': IAH_URL,
    'Origin': 'https://www.saopaulo.sp.leg.br',
    'Content-Type': 'application/x-www-form-urlencoded',
}


# --- UTILITÁRIOS ---

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def load_json(filename: str) -> Optional[Dict]:
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"  Erro ao ler {filename}: {e}")
        return None

def save_json(filename: str, data: Any):
    ensure_data_dir()
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
    print(f"  💾 Salvo: {filename}")

def content_hash(data: Any) -> str:
    """SHA256 do conteúdo JSON serializado (determinístico)."""
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()

def normalize_string(text: str) -> str:
    """Normaliza string para busca: lowercase, sem acentos, sem pontuação."""
    if not text:
        return ""
    text = text.lower()
    text = unicodedata.normalize('NFD', text).encode('ASCII', 'ignore').decode('utf-8')
    text = re.sub(r'(?<=\d)\.(?=\d)', '', text)
    text = text.replace('_', ' ')
    text = re.sub(r'[^a-z0-9\s|/\-\(\)]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def normalize_searchable(components: List[str]) -> str:
    """Constrói o campo searchable final normalizado."""
    raw_text = " | ".join([c if c else "" for c in components])
    normalized = normalize_string(raw_text)
    final_text = re.sub(r'\s*\|\s*', ' | ', normalized)
    return f" {final_text} "


# --- DOWNLOAD ---

def download_iso(expr_search: str) -> bytes:
    """Baixa um export ISO 2709 completo para a expressão de busca dada."""
    form_data = list(IAH_BASE_FORM)
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
    session.headers.update(IAH_HEADERS)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = session.post(IAH_URL, data=form_data, timeout=TIMEOUT_SECONDS)
            if r.status_code == 200 and r.content[:5].isdigit():
                return r.content
            else:
                print(f"    ⚠️ Tentativa {attempt}: status={r.status_code}, content-type={r.headers.get('Content-Type','?')}, len={len(r.content)}")
        except Exception as e:
            print(f"    ⚠️ Tentativa {attempt}: {e}")

        if attempt < MAX_RETRIES:
            wait = 15 * (2 ** (attempt - 1))
            print(f"    ⏳ Aguardando {wait}s...")
            time.sleep(wait)

    raise Exception(f"Falha ao baixar ISO para {expr_search} após {MAX_RETRIES} tentativas")


def download_all() -> List[Dict]:
    """Baixa, parseia e filtra todos os tipos de norma. Retorna lista de registros ISIS (dicts)."""
    all_records = []

    for expr in PESQUISAS:
        print(f"  🔄 Baixando {expr}...")
        iso_bytes = download_iso(expr)

        # Salvar temporariamente para parsear
        tmp = os.path.join(tempfile.gettempdir(), f'norma_{expr.strip(chr(34))}.iso')
        with open(tmp, 'wb') as f:
            f.write(iso_bytes)

        records = parse_iso2709_isis(tmp)
        before = len(records)

        # Filtrar tipos aceitos
        filtered = []
        for rec in records:
            tipo = rec.get('005', '')
            if isinstance(tipo, list):
                tipo = tipo[0]
            if tipo in TIPOS_ACEITOS:
                filtered.append(rec)

        print(f"    ✅ {before} registros → {len(filtered)} aceitos (descartados: {before - len(filtered)})")
        all_records.extend(filtered)

        # Limpar arquivo temp
        try:
            os.remove(tmp)
        except:
            pass

    print(f"  📊 Total: {len(all_records)} normas")
    return all_records


# --- TRANSFORMAÇÃO ---

def get_ano_from_data(data_str: str) -> Optional[int]:
    """Extrai o ano de uma data DD/MM/AAAA. Retorna None se inválido."""
    if not data_str or '/' not in data_str:
        return None
    try:
        ano = int(data_str.split('/')[-1])
        if 1800 <= ano <= 2100:
            return ano
    except ValueError:
        pass
    return None

def parse_data_sortkey(data_str: str) -> Tuple[int, int, int]:
    """Converte DD/MM/AAAA em tupla (ano, mes, dia) para ordenação."""
    try:
        parts = data_str.split('/')
        if len(parts) == 3:
            dia, mes, ano = int(parts[0]), int(parts[1]), int(parts[2])
            if 1800 <= ano <= 2100:
                return (ano, mes, dia)
    except (ValueError, IndexError):
        pass
    return (0, 0, 0)

def transform_isis_record(rec: Dict) -> Optional[List[str]]:
    """Transforma um registro ISIS parseado em row array para o JSON final."""
    # Tipo
    tipo_extenso = rec.get('005', '')
    if isinstance(tipo_extenso, list):
        tipo_extenso = tipo_extenso[0]
    sigla = TIPO_SIGLA.get(tipo_extenso)
    if not sigla:
        return None  # tipo não reconhecido

    # Número (remover pontos de milhar)
    numero = rec.get('006', '').replace('.', '')

    # Data
    data = rec.get('010', '')

    # Ementa (pode ser lista em casos raros)
    ementa = rec.get('025', '')
    if isinstance(ementa, list):
        ementa = ' '.join(ementa)

    # Autores (tag 032, repetitivo)
    autores_raw = rec.get('032', '')
    if isinstance(autores_raw, list):
        autores = ' | '.join(autores_raw)
    else:
        autores = autores_raw

    # Publicação (pode ser lista)
    publicacao = rec.get('035', '')
    if isinstance(publicacao, list):
        publicacao = ' | '.join(publicacao)

    # Projeto de origem (030 + 031 + 033)
    tipo_projeto = rec.get('030', '')
    num_projeto = rec.get('031', '')
    ano_projeto = rec.get('033', '')
    projeto = ''
    if tipo_projeto and num_projeto:
        projeto = f"{tipo_projeto} {num_projeto}"
        if ano_projeto:
            projeto += f"/{ano_projeto}"

    # Palavras-chave/indexação (tag 070, repetitivo, entre <>)
    idx_raw = rec.get('070', [])
    if isinstance(idx_raw, str):
        idx_raw = [idx_raw]
    palavras = []
    for item in idx_raw:
        clean = item.strip('<>').strip()
        if clean:
            palavras.append(clean)
    palavras_chave = ' | '.join(palavras) if palavras else ''

    # Notas (pode ser lista)
    notas = rec.get('045', '')
    if isinstance(notas, list):
        notas = ' | '.join(notas)

    # Revogação (pode ser lista se múltiplas)
    revogacao = rec.get('042', '')
    if isinstance(revogacao, list):
        revogacao = ' | '.join(revogacao)

    # Searchable
    extenso = TIPO_EXTENSO.get(sigla, '')
    search_components = [
        sigla,
        extenso,
        numero,
        data,
        ementa,
        palavras_chave,
        autores,
        projeto,
        notas,
        revogacao,
        f"{numero}/{data.split('/')[-1]}" if data and '/' in data else "",
    ]
    searchable = normalize_searchable(search_components)

    return [
        sigla,          # 0
        numero,         # 1
        data,           # 2
        ementa,         # 3
        autores,        # 4
        publicacao,     # 5
        projeto,        # 6
        palavras_chave, # 7
        notas,          # 8
        revogacao,      # 9
        searchable,     # 10
    ]


# --- PROCESSAMENTO DE LAYERS ---

def split_into_layers(records: List[Dict], ano_corrente: int) -> Dict[str, List[Dict]]:
    """
    Distribui os registros ISIS nas layers por período.
    Retorna dict {nome_arquivo: [registros_isis]}.
    """
    layers = {}

    # Inicializar todas as layers
    atual_name = "normas-atual.json"
    layers[atual_name] = []
    for name, _, _ in LAYER_DECADAS:
        layers[name] = []

    sem_data = []

    for rec in records:
        data = rec.get('010', '')
        ano = get_ano_from_data(data)

        if ano is None:
            sem_data.append(rec)
            continue

        if ano == ano_corrente:
            layers[atual_name].append(rec)
            continue

        # Procurar layer correta
        placed = False
        for name, start, end in LAYER_DECADAS:
            real_end = end if end is not None else (ano_corrente - 1)
            if start <= ano <= real_end:
                layers[name].append(rec)
                placed = True
                break

        if not placed:
            # Ano fora de qualquer range (improvável, mas seguro)
            layers["normas-antigo.json"].append(rec)

    if sem_data:
        print(f"  ⚠️ {len(sem_data)} registros sem data válida (descartados)")
        for rec in sem_data[:3]:
            print(f"    → {rec.get('001', '?')} | data={rec.get('010', '?')}")

    return layers


def process_layer(name: str, isis_records: List[Dict], existing_hashes: Dict[str, str]) -> Tuple[bool, int, Optional[str]]:
    """
    Transforma e salva uma layer, verificando hash para evitar gravações desnecessárias.
    Retorna (changed, count, new_hash).
    """
    if not isis_records:
        return False, 0, None

    # Ordenar por data decrescente
    isis_records.sort(key=lambda r: parse_data_sortkey(r.get('010', '')), reverse=True)

    # Transformar
    rows = []
    for rec in isis_records:
        row = transform_isis_record(rec)
        if row:
            rows.append(row)

    if not rows:
        return False, 0, None

    layer_data = {
        "columns": COLUMNS,
        "data": rows,
    }

    new_hash = content_hash(layer_data)
    old_hash = existing_hashes.get(name)

    if new_hash == old_hash:
        print(f"  ⏭️  {name}: sem mudanças ({len(rows)} normas, hash={new_hash[:12]}...)")
        return False, len(rows), new_hash

    # Validar antes de salvar
    if not validate_layer(name, rows):
        print(f"  ❌ {name}: validação falhou! Não salvo.")
        return False, 0, None

    save_json(name, layer_data)
    print(f"     → {len(rows)} normas, hash={new_hash[:12]}...")
    return True, len(rows), new_hash


# --- VALIDAÇÃO ---

def validate_layer(name: str, rows: List[List[str]]) -> bool:
    """Validação básica dos dados transformados."""
    valid_tipos = set(TIPO_SIGLA.values())

    for i, row in enumerate(rows):
        if len(row) != len(COLUMNS):
            print(f"    Erro: row {i} tem {len(row)} campos (esperado {len(COLUMNS)})")
            return False

        tipo = row[0]
        if tipo not in valid_tipos:
            print(f"    Erro: row {i} tipo inválido: {tipo}")
            return False

        searchable = row[10]
        if not searchable or '|' not in searchable:
            print(f"    Erro: row {i} searchable inválido")
            return False

        # Verificar que searchable está normalizado (sem acentos)
        if any(c in searchable for c in "áéíóúãõçÁÉÍÓÚÃÕÇ"):
            print(f"    Erro: row {i} searchable contém acentos")
            return False

    return True


# --- FLUXO PRINCIPAL ---

def main():
    sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description="Atualiza base de normas municipais de São Paulo")
    parser.add_argument('--layer', type=str, default='all',
                        help='Layers a processar: all, atual, 2020, 2010, ... ou combinações separadas por vírgula')
    args = parser.parse_args()

    ano_corrente = datetime.now(SP_TZ).year
    print(f"🏛️  Atualização de Normas Municipais — {datetime.now(SP_TZ).strftime('%d/%m/%Y %H:%M')}")
    print(f"   Ano corrente: {ano_corrente}")
    print()

    # 1. Download de todos os ISOs
    print("📥 FASE 1: Download dos dados ISO 2709")
    try:
        all_isis = download_all()
    except Exception as e:
        print(f"\n🚨 Erro fatal no download: {e}")
        sys.exit(1)

    # 2. Distribuir em layers
    print(f"\n📂 FASE 2: Distribuição em layers")
    layer_map = split_into_layers(all_isis, ano_corrente)

    # Estatísticas
    for name in ["normas-atual.json"] + [n for n, _, _ in LAYER_DECADAS]:
        count = len(layer_map.get(name, []))
        if count > 0:
            print(f"  {name}: {count} registros")

    # 3. Carregar version.json existente
    existing_version = load_json("normas-version.json") or {}
    existing_hashes = {}
    for key, info in existing_version.get("camadas", {}).items():
        if "hash" in info:
            existing_hashes[info.get("arquivo", "")] = info["hash"]

    # 4. Determinar quais layers processar
    requested = args.layer.strip()
    if requested == 'all':
        layers_to_process = ["normas-atual.json"] + [n for n, _, _ in LAYER_DECADAS]
    else:
        parts = [p.strip() for p in requested.split(',')]
        layers_to_process = []
        for p in parts:
            if p == 'atual':
                layers_to_process.append("normas-atual.json")
            elif p == 'antigo':
                layers_to_process.append("normas-antigo.json")
            else:
                # Tentar como década: "2010" → "normas-2010.json"
                candidate = f"normas-{p}.json"
                if candidate in layer_map:
                    layers_to_process.append(candidate)
                else:
                    print(f"  ⚠️ Layer desconhecida: {p}")

    if not layers_to_process:
        print("Nenhuma layer selecionada!")
        sys.exit(1)

    # 5. Processar cada layer
    print(f"\n⚙️  FASE 3: Processamento de {len(layers_to_process)} layer(s)")
    version_info = {
        "lastUpdate": datetime.now(SP_TZ).isoformat(),
        "anoCorrente": ano_corrente,
        "camadas": existing_version.get("camadas", {}),
    }

    total_normas = 0
    layers_changed = 0
    has_error = False

    for name in layers_to_process:
        isis_records = layer_map.get(name, [])

        if not isis_records:
            # Layer vazia: remover do version se existia
            key = name.replace(".json", "")
            if key in version_info["camadas"]:
                del version_info["camadas"][key]
            continue

        changed, count, new_hash = process_layer(name, isis_records, existing_hashes)
        total_normas += count

        if new_hash:
            key = name.replace(".json", "")

            # Determinar período
            if name == "normas-atual.json":
                periodo = f"{ano_corrente}"
            else:
                for lname, start, end in LAYER_DECADAS:
                    if lname == name:
                        real_end = end if end is not None else (ano_corrente - 1)
                        periodo = f"{start}-{real_end}"
                        break

            version_info["camadas"][key] = {
                "arquivo": name,
                "anos": periodo,
                "normas": count,
                "hash": new_hash,
            }

            if changed:
                layers_changed += 1

    # 6. Salvar version.json (totalNormas soma de TODAS as camadas, não só as processadas)
    version_info["totalNormas"] = sum(
        info.get("normas", 0) for info in version_info["camadas"].values()
    )
    save_json("normas-version.json", version_info)

    # 7. Resumo
    print(f"\n🏁 Concluído!")
    print(f"   Total: {total_normas} normas em {len([n for n in layers_to_process if layer_map.get(n)])} layers")
    print(f"   Layers atualizadas: {layers_changed}")

    if has_error:
        print("   ⚠️ Houve erros durante o processamento.")
        sys.exit(1)


if __name__ == "__main__":
    main()
