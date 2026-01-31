# Especificação Técnica: Conversão de Dados SPLegis

**Versão:** 1.0  
**Data:** 28 de Janeiro de 2026  
**Sistema:** Atualização Automática de Base Legislativa - CMSP

---

## 1. Objetivo

Transformar dados da API SPLegis em estrutura otimizada para busca no frontend, com:
- Ordenação cronológica real (por data de protocolo)
- Campos concatenados e normalizados
- Validação completa de integridade
- Atualização automatizada em camadas

---

## 2. Fonte de Dados

### 2.1 Endpoint API
```
URL: https://splegisconsulta.saopaulo.sp.leg.br/Pesquisa/PageDataProjeto
Método: GET
Formato: JSON
```

### 2.2 Parâmetros Principais
```
anoInicio: Ano inicial do filtro
anoFim: Ano final do filtro
length: 0 (retorna todos os registros sem paginação)
tipo: 0 (todos os tipos)
```

### 2.3 Capacidade Testada
- Até cerca de 10 anos de dados por requisição (~11.000 projetos)
- Blocos maiores resultam em timeout (504)

---

## 3. Estrutura de Dados


### 3.1 Input (API Response)

#### Estrutura Completa

```json
{
  "draw": 12,
  "recordsTotal": 32423,
  "recordsFiltered": 1853,
  "data": [
    {
      "codigo": 784197,
      "natodigital": true,
      "tipo": 1,
      "numero": 31,
      "ano": 2026,
      "sigla": "PL",
      "texto": "PL 31/2026",
      "ementa": "Regulamenta, no âmbito do Município de São Paulo, o disposto no art. 59-A do Estatuto da Criança e do Adolescente – ECA, incluído pela Lei Federal nº 14.811, de 12 de janeiro de 2024, e estabelece procedimentos institucionais relativos à exigência de Certidão de Antecedentes Criminais.",
      "norma": {
        "numero": null,
        "ano": 0
      },
      "promoventes": [
        {
          "codigo": 1487,
          "texto": "Ver. ELISEU GABRIEL (PSB)"
        }
      ],
      "assuntos": [
        {
          "codigo": 63,
          "texto": "ADOLESCENTE"
        },
        {
          "codigo": 61,
          "texto": "ADMISSAO"
        },
        {
          "codigo": 14477,
          "texto": "ANTECEDENTES"
        }
      ],
      "dT_RowId": 784197
    }
  ]
}
```

#### Campos da Raiz

| Campo | Tipo | Descrição | Uso |
|-------|------|-----------|-----|
| `draw` | number | Contador de requisições (DataTables) | ❌ Ignorado |
| `recordsTotal` | number | Total de projetos no sistema | ℹ️ Informativo |
| `recordsFiltered` | number | Total de projetos no filtro atual | ℹ️ Informativo |
| `data` | array | Array com os projetos | ✅ **Processado** |

#### Campos de Cada Projeto

| Campo | Tipo | Exemplo | Uso | Observação |
|-------|------|---------|-----|------------|
| `codigo` | number | 784197 | ✅ **Ordenação** | ID único, usado para ordenar cronologicamente |
| `natodigital` | boolean | true | ❌ Ignorado | Indica se projeto nasceu digital |
| `tipo` | number | 1 | ❌ Ignorado | Tipo numérico (usamos `sigla`) |
| `numero` | number | 31 | ✅ **Coluna** | Número do projeto |
| `ano` | number | 2026 | ✅ **Coluna** | Ano do projeto |
| `sigla` | string | "PL" | ✅ **Coluna** | Tipo: PL, PDL, PR, PLO |
| `texto` | string | "PL 31/2026" | ❌ Ignorado | Texto formatado do projeto |
| `ementa` | string | "Regulamenta..." | ✅ **Coluna** | Descrição completa |
| `norma` | object | {...} | ✅ **Coluna** | Lei resultante (quando aprovado) |
| `promoventes` | array | [{...}] | ✅ **Coluna** | Autores/proponentes |
| `assuntos` | array | [{...}] | ✅ **Coluna** | Palavras-chave/descritores |
| `dT_RowId` | number | 784197 | ❌ Ignorado | ID interno DataTables |

#### Estrutura do Campo `norma`

```json
{
  "numero": null,  // number | null
  "ano": 0         // number (0 quando null)
}
```

**Exemplos:**
```json
// Projeto em tramitação
{"numero": null, "ano": 0}

// Projeto aprovado (virou lei)
{"numero": 18349, "ano": 2025}
```

#### Estrutura do Campo `promoventes`

```json
[
  {
    "codigo": 1487,               // number - ID do promovente
    "texto": "Ver. ELISEU GABRIEL (PSB)"  // string - Nome completo
  }
]
```

**Tipos observados:**
- Vereadores: `"Ver. NOME (PARTIDO)"` (~95% dos casos)
- Comissões: `"Comissão de..."`
- Executivo: `"Executivo - NOME"`
- Mesa: `"MESA DA CAMARA MUNICIPAL..."`
- Tribunal: `"TRIBUNAL DE CONTAS DO MUNICIPIO"`

**Observações:**
- Array pode ser vazio `[]`
- Maioria tem 1 promovente
- Alguns têm vários promoventes (coautoria)
- Campo `codigo` é ignorado, apenas `texto` é usado

#### Estrutura do Campo `assuntos`

```json
[
  {
    "codigo": 63,           // number - ID do assunto
    "texto": "ADOLESCENTE"  // string - Palavra-chave
  },
  {
    "codigo": 61,
    "texto": "ADMISSAO"
  }
]
```

**Características:**
- Média: 33 palavras-chave por projeto
- É possível que um projeto tenha centenas de palavras-chave
- Campo `codigo` é ignorado, apenas `texto` é usado
- Array pode estar vazio `[]` (raro)
- Palavras geralmente em MAIÚSCULAS

---

