import json
import os
import subprocess
import time
import requests
import unicodedata
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from zoneinfo import ZoneInfo

# --- CONFIGURAÇÃO ---
BASE_URL = "https://splegisconsulta.saopaulo.sp.leg.br/Pesquisa/PageDataProjeto"
MAX_RETRIES = 3
TIMEOUT_SECONDS = 180
ANO_INICIO_HISTORICO = 1991
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dados")
SP_TZ = ZoneInfo("America/Sao_Paulo")

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
        print(f"Erro ao ler {filename}: {e}")
        return None

def save_json(filename: str, data: Any):
    ensure_data_dir()
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
    print(f"💾 Arquivo salvo: {filename}")

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
            print(f"🔄 Buscando {ano_inicio}-{ano_fim} (Tentativa {attempt}/{MAX_RETRIES})...")
            response = session.get(url, params=params, timeout=TIMEOUT_SECONDS)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    filtered = data.get("recordsFiltered", 0)
                    items = data.get("data", [])
                    print(f"✅ Sucesso: {len(items)} projetos encontrados (Total: {filtered})")
                    return items
                except json.JSONDecodeError:
                    print(f"❌ Erro: Response not valid JSON. Headers: {dict(response.headers)}. Len: {len(response.content)}. Init: {response.text[:100]}")
            else:
                print(f"❌ Erro HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Exceção: {e}")
        
        if attempt < MAX_RETRIES:
            wait_time = 15 * (2 ** (attempt - 1))
            print(f"⏳ Aguardando {wait_time}s...")
            time.sleep(wait_time)
            
    print(f"🚨 Falha definitiva ao buscar {ano_inicio}-{ano_fim}")
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
        
        # 1. Include NORMA in searchable
        search_components = [
            tipo,
            tipo_extenso,
            numero,
            ano,
            norma, # ADDED
            ementa,
            keywords,
            promoventes,
            f"{numero}/{ano}" # ADDED: Identificador número/ano
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

def process_layer(ano_inicio: int, ano_fim: int, output_filename: str):
    print(f"\n🚀 Iniciando processamento de {output_filename} ({ano_inicio}-{ano_fim})")
    
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
        
        # VALIDATE BEFORE SAVING
        if validate_data(raw_projects, final_json):
            save_json(output_filename, final_json)
            return True, len(processed_data)
        else:
            print(f"❌ Validação falhou para {output_filename}. Arquivo não salvo.")
            return False, 0
            
    except Exception as e:
        print(f"❌ Falha crítica processando camada: {e}")
        return False, 0

# --- VALIDAÇÃO ---

def validate_data(original: List[Dict], processed: Dict) -> bool:
    print("🔍 Iniciando validação...")
    
    if "columns" not in processed or "data" not in processed: return False
    
    stats = {
        "sem_promoventes": 0,
        "sem_palavras": 0,
        "com_norma": 0,
        "searchable_chars_sum": 0,
        "tipos": {}
    }
    
    ano_corrente = datetime.now(SP_TZ).year
    
    for i, row in enumerate(processed["data"]):
        tipo, numero, ano, norma, ementa, promoventes, keywords, searchable = row
        
        if tipo not in ["PL", "PDL", "PR", "PLO"]: return False
        if not numero.isdigit(): return False
        if not (1991 <= int(ano) <= ano_corrente + 1): return False
        if norma and "/" not in norma: return False
        
        # Check empty keywords correctly
        if not keywords: return False 
        
        # Robust Mesa check
        if "Ver. " in promoventes:
            print(f"❌ FALHA: 'Ver.' encontrado em {promoventes}")
            return False
        if "MESA DA CAMARA" in promoventes.upper():
             print(f"❌ FALHA: Mesa não simplificada: {promoventes}")
             return False
             
        # Check searchable normalization
        if any(c in searchable for c in "áéíóúãõç_"): return False
        if "|" not in searchable: return False
        
        if not promoventes: stats["sem_promoventes"] += 1
        if keywords == "SEM_PALAVRAS": stats["sem_palavras"] += 1
        if norma: stats["com_norma"] += 1
        stats["searchable_chars_sum"] += len(searchable)
        stats["tipos"][tipo] = stats["tipos"].get(tipo, 0) + 1

    if len(original) != len(processed["data"]): return False
    
    print("✅ Validação OK")
    return True

# --- FLUXO PRINCIPAL ---

def main():
    ano_corrente = datetime.now(SP_TZ).year
    
    layer_atual = {"name": "atual.json", "start": ano_corrente, "end": ano_corrente}
    layer_recente = {"name": "recente.json", "start": ano_corrente - 5, "end": ano_corrente - 1}
    layer_medio = {"name": "medio.json", "start": ano_corrente - 15, "end": ano_corrente - 6}
    
    hist_inicio = ANO_INICIO_HISTORICO
    hist_fim = ano_corrente - 16
    hist_meio = hist_inicio + (hist_fim - hist_inicio + 1) // 2 # Integer division
    
    layer_hist_a = {"name": "historico-a.json", "start": hist_meio, "end": hist_fim}
    layer_hist_b = {"name": "historico-b.json", "start": hist_inicio, "end": hist_meio - 1}
    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--layer', type=str, default='all')
    args = parser.parse_args()
    
    layers_map = {
        "atual": [layer_atual],
        "recente": [layer_recente],
        "medio": [layer_medio],
        "historico-a": [layer_hist_a],
        "historico-b": [layer_hist_b],
        "all": [layer_atual, layer_recente, layer_medio, layer_hist_a, layer_hist_b]
    }
    
    selected_layers = layers_map.get(args.layer, [])
    
    version_info = {
        "lastUpdate": datetime.now(SP_TZ).isoformat(),
        "anoCorrente": ano_corrente,
        "camadas": {}
    }
    
    existing_version = load_json("version.json")
    if existing_version:
        version_info["camadas"] = existing_version.get("camadas", {})
        
    for layer in selected_layers:
        success, count = process_layer(layer["start"], layer["end"], layer["name"])
        if success:
            key = layer["name"].replace(".json", "")
            version_info["camadas"][key] = {
                "arquivo": f"dados/{layer['name']}",
                "anos": f"{layer['start']}-{layer['end']}",
                "projetos": count,
                "descricao": f"Camada {key} ({layer['start']} a {layer['end']})"
            }
            if layer != selected_layers[-1]:
                time.sleep(15)
    
    save_json("version.json", version_info)
    print("\n🏁 Processamento concluído.")
    
    # Auto-commit logic
    auto_git_commit()

GIT_COMMIT_MSG = "Atualização automática de dados"

def run_git_cmd(args):
    """Executa comando git e retorna (success, stdout)."""
    try:
        result = subprocess.run(
            ["git"] + args, 
            capture_output=True, 
            text=True, 
            encoding='utf-8',
            check=False
        )
        return result.returncode == 0, result.stdout.strip()
    except FileNotFoundError:
        return False, "Git not found"

def auto_git_commit():
    """Realiza commit ou amend se o último commit for de atualização."""
    print("\n📦 Verificando Git...")
    
    # 1. Check status
    changed, _ = run_git_cmd(["status", "--porcelain"])
    if not changed:
        print("   Nada para commitar.")
        return

    # 2. Add files
    print("   Adicionando arquivos...")
    run_git_cmd(["add", "dados/*.json", "version.json"])
    
    # 3. Check last commit message
    success, last_msg = run_git_cmd(["log", "-1", "--pretty=%B"])
    
    if success and last_msg.startswith(GIT_COMMIT_MSG):
        print("   🔄 Último commit é atualização automática. Fazendo AMEND...")
        success, out = run_git_cmd(["commit", "--amend", "--no-edit"])
    else:
        print("   🆕 Criando NOVO commit de atualização...")
        success, out = run_git_cmd(["commit", "-m", GIT_COMMIT_MSG])
        
    if success:
        print("   ✅ Commit realizado com sucesso.")
    else:
        print(f"   ❌ Falha no commit: {out}")

if __name__ == "__main__":
    main()
