import json
import os
import sys
import time
import hashlib
import argparse
import requests
import unicodedata
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from zoneinfo import ZoneInfo

# --- CONFIGURAÇÃO ---
BASE_URL = "https://splegisconsulta.saopaulo.sp.leg.br/Pesquisa/PageDataProjeto"
MAX_RETRIES = 3
TIMEOUT_SECONDS = 180
ANO_INICIO = 1991
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dados", "projetos")
SP_TZ = ZoneInfo("America/Sao_Paulo")

# Tamanho de cada quinquênio (5 anos)
QUINQUENIO = 5

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
    """
    Normaliza string para o campo searchable:
    1. Lowercase
    2. Remove acentos (NFD)
    3. Remove pontos de milhar em números
    4. Substitui underscore por espaço (SEM_PALAVRAS -> sem palavras)
    5. Remove pontuação restante (mantendo letras, números, espaços e pipe)
    6. Normaliza espaços
    """
    if not text:
        return ""

    # 1. Lowercase
    text = text.lower()

    # 2. Remover acentos (NFD)
    text = unicodedata.normalize('NFD', text).encode('ASCII', 'ignore').decode('utf-8')

    # 3. Remover pontos de milhar (pontos entre dígitos)
    text = re.sub(r'(?<=\d)\.(?=\d)', '', text)

    # 4. Substituir underscore por espaço
    text = text.replace('_', ' ')

    # 5. Remover pontuação restante (mantendo pipe, barra, hífen e parênteses)
    text = re.sub(r'[^a-z0-9\s|/\-\(\)]', '', text)

    # 6. Normalizar espaços
    text = re.sub(r'\s+', ' ', text).strip()

    return text

def normalize_searchable(components: List[str]) -> str:
    """
    Constrói o campo searchable final:
    1. Concatena com " | "
    2. Normaliza tudo
    3. Garante pipes sem espaços nas barreiras
    """

    # 1. Concatenar COM espaços (para evitar aglutinação na normalização)
    raw_text = " | ".join([c if c else "" for c in components])

    # 2. Normaliza
    normalized = normalize_string(raw_text)

    # 3. Garantir espaços ao redor de pipes
    # Ex: "pl | projeto" -> " pl | projeto | "
    # Primeiro substitui pipes por " | "
    final_text = re.sub(r'\s*\|\s*', ' | ', normalized)

    # 4. Adicionar espaços no início e fim
    final_text = f" {final_text} "

    return final_text

# --- EXTRAÇÃO E TRANSFORMAÇÃO ---

def fetch_projects(ano_inicio: int, ano_fim: int) -> List[Dict]:
    """
    Busca projetos na API com paginação implícita e retries.
    """
    params = {
        "anoInicio": ano_inicio,
        "anoFim": ano_fim,
        "length": 0,
        "tipo": 0,
        "start": 0,
        "draw": 1
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": "https://splegisconsulta.saopaulo.sp.leg.br/Pesquisa/IndexProjeto",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://splegisconsulta.saopaulo.sp.leg.br"
    }

    session = requests.Session()
    session.headers.update(headers)

    try:
        session.get("https://splegisconsulta.saopaulo.sp.leg.br/Pesquisa/IndexProjeto", timeout=30)
    except:
        pass

    url = BASE_URL

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"  🔄 Buscando {ano_inicio}-{ano_fim} (Tentativa {attempt}/{MAX_RETRIES})...")
            response = session.get(url, params=params, timeout=TIMEOUT_SECONDS)

            if response.status_code == 200:
                try:
                    data = response.json()
                    filtered = data.get("recordsFiltered", 0)
                    items = data.get("data", [])
                    print(f"  ✅ {len(items)} projetos (Total: {filtered})")
                    return items
                except json.JSONDecodeError:
                    print(f"  ❌ Erro: Response not valid JSON. Headers: {dict(response.headers)}. Len: {len(response.content)}. Init: {response.text[:100]}")
            else:
                print(f"  ❌ Erro HTTP {response.status_code}")

        except Exception as e:
            print(f"  ❌ Exceção: {e}")

        if attempt < MAX_RETRIES:
            wait_time = 15 * (2 ** (attempt - 1))
            print(f"  ⏳ Aguardando {wait_time}s...")
            time.sleep(wait_time)

    print(f"  🚨 Falha definitiva ao buscar {ano_inicio}-{ano_fim}")
    raise Exception(f"Falha ao buscar dados de {ano_inicio}-{ano_fim}")