**Campos utilizados no processamento:**
- ✅ `data` (raiz)
- ✅ `codigo` (ordenação)
- ✅ `sigla` → tipo
- ✅ `numero` → numero
- ✅ `ano` → ano
- ✅ `norma` → norma
- ✅ `ementa` → ementa
- ✅ `promoventes[].texto` → promoventes
- ✅ `assuntos[].texto` → palavras-chave

**Campos ignorados:**
- ❌ `draw`, `recordsTotal`, `recordsFiltered` (metadados da API)
- ❌ `natodigital`, `tipo`, `texto`, `dT_RowId` (dados redundantes ou não necessários)
- ❌ `promoventes[].codigo`, `assuntos[].codigo` (IDs não utilizados)



---

### 3.2 Output (Dados Processados)

```json
{
  "columns": [
    "tipo",
    "numero",
    "ano",
    "norma",
    "ementa",
    "promoventes",
    "palavras-chave",
    "searchable"
  ],
  "data": [
    [
      "PL",
      "31",
      "2026",
      "",
      "Regulamenta, no âmbito do Município...",
      "ELISEU GABRIEL (PSB)",
      "ADOLESCENTE | ADMISSAO",
      "pl|projeto de lei|31|2026||regulamenta ambito municipio...|adolescente|admissao|eliseu gabriel psb"
    ]
  ]
}
```

**Estrutura:**
- Formato: Arrays de arrays (otimizado para tamanho)
- 8 colunas fixas por projeto
- Ordem das colunas é imutável
- Todos os valores são strings

---

## 4. Comportamentos Obrigatórios

### 4.1 Extração de Campos Básicos

**Mapeamento direto:**
- `tipo` ← `sigla` da API
- `numero` ← `numero` da API (converter para string)
- `ano` ← `ano` da API (converter para string)
- `ementa` ← `ementa` da API (preservar texto original sem modificações)

**Não aplicar transformações em:**
- Ementa: manter caracteres especiais, pontuação, quebras de linha, tudo. Não aplicar transformações no campo final ementa (a normalização ocorre apenas no searchable).

---

### 4.2 Campo NORMA

**Regra de formatação:**
- Se `norma.numero` é `null` → string vazia `""`
- Se `norma.numero` tem valor → formato `"numero/ano"`

**Exemplos:**
```
Input:  {"numero": null, "ano": 0}
Output: ""

Input:  {"numero": 18349, "ano": 2025}
Output: "18349/2025"

Input:  {"numero": 18380, "ano": 2026}
Output: "18380/2026"
```

**Estatística esperada:**
- ~8-10% dos projetos têm norma preenchida
- Projetos recentes raramente têm norma (ainda em tramitação)

---

### 4.3 Campo PROMOVENTES

**Transformações obrigatórias:**

1. **Limpeza de vereadores:** Remover prefixo `"Ver. "` quando presente
2. **Simplificação da Mesa:** Transformar qualquer texto que comece com `"MESA"` em `"Mesa Diretora"`
3. **Preservar outros tipos:** Manter texto original para:
   - Executivo: `"Executivo - NOME"`
   - Comissões: `"Comissão de..."`
   - Tribunal: `"TRIBUNAL DE CONTAS..."`
4. **Concatenação:** Unir múltiplos promoventes com `" | "` (pipe com espaços)

**Exemplos:**

```
Input:  [{"texto": "Ver. ELISEU GABRIEL (PSB)"}]
Output: "ELISEU GABRIEL (PSB)"

Input:  [{"texto": "Ver. DR. MURILLO LIMA (PP)"}, {"texto": "Ver. RICARDO TEIXEIRA (UNIÃO)"}]
Output: "DR. MURILLO LIMA (PP) | RICARDO TEIXEIRA (UNIÃO)"

Input:  [{"texto": "Executivo - RICARDO NUNES"}]
Output: "Executivo - RICARDO NUNES"

Input:  [{"texto": "MESA DA CAMARA MUNICIPAL DE SAO PAULO - 01/01/2025 a 31/12/2025"}]
Output: "Mesa Diretora"

Input:  [{"texto": "Comissão de Trânsito, Transporte e Atividade Econômica"}]
Output: "Comissão de Trânsito, Transporte e Atividade Econômica"

Input:  [{"texto": "TRIBUNAL DE CONTAS DO MUNICIPIO"}]
Output: "TRIBUNAL DE CONTAS DO MUNICIPIO"

Input:  []
Output: ""
```

**Regra de detecção da Mesa:**
- Se o texto começa com `"MESA"` (case-insensitive)
- Substituir o texto completo por `"Mesa Diretora"`
- Motivo: O período (ex: "01/01/2025 a 31/12/2025") é redundante, pois o ano do projeto já indica o período

**Tipos de promoventes observados:**
- Vereadores: maioria (~95%)
- Mesa Diretora: ocasional (~1-2%)
- Comissões: raro
- Executivo: ocasional
- Tribunal: muito raro

---

## 4.4 Campo PALAVRAS-CHAVE

**Transformações obrigatórias:**

1. **Extrair textos:** Pegar apenas campo `texto` de cada assunto, ignorar `codigo`
2. **Concatenar:** Unir com `" | "` (pipe com espaços)
3. **Preservar ordem:** Manter sequência da API
4. **NÃO truncar:** Incluir TODAS as palavras-chave, mesmo que sejam centenas
5. **Projeto sem palavras-chave:** Se array vazio `[]`, usar `"SEM_PALAVRAS"`

**Exemplos:**

```
Input:  [{"codigo": 63, "texto": "ADOLESCENTE"}, {"codigo": 61, "texto": "ADMISSAO"}]
Output: "ADOLESCENTE | ADMISSAO"

Input:  []
Output: "SEM_PALAVRAS"

Input:  [44 palavras-chave]
Output: "PALAVRA1 | PALAVRA2 | ... | PALAVRA44" (todas incluídas)
```

**Estatísticas esperadas:**
- Média: 33 palavras-chave por projeto
- Projetos sem palavras-chave: 0-5% (receberão `"SEM_PALAVRAS"`)

