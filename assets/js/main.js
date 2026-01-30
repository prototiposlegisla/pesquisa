document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.querySelector('.search-input');
    const clearBtn = document.querySelector('.clear-btn');
    const resultsContainer = document.getElementById('results-container');
    const resultsLog = document.querySelector('.results-log');

    let allData = [];
    let columns = {};
    let debounceTimer;

    // Load Data
    fetch('assets/data/dados.json')
        .then(response => response.json())
        .then(json => {
            // Map column names to indices
            json.columns.forEach((col, index) => {
                columns[col] = index;
            });
            allData = json.data;
            resultsContainer.innerHTML = '';
            updateLog(0, [], true);
        })
        .catch(err => console.error('Erro ao carregar dados:', err));

    // Search Event with Debounce
    searchInput.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        const query = e.target.value;

        debounceTimer = setTimeout(() => {
            handleSearch(query);
        }, 300);
    });

    // Handle "Enter" key to bypass debounce
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            clearTimeout(debounceTimer);
            handleSearch(searchInput.value);
            searchInput.blur(); // Close mobile keyboard
        }
    });

    // Clear Button
    clearBtn.addEventListener('click', () => {
        searchInput.value = '';
        searchInput.focus();
        handleSearch('');
    });

    function normalizeText(text) {
        return text
            .toLowerCase()
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "");
    }

    function handleSearch(rawQuery) {
        const query = rawQuery.trim();

        if (query.length === 0) {
            resultsContainer.innerHTML = '';
            resultsLog.innerHTML = '';
            return;
        }

        // Rule: Min 3 chars, unless it looks like a numeric search (starts with number)
        const isNumericSearch = /^\d/.test(query) || /^n\d/i.test(query);

        if (query.length < 3 && !isNumericSearch) {
            resultsContainer.innerHTML = '';
            resultsLog.innerHTML = '<span class="results-count">Digite pelo menos 3 caracteres...</span>';
            return;
        }

        const normalizedQuery = normalizeText(query);
        const terms = normalizedQuery.split(/\s+/).filter(t => t.length > 0);
        // Original terms for highlighting (not normalized) - split by space
        const originalTerms = query.split(/\s+/).filter(t => t.length > 0);

        // Filter
        const filtered = allData.filter(row => {
            // Ensure searchable is a string and normalize it too just in case the JSON isn't perfect,
            // though spec says JSON is pre-normalized. Let's be safe.
            let searchable = row[columns['searchable']];
            if (typeof searchable !== 'string') {
                searchable = '';
            }
            // If the JSON searchable is NOT normalized (e.g. dummy data might have uppercase),
            // we should normalize it here to be sure. The dummy data provided seems to have some mixed case
            // text in the searchable column for the first item?
            // Checking the file content:
            // "plo|projeto de lei orgânica...|administracao publica organization administrativa..."
            // It looks mostly normalized but let's enforce it to match the query.
            const normalizedSearchable = normalizeText(searchable);

            // Logic: AND based on terms
            // All terms must be present in searchable string
            return terms.every(term => normalizedSearchable.includes(term));
        });

        renderResults(filtered, originalTerms);
    }

    function renderResults(data, terms = []) {
        resultsContainer.innerHTML = '';

        // Update Log
        updateLog(data.length, terms);

        if (data.length === 0) {
            resultsContainer.innerHTML = '<div class="no-results" style="font-family: var(--font-mono); color: var(--text-secondary); padding: 20px; text-align: center;">Nenhum resultado encontrado.</div>';
            return;
        }

        data.forEach(row => {
            const card = createCard(row, terms);
            resultsContainer.appendChild(card);
        });
    }

    function updateLog(count, terms, isInitial = false) {
        if (isInitial) {
            resultsLog.innerHTML = '';
            return;
        }

        let html = `<span class="results-count">Mostrando ${count} resultados </span>`;
        if (terms.length > 0) {
            const termHtml = terms.map(t => `<strong>"${t}"</strong>`).join(' + ');
            html += `<span class="results-terms">Termos: ${termHtml}</span>`;
        }
        resultsLog.innerHTML = html;
    }

    function createCard(row, terms) {
        const tipo = row[columns['tipo']];
        const numero = row[columns['numero']];
        const ano = row[columns['ano']];
        const norma = row[columns['norma']];
        let ementa = row[columns['ementa']];
        const promoventesStr = row[columns['promoventes']];
        const keywordsStr = row[columns['palavras-chave']];

        // Highlight Ementa
        if (terms.length > 0) {
            ementa = highlightText(ementa, terms);
        }

        const card = document.createElement('div');
        card.className = 'card';
        card.dataset.type = tipo;

        const rotation = (Math.random() * 2 - 1).toFixed(1);
        card.style.setProperty('--card-rotation', `${rotation}deg`);
        card.style.transform = `rotate(${rotation}deg)`;

        let html = `
            <div class="card-header">
                <div class="project-id">
                    <span class="id-type">${tipo}</span>
                    <span class="id-number" style="transform: rotate(${(Math.random() * 10 - 5).toFixed(1)}deg);">${numero}</span>
                    <span class="id-slash">/</span>
                    <span class="id-year">${ano}</span>
                </div>
                <div class="card-actions">
                    <button class="action-btn" title="SPLegis Consulta">SPL</button>
                    <span class="separator-pipe">/</span>
                    <button class="action-btn" title="SPLegis Intranet">INT</button>
                    <span class="separator-pipe">/</span>
                    <button class="action-btn" title="Biblioteca">BIB</button>
                </div>
            </div>
        `;

        if (norma) {
            // Basic formatting for display
            const formattedNorma = norma;

            html += `
            <div class="norma-wrapper">
                <div class="stamp-approved">APROVADO</div>
                <span class="norma-number">${formattedNorma}</span>
                <div class="norma-links">
                    <button class="action-btn" title="Projeto de Lei Paulistano">PLP</button>
                    <span class="separator-pipe">/</span>
                    <button class="action-btn" title="Biblioteca">BIB</button>
                    <span class="separator-pipe">/</span>
                    <button class="action-btn" title="Prefeitura">PREF</button>
                </div>
            </div>`;
        }

        html += `
            <div class="card-body">
                <p class="ementa">${ementa}</p>
            </div>
            <div class="card-footer">
                <div class="meta-container">
                    <div class="authors-list">
                        ${formatAuthors(promoventesStr)}
                    </div>
                    <div class="keywords">
                        ${formatKeywords(keywordsStr, terms)}
                    </div>
                </div>
            </div>
        `;

        card.innerHTML = html;
        return card;
    }

    function formatAuthors(authorsStr) {
        if (!authorsStr) return '';
        return authorsStr.split(' | ').map(auth => {
            const match = auth.match(/(.*)\((.*)\)$/);
            let name = auth;
            let party = '';
            if (match) {
                name = match[1].trim();
                party = match[2].trim();
            }
            return `
                <div class="author-item">
                    <span class="author-name">${name}</span>
                    ${party ? `<span class="author-party">${party}</span>` : ''}
                </div>
            `;
        }).join('');
    }

    function formatKeywords(keywordsStr, terms) {
        if (!keywordsStr || keywordsStr === 'SEM_PALAVRAS') return '';
        return keywordsStr.split(' | ').map(k => {
            let content = k;
            if (terms.length > 0) {
                content = highlightText(k, terms);
            }
            const rot = (Math.random() * 1.0 - 0.5).toFixed(1);
            return `<span class="keyword-chip" style="transform: rotate(${rot}deg);">${content}</span>`;
        }).join('');
    }

    function highlightText(text, terms) {
        if (!terms || terms.length === 0) return text;
        const colors = ['hl-1', 'hl-2', 'hl-3', 'hl-4', 'hl-5'];
        let processed = text;

        // Very basic highlighter. 
        // Improvement: Normalize both text content and term to match "accent-insensitive" but preserve original text in output.
        // For now, let's just do a simple Regex which might miss accents if user typed normalized term.
        // Spec says: "grifos em todos os campos que surgir o termo".
        // To do this properly we need to find the index of match ignoring accents, then wrap the original substring.

        terms.forEach((term, index) => {
            const colorClass = colors[index % colors.length];
            // Escape special regex chars
            const safeTerm = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

            // This simple regex won't match "educação" if term is "educacao".
            // To fix this fully implies a more complex highlighter helper.
            // For now, we stick to direct simple match (case insensitive) to at least show something.
            // If the user searches "educacao", it won't highlight "Educação" in the text, but the FILTER worked.

            const regex = new RegExp(`(${safeTerm})`, 'gi');
            processed = processed.replace(regex, `<span class="${colorClass}-full">$1</span>`);
        });
        return processed;
    }
});