def transform_norma(norma: Dict) -> str:
    """Input: {'numero': 18349, 'ano': 2025} -> Output: '18349/2025'"""
    if norma and norma.get("numero"):
        return f"{norma['numero']}/{norma['ano']}"
    return ""

def transform_promoventes(promoventes: List[Dict]) -> str:
    """Output: 'ELISEU | Mesa Diretora'"""
    result = []
    if not promoventes:
        return ""

    for p in promoventes:
        texto = p.get("texto", "").strip()

        # Regra Mesa Diretora
        if texto.upper().startswith("MESA"):
            result.append("Mesa Diretora")
            continue

        # Regra Vereador
        if texto.startswith("Ver. "):
            texto = texto.replace("Ver. ", "")

        result.append(texto)

    return " | ".join(result)

def transform_assuntos(assuntos: List[Dict]) -> str:
    """Output: 'A | B' or 'SEM_PALAVRAS'"""
    if not assuntos:
        return "SEM_PALAVRAS"

    palavras = [a.get("texto", "").strip() for a in assuntos]
    return " | ".join(palavras)

def transform_project(proj: Dict) -> List[str]:
    try:
        tipo = proj.get("sigla", "")
        numero = str(proj.get("numero", ""))
        ano = str(proj.get("ano", ""))
        ementa = proj.get("ementa", "")

        norma = transform_norma(proj.get("norma"))
        promoventes = transform_promoventes(proj.get("promoventes"))
        keywords = transform_assuntos(proj.get("assuntos"))

        tipo_map = {
            "PL": "Projeto de Lei",
            "PDL": "Projeto de Decreto Legislativo",
            "PR": "Projeto de Resolução",
            "PLO": "Projeto de Lei Orgânica"
        }
        tipo_extenso = tipo_map.get(tipo, "")

        search_components = [
            tipo,
            tipo_extenso,
            numero,
            ano,
            norma,
            ementa,
            keywords,
            promoventes,
            f"{numero}/{ano}"
        ]
        searchable = normalize_searchable(search_components)

        return [
            tipo,
            numero,
            ano,
            norma,
            ementa,
            promoventes,
            keywords,
            searchable
        ]
    except Exception as e:
        print(f"Erro ao transformar projeto {proj.get('codigo')}: {e}")
        return None

# --- PROCESSAMENTO ---

def process_layer(ano_inicio: int, ano_fim: int, output_filename: str,
                  existing_hashes: Dict[str, str]) -> Tuple[bool, int, Optional[str]]:
    """
    Busca, transforma e salva uma layer, verificando hash para evitar gravações desnecessárias.
    Retorna (success, count, new_hash).
    """
    print(f"\n  📦 {output_filename} ({ano_inicio}-{ano_fim})")

    try:
        raw_projects = fetch_projects(ano_inicio, ano_fim)
        raw_projects.sort(key=lambda x: x.get("codigo", 0), reverse=True)

        processed_data = []
        for proj in raw_projects:
            row = transform_project(proj)
            if row:
                processed_data.append(row)

        final_json = {
            "columns": ["tipo", "numero", "ano", "norma", "ementa", "promoventes", "palavras-chave", "searchable"],
            "data": processed_data
        }

        # Hash check
        new_hash = content_hash(final_json)
        old_hash = existing_hashes.get(output_filename)

        if new_hash == old_hash:
            print(f"  ⏭️  sem mudanças ({len(processed_data)} projetos, hash={new_hash[:12]}...)")
            return True, len(processed_data), new_hash

        # Validar antes de salvar
        if validate_data(raw_projects, final_json):
            save_json(output_filename, final_json)
            print(f"     → {len(processed_data)} projetos, hash={new_hash[:12]}...")
            return True, len(processed_data), new_hash
        else:
            print(f"  ❌ Validação falhou para {output_filename}. Arquivo não salvo.")
            return False, 0, None

    except Exception as e:
        print(f"  ❌ Falha crítica processando camada: {e}")
        return False, 0, None