---

## 4.5 Campo SEARCHABLE

**Objetivo:** Campo normalizado para busca full-text no frontend.

**Composição (nesta ordem):**
1. Sigla do tipo (ex: "PL")
2. Tipo por extenso (ex: "Projeto de Lei")
3. Número do projeto
4. Ano do projeto
5. Norma (se existir)
6. Ementa completa
7. Palavras-chave concatenadas (ou "SEM_PALAVRAS")
8. Promoventes concatenados

**Separação entre campos:**
- Usar `|` (pipe SEM espaços) para separar cada campo
- **Importante:** Cria uma barreira física entre campos para evitar falsos positivos
- Exemplo de problema evitado: Busca "trabalhador paulistano" encontrando "João Trabalhador" (Promovente) + "Paulistano" (Palavra-chave)
- Solução: "joao trabalhador|paulistano" (Barreira impede match de frase exata cruzando campos)

**Mapeamento de tipos por extenso:**
```
PL  → "Projeto de Lei"
PDL → "Projeto de Decreto Legislativo"
PR  → "Projeto de Resolução"
PLO → "Projeto de Lei Orgânica"
```

**Normalização aplicada (nesta ordem):**
1. **Lowercase:** Converter tudo para minúsculas
2. **Remover acentos:** ã→a, é→e, í→i, ó→o, ú→u, ç→c, etc.
3. **Remover pontos de milhar:** Remover pontos que estejam entre dígitos (ex: "14.811" → "14811")
4. **Remover pontuação restante:** Eliminar restantes caracteres especiais, mantendo apenas letras, números, espaços e o caractere pipe `|`
5. **Normalizar espaços:** Converter múltiplos espaços em espaço único

**Exemplos de normalização:**

```
"Lei 14.811" → "lei 14811"
"José Américo" → "jose americo"
"São Paulo" → "sao paulo"
"Criança/Adolescente" → "crianca adolescente"
"Art. 59-A" → "art 59 a"
"(ECA)" → "eca"
"SEM_PALAVRAS" → "sem palavras"
```

**Exemplo completo com palavras-chave:**

```
Input (campos separados):
  tipo: "PL"
  numero: "31"
  ano: "2026"
  norma: ""
  ementa: "Regulamenta o art. 59-A do ECA..."
  palavras-chave: "ADOLESCENTE | ADMISSAO"
  promoventes: "ELISEU GABRIEL (PSB)"

Concatenação bruta:
  "PL|Projeto de Lei|31|2026||Regulamenta o art. 59-A do ECA...|ADOLESCENTE | ADMISSAO|ELISEU GABRIEL (PSB)"

Após normalização:
  "pl|projeto de lei|31|2026||regulamenta o art 59 a do eca...|adolescente | admissao|eliseu gabriel psb"
```

**Exemplo completo sem palavras-chave:**

```
Input (campos separados):
  tipo: "PL"
  numero: "25"
  ano: "2026"
  norma: ""
  ementa: "Autoriza o Poder Executivo..."
  palavras-chave: "SEM_PALAVRAS"
  promoventes: "JOÃO SILVA (PT)"

Concatenação bruta:
  "PL|Projeto de Lei|25|2026||Autoriza o Poder Executivo...|SEM_PALAVRAS|JOÃO SILVA (PT)"

Após normalização:
  "pl|projeto de lei|25|2026||autoriza poder executivo...|sem palavras|joao silva pt"
```


---

### 4.6 Ordenação

**Critério:** Campo `codigo` da API em ordem DECRESCENTE.

**Motivo:** O código representa a ordem cronológica real de protocolo dos projetos, não o número/tipo. O campo codigo é estritamente crescente ao longo do tempo.

**Comportamento esperado:**
- Projetos mais recentes aparecem primeiro
- Um PR 2/2026 protocolado depois de PL 31/2026 aparece ANTES
- Ordem reflete data de entrada no sistema, não numeração arbitrária

**Implementação:**
- O campo `codigo` deve ser usado durante o processamento para ordenação
- O código NÃO deve aparecer na estrutura final (8 colunas apenas)
- Ordenar ANTES de remover o código

**Exemplo:**
```
API retorna (ordenado por número):
  PL 31/2026 (codigo: 784197)
  PL 30/2026 (codigo: 784196)
  PR 2/2026  (codigo: 784202) ← protocolado depois

Após ordenar por codigo DESC:
  PR 2/2026  (codigo: 784202) ← primeiro
  PL 31/2026 (codigo: 784197)
  PL 30/2026 (codigo: 784196)

JSON final (sem codigo):
  ["PR", "2", "2026", ...]
  ["PL", "31", "2026", ...]
  ["PL", "30", "2026", ...]
```

---

## 5. Validação Completa

O script deve executar validação em 5 níveis após processar os dados, ANTES de salvar o arquivo.

### 5.1 Nível 1: Validação de Estrutura (CRÍTICO)

**Objetivo:** Garantir que JSON tem estrutura mínima esperada.

**Verificações:**
- Campo `columns` existe
- Campo `data` existe
- `columns` tem exatamente 8 elementos
- `data` é um array não vazio

**Ação em falha:** ABORTAR execução, não salvar arquivo.

---

### 5.2 Nível 2: Validação de Schema (CRÍTICO)

**Objetivo:** Garantir que cada projeto tem formato correto.

**Verificações:**
- Cada elemento de `data` é um array
- Cada array tem exatamente 8 elementos
- Todos os elementos são strings
- `columns` contém exatamente: `["tipo", "numero", "ano", "norma", "ementa", "promoventes", "palavras-chave", "searchable"]`

**Ação em falha:** ABORTAR execução, não salvar arquivo.

---


## 5.3 Nível 3: Validação de Integridade (CRÍTICO)

**Objetivo:** Garantir que dados processados seguem regras de negócio.

**Verificações obrigatórias:**

