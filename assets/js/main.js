/**
 * LEISP - Main JavaScript
 * Site de busca de projetos legislativos da Câmara Municipal de São Paulo
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
        DATA_FILES: [
            './dados/atual.json',
            './dados/recente.json',
            './dados/medio.json',
            './dados/historico-a.json',
            './dados/historico-b.json'
        ],
        CARD_ROTATIONS: [-0.4, 0.3, -0.2, 0.5, -0.3, 0.2, -0.5, 0.4]
    };

    // Mapeamento de tipos de projeto para códigos da URL
    const TYPE_CODES = { 'PL': 1, 'PDL': 2, 'PR': 3, 'PLO': 4 };

    // Mapeamento de tipos de norma para PLP
    const NORMA_TIPOS_PLP = {
        'Lei': 'Lei',
        'Decreto-Legislativo': 'DECLEG',
        'Resolução': 'RESCMSP'
    };

    // Mapeamento de tipos de norma para Biblioteca
    const NORMA_TIPOS_BIB = {
        'Lei': 'LEI',
        'Decreto-Legislativo': 'DLE',
        'Resolução': 'RESOLUCAO*DA*CMSP*'
    };

    // Sequência de cores para highlight (classes CSS)
    // Ordem: ciano, amarelo, verde, magenta, laranja
    const HIGHLIGHT_COLORS = [
        'hl-1', // ciano
        'hl-2', // amarelo
        'hl-3', // verde
        'hl-4', // magenta
        'hl-5', // laranja
        'hl-6', // marrom (era roxo)
        'hl-7', // vermelho
        'hl-8'  // roxo (era marrom)
    ];

    // =========================================
    // ESTADO
    // =========================================

    let allData = [];
    let isDataLoaded = false;
    let loadError = false;
    let currentResults = [];
    let displayedCount = 0;
    let currentSearchTerms = [];
    let debounceTimer = null;

    // =========================================
    // ELEMENTOS DOM
    // =========================================

    let searchInput, clearBtn, resultsLog, resultsCount, resultsTerms, mainContainer;
    let loadMoreBtn, infoField;

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
            .trim();
    }

    /**
     * Escapa caracteres especiais para uso em regex
     */
    function escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    // =========================================
    // MÓDULO: CARREGAMENTO DE DADOS
    // =========================================

    /**
     * Carrega todos os arquivos JSON em paralelo
     */
    async function loadAllData() {
        try {
            const responses = await Promise.all(
                CONFIG.DATA_FILES.map(file => fetch(file))
            );

            // Verifica se todas as respostas foram OK
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
     * Extrai termos e frases entre aspas do input
     */
    function parseTermsFromInput(input) {
        const normalized = [];
        const original = [];
        let remaining = input;

        // Extrai frases entre aspas
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

        // Extrai termos individuais restantes
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
                    return query.terms.every(term => searchable.includes(term.value));
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
                    return query.terms.every(term => searchable.includes(term.value));
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
            return query.terms.every(term => searchable.includes(term.value));
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
    // MÓDULO: HIGHLIGHTER (GRIFO)
    // =========================================

    /**
     * Aplica highlight nos termos encontrados no texto
     */
    function highlightText(text, terms) {
        if (!text || !terms || terms.length === 0) return text;

        let result = text;

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

            // Altura variável para efeito marca-texto
            const height = 40 + Math.random() * 20;

            return `<span class="${colorClass}-full" style="--hl-height: ${height.toFixed(0)}%">${match}</span>`;
        });

        return result;
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

        let pattern = '';
        for (const char of normalizedTerm) {
            if (accentMap[char]) {
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
            return `<span class="${colorClass}-full" style="--hl-height: 50%">${displayTerm.toUpperCase()}</span>`;
        }).join(' + ');
    }

    // =========================================
    // MÓDULO: RENDERIZAÇÃO
    // =========================================

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

        const idRotation = (Math.random() * 8 - 4).toFixed(0);
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
                    authorItem.innerHTML = `
                        <span class="author-name">${highlightText(match[1].trim(), highlightTerms)}</span>
                        <span class="author-party">${highlightText(match[2].trim(), highlightTerms)}</span>
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
                const chipRotation = (Math.random() * 1 - 0.5).toFixed(1);
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
    function renderResults(append = false) {
        if (!append) {
            // Remove cards existentes (exceto elementos fixos)
            const existingCards = mainContainer.querySelectorAll('.card');
            existingCards.forEach(card => card.remove());
            displayedCount = 0;
        }

        // Esconde campo de informações quando há resultados
        if (infoField) {
            infoField.style.display = 'none';
        }

        // Calcula fatia a renderizar
        const start = displayedCount;
        const end = Math.min(start + CONFIG.RESULTS_PER_PAGE, currentResults.length);
        const slice = currentResults.slice(start, end);

        // Usa DocumentFragment para performance
        const fragment = document.createDocumentFragment();

        slice.forEach((row, index) => {
            const card = createCard(row, currentSearchTerms, displayedCount + index);
            fragment.appendChild(card);
        });

        // Insere antes do botão "Carregar Mais" ou no final
        if (loadMoreBtn && loadMoreBtn.parentNode === mainContainer) {
            mainContainer.insertBefore(fragment, loadMoreBtn);
        } else {
            mainContainer.appendChild(fragment);
        }

        displayedCount = end;

        // Atualiza botão "Carregar Mais"
        updateLoadMoreButton();
    }

    /**
     * Atualiza visibilidade do botão "Carregar Mais"
     */
    function updateLoadMoreButton() {
        if (!loadMoreBtn) return;

        if (currentResults.length > displayedCount) {
            loadMoreBtn.style.display = 'block';
            loadMoreBtn.disabled = false;
        } else {
            loadMoreBtn.style.display = 'none';
        }
    }

    /**
     * Atualiza o log de resultados
     */
    function updateResultsLog(query) {
        // Caso de carregando
        if (!isDataLoaded && !loadError) {
            resultsCount.textContent = '';
            resultsTerms.textContent = 'Carregando...';
            return;
        }

        // Caso de erro
        if (loadError) {
            return; // showLoadError já tratou
        }

        // Caso de input vazio ou muito curto (se não for busca numérica/norma)
        if (!query || query.type === 'empty') {
            resultsCount.textContent = '';
            resultsTerms.textContent = '';
            return;
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
        if (displayedCount < total) {
            resultsCount.innerHTML = ` <strong>${total}</strong> resultados`;
        } else {
            resultsCount.innerHTML = `<strong>${total}</strong> resultado${total !== 1 ? 's' : ''}`;
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
                <p class="info-title">COMO ABRIR PROJETOS</p>
                <p>Para abrir os projetos, clique nos botões no canto superior direito dos cards de resultado. São 3 repositórios:</p>
                <ul>
                    <li>SPLegis Consulta/SPLegis Intranet/Biblioteca</li>
                </ul>
                <p>Caso haja uma norma decorrente do projeto, também haverá botões próximos ao número da norma:</p>
                <ul>
                    <li>PLP/Biblioteca/Prefeitura</li>
                </ul>
            </div>
            <div class="info-section">
                <p class="info-title">TRUQUES DE PESQUISA</p>
                <p>O site permite truques que facilitam a busca por projetos ou normas diretamente pelo número:</p>
                <ul>
                    <li><strong>Busca por número do projeto:</strong> Comece com a letra <code>p</code> (minúscula ou maiúscula) seguida do número. Ex: <code>p3 educ</code> encontra projetos de número 3 que contenham "educ".</li>
                    <li><strong>Busca por número da norma:</strong> Comece com a letra <code>n</code> seguido do número. Ex: <code>n18000</code>.</li>
                    <li><strong>Para buscar apenas projetos com norma promulgada: </strong>Comece com a letra <code>n</code> (minúscula ou maiúscula) seguida de espaço. Ex: <code>n educ</code> encontra projetos que contenham "educ" e viraram norma.</li>
                </ul>
            </div>
            <div class="info-section">
                <p class="info-title">INFORMAÇÕES GERAIS</p>
                <p>Os resultados são ordenados cronologicamente, considerando a data de protocolo, com os projetos mais recentes aparecendo primeiro.</p>
                <p>A pesquisa é feita em todos os campos do projeto: tipo, número, ano, ementa, palavras-chave, proponente, partido do proponente, número da norma decorrente e ano da norma decorrente.</p>
                <p>A pesquisa ignora acentos e maiúsculas/minúsculas. Múltiplos termos são combinados com AND (ou seja, todos devem estar presentes, ainda que em campos diferentes do projeto).</p>
                <p>Busca exata: Use aspas para buscar frases exatas. Ex: <code>"plano diretor"</code> não encontra as palavras <code>plano</code> e <code>diretor</code> separadas por outras palavras.</p>
                <p>Veja também minha ferramenta para abrir projetos e normas diretamente pelo número: <a
                        href="https://prototiposlegisla.github.io/abrir-projetos/">Link</a></p>
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
        if (!isDataLoaded) {
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

        // Renderiza
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

        // Remove cards
        const cards = mainContainer.querySelectorAll('.card');
        cards.forEach(card => card.remove());

        // Esconde botão carregar mais
        if (loadMoreBtn) {
            loadMoreBtn.style.display = 'none';
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
     * Handler para botão carregar mais
     */
    function onLoadMoreClick() {
        renderResults(true);
        const query = parseSearchQuery(searchInput.value);
        updateResultsLog(query);
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
     * Cria botão "Carregar Mais"
     */
    function createLoadMoreButton() {
        const btn = document.createElement('button');
        btn.className = 'load-more-btn';
        btn.textContent = '[carregar mais]';
        btn.style.display = 'none';
        btn.addEventListener('click', onLoadMoreClick);
        mainContainer.appendChild(btn);
        return btn;
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



        // Configura input
        setupSearchInput();

        // Cria campo de informações
        infoField = createInfoField();
        mainContainer.appendChild(infoField);

        // Cria botão carregar mais
        loadMoreBtn = createLoadMoreButton();

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