# --- VALIDAÇÃO ---

def validate_data(original: List[Dict], processed: Dict) -> bool:
    print("  🔍 Validando...")

    if "columns" not in processed or "data" not in processed: return False

    ano_corrente = datetime.now(SP_TZ).year

    for i, row in enumerate(processed["data"]):
        tipo, numero, ano, norma, ementa, promoventes, keywords, searchable = row

        if tipo not in ["PL", "PDL", "PR", "PLO"]: return False
        if not numero.isdigit(): return False
        if not (ANO_INICIO <= int(ano) <= ano_corrente + 1): return False
        if norma and "/" not in norma: return False

        if not keywords: return False

        if "Ver. " in promoventes:
            print(f"  ❌ FALHA: 'Ver.' encontrado em {promoventes}")
            return False
        if "MESA DA CAMARA" in promoventes.upper():
             print(f"  ❌ FALHA: Mesa não simplificada: {promoventes}")
             return False

        if any(c in searchable for c in "áéíóúãõç_"): return False
        if "|" not in searchable: return False

    if len(original) != len(processed["data"]): return False

    print("  ✅ Validação OK")
    return True

# --- DEFINIÇÃO DE LAYERS ---

def build_layers(ano_corrente: int) -> List[Dict]:
    """
    Constrói a lista de layers a processar.
    - Layer "atual": ano corrente
    - Layer do quinquênio corrente (dinâmica): do início do quinquênio até ano_corrente-1
    - Layers completas de quinquênios passados (geradas dinamicamente)

    Quinquênios: 1991-1995, 1996-2000, 2001-2005, ..., 2026-2030, ...
    """
    layers = []

    # 1. Layer atual (ano corrente)
    layers.append({
        "name": "projetos-atual.json",
        "start": ano_corrente,
        "end": ano_corrente,
        "key": "projetos-atual",
    })

    # 2. Gerar todos os quinquênios de ANO_INICIO até ano_corrente-1
    # Início do quinquênio do ano corrente
    quinq_corrente_start = ((ano_corrente - ANO_INICIO) // QUINQUENIO) * QUINQUENIO + ANO_INICIO

    # Layer do quinquênio corrente (parcial: de quinq_start até ano_corrente-1)
    quinq_end = ano_corrente - 1
    if quinq_end >= quinq_corrente_start:
        if quinq_corrente_start == quinq_end:
            name = f"projetos-{quinq_corrente_start}.json"
        else:
            name = f"projetos-{quinq_corrente_start}-{quinq_end}.json"

        layers.append({
            "name": name,
            "start": quinq_corrente_start,
            "end": quinq_end,
            "key": name.replace(".json", ""),
        })

    # 3. Layers de quinquênios completos (passados)
    q_start = ANO_INICIO
    while q_start + QUINQUENIO - 1 < quinq_corrente_start:
        q_end = q_start + QUINQUENIO - 1
        name = f"projetos-{q_start}-{q_end}.json"
        layers.append({
            "name": name,
            "start": q_start,
            "end": q_end,
            "key": name.replace(".json", ""),
        })
        q_start += QUINQUENIO

    return layers

# --- FLUXO PRINCIPAL ---

def main():
    sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description="Atualiza base de projetos legislativos de São Paulo")
    parser.add_argument('--layer', type=str, default='all',
                        help='Layers a processar: all, atual, ou nomes separados por vírgula')
    args = parser.parse_args()

    ano_corrente = datetime.now(SP_TZ).year
    all_layers = build_layers(ano_corrente)

    print(f"📋 Atualização de Projetos Legislativos — {datetime.now(SP_TZ).strftime('%d/%m/%Y %H:%M')}")
    print(f"   Ano corrente: {ano_corrente}")
    print(f"   Layers disponíveis: {len(all_layers)}")
    for l in all_layers:
        print(f"     {l['name']} ({l['start']}-{l['end']})")
    print()

    # Determinar quais layers processar
    requested = args.layer.strip()
    if requested == 'all':
        selected_layers = all_layers
    else:
        parts = [p.strip() for p in requested.split(',')]
        selected_layers = []
        layer_by_key = {l["key"]: l for l in all_layers}
        # Também mapear por "atual" como alias
        layer_by_alias = {"atual": "projetos-atual"}

        for p in parts:
            key = layer_by_alias.get(p, p)
            # Tentar match direto
            if key in layer_by_key:
                selected_layers.append(layer_by_key[key])
            else:
                # Tentar como prefixo: "projetos-2021-2025" ou "2021-2025" ou "2021"
                candidate = f"projetos-{p}" if not p.startswith("projetos-") else p
                if candidate in layer_by_key:
                    selected_layers.append(layer_by_key[candidate])
                else:
                    # Buscar por match parcial
                    found = False
                    for l in all_layers:
                        if p in l["key"] or p in l["name"]:
                            selected_layers.append(l)
                            found = True
                            break
                    if not found:
                        print(f"  ⚠️ Layer desconhecida: {p}")

    if not selected_layers:
        print("Nenhuma layer selecionada!")
        sys.exit(1)

    # Carregar version.json existente e extrair hashes
    existing_version = load_json("version.json") or {}
    existing_hashes = {}
    for key, info in existing_version.get("camadas", {}).items():
        if "hash" in info:
            existing_hashes[info.get("arquivo", "").replace("dados/projetos/", "")] = info["hash"]

    # Processar layers
    print(f"⚙️  Processando {len(selected_layers)} layer(s)")

    version_info = {
        "lastUpdate": datetime.now(SP_TZ).isoformat(),
        "anoCorrente": ano_corrente,
        "camadas": existing_version.get("camadas", {}),
    }

    has_error = False
    layers_changed = 0

    for i, layer in enumerate(selected_layers):
        success, count, new_hash = process_layer(
            layer["start"], layer["end"], layer["name"], existing_hashes
        )

        if success and new_hash:
            version_info["camadas"][layer["key"]] = {
                "arquivo": f"dados/projetos/{layer['name']}",
                "anos": f"{layer['start']}-{layer['end']}" if layer['start'] != layer['end'] else str(layer['start']),
                "projetos": count,
                "hash": new_hash,
            }
            # Detectar se houve mudança real
            if existing_hashes.get(layer["name"]) != new_hash:
                layers_changed += 1
        elif not success:
            has_error = True
            print(f"  ⚠️ Erro ao processar: {layer['name']}")

        if i < len(selected_layers) - 1:
            time.sleep(15)

    # Remover layers antigas que não existem mais na nova estrutura
    valid_keys = {l["key"] for l in all_layers}
    old_keys = [k for k in version_info["camadas"] if k not in valid_keys]
    for k in old_keys:
        del version_info["camadas"][k]

    # Ordenar camadas por ano DESC (mais recente primeiro) para manter cronologia
    camadas_ordenadas = dict(sorted(
        version_info["camadas"].items(),
        key=lambda item: int(item[1]["anos"].split("-")[-1]),
        reverse=True
    ))
    version_info["camadas"] = camadas_ordenadas

    # Calcular total
    version_info["totalProjetos"] = sum(
        info.get("projetos", 0) for info in version_info["camadas"].values()
    )

    save_json("version.json", version_info)

    # Resumo
    total = version_info["totalProjetos"]
    print(f"\n🏁 Concluído!")
    print(f"   Total: {total} projetos em {len(version_info['camadas'])} layers")
    print(f"   Layers atualizadas: {layers_changed}")

    if has_error:
        print("   ⚠️ Houve erros durante o processamento.")
        sys.exit(1)

if __name__ == "__main__":
    main()