1. **Campo TIPO:**
   - Valor está em: `["PL", "PDL", "PR", "PLO"]`

2. **Campo NUMERO:**
   - É numérico
   - Maior que zero

3. **Campo ANO:**
   - É numérico
   - Entre 1991 e (ANO_CORRENTE + 1) 

4. **Campo NORMA:**
   - Se preenchida, contém "/"
   - Formato: "numero/ano"

5. **Campo EMENTA:**
   - Não está vazia (trim)

6. **Campo PALAVRAS-CHAVE:**
   - Não pode ser string vazia `""`
   - Se projeto não tem palavras-chave, deve ser exatamente `"SEM_PALAVRAS"`
   - Se tem palavras, deve conter pelo menos um " | " OU ser palavra única válida

7. **Campo PROMOVENTES:**
   - NÃO contém "Ver. " (deve ter sido removido)
   - NÃO contém "MESA DA CAMARA" ou datas tipo "01/01/2025" (deve ter sido simplificado para "Mesa Diretora")

8. **Campo SEARCHABLE:**
   - Não está vazio
   - Está em lowercase
   - Não contém acentos (amostragem: á, é, í, ó, ú, ã, õ, ç)
   - Não contém underscore "_" (SEM_PALAVRAS deve virar "sem palavras")
   - Contém o caractere `|` separando os campos

**Diferenciação:**
- **Erros:** Violam regras obrigatórias → ABORTAR
- **Avisos:** Situações suspeitas mas válidas → REGISTRAR e continuar

**Exemplos de validação:**

```python
# ERRO: palavras-chave vazia
palavras_chave = ""  
# Deveria ser "SEM_PALAVRAS"

# OK: projeto sem palavras-chave
palavras_chave = "SEM_PALAVRAS"

# OK: projeto com uma palavra
palavras_chave = "EDUCACAO"

# OK: projeto com múltiplas palavras
palavras_chave = "EDUCACAO | ENSINO | ESCOLA"

# ERRO: ainda tem "Ver."
promoventes = "Ver. FULANO (PT)"
# Deveria ser "FULANO (PT)"

# ERRO: Mesa não foi simplificada
promoventes = "MESA DA CAMARA MUNICIPAL DE SAO PAULO - 01/01/2025 a 31/12/2025"
# Deveria ser "Mesa Diretora"

# OK: Mesa simplificada
promoventes = "Mesa Diretora"

# ERRO: searchable não foi normalizado
searchable = "PL Projeto de Lei José"
# Deveria estar lowercase: "pl projeto de lei jose"
```

**Ação em erro:** ABORTAR execução, não salvar arquivo.
**Ação em aviso:** REGISTRAR no log, continuar.

---

### 5.4 Nível 4: Validação de Consistência (IMPORTANTE)

**Objetivo:** Garantir fidelidade aos dados originais da API.

**Verificações:**

1. **Contagem de projetos:**
   - Total na API = Total processado
   - Se diferente: ERRO CRÍTICO

2. **Amostragem de projetos (10-20 projetos):**
   - Para cada projeto processado, localizar correspondente na API
   - Verificar se ementa está idêntica (não foi modificada)
   - Verificar se tipo/numero/ano batem

3. **Códigos únicos:**
   - Todos os projetos da API foram processados
   - Nenhum projeto foi duplicado

**Ação em falha:** ABORTAR execução, não salvar arquivo.

---

## 5.5 Nível 5: Validação de Qualidade (INFORMATIVO)

**Objetivo:** Análise estatística e detecção de anomalias.

**Métricas a calcular:**

1. **Completude:**
   - Projetos sem promoventes (esperado: 0-1%)
   - Projetos com "SEM_PALAVRAS" (esperado: 0-5%)
   - Projetos com norma (esperado: 8-10%)

2. **Qualidade do searchable:**
   - Tamanho médio (caracteres)
   - Projetos com searchable < 100 chars (suspeito)

3. **Distribuição por tipo:**
   - % de PL, PDL, PR, PLO

4. **Distribuição de palavras-chave:**
   - Mínimo de palavras por projeto (excluindo "SEM_PALAVRAS")
   - Máximo de palavras por projeto
   - Média de palavras por projeto

**Exemplo de output:**

```
📊 Validação de Qualidade:

Completude:
  - Projetos sem promoventes: 0 (0.0%)
  - Projetos com SEM_PALAVRAS: 85 (4.6%)
  - Projetos com norma: 149 (8.0%)

Searchable:
  - Tamanho médio: 856 caracteres
  - Projetos suspeitos (<100 chars): 0

Distribuição por tipo:
  - PL: 1650 (89.0%)
  - PDL: 120 (6.5%)
  - PR: 80 (4.3%)
  - PLO: 3 (0.2%)

Palavras-chave:
  - Projetos com SEM_PALAVRAS: 85
  - Mínimo: 1 palavra
  - Máximo: 241 palavras
  - Média: 33.1 palavras/projeto
```

**Ação:** REGISTRAR estatísticas, NÃO bloquear salvamento.

---

### 5.6 Fluxo de Validação

```
Processar dados
     ↓
Nível 1: Estrutura → ERRO? → ABORTAR
     ↓
Nível 2: Schema → ERRO? → ABORTAR
     ↓
Nível 3: Integridade → ERRO? → ABORTAR
     ↓                   AVISO? → REGISTRAR
Nível 4: Consistência → ERRO? → ABORTAR
     ↓
Nível 5: Qualidade → REGISTRAR stats
     ↓
Salvar arquivo
```

**Output esperado:**
```
🔍 Validando estrutura... ✅
🔍 Validando schema... ✅
🔍 Validando integridade... ✅
⚠️  Avisos: 15 projetos sem palavras-chave
🔍 Validando consistência... ✅
📊 Qualidade:
  - Projetos sem promoventes: 0
  - Projetos sem palavras-chave: 15 (0.8%)
  - Projetos com norma: 149 (8.0%)
  - Searchable médio: 856 caracteres
✅ Validação completa passou!
💾 Salvando arquivo...
```

