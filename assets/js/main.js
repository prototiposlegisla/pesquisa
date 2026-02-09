/**
 * LEISP - Main JavaScript
 * Site de busca de projetos legislativos e normas do Município de São Paulo
 */

(function () {
    'use strict';

    // =========================================
    // CONFIGURAÇÃO
    // =========================================

    const CONFIG = {
        RESULTS_PER_PAGE: 25,
        DEBOUNCE_MS: 0o30,
        MIN_SEARCH_LENGTH: 3,
        VERSION_FILE: './dados/projetos/version.json',
        CARD_ROTATIONS: [-0.4, 0.3, -0.2, 0.5, -0.3, 0.2, -0.5, 0.4],
        NORMAS_FILES: [
            './dados/normas/normas-atual.json',
            './dados/normas/normas-2020.json',
            './dados/normas/normas-2010.json',
            './dados/normas/normas-2000.json',
            './dados/normas/normas-1990.json',
            './dados/normas/normas-1980.json',
            './dados/normas/normas-1970.json',
            './dados/normas/normas-1960.json',
            './dados/normas/normas-1950.json',
            './dados/normas/normas-1940.json',
            './dados/normas/normas-1930.json',
            './dados/normas/normas-1920.json',
            './dados/normas/normas-1910.json',
            './dados/normas/normas-1900.json',
            './dados/normas/normas-antigo.json'
        ]
    };

    // Mapeamento de tipos de projeto para códigos da URL
    const TYPE_CODES = { 'PL': 1, 'PDL': 2, 'PR': 3, 'PLO': 4 };

    // Mapeamento de tipos de norma para PLP
    const NORMA_TIPOS_PLP = {
        'Lei': 'Lei',
        'Decreto-Legislativo': 'DECLEG',
        'Resolução': 'RESCMSP',
        'Ato': 'Ato'
    };

    // Mapeamento de tipos de norma para Biblioteca
    const NORMA_TIPOS_BIB = {
        'Lei': 'LEI',
        'Decreto-Legislativo': 'DLE',
        'Resolução': 'RESOLUCAO*DA*CMSP*',
        'Ato': 'ATO*DA*CMSP*'
    };

    // Mapeamento de tipo de norma para data-type do card (reutiliza cores dos projetos)
    const NORMA_CARD_TYPE_MAP = {
        'LEI': 'PL',
        'RES': 'PR',
        'ELO': 'PLO',
        'ATO': 'PLO',
        'DL': 'PDL'
    };

    // Mapeamento de texto do campo "projeto" para tipo de projeto
    const PROJETO_TEXT_MAP = {
        'Projeto de Emenda à Lei Orgânica': 'PLO',
        'Projeto de Decreto Legislativo': 'PDL',
        'Projeto de Resolução': 'PR',
        'Projeto de Lei': 'PL'
    };

    // Sequência de cores para highlight (classes CSS)
    const HIGHLIGHT_COLORS = [
        'hl-1',
        'hl-2',
        'hl-3',
        'hl-4',
        'hl-5',
        'hl-6',
        'hl-7',
        'hl-8'
    ];

    // =========================================
    // ESTADO
    // =========================================

    let allData = [];
    let isDataLoaded = false;
    let loadError = false;
    let currentResults = [];
    let displayedCount = 0;
    let currentPage = 0;
    let currentSearchTerms = [];
    let debounceTimer = null;

    // Estado de normas
    let allNormasData = [];
    let isNormasLoaded = false;
    let normasLoadError = false;
    let isNormasLoading = false;
    let activeMode = 'projetos'; // 'projetos' | 'normas'

    // =========================================
    // ELEMENTOS DOM
    // =========================================

    let searchInput, clearBtn, resultsLog, resultsCount, resultsTerms, mainContainer;
    let paginationContainer, infoField, toggleContainer;

    // =========================================
    // MÓDULO: NORMALIZAÇÃO DE TEXTO
    // =========================================

    /**
     * Normaliza texto para busca: lowercase, sem acentos
     */
    function normalizeText(text) {
        if (!text) return '';
        return text
            .toLowerCase()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .replace(/\.(?=\d{3})/g, '') // Remove pontos de milhar (ex: 10.000 -> 10000)
            .replace(/[^a-z0-9\s|/\-\(\)]/g, ''); // Mantém apenas caracteres permitidos (igual ao backend)
    }

    /**
     * Escapa caracteres especiais para uso em regex
     */
    function escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    /**
     * Escapa caracteres HTML para prevenir XSS
     */
    function escapeHtml(text) {
        if (!text) return text;
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    // =========================================
    // MÓDULO: CARREGAMENTO DE DADOS
    // =========================================

    /**
     * Carrega todos os arquivos JSON em paralelo
     */
    async function loadAllData() {
        try {
            // 1. Carregar version.json para descobrir os arquivos de dados
            const versionRes = await fetch(CONFIG.VERSION_FILE);
            if (!versionRes.ok) {
                throw new Error(`Erro HTTP ${versionRes.status} ao carregar version.json`);
            }
            const version = await versionRes.json();

            // Ordenar camadas por ano DESC para manter cronologia (código DESC)
            const dataFiles = Object.values(version.camadas)
                .sort((a, b) => {
                    const anoA = parseInt(a.anos.split('-').pop());
                    const anoB = parseInt(b.anos.split('-').pop());
                    return anoB - anoA;
                })
                .map(c => './' + c.arquivo);

            // 2. Carregar todos os arquivos de dados em paralelo
            const responses = await Promise.all(
                dataFiles.map(file => fetch(file))
            );

            for (const res of responses) {
                if (!res.ok) {
                    throw new Error(`Erro HTTP ${res.status} ao carregar dados`);
                }
            }

            const jsons = await Promise.all(
                responses.map(res => res.json())
            );

            // Mescla todos os arrays de dados
            allData = jsons.flatMap(json => json.data || []);
            isDataLoaded = true;
            loadError = false;

            console.log(`Dados carregados: ${allData.length} projetos`);

            // Se havia uma busca pendente, executa agora
            if (searchInput && searchInput.value.trim()) {
                performSearch();
            }

            // Após carregar projetos, inicia carregamento de normas em background
            loadAllNormasData();

        } catch (error) {
            console.error('Erro ao carregar dados:', error);
            loadError = true;
            showLoadError();
        }
    }

    /**
     * Mostra mensagem de erro de carregamento
     */
    function showLoadError() {
        resultsCount.innerHTML = '';
        resultsTerms.innerHTML = `
            <span style="color: #951D36;">Erro ao carregar dados. Verifique sua conexão.</span>
            <button class="reload-btn" onclick="location.reload()">[Recarregar]</button>
        `;
    }

    /**
     * Carrega todos os arquivos JSON de normas
     * Chamado automaticamente após o carregamento dos projetos
     */
    async function loadAllNormasData() {
        if (isNormasLoaded || isNormasLoading) return;

        isNormasLoading = true;

        try {
            const responses = await Promise.all(
                CONFIG.NORMAS_FILES.map(file => fetch(file))
            );

            for (const res of responses) {
                if (!res.ok) {
                    throw new Error(`Erro HTTP ${res.status} ao carregar normas`);
                }
            }

            const jsons = await Promise.all(
                responses.map(res => res.json())
            );

            allNormasData = jsons.flatMap(json => json.data || []);
            isNormasLoaded = true;
            normasLoadError = false;

            console.log(`Normas carregadas: ${allNormasData.length} normas`);

            // Se o usuário está no modo normas e tinha busca pendente, executa
            if (activeMode === 'normas' && searchInput && searchInput.value.trim()) {
                performSearch();
            }

        } catch (error) {
            console.error('Erro ao carregar normas:', error);
            normasLoadError = true;
            if (activeMode === 'normas') {
                showLoadError();
            }
        } finally {
            isNormasLoading = false;
        }
    }

    // =========================================
    // MÓDULO: PARSER DE QUERY
    // =========================================

    /**
     * Analisa a query de busca e retorna estrutura com tipo e termos
     */
    function parseSearchQuery(input) {
        const trimmed = input.trim();
        const normalized = normalizeText(trimmed);

        if (!normalized) {
            return { type: 'empty', terms: [], originalTerms: [] };
        }

        // Busca por norma: começa com n/N seguido de número (ex: n1000 ou n1000 educ)
        if (/^n\d+/i.test(trimmed)) {
            // Extrai número da norma e o resto
            const match = trimmed.match(/^n(\d+)(.*)/i);
            const normaNumber = match[1];
            const remainingInput = match[2];

            // Se houver texto restante, parseia como termos
            // Mas mantém type='norma' para filtrar pelo número exato da norma
            const parsed = parseTermsFromInput(remainingInput || '');

            return {
                type: 'norma',
                normaNumber: normaNumber,
                terms: parsed.normalized,
                originalTerms: [trimmed]
            };
        }

        // Busca com filtro de norma: começa com n/N sozinho (ex: n educ)
        if (/^n\s+/i.test(trimmed) || normalized === 'n') {
            const remainingInput = trimmed.substring(1).trim(); // remove o 'n'

            // Se for só 'n', busca tudo que tem norma
            if (!remainingInput) {
                return {
                    type: 'normal',
                    terms: [],
                    originalTerms: ['[COM NORMA]'],
                    requireNorma: true
                };
            }

            const parsed = parseTermsFromInput(remainingInput);
            return {
                type: 'normal',
                terms: parsed.normalized,
                originalTerms: parsed.original,
                requireNorma: true
            };
        }

        // Busca numérica de projeto: começa com p/P seguido de número
        if (/^p\d+/i.test(trimmed)) {
            const parts = trimmed.split(/\s+/);
            const prefixAndNumber = parts[0]; // ex: "p123"
            const projectNumber = prefixAndNumber.substring(1); // remove o 'p'

            const remainingInput = parts.slice(1).join(' ');
            const remainingTerms = parseTermsFromInput(remainingInput);

            return {
                type: 'project_number',
                projectNumber: projectNumber,
                terms: remainingTerms.normalized,
                originalTerms: [projectNumber, ...remainingTerms.original]
            };
        }

        // Busca normal: parse de termos e frases entre aspas
        const parsed = parseTermsFromInput(trimmed);
        return {
            type: 'normal',
            terms: parsed.normalized,
            originalTerms: parsed.original
        };
    }

    /**
     * Extrai termos e frases entre aspas do input e números barra ano
     */
    function parseTermsFromInput(input) {
        const normalized = [];
        const original = [];
        let remaining = input;

        // 1. Extrai frases entre aspas
        const quoteRegex = /"([^"]+)"/g;
        let match;

        while ((match = quoteRegex.exec(input)) !== null) {
            const phrase = match[1];
            normalized.push({
                value: normalizeText(phrase),
                isPhrase: true,
                original: phrase
            });
            original.push(`"${phrase}"`);
            remaining = remaining.replace(match[0], ' ');
        }

        // 2. (REMOVIDO) A regra especial de número/número foi removida conforme solicitado.
        // Os números serão tratados como termos normais ou frases se estiverem entre aspas.

        // 3. Extrai termos individuais restantes
        remaining.split(/\s+/).forEach(term => {
            const trimmedTerm = term.trim();
            if (trimmedTerm.length > 0) {
                normalized.push({
                    value: normalizeText(trimmedTerm),
                    isPhrase: false,
                    original: trimmedTerm
                });
                original.push(trimmedTerm);
            }
        });

        return { normalized, original };
    }

    // =========================================
    // MÓDULO: MOTOR DE BUSCA
    // =========================================

    /**
     * Executa a busca com base na query parseada
     */
    function executeSearch(query) {
        if (activeMode === 'normas') {
            return executeNormasSearch(query);
        }

        if (!isDataLoaded) {
            return [];
        }

        // Busca por norma
        if (query.type === 'norma') {
            let results = allData.filter(row => {
                const norma = row[3]; // índice 3 = norma
                if (!norma) return false;
                const normaNum = norma.split('/')[0].replace(/\./g, '');
                return normaNum === query.normaNumber;
            });

            // Aplica termos adicionais se existirem
            if (query.terms && query.terms.length > 0) {
                results = results.filter(row => {
                    const searchable = row[7]; // índice 7 = searchable
                    return checkTermsMatch(searchable, query.terms);
                });
            }

            return results;
        }

        // Busca numérica de projeto
        if (query.type === 'project_number') {
            let results = allData.filter(row => row[1] === query.projectNumber);

            // Aplica termos adicionais se existirem
            if (query.terms.length > 0) {
                results = results.filter(row => {
                    const searchable = row[7]; // índice 7 = searchable
                    return checkTermsMatch(searchable, query.terms);
                });
            }

            return results;
        }

        // Busca normal - todos os termos devem estar presentes (AND)
        // Se query.requireNorma for true, filtramos também por presença de norma

        let initialData = allData;

        if (query.requireNorma) {
            initialData = allData.filter(row => row[3]); // row[3] é norma
        }

        if (query.terms.length === 0) {
            // Se for busca apenas por "n" (requireNorma=true e sem termos), retorna todos com norma
            if (query.requireNorma) {
                return initialData;
            }
            return [];
        }

        return initialData.filter(row => {
            const searchable = row[7];
            return checkTermsMatch(searchable, query.terms);
        });
    }

    /**
     * Verifica se todos os termos dão match no texto pesquisável
     */
    function checkTermsMatch(searchable, terms) {
        return terms.every(term => {
            if (term.isRegex) {
                return term.searchValue.test(searchable);
            }
            return searchable.includes(term.value);
        });
    }

    /**
     * Executa busca no dataset de normas
     */
    function executeNormasSearch(query) {
        if (!isNormasLoaded) {
            return [];
        }

        // Busca por número de norma: n123
        if (query.type === 'norma') {
            let results = allNormasData.filter(row => {
                return row[1] === query.normaNumber;
            });

            if (query.terms && query.terms.length > 0) {
                results = results.filter(row => {
                    const searchable = row[10];
                    return checkTermsMatch(searchable, query.terms);
                });
            }
            return results;
        }

        // Busca por número de projeto de origem: p123
        if (query.type === 'project_number') {
            let results = allNormasData.filter(row => {
                const projeto = row[6];
                if (!projeto) return false;
                const match = projeto.match(/(\d+)\//);
                return match && match[1] === query.projectNumber;
            });

            if (query.terms.length > 0) {
                results = results.filter(row => {
                    const searchable = row[10];
                    return checkTermsMatch(searchable, query.terms);
                });
            }
            return results;
        }

        // Busca normal
        let initialData = allNormasData;

        if (query.terms.length === 0) {
            if (query.requireNorma) {
                return initialData; // No modo normas, tudo é norma
            }
            return [];
        }

        return initialData.filter(row => {
            const searchable = row[10];
            return checkTermsMatch(searchable, query.terms);
        });
    }

    // =========================================
    // MÓDULO: CONSTRUTOR DE URLs
    // =========================================

    /**
     * Formata número com pontos de milhar (ex: 18000 -> 18.000)
     */
    function formatWithDots(value) {
        if (!value) return value;
        return value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    }

    /**
     * Constrói URL para SPLegis Consulta
     */
    function buildSPLegisURL(tipo, numero, ano) {
        const tipoCode = TYPE_CODES[tipo] || 1;
        return `https://splegisconsulta.saopaulo.sp.leg.br/Pesquisa/DetailsMateriaTramitacaoLegislativa?tipo=${tipoCode}&numero=${numero}&ano=${ano}`;
    }

    /**
     * Constrói URL para SPLegis Intranet
     */
    function buildIntranetURL(tipo, numero, ano) {
        const tipoCode = TYPE_CODES[tipo] || 1;
        return `https://splegis.saopaulo.sp.leg.br/Pesquisa/DetailsMateriaTramitacaoLegislativa?tipo=${tipoCode}&numero=${numero}&ano=${ano}`;
    }

    /**
     * Constrói URL para Biblioteca (Projeto)
     */
    function buildBibliotecaProjetoURL(tipo, numero, ano) {
        return `https://www.saopaulo.sp.leg.br/cgi-bin/wxis.bin/iah/scripts/?IsisScript=iah.xis&lang=pt&format=detalhado.pft&base=proje&form=A&nextAction=search&indexSearch=^nTw^lTodos%20os%20campos&exprSearch=P=${tipo}${numero}${ano}`;
    }

    /**
     * Determina o tipo de norma baseado no tipo de projeto
     */
    function getNormaTipo(tipoProj) {
        if (tipoProj === 'PL' || tipoProj === 'PLO') return 'Lei';
        if (tipoProj === 'PDL') return 'Decreto-Legislativo';
        if (tipoProj === 'PR') return 'Resolução';
        return 'Lei';
    }

    /**
     * Constrói URL para PLP (Norma)
     */
    function buildPLPURL(tipoProj, normaNum, normaAno) {
        const normaTipo = getNormaTipo(tipoProj);
        const tipoPLP = NORMA_TIPOS_PLP[normaTipo] || 'Lei';
        return `https://app-plpconsulta-prd.azurewebsites.net/Forms/MostrarArquivo?TIPO=${tipoPLP}&NUMERO=${normaNum}&ANO=${normaAno}&DOCUMENTO=Ficha`;
    }

    /**
     * Constrói URL para Biblioteca (Norma)
     */
    function buildBibliotecaNormaURL(tipoProj, normaNum, normaAno) {
        const normaTipo = getNormaTipo(tipoProj);
        const tipoBib = NORMA_TIPOS_BIB[normaTipo];
        const formattedNum = formatWithDots(normaNum);

        if (normaTipo === 'Lei') {
            return `https://www.saopaulo.sp.leg.br/cgi-bin/wxis.bin/iah/scripts/?IsisScript=iah.xis&lang=pt&format=detalhado.pft&base=legis&nextAction=search&form=A&indexSearch=^nTw^lTodos%20os%20campos&&exprSearch=${tipoBib}${formattedNum}/${normaAno}`;
        } else if (normaTipo === 'Decreto-Legislativo') {
            return `https://www.saopaulo.sp.leg.br/cgi-bin/wxis.bin/iah/scripts/?IsisScript=iah.xis&lang=pt&format=detalhado.pft&base=legis&nextAction=search&form=A&indexSearch=^nTw^lTodos%20os%20campos&&exprSearch=${tipoBib}${formattedNum}/${normaAno}`;
        } else {
            // Resolução tem formato especial
            return `https://www.saopaulo.sp.leg.br/cgi-bin/wxis.bin/iah/scripts/?IsisScript=iah.xis&lang=pt&format=detalhado.pft&base=legis&nextAction=search&form=A&indexSearch=^nTw^lTodos%20os%20campos&&exprSearch=${tipoBib}${formattedNum}/(6)*${normaAno}`;
        }
    }

    /**
     * Constrói URL para Prefeitura (apenas Leis)
     */
    function buildPrefeituraURL(normaNum) {
        const formattedNum = formatWithDots(normaNum);
        return `https://legislacao.prefeitura.sp.gov.br/busca?nr_lei=${formattedNum}`;
    }

    // =========================================
    // MÓDULO: PARSE DE REFERÊNCIA DE PROJETO (NORMAS)
    // =========================================

    /**
     * Extrai tipo, numero e ano de texto como "Projeto de Lei 396/2021"
     */
    function parseProjetoReference(projetoText) {
        if (!projetoText) return null;

        // Tenta cada prefixo conhecido (do mais longo para o mais curto)
        for (const [prefix, tipo] of Object.entries(PROJETO_TEXT_MAP)) {
            if (projetoText.startsWith(prefix)) {
                const remainder = projetoText.substring(prefix.length).trim();
                const match = remainder.match(/^(\d+)\/(\d+)/);
                if (match) {
                    return { tipo, numero: match[1], ano: match[2] };
                }
            }
        }

        // Fallback: padrão genérico número/ano
        const genericMatch = projetoText.match(/(\d+)\/(\d{4})/);
        if (genericMatch) {
            return { tipo: 'PL', numero: genericMatch[1], ano: genericMatch[2] };
        }

        return null;
    }

    /**
     * Limpa campo de revogação: remove ^t... e usa só primeira metade antes do |
     */
    function cleanRevogacao(revogacao) {
        if (!revogacao) return '';
        // Pega só a primeira parte antes do pipe
        const parts = revogacao.split(' | ');
        let text = parts[0].trim();
        // Remove sufixo ^t... (ex: ^tL14485)
        text = text.replace(/\^t\S*/gi, '').trim();
        return text;
    }

    // =========================================
    // MÓDULO: HIGHLIGHTER (GRIFO)
    // =========================================

    /**
     * Aplica highlight nos termos encontrados no texto
     */
    function highlightText(text, terms) {
        if (!text || !terms || terms.length === 0) return escapeHtml(text);

        let result = escapeHtml(text);

        // Create a single regex with capturing groups for each term: (term1)|(term2)|...
        const patterns = terms.map(term => `(${createFlexiblePattern(term.value)})`);
        const combinedPattern = patterns.join('|');
        const regex = new RegExp(combinedPattern, 'gi');

        return result.replace(regex, (...args) => {
            // args: [match, p1, p2, ..., offset, string]
            const match = args[0];

            // Find which group matched (which term index)
            // Groups start at index 1
            let termIndex = -1;
            for (let i = 1; i <= terms.length; i++) {
                if (args[i] !== undefined) {
                    termIndex = i - 1;
                    break;
                }
            }

            if (termIndex === -1) return match;

            const colorClass = termIndex < HIGHLIGHT_COLORS.length
                ? HIGHLIGHT_COLORS[termIndex]
                : 'hl-gray';

            return `<span class="${colorClass}-full">${match}</span>`;
        });

        // return result;
    }

    /**
     * Aplica highlight no campo de partido, tratando termos entre parênteses.
     * Termos entre parênteses na query (ex: "(pt)") exigem match EXATO com o partido,
     * para que "(psd)" não grife parcialmente "PSDB".
     * Termos normais passam pelo highlightText padrão.
     */
    function highlightParty(partyText, terms) {
        if (!partyText || !terms || terms.length === 0) return escapeHtml(partyText);

        const normalizedParty = normalizeText(partyText);

        // Primeiro, verifica se algum termo entre parênteses casa EXATAMENTE com o partido
        for (let i = 0; i < terms.length; i++) {
            const parenMatch = terms[i].value.match(/^\((.+)\)$/);
            if (parenMatch && normalizedParty === parenMatch[1]) {
                const colorClass = i < HIGHLIGHT_COLORS.length
                    ? HIGHLIGHT_COLORS[i]
                    : 'hl-gray';
                return `<span class="${colorClass}-full">${escapeHtml(partyText)}</span>`;
            }
        }

        // Senão, filtra os termos entre parênteses e aplica highlight normal com os demais
        const nonParenTerms = terms.filter(term => !term.value.match(/^\((.+)\)$/));
        return highlightText(partyText, nonParenTerms);
    }

    /**
     * Cria padrão de regex flexível que casa texto com ou sem acentos
     */
    function createFlexiblePattern(normalizedTerm) {
        // Mapeia cada caractere para aceitar versão acentuada ou não
        const accentMap = {
            'a': '[aáàâãä]',
            'e': '[eéèêë]',
            'i': '[iíìîï]',
            'o': '[oóòôõö]',
            'u': '[uúùûü]',
            'c': '[cç]',
            'n': '[nñ]'
        };

        // Regex para "Não Letra/Número" (exclui acentos também)
        // Isso serve para simular \b, mas permitindo que " " na query case com qualquer separador
        const NON_WORD_CHAR = '[^a-zA-Z0-9áàâãäéèêëiíìîïoóòôõöuúùûücçñ]';

        let pattern = '';
        for (const char of normalizedTerm) {
            if (char === ' ') {
                // Espaço na query significa "início/fim de linha ou caractere não-alfanumérico"
                pattern += `(?:^|$|${NON_WORD_CHAR})`;
            } else if (accentMap[char]) {
                pattern += accentMap[char];
            } else if (/\d/.test(char)) {
                // Se for dígito, aceita opcionalmente um ponto depois
                pattern += char + '[\\.]?';
            } else {
                pattern += escapeRegex(char);
            }
        }

        return pattern;
    }

    /**
     * Gera HTML dos termos com highlight para o log de resultados
     */
    function highlightTermsForLog(terms) {
        return terms.map((term, index) => {
            const colorClass = index < HIGHLIGHT_COLORS.length
                ? HIGHLIGHT_COLORS[index]
                : 'hl-gray';
            const displayTerm = term.original || term.value || term;
            return `<span class="${colorClass}-full">${escapeHtml(displayTerm.toUpperCase())}</span>`;
        }).join(' + ');
    }

    // =========================================
    // MÓDULO: RENDERIZAÇÃO
    // =========================================

    /**
     * Gera um hash numérico a partir de uma string
     */
    function stringToHash(string) {
        let hash = 0;
        if (string.length === 0) return hash;
        for (let i = 0; i < string.length; i++) {
            const char = string.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32bit integer
        }
        return hash;
    }

    /**
     * Cria elemento de card para um projeto
     */
    function createCard(row, highlightTerms, index) {
        const [tipo, numero, ano, norma, ementa, promoventes, palavrasChave] = row;

        const card = document.createElement('div');
        card.className = 'card';
        card.dataset.type = tipo;

        // Rotação fixa baseada no índice
        const rotation = CONFIG.CARD_ROTATIONS[index % CONFIG.CARD_ROTATIONS.length];
        card.style.setProperty('--card-rotation', `${rotation}deg`);
        card.style.transform = `rotate(var(--card-rotation))`;

        // ===== HEADER =====
        const header = document.createElement('div');
        header.className = 'card-header';

        // ID do projeto
        const projectId = document.createElement('div');
        projectId.className = 'project-id';

        const idRotation = '-2';
        projectId.innerHTML = `
            <span class="id-type">${highlightText(tipo, highlightTerms)}</span>
            <span class="id-number" style="transform: rotate(${idRotation}deg);">${highlightText(numero, highlightTerms)}</span>
            <span class="id-slash">/</span>
            <span class="id-year">${highlightText(ano, highlightTerms)}</span>
        `;

        // Botões de ação
        const actions = document.createElement('div');
        actions.className = 'card-actions';
        actions.innerHTML = `
            <a href="${buildSPLegisURL(tipo, numero, ano)}" class="action-btn" title="SPLegis Consulta">SPL</a>
            <span class="separator-pipe">/</span>
            <a href="${buildIntranetURL(tipo, numero, ano)}" class="action-btn" title="SPLegis Intranet">INT</a>
            <span class="separator-pipe">/</span>
            <a href="${buildBibliotecaProjetoURL(tipo, numero, ano)}" class="action-btn" title="Biblioteca">BIB</a>
        `;

        header.appendChild(projectId);
        header.appendChild(actions);
        card.appendChild(header);

        // ===== NORMA (se existir) =====
        if (norma) {
            const normaWrapper = document.createElement('div');
            normaWrapper.className = 'norma-wrapper';

            const [normaNum, normaAno] = norma.split('/');
            const normaTipo = getNormaTipo(tipo);
            const isLei = normaTipo === 'Lei';

            normaWrapper.innerHTML = `
                <div class="stamp-approved">PROMULGADO</div>
                <span class="norma-number">${highlightText(norma, highlightTerms)}</span>
                <div class="norma-links">
                    <a href="${buildPLPURL(tipo, normaNum.replace(/\./g, ''), normaAno)}" class="action-btn" title="Portal de Legislação Paulista">PLP</a>
                    <span class="separator-pipe">/</span>
                    <a href="${buildBibliotecaNormaURL(tipo, normaNum, normaAno)}" class="action-btn" title="Biblioteca">BIB</a>
                    ${isLei ? `
                        <span class="separator-pipe">/</span>
                        <a href="${buildPrefeituraURL(normaNum)}" class="action-btn" title="Prefeitura">PREF</a>
                    ` : ''}
                </div>
            `;

            card.appendChild(normaWrapper);
        }

        // ===== BODY (Ementa) =====
        const body = document.createElement('div');
        body.className = 'card-body';
        body.innerHTML = `<p class="ementa">${highlightText(ementa, highlightTerms)}</p>`;
        card.appendChild(body);

        // ===== FOOTER =====
        const footer = document.createElement('div');
        footer.className = 'card-footer';

        const metaContainer = document.createElement('div');
        metaContainer.className = 'meta-container';

        // Autores
        const authorsList = document.createElement('div');
        authorsList.className = 'authors-list';

        if (promoventes) {
            const autores = promoventes.split(' | ');
            autores.forEach(autor => {
                const authorItem = document.createElement('div');
                authorItem.className = 'author-item';

                // Separa nome e partido: "NOME (PARTIDO)"
                const match = autor.match(/^(.+?)\s*\((.+?)\)$/);
                if (match) {
                    const partyText = match[2].trim();
                    authorItem.innerHTML = `
                        <span class="author-name">${highlightText(match[1].trim(), highlightTerms)}</span>
                        <span class="author-party">${highlightParty(partyText, highlightTerms)}</span>
                    `;
                } else {
                    // Sem partido (ex: Mesa Diretora)
                    authorItem.innerHTML = `
                        <span class="author-name">${highlightText(autor.trim(), highlightTerms)}</span>
                    `;
                }

                authorsList.appendChild(authorItem);
            });
        }

        metaContainer.appendChild(authorsList);

        // Palavras-chave (se não for "SEM_PALAVRAS")
        if (palavrasChave && palavrasChave !== 'SEM_PALAVRAS') {
            const keywords = document.createElement('div');
            keywords.className = 'keywords';

            const palavras = palavrasChave.split(' | ');
            palavras.forEach(palavra => {
                const chip = document.createElement('span');
                chip.className = 'keyword-chip';
                const hash = stringToHash(palavra.trim());
                // Rotação determinística suave (entre -0.5deg e 0.5deg)
                const chipRotation = ((Math.abs(hash) % 11 - 5) / 10).toFixed(1);
                chip.style.transform = `rotate(${chipRotation}deg)`;
                chip.innerHTML = highlightText(palavra.trim(), highlightTerms);
                keywords.appendChild(chip);
            });

            metaContainer.appendChild(keywords);
        }

        footer.appendChild(metaContainer);
        card.appendChild(footer);

        return card;
    }

    /**
     * Cria elemento de card para uma norma
     */
    function createNormaCard(row, highlightTerms, index) {
        const tipo = row[0];          // LEI, ATO, ELO, DL, RES
        const numero = row[1];
        const data = row[2];          // DD/MM/YYYY
        const ementa = row[3];
        const autores = row[4];
        const publicacao = row[5];
        const projeto = row[6];
        const palavrasChave = row[7];
        const notas = row[8];
        const revogacao = row[9];

        const card = document.createElement('div');
        card.className = 'card';
        card.dataset.type = NORMA_CARD_TYPE_MAP[tipo] || 'PL';

        // Rotação fixa baseada no índice
        const rotation = CONFIG.CARD_ROTATIONS[index % CONFIG.CARD_ROTATIONS.length];
        card.style.setProperty('--card-rotation', `${rotation}deg`);
        card.style.transform = `rotate(var(--card-rotation))`;

        // ===== HEADER =====
        const header = document.createElement('div');
        header.className = 'card-header';

        const normaId = document.createElement('div');
        normaId.className = 'project-id';

        const idRotation = '-2';
        normaId.innerHTML = `
            <span class="id-type">${highlightText(tipo, highlightTerms)}</span>
            <span class="id-number" style="transform: rotate(${idRotation}deg);">${highlightText(numero, highlightTerms)}</span>
            <span class="id-year">${highlightText(data, highlightTerms)}</span>
        `;

        // Botões de ação da norma (PLP, BIB, PREF)
        const actions = document.createElement('div');
        actions.className = 'card-actions';

        // Extrair ano da data (DD/MM/YYYY)
        const dataMatch = data.match(/(\d{4})$/);
        const normaAno = dataMatch ? dataMatch[1] : '';
        const normaNumClean = numero.replace(/\./g, '');

        // Determinar tipo de norma para URLs
        let normaTipoForURL;
        if (tipo === 'LEI' || tipo === 'ELO') normaTipoForURL = 'Lei';
        else if (tipo === 'DL') normaTipoForURL = 'Decreto-Legislativo';
        else if (tipo === 'RES') normaTipoForURL = 'Resolução';
        else if (tipo === 'ATO') normaTipoForURL = 'Ato';
        else normaTipoForURL = null;

        if (normaTipoForURL) {
            const tipoPLP = NORMA_TIPOS_PLP[normaTipoForURL] || 'Lei';
            const plpURL = `https://app-plpconsulta-prd.azurewebsites.net/Forms/MostrarArquivo?TIPO=${tipoPLP}&NUMERO=${normaNumClean}&ANO=${normaAno}&DOCUMENTO=Ficha`;

            const tipoBib = NORMA_TIPOS_BIB[normaTipoForURL];
            const formattedNum = formatWithDots(numero);
            let bibURL;
            if (normaTipoForURL === 'Resolução' || normaTipoForURL === 'Ato') {
                // Resolução e Ato usam formato com (6)*ano
                bibURL = `https://www.saopaulo.sp.leg.br/cgi-bin/wxis.bin/iah/scripts/?IsisScript=iah.xis&lang=pt&format=detalhado.pft&base=legis&nextAction=search&form=A&indexSearch=^nTw^lTodos%20os%20campos&&exprSearch=${tipoBib}${formattedNum}/(6)*${normaAno}`;
            } else {
                bibURL = `https://www.saopaulo.sp.leg.br/cgi-bin/wxis.bin/iah/scripts/?IsisScript=iah.xis&lang=pt&format=detalhado.pft&base=legis&nextAction=search&form=A&indexSearch=^nTw^lTodos%20os%20campos&&exprSearch=${tipoBib}${formattedNum}/${normaAno}`;
            }

            // Apenas Lei e ELO têm link para Prefeitura
            const isLei = (tipo === 'LEI' || tipo === 'ELO');

            actions.innerHTML = `
                <a href="${plpURL}" class="action-btn" title="Portal de Legislação Paulista">PLP</a>
                <span class="separator-pipe">/</span>
                <a href="${bibURL}" class="action-btn" title="Biblioteca">BIB</a>
                ${isLei ? `
                    <span class="separator-pipe">/</span>
                    <a href="${buildPrefeituraURL(numero)}" class="action-btn" title="Prefeitura">PREF</a>
                ` : ''}
            `;
        }

        header.appendChild(normaId);
        header.appendChild(actions);
        card.appendChild(header);

        // ===== BODY (Ementa + Notas + Revogação) =====
        const body = document.createElement('div');
        body.className = 'card-body';

        let ementaHtml = highlightText(ementa, highlightTerms);

        if (notas) {
            ementaHtml += `<br><br><em>${highlightText(notas, highlightTerms)}</em>`;
        }

        const revogacaoClean = cleanRevogacao(revogacao);
        if (revogacaoClean) {
            ementaHtml += `<br><br><strong style="color: var(--color-plo);">${highlightText(revogacaoClean, highlightTerms)}</strong>`;
        }

        body.innerHTML = `<p class="ementa">${ementaHtml}</p>`;
        card.appendChild(body);

        // ===== REFERÊNCIA AO PROJETO (se preenchido) =====
        if (projeto) {
            const parsed = parseProjetoReference(projeto);
            if (parsed) {
                const anoInt = parseInt(parsed.ano);
                let actionsHtml = '';
                if (anoInt >= 1991) {
                    actionsHtml += `<a href="${buildSPLegisURL(parsed.tipo, parsed.numero, parsed.ano)}" class="action-btn" title="SPLegis Consulta">SPL</a>`;
                    actionsHtml += `<span class="separator-pipe">/</span>`;
                    actionsHtml += `<a href="${buildIntranetURL(parsed.tipo, parsed.numero, parsed.ano)}" class="action-btn" title="SPLegis Intranet">INT</a>`;
                    actionsHtml += `<span class="separator-pipe">/</span>`;
                }
                actionsHtml += `<a href="${buildBibliotecaProjetoURL(parsed.tipo, parsed.numero, parsed.ano)}" class="action-btn" title="Biblioteca">BIB</a>`;

                const projRef = document.createElement('div');
                projRef.className = 'norma-project-ref';
                projRef.innerHTML = `
                    <span class="ref-label">${highlightText(projeto, highlightTerms)}</span>
                    <div class="ref-actions">
                        ${actionsHtml}
                    </div>
                `;
                card.appendChild(projRef);
            }
        }

        // ===== FOOTER =====
        const footer = document.createElement('div');
        footer.className = 'card-footer';

        const metaContainer = document.createElement('div');
        metaContainer.className = 'meta-container';

        // Autores
        const authorsList = document.createElement('div');
        authorsList.className = 'authors-list';

        if (autores) {
            const autoresArr = autores.split(' | ');
            autoresArr.forEach(autor => {
                const authorItem = document.createElement('div');
                authorItem.className = 'author-item';
                const match = autor.match(/^(.+?)\s*\((.+?)\)$/);
                if (match) {
                    const partyText = match[2].trim();
                    authorItem.innerHTML = `
                        <span class="author-name">${highlightText(match[1].trim(), highlightTerms)}</span>
                        <span class="author-party">${highlightParty(partyText, highlightTerms)}</span>
                    `;
                } else {
                    authorItem.innerHTML = `
                        <span class="author-name">${highlightText(autor.trim(), highlightTerms)}</span>
                    `;
                }
                authorsList.appendChild(authorItem);
            });
        }

        metaContainer.appendChild(authorsList);

        // Palavras-chave
        if (palavrasChave && palavrasChave !== 'SEM_PALAVRAS') {
            const keywords = document.createElement('div');
            keywords.className = 'keywords';

            const palavras = palavrasChave.split(' | ');
            palavras.forEach(palavra => {
                const chip = document.createElement('span');
                chip.className = 'keyword-chip';
                const hash = stringToHash(palavra.trim());
                // Rotação determinística suave (entre -0.5deg e 0.5deg)
                const chipRotation = ((Math.abs(hash) % 11 - 5) / 10).toFixed(1);
                chip.style.transform = `rotate(${chipRotation}deg)`;
                chip.innerHTML = highlightText(palavra.trim(), highlightTerms);
                keywords.appendChild(chip);
            });

            metaContainer.appendChild(keywords);
        }

        footer.appendChild(metaContainer);
        card.appendChild(footer);

        return card;
    }

    /**
     * Renderiza os resultados na página
     */
    function renderResults(shouldScroll) {
        // Sempre limpa cards existentes
        const existingCards = mainContainer.querySelectorAll('.card');
        existingCards.forEach(card => card.remove());

        // Esconde campo de informações quando há resultados
        if (infoField) {
            infoField.style.display = 'none';
        }

        // Calcula fatia a renderizar baseado em currentPage
        const start = currentPage * CONFIG.RESULTS_PER_PAGE;
        const end = Math.min(start + CONFIG.RESULTS_PER_PAGE, currentResults.length);
        const slice = currentResults.slice(start, end);

        // Usa DocumentFragment para performance
        const fragment = document.createDocumentFragment();

        slice.forEach((row, index) => {
            const card = activeMode === 'normas'
                ? createNormaCard(row, currentSearchTerms, start + index)
                : createCard(row, currentSearchTerms, start + index);
            fragment.appendChild(card);
        });

        // Insere antes do container de paginação ou no final
        if (paginationContainer && paginationContainer.parentNode === mainContainer) {
            mainContainer.insertBefore(fragment, paginationContainer);
        } else {
            mainContainer.appendChild(fragment);
        }

        displayedCount = end;

        // Atualiza paginação
        updatePagination();

        // Scroll para o topo ao mudar de página
        if (shouldScroll) {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }

    /**
     * Atualiza controles de paginação
     */
    function updatePagination() {
        if (!paginationContainer) return;

        const total = currentResults.length;
        const totalPages = Math.ceil(total / CONFIG.RESULTS_PER_PAGE);

        // Se 1 página ou menos, esconde paginação
        if (totalPages <= 1) {
            paginationContainer.style.display = 'none';
            return;
        }

        paginationContainer.style.display = 'flex';
        paginationContainer.innerHTML = '';

        const current = currentPage; // 0-indexed

        // Botão anterior
        const prevBtn = document.createElement('button');
        prevBtn.className = 'prev';
        prevBtn.textContent = '<';
        prevBtn.disabled = current === 0;
        prevBtn.addEventListener('click', function () { goToPage(current - 1); });
        paginationContainer.appendChild(prevBtn);

        // Calcula quais páginas mostrar
        const pages = [];
        pages.push(0); // Primeira sempre

        const windowStart = Math.max(1, current - 1);
        const windowEnd = Math.min(totalPages - 2, current + 1);

        for (let i = windowStart; i <= windowEnd; i++) {
            pages.push(i);
        }

        if (totalPages > 1) {
            pages.push(totalPages - 1); // Última sempre
        }

        // Remove duplicatas e ordena
        const uniquePages = [...new Set(pages)].sort((a, b) => a - b);

        // Renderiza botões com reticências
        let lastPage = -1;
        uniquePages.forEach(function (page) {
            // Adiciona reticências se há gap
            if (lastPage !== -1 && page - lastPage > 1) {
                const ellipsis = document.createElement('span');
                ellipsis.className = 'ellipsis';
                ellipsis.textContent = '...';
                paginationContainer.appendChild(ellipsis);
            }

            const btn = document.createElement('button');
            btn.textContent = page + 1; // Exibe 1-indexed
            if (page === current) {
                btn.className = 'active';
            }
            btn.addEventListener('click', function () { goToPage(page); });
            paginationContainer.appendChild(btn);

            lastPage = page;
        });

        // Botão próxima
        const nextBtn = document.createElement('button');
        nextBtn.className = 'next';
        nextBtn.textContent = '>';
        nextBtn.disabled = current === totalPages - 1;
        nextBtn.addEventListener('click', function () { goToPage(current + 1); });
        paginationContainer.appendChild(nextBtn);
    }

    /**
     * Navega para uma página específica
     */
    function goToPage(page) {
        const totalPages = Math.ceil(currentResults.length / CONFIG.RESULTS_PER_PAGE);
        if (page < 0 || page >= totalPages) return;
        currentPage = page;
        renderResults(true);
        const query = parseSearchQuery(searchInput.value);
        updateResultsLog(query);
    }

    /**
     * Atualiza o log de resultados
     */
    function updateResultsLog(query) {
        // Caso de input vazio: nunca mostra "Carregando..." se não há busca
        if (!query || query.type === 'empty') {
            resultsCount.textContent = '';
            resultsTerms.textContent = '';
            return;
        }

        // Caso de carregando (só mostra se o usuário já digitou algo)
        if (!isDataLoaded && !loadError && activeMode === 'projetos') {
            resultsCount.textContent = '';
            resultsTerms.textContent = 'Carregando...';
            return;
        }
        if (!isNormasLoaded && !normasLoadError && activeMode === 'normas') {
            resultsCount.textContent = '';
            resultsTerms.textContent = 'Carregando normas...';
            return;
        }

        // Caso de erro
        if ((activeMode === 'projetos' && loadError) || (activeMode === 'normas' && normasLoadError)) {
            return; // showLoadError já tratou
        }

        // Verifica se tem termos suficientes APENAS se for busca normal
        if (query.type === 'normal') {
            // Opcional: Se quiser mostrar msg de erro no log também
            // Mas aqui geralmente já passou pelo filtro do performSearch,
            // exceto se for chamado manualmente.
            // Vamos manter simples.
            if (query.terms.length === 0) {
                resultsCount.textContent = '';
                resultsTerms.textContent = 'Digite pelo menos 3 caracteres para pesquisar';
                return;
            }
        }

        // Mostra resultados
        const total = currentResults.length;

        if (total === 0) {
            resultsCount.textContent = '';
            resultsTerms.textContent = 'Nenhum resultado encontrado';
            return;
        }

        // Formata contagem
        const modeLabel = activeMode === 'normas' ? 'norma' : 'resultado';
        const modeLabelPlural = activeMode === 'normas' ? 'normas' : 'resultados';

        if (displayedCount < total) {
            resultsCount.innerHTML = ` <strong>${total}</strong> ${modeLabelPlural}`;
        } else {
            resultsCount.innerHTML = `<strong>${total}</strong> ${total !== 1 ? modeLabelPlural : modeLabel}`;
        }

        // Formata termos com highlight
        const termsHtml = highlightTermsForLog(query.originalTerms);
        resultsTerms.innerHTML = `${termsHtml}`;
    }

    // =========================================
    // MÓDULO: CAMPO DE INFORMAÇÕES (HELP)
    // =========================================

    /**
     * Cria o campo de informações/ajuda
     */
    function createInfoField() {
        const info = document.createElement('div');
        info.className = 'info-field';
        info.innerHTML = `
            <div class="info-section">
                <p class="info-title">COMO ABRIR PROJETOS E NORMAS</p>
                <p>Para abrir, clique nos botões no canto superior direito dos cartões de resultado.</p>
                <p>Para projetos, são 3 repositórios:</p>
                <ul>
                    <li>SPLegis Consulta/SPLegis Intranet/Biblioteca da CMSP</li>
                </ul>
                <p>Para normas, em geral, são 3 repositórios:</p>
                <ul>
                    <li>PLP/Biblioteca da CMSP/Prefeitura</li>
                </ul>
                <p>Se houver norma decorrente do projeto, ou projeto que gerou a norma, também serão exibidos botões para estes.</p>
            </div>
            <div class="info-section">
                <p class="info-title">TRUQUES DE PESQUISA</p>
                <p>A pesquisa pode ser feita de forma simples, mas também é possível usar os seguintes truques para uma pesquisa avançada:</p>
                <ul>
                    <li><strong>Busca por número do projeto:</strong> Comece com a letra <code>p</code> (minúscula ou maiúscula) seguida do número. Ex: <code>p3 educ</code> encontra projetos de número 3 que contenham <code>educ</code>.</li>
                    <li><strong>Busca por número da norma:</strong> Comece com a letra <code>n</code> seguida do número. Ex: <code>n18000</code>.</li>
                    <li><strong>Para buscar apenas projetos com norma promulgada: </strong>Comece com a letra <code>n</code> (minúscula ou maiúscula) seguida de espaço. Ex: <code>n educ</code> encontra projetos que contenham <code>educ</code> e resultaram em norma.</li>
                    <li><strong>Pesquisa com aspas combinadas com espaços: </strong> Use aspas com a palavra precedida e/ou seguida de espaço para que ela seja pesquisada exatamente como escrita. Ex: <code>" obra "</code> (espaço antes e depois da palavra, separando-a das aspas) encontra projetos que contenham <code>obra</code>, mas não encontra <code>cobrança</code>. Ex2: <code>" obra"</code> (espaço antes da palavra) encontra projetos que contenham <code>obra</code> ou <code>obras</code> mas não encontra <code>manobra</code>. Obs: a mágica funciona ainda que a palavra esteja, nos campos do resultado, precedida ou seguida de pontuação, ou esteja em início de frase etc.</li>
                    <li><strong>Pesquisa por partido (o que inclui todos os vereadores do partido): </strong> Em geral, siglas que não aparecem em outras palavras já trazem o resultado esperado. Ex: <code>mdb</code>. Entretanto, algumas siglas dão muitos falsos positivos, por serem comuns dentro de outras palavras. Ex: <code>pl</code> e <code>pt</code>. Para esses casos, pesquise a sigla entre parênteses. Ex: <code>(pl)</code>.</li>
                    <li><strong>Pesquisa por tipo específico de projeto ou norma: </strong> Pesquisa simples por <code>pdl</code> dá poucos falsos positivos. Para os demais tipos, use truque de aspas com espaços explicado acima. Ex: <code>" pr "</code> (espaços separando a palavra das aspas) filtrará apenas por Projetos de Resolução.</li>
                </ul>
            </div>
            <div class="info-section">
                <p class="info-title">INFORMAÇÕES GERAIS</p>
                <p>Os resultados são ordenados cronologicamente, com os mais recentes aparecendo primeiro. Para projetos, é considerada a data de protocolo. Para normas, é considerada a data de promulgação.</p>
                <p>A base de dados dos projetos é baseada nos dados do SPLegis. Já a base de dados das normas é baseada nos dados da Biblioteca da CMSP.</p>
                <p>A pesquisa é feita em todos os campos do projeto: tipo, número, ano, ementa, palavras-chave, proponente, partido do proponente, número da norma decorrente e ano da norma decorrente. Para normas, também há os campos de "observações" e "revogações".</p>
                <p>A pesquisa ignora acentos e maiúsculas/minúsculas. Múltiplos termos são combinados com AND (ou seja, todos devem estar presentes, ainda que em campos diferentes do projeto ou norma).</p>
                <p>Busca exata: Use aspas para buscar frases exatas. Ex: <code>"plano diretor"</code> não encontra as palavras <code>plano</code> e <code>diretor</code> se estiverem separadas por outras palavras.</p>
                <p>Veja também minha ferramenta para abrir projetos e normas diretamente pelo número: <a
                        href="https://prototiposlegisla.github.io/abrir-projetos/">Link</a></p>
            </div>
            <div class="info-section">
                <p class="info-title">SOBRE A PESQUISA DE NORMAS</p>
                <p>Use o botão <strong>NORMAS</strong> acima da barra de busca para pesquisar normas promulgadas (leis, atos, resoluções, decretos legislativos e emendas à Lei Orgânica).</p>
                <p>Quando uma norma tem projeto de origem (a partir de 1991), são exibidos botões para acessar o projeto nos repositórios SPLegis e Biblioteca.</p>
            </div>
        `;
        return info;
    }

    /**
     * Mostra ou esconde o campo de informações
     */
    function toggleInfoField(show) {
        if (!infoField) return;
        infoField.style.display = show ? 'block' : 'none';
    }

    // =========================================
    // MÓDULO: BUSCA PRINCIPAL
    // =========================================

    /**
     * Executa a busca completa
     */
    function performSearch() {
        const input = searchInput.value;
        const query = parseSearchQuery(input);

        // Limpa se input vazio ou query vazia
        if (query.type === 'empty') {
            clearResults();
            toggleInfoField(true);
            updateResultsLog(query);
            return;
        }

        // Verifica tamanho mínimo APENAS para busca normal
        if (query.type === 'normal') {
            if (input.trim().length < CONFIG.MIN_SEARCH_LENGTH) {
                // Se tiver algo digitado mas for curto (ex: "PL"), mostra aviso
                if (input.trim().length > 0) {
                    clearResults();
                    resultsCount.textContent = '';
                    resultsTerms.textContent = 'Digite pelo menos 3 caracteres para pesquisar';
                    return;
                }
                // Se estiver vazio mesmo (já capturado pelo empty, mas por segurança)
                clearResults();
                toggleInfoField(true);
                updateResultsLog(query);
                return;
            }
        }

        // Se após o parse não sobrar nenhum termo válido para busca normal
        if (query.type === 'normal' && query.terms.length === 0) {
            clearResults();
            if (input.trim().length >= CONFIG.MIN_SEARCH_LENGTH) {
                resultsCount.textContent = '';
                resultsTerms.textContent = 'Nenhum termo válido para pesquisa';
            }
            return;
        }

        // Esconde info field
        toggleInfoField(false);

        // Verifica se ainda está carregando
        const dataReady = activeMode === 'projetos' ? isDataLoaded : isNormasLoaded;
        if (!dataReady) {
            updateResultsLog(query);
            return;
        }

        // Salva termos para highlight
        currentSearchTerms = query.terms || [];
        if (query.type === 'norma') {
            currentSearchTerms = [
                { value: query.normaNumber, isPhrase: false, original: query.normaNumber },
                ...(query.terms || [])
            ];
        } else if (query.type === 'project_number') {
            currentSearchTerms = [
                { value: query.projectNumber, isPhrase: false, original: query.projectNumber },
                ...query.terms
            ];
        }

        // Executa busca
        currentResults = executeSearch(query);

        // Renderiza (reset para página 0, sem scroll)
        currentPage = 0;
        renderResults(false);
        updateResultsLog(query);
    }

    /**
     * Limpa resultados e volta ao estado inicial
     */
    function clearResults() {
        currentResults = [];
        currentSearchTerms = [];
        displayedCount = 0;
        currentPage = 0;

        // Remove cards
        const cards = mainContainer.querySelectorAll('.card');
        cards.forEach(card => card.remove());

        // Esconde paginação
        if (paginationContainer) {
            paginationContainer.style.display = 'none';
        }
    }

    // =========================================
    // EVENT HANDLERS
    // =========================================

    /**
     * Handler para input na barra de busca (com debounce)
     */
    function onSearchInput() {
        clearTimeout(debounceTimer);

        debounceTimer = setTimeout(() => {
            performSearch();
        }, CONFIG.DEBOUNCE_MS);
    }

    /**
     * Handler para tecla Enter (bypass debounce)
     */
    function onSearchKeydown(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            clearTimeout(debounceTimer);
            performSearch();
            searchInput.blur(); // Fecha teclado mobile
        }
    }

    /**
     * Handler para botão limpar
     */
    function onClearClick() {
        searchInput.value = '';
        clearResults();
        toggleInfoField(true);
        updateResultsLog(null);
        searchInput.focus();
    }

    /**
     * Handler para troca de modo (projetos/normas)
     */
    function onToggleMode(e) {
        const btn = e.target.closest('.toggle-btn');
        if (!btn || btn.classList.contains('active')) return;

        const newMode = btn.dataset.mode;
        activeMode = newMode;

        // Atualiza UI do toggle
        document.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // Limpa resultados atuais
        clearResults();

        // Re-executa busca se houver input
        if (searchInput.value.trim()) {
            performSearch();
        } else {
            toggleInfoField(true);
            updateResultsLog(null);
        }
    }

    /**
     * Handler para fechar teclado ao clicar fora
     */
    function onDocumentClick(e) {
        if (!e.target.closest('.search-box') && document.activeElement === searchInput) {
            searchInput.blur();
        }
    }

    // =========================================
    // INICIALIZAÇÃO
    // =========================================



    /**
     * Configura o input de busca
     */
    function setupSearchInput() {
        searchInput.setAttribute('type', 'search');
        searchInput.setAttribute('enterkeyhint', 'search');
        searchInput.setAttribute('autocomplete', 'off');
        searchInput.setAttribute('autocorrect', 'off');
        searchInput.setAttribute('autocapitalize', 'off');
        searchInput.setAttribute('spellcheck', 'false');
    }

    /**
     * Cria container de paginação
     */
    function createPaginationContainer() {
        const div = document.createElement('div');
        div.className = 'pagination';
        div.style.display = 'none';
        mainContainer.appendChild(div);
        return div;
    }

    /**
     * Inicializa a aplicação
     */
    function init() {
        // Captura elementos DOM
        searchInput = document.querySelector('.search-input');
        clearBtn = document.querySelector('.clear-btn');
        resultsLog = document.querySelector('.results-log');
        resultsCount = document.querySelector('.results-count');
        resultsTerms = document.querySelector('.results-terms');
        mainContainer = document.querySelector('.main-container');

        if (!searchInput || !mainContainer) {
            console.error('Elementos essenciais não encontrados');
            return;
        }

        // Captura e configura toggle
        toggleContainer = document.querySelector('.search-toggle');
        if (toggleContainer) {
            toggleContainer.addEventListener('click', onToggleMode);
        }

        // Configura input
        setupSearchInput();

        // Cria campo de informações
        infoField = createInfoField();
        mainContainer.appendChild(infoField);

        // Cria container de paginação
        paginationContainer = createPaginationContainer();

        // Limpa log inicial
        resultsCount.textContent = '';
        resultsTerms.textContent = '';

        // Configura event listeners
        searchInput.addEventListener('input', onSearchInput);
        searchInput.addEventListener('keydown', onSearchKeydown);

        // Reconfigura botão limpar
        clearBtn.onclick = onClearClick;

        // Foco ao clicar no ícone
        const searchIcon = document.querySelector('.search-icon');
        if (searchIcon) {
            searchIcon.addEventListener('click', () => searchInput.focus());
        }

        // Fecha teclado ao clicar fora
        document.addEventListener('click', onDocumentClick);

        // Foco no input
        searchInput.focus();

        // Inicia carregamento de dados
        loadAllData();

        console.log('LEISP inicializado');
    }

    // =========================================
    // MÓDULO: BOTÃO VOLTAR AO TOPO
    // =========================================

    function initBackToTop() {
        const backToTopBtn = document.querySelector('.back-to-top');
        if (!backToTopBtn) return;

        // Mostra/esconde botão baseado no scroll
        function toggleBackToTop() {
            if (window.scrollY > 400) {
                backToTopBtn.classList.add('visible');
            } else {
                backToTopBtn.classList.remove('visible');
            }
        }

        // Scroll suave ao topo
        function scrollToTop() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        }

        // Event listeners
        window.addEventListener('scroll', toggleBackToTop, { passive: true });
        backToTopBtn.addEventListener('click', scrollToTop);

        // Verifica estado inicial
        toggleBackToTop();
    }

    // Aguarda DOM carregar
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            init();
            initBackToTop();
        });
    } else {
        init();
        initBackToTop();
    }

})();