---

## 6. Arquitetura de Camadas

### 6.1 Estrutura de Arquivos

```
repo/
├── dados/
│   ├── atual.json              # Ano corrente
│   ├── recente.json            # 5 anos anteriores
│   ├── medio.json              # 10 anos semi-estáveis
│   ├── historico-a.json        # Histórico recente
│   ├── historico-b.json        # Histórico antigo
│   └── version.json            # Metadados
└── scripts/
    └── atualizar.py            # Script de atualização
```

### 6.2 Definição das Camadas (Relativas ao Ano Corrente)

**Cálculo dinâmico baseado em `ANO_CORRENTE`:**

```python
ANO_CORRENTE = datetime.now().year  # Ex: 2026
ANO_MAIS_ANTIGO = 1991  # Fixo
```

**Camada 1 - ATUAL:**
```
Arquivo: dados/atual.json
Anos: ANO_CORRENTE
Exemplo 2026: 2026
Frequência: Diária
```

**Camada 2 - RECENTE:**
```
Arquivo: dados/recente.json
Anos: (ANO_CORRENTE - 5) até (ANO_CORRENTE - 1)
Exemplo 2026: 2021-2025
Frequência: Semanal
```

**Camada 3 - MEDIO:**
```
Arquivo: dados/medio.json
Anos: (ANO_CORRENTE - 15) até (ANO_CORRENTE - 6)
Exemplo 2026: 2011-2020
Frequência: Semestral
```

**Camada 4A - HISTORICO-A:**
```
Arquivo: dados/historico-a.json
Anos: Metade mais recente do histórico
Cálculo:
  hist_inicio = 1991
  hist_fim = ANO_CORRENTE - 16
  hist_meio = hist_inicio + ((hist_fim - hist_inicio + 1) / 2)
  anos = hist_meio até hist_fim
Exemplo 2026: 2001-2010
Frequência: Anual
```

**Camada 4B - HISTORICO-B:**
```
Arquivo: dados/historico-b.json
Anos: Metade mais antiga do histórico
Cálculo:
  anos = 1991 até (hist_meio - 1)
Exemplo 2026: 1991-2000
Frequência: Anual
```

**Divisão do histórico em 2 arquivos:**
- Motivo: Blocos de 25+ anos causam timeout na API
- Solução: Dividir em blocos de ~10-13 anos cada

---

### 6.3 Arquivo version.json

**Objetivo:** Metadados sobre cada camada, atualizado a cada execução.

**Estrutura:**
```json
{
  "lastUpdate": "2026-01-27T03:00:00Z",
  "anoCorrente": 2026,
  "camadas": {
    "atual": {
      "arquivo": "dados/atual.json",
      "anos": "2026-2026",
      "projetos": 680,
      "descricao": "Ano corrente (2026)"
    },
    "recente": {
      "arquivo": "dados/recente.json",
      "anos": "2021-2025",
      "projetos": 3400,
      "descricao": "5 anos anteriores (2021 a 2025)"
    },
    "medio": {
      "arquivo": "dados/medio.json",
      "anos": "2011-2020",
      "projetos": 6800,
      "descricao": "10 anos semi-estáveis (2011 a 2020)"
    },
    "historico-a": {
      "arquivo": "dados/historico-a.json",
      "anos": "2001-2010",
      "projetos": 6800,
      "descricao": "Histórico recente (2001 a 2010)"
    },
    "historico-b": {
      "arquivo": "dados/historico-b.json",
      "anos": "1991-2000",
      "projetos": 6800,
      "descricao": "Histórico antigo (1991 a 2000)"
    }
  }
}
```

---

## 7. Automação via GitHub Actions

### 7.1 Workflow: Atualização Diária

```yaml
name: Atualização Diária
on:
  schedule:
    - cron: '0 3 * * 2-6'  # 3h AM de Terça a Sábado
  workflow_dispatch:
```

**Executa:** Atualiza `atual.json` (Pula Domingo e Segunda pois não há novos projetos)
**Duração esperada:** 10-15 segundos

---

### 7.2 Workflow: Atualização Semanal

```yaml
name: Atualização Semanal
on:
  schedule:
    - cron: '30 3 * * 0'  # 3h30 AM domingos
  workflow_dispatch:
```

**Executa:** Atualiza `recente.json`
**Duração esperada:** 15-20 segundos

---

### 7.3 Workflow: Atualização Semestral

```yaml
name: Atualização Semestral
on:
  schedule:
    - cron: '0 4 1 7 *'  # 4h AM em 1º julho
  workflow_dispatch:
```

**Executa:** Atualiza `medio.json`
**Duração esperada:** 30 segundos
**Observação:** 1º de Janeiro é coberto pela Virada de Ano

---



### 7.5 Workflow: Virada de Ano

```yaml
name: Virada de Ano - Reconstrução Total
on:
  schedule:
    - cron: '0 8 1 1 *'  # 8h AM UTC em 1º janeiro (05:00 SP)
  workflow_dispatch:
```

**Executa:** Atualiza TODAS as camadas
**Motivo:** As faixas de anos mudam com o novo ano corrente. O horário de 08:00 UTC (05:00 SP) garante que a virada já ocorreu em ambos os servidores.
**Duração esperada:** 2-3 minutos
**Delays:** 15 segundos entre cada chamada

**Comportamento esperado:**
- Script recalcula automaticamente as faixas de anos
- Arquivos são sobrescritos com novos conteúdos
- Nomes dos arquivos permanecem os mesmos
- Frontend não precisa de alteração

---

### 7.6 Workflow: Atualização Manual (Forçada)

```yaml
name: Atualização Manual
on:
  workflow_dispatch:
    inputs:
      atual:
        description: 'Atualizar atual?'
        type: boolean
        default: false
      recente:
        description: 'Atualizar recente?'
        type: boolean
        default: false
      medio:
        description: 'Atualizar medio?'
        type: boolean
        default: false
      historico-a:
        description: 'Atualizar historico-a?'
        type: boolean
        default: false
      historico-b:
        description: 'Atualizar historico-b?'
        type: boolean
        default: false
```

**Uso:** Interface com checkboxes no GitHub Actions
**Objetivo:** Forçar atualização de camadas específicas fora do cronograma
**Exemplo:** Correção de dados em projeto de 1995 → marcar checkbox `historico-b`

**Implementação:**
- Cada checkbox controla execução condicional de um step
- Pode marcar múltiplas camadas simultaneamente
- Delays de 15 segundos entre execuções

---

## 8. Mitigações de Risco

### 8.1 Proteções Contra Bloqueio

**Risco:** Servidor SPLegis pode bloquear por excesso de requisições.

**Mitigações:**

1. **Volume baixo:**
   - Máximo 5 requisições/dia (rotinas normais)
   - Máximo 12 requisições em dia de virada de ano

2. **Horário estratégico:**
   - Todas execuções na madrugada (2h-4h AM)
   - Servidor menos carregado, menos usuários

3. **Headers realistas:**
   - User-Agent de navegador real
   - Accept: application/json
   - Referer da página de consulta

4. **Delays entre chamadas:**
   - 15 segundos entre requisições sequenciais
   - Nunca fazer chamadas paralelas

5. **Retry com backoff:**
   - 3 tentativas em caso de falha
   - Espera exponencial: 5s, 10s, 20s
   - Timeout de 120 segundos por requisição

6. **Session persistente:**
   - Obter cookies antes das chamadas reais
   - Simular navegação humana

**Avaliação de risco:** BAIXO (1-2% de chance de bloqueio)

---

### 8.3 Risco na Virada do Ano (Timezone)

**Cenário:** 
O servidor do GitHub Actions roda em UTC. O servidor da Câmara e a virada do ano ocorrem em UTC-3 (São Paulo).

**Risco:** 
O workflow de "Virada de Ano" rodar quando ainda é dia 31/12 em SP (ex: 02:00 UTC é 23:00 em SP), ou vice-versa, causando inconsistência nos filtros de data e na reconstrução das camadas.

**Solução:** 
Agendar o workflow de virada para quando **já for dia 1º de janeiro em ambos os locais**.
- **08:00 UTC = 05:00 SP**.
- Isso garante que tanto o relógio global quanto o relógio local da Câmara já viraram o ano.

---

### 8.2 Tratamento de Falhas

**Cenários:**

1. **Timeout em bloco específico:**
   - Registrar erro
   - Manter versão anterior do arquivo
   - Continuar com próximos blocos
   - Notificar no log

2. **Validação falha:**
   - NÃO salvar arquivo
   - Manter versão anterior
   - Registrar todos os erros
   - Exit code ≠ 0

3. **API retorna erro (500, 503):**
   - Retry automático
   - Se persistir: manter versão anterior
   - Registrar no log

4. **Git push falha:**
   - Retry automático
   - Alertar se persistir

---

## 9. Edge Cases

### 9.1 Dados Incomuns

**Projeto sem promoventes:**
```
Input:  {"promoventes": []}
Output: promoventes = ""
        searchable inclui campo vazio normalmente
```

**Projeto sem palavras-chave:**
```
Input:  {"assuntos": []}
Output: palavras-chave = "SEM_PALAVRAS"
        searchable inclui "sem palavras" após normalização
```

**Projeto com 241 palavras-chave:**
```
Output: Todas as 241 concatenadas com " | "
        Não truncar
```

**Ementa com caracteres especiais:**
```
Input:  "Art. 59-A – ECA (Lei nº 14.811)"
Output: ementa = "Art. 59-A – ECA (Lei nº 14.811)" (preservado)
        searchable = "art 59 a eca lei 14 811" (normalizado)
```

**Promovente não-vereador:**
```
Input:  "Executivo - RICARDO NUNES"
Output: "Executivo - RICARDO NUNES" (mantém texto completo)
```

**Promovente Mesa da Câmara:**
```
Input:  "MESA DA CAMARA MUNICIPAL DE SAO PAULO - 01/01/2025 a 31/12/2025"
Output: "Mesa Diretora" (simplificado, remove período)
```

**Múltiplos promoventes mistos:**
```
Input:  ["Ver. FULANO", "Executivo - X", "Ver. BELTRANO"]
Output: "FULANO | Executivo - X | BELTRANO"

Input:  ["Ver. FULANO", "MESA DA CAMARA..."]
Output: "FULANO | Mesa Diretora"
```

**Projeto só com ementa (sem promoventes e palavras-chave):**
```
Input:  {
  "ementa": "Autoriza o Poder Executivo...",
  "promoventes": [],
  "assuntos": []
}
Output: [
  "PL",
  "10",
  "2026",
  "",
  "Autoriza o Poder Executivo...",
  "",                           # promoventes vazio
  "SEM_PALAVRAS",              # palavras-chave marcado
  "pl projeto de lei 10 2026 autoriza poder executivo sem palavras"
]

```

---

### 9.2 Situações Limítrofes

**Ano na virada (31/12 → 01/01):**
- Script recalcula faixas automaticamente
- Estrutura se ajusta ao novo ano corrente
- **Atenção:** Workflow aguarda janela segura de timezone (08:00 UTC)

**Primeiro dia do ano (1º janeiro):**
- Workflow de virada (2h AM) roda antes
- Workflows regulares (3h-4h AM) rodam depois
- Garantir que arquivos estão com estrutura do novo ano

---

## 10. Exemplo Completo End-to-End

### 10.1 Input Completo

```json
{
  "recordsFiltered": 1853,
  "data": [
    {
      "codigo": 784197,
      "natodigital": true,
      "tipo": 1,
      "numero": 31,
      "ano": 2026,
      "sigla": "PL",
      "texto": "PL 31/2026",
      "ementa": "Regulamenta, no âmbito do Município de São Paulo, o disposto no art. 59-A do Estatuto da Criança e do Adolescente – ECA, incluído pela Lei Federal nº 14.811, de 12 de janeiro de 2024, e estabelece procedimentos institucionais relativos à exigência de Certidão de Antecedentes Criminais.",
      "norma": {
        "numero": null,
        "ano": 0
      },
      "dT_RowId": 784197,
      "promoventes": [
        {
          "codigo": 776,
          "texto": "Ver. ELISEU GABRIEL (PSB)"
        }
      ],
      "assuntos": [
        {
          "codigo": 61,
          "texto": "ADMISSAO"
        },
        {
          "codigo": 63,
          "texto": "ADOLESCENTE"
        },
        {
          "codigo": 14477,
          "texto": "ANTECEDENTES"
        }
      ]
    },
    {
      "codigo": 783611,
      "natodigital": true,
      "tipo": 3,
      "numero": 1,
      "ano": 2026,
      "sigla": "PR",
      "texto": "PR 1/2026",
      "ementa": "Institui a Comissão Especial de Estudos sobre Inteligência Artificial.",
      "norma": {
        "numero": null,
        "ano": 0
      },
      "dT_RowId": 783611,
      "promoventes": [
        {
          "codigo": 100,
          "texto": "MESA DA CAMARA MUNICIPAL DE SAO PAULO - 01/01/2025 a 31/12/2025"
        }
      ],
      "assuntos": [
        {
          "codigo": 1045,
          "texto": "COMISSAO ESPECIAL"
        },
        {
          "codigo": 6500,
          "texto": "INTELIGENCIA ARTIFICIAL"
        }
      ]
    },
    {
      "codigo": 782898,
      "natodigital": true,
      "tipo": 2,
      "numero": 142,
      "ano": 2025,
      "sigla": "PDL",
      "texto": "PDL 142/2025",
      "ementa": "Concede Título de Cidadão Paulistano ao Sr. João Silva.",
      "norma": {
        "numero": 18400,
        "ano": 2026
      },
      "dT_RowId": 782898,
      "promoventes": [
        {
          "codigo": 450,
          "texto": "Ver. ANTONIO DONATO (PT)"
        },
        {
          "codigo": 451,
          "texto": "Ver. MARIA SANTOS (PSOL)"
        }
      ],
      "assuntos": [
        {
          "codigo": 890,
          "texto": "CIDADAO PAULISTANO"
        },
        {
          "codigo": 1700,
          "texto": "HOMENAGEM"
        }
      ]
    },
    {
      "codigo": 782500,
      "natodigital": true,
      "tipo": 1,
      "numero": 120,
      "ano": 2025,
      "sigla": "PL",
      "texto": "PL 120/2025",
      "ementa": "Autoriza o Poder Executivo a celebrar convênio com entidade filantrópica.",
      "norma": {
        "numero": null,
        "ano": 0
      },
      "dT_RowId": 782500,
      "promoventes": [
        {
          "codigo": 600,
          "texto": "Ver. JOÃO SILVA (PT)"
        }
      ],
      "assuntos": []
    }
  ]
}
```

---

### 10.2 Output Esperado

```json
{
  "columns": [
    "tipo",
    "numero",
    "ano",
    "norma",
    "ementa",
    "promoventes",
    "palavras-chave",
    "searchable"
  ],
  "data": [
    [
      "PL",
      "31",
      "2026",
      "",
      "Regulamenta, no âmbito do Município de São Paulo, o disposto no art. 59-A do Estatuto da Criança e do Adolescente – ECA, incluído pela Lei Federal nº 14.811, de 12 de janeiro de 2024, e estabelece procedimentos institucionais relativos à exigência de Certidão de Antecedentes Criminais.",
      "ELISEU GABRIEL (PSB)",
      "ADMISSAO | ADOLESCENTE | ANTECEDENTES",
      "pl projeto de lei 31 2026 regulamenta ambito municipio sao paulo disposto art 59 a estatuto crianca adolescente eca incluido lei federal 14 811 12 janeiro 2024 estabelece procedimentos institucionais relativos exigencia certidao antecedentes criminais admissao adolescente antecedentes eliseu gabriel psb"
    ],
    [
      "PR",
      "1",
      "2026",
      "",
      "Institui a Comissão Especial de Estudos sobre Inteligência Artificial.",
      "Mesa Diretora",
      "COMISSAO ESPECIAL | INTELIGENCIA ARTIFICIAL",
      "pr projeto de resolucao 1 2026 institui comissao especial estudos inteligencia artificial comissao especial inteligencia artificial mesa diretora"
    ],
    [
      "PDL",
      "142",
      "2025",
      "18400/2026",
      "Concede Título de Cidadão Paulistano ao Sr. João Silva.",
      "ANTONIO DONATO (PT) | MARIA SANTOS (PSOL)",
      "CIDADAO PAULISTANO | HOMENAGEM",
      "pdl projeto de decreto legislativo 142 2025 18400 2026 concede titulo cidadao paulistano sr joao silva cidadao paulistano homenagem antonio donato pt maria santos psol"
    ],
    [
      "PL",
      "120",
      "2025",
      "",
      "Autoriza o Poder Executivo a celebrar convênio com entidade filantrópica.",
      "JOÃO SILVA (PT)",
      "SEM_PALAVRAS",
      "pl projeto de lei 120 2025 autoriza poder executivo celebrar convenio entidade filantropica sem palavras joao silva pt"
    ]
  ]
}
```

---

### 10.3 Transformações Aplicadas

**Projeto 1 (PL 31/2026):**
- Código: 784197 (usado para ordenar, depois removido)
- Promovente: "Ver. ELISEU GABRIEL" → "ELISEU GABRIEL" (removeu "Ver. ")
- Norma: null → "" (vazio)
- Palavras-chave: 3 palavras concatenadas
- Searchable: incluiu tipo extenso "Projeto de Lei", normalizou acentos e pontuação

**Projeto 2 (PR 1/2026):**
- Código: 783611
- Promovente: "MESA DA CAMARA MUNICIPAL DE SAO PAULO - 01/01/2025 a 31/12/2025" → **"Mesa Diretora"** (simplificado)
- Tipo extenso: "Projeto de Resolução"
- Searchable: inclui "mesa diretora" normalizado

**Projeto 3 (PDL 142/2025):**
- Código: 782898
- Norma: {"numero": 18400, "ano": 2026} → "18400/2026"
- Promoventes: concatenados com " | "

**Projeto 4 (PL 120/2025) - SEM PALAVRAS-CHAVE:**
- Código: 782500 (menor código → aparece por último)
- Promovente: "Ver. JOÃO SILVA" → "JOÃO SILVA"
- Assuntos: [] (vazio)
- Palavras-chave: **"SEM_PALAVRAS"**
- Searchable: inclui "sem palavras" após normalização

**Ordenação final por código DESC:**
1. PL 31/2026 (784197)
2. PR 1/2026 (783611)
3. PDL 142/2025 (782898)
4. PL 120/2025 (782500)

---

---


## 11. Contrato de Dados

```
ESTRUTURA DE SAÍDA
==================
{
  "columns": [...],  # Array com 8 nomes de colunas
  "data": [...]      # Array de arrays (cada projeto = 1 array de 8 strings)
}

COLUNAS (índices 0-7)
=====================
[0] tipo           : str  - Sigla (PL, PDL, PR, PLO)
[1] numero         : str  - Número do projeto
[2] ano            : str  - Ano
[3] norma          : str  - Lei resultante ("numero/ano" ou "")
[4] ementa         : str  - Texto original sem modificações
[5] promoventes    : str  - Concatenado com " | " 
                             Ver. removido de vereadores
                             Mesa simplificada para "Mesa Diretora"
[6] palavras-chave : str  - Concatenado com " | " (todas, sem truncar)
                             "SEM_PALAVRAS" se array vazio
[7] searchable     : str  - Normalizado (lowercase, sem acentos, sem pontuação)

GARANTIAS
=========
✓ Ordem das colunas é fixa e imutável
✓ Todos os valores são strings
✓ Searchable inclui tipo por extenso
✓ Separador " | " previne palavras falsas
✓ Ementa preservada exatamente como vem da API
✓ Todas palavras-chave incluídas (sem truncamento)
✓ Projetos sem palavras-chave: "SEM_PALAVRAS"
✓ Projetos sem promoventes: string vazia ""
✓ Mesa da Câmara simplificada: "Mesa Diretora"
✓ Ordenação por código DESC (cronológica real)
✓ Validação completa executada antes de salvar

TIPOS DE PROMOVENTES
====================
- Vereadores: "NOME (PARTIDO)" (removido "Ver. ")
- Mesa Diretora: "Mesa Diretora" (simplificado, período removido)
- Executivo: "Executivo - NOME" (mantido)
- Comissões: "Comissão de..." (mantido)
- Tribunal: "TRIBUNAL DE CONTAS..." (mantido)
- Vazio: "" (quando array vazio)

TRANSFORMAÇÕES DE PROMOVENTES
=============================
Entrada                                              → Saída
"Ver. FULANO (PT)"                                   → "FULANO (PT)"
"MESA DA CAMARA MUNICIPAL DE SAO PAULO - 01/01/..." → "Mesa Diretora"
"Executivo - RICARDO NUNES"                          → "Executivo - RICARDO NUNES"
"Comissão de Trânsito..."                            → "Comissão de Trânsito..."
"TRIBUNAL DE CONTAS DO MUNICIPIO"                    → "TRIBUNAL DE CONTAS DO MUNICIPIO"

PALAVRAS-CHAVE
==============
- Concatenadas com " | "
- TODAS incluídas (sem truncamento)
- Valor especial: "SEM_PALAVRAS" quando array vazio
- Após normalização: "sem palavras"

NORMALIZAÇÃO SEARCHABLE
=======================
1. Lowercase
2. Remove acentos (ã→a, é→e, ç→c)
3. Remove pontuação
4. Remove underscore (SEM_PALAVRAS → sem palavras)
5. Normaliza espaços múltiplos
6. Mantém: letras, números, espaços

TIPOS POR EXTENSO
=================
PL  → Projeto de Lei
PDL → Projeto de Decreto Legislativo
PR  → Projeto de Resolução
PLO → Projeto de Lei Orgânica

ESTATÍSTICAS ESPERADAS
======================
- ~32.000 projetos totais (1991-2026)
- ~680 projetos/ano (média)
- Média 33 palavras-chave/projeto
- Máximo 241 palavras-chave observado
- ~8-10% projetos com norma preenchida
- ~95% promoventes são vereadores
- ~1-2% promoventes são Mesa Diretora
- ~0-5% projetos com "SEM_PALAVRAS"
```

---

## 12. Observações Finais

### 12.1 Nomes de Arquivo

**Sempre os mesmos nomes:**
- `atual.json`, `recente.json`, `medio.json`, `historico-a.json`, `historico-b.json`
- Conteúdo muda conforme ano, nomes permanecem fixos
- Frontend nunca precisa atualizar URLs

### 12.2 Virada de Ano

**Totalmente automática:**
- Script detecta novo ano
- Recalcula faixas automaticamente
- Sobrescreve arquivos com nova estrutura
- Zero intervenção manual necessária

### 12.3 Sustentabilidade

**GitHub Pages gratuito:**
- Crescimento estimado: ~150MB/ano no Git
- Viável por 6+ anos
- Arquivos finais: ~13MB gzip total

### 12.4 Performance

**Usuário frequente (diário):**
- Primeira visita: ~13MB (3-4 segundos)
- Visitas seguintes: ~0.5MB (0.3 segundos)
- Economia de banda: 96%

---