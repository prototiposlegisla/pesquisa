Resumo do Projeto
	Objetivo: Criar um site estático de página única para busca em cerca de 32.000 projetos legislativos da Câmara Municipal de São Paulo, hospedado gratuitamente no GitHub Pages.
	Solução: Interface web com busca em tempo real totalmente client-side (sem backend), carregando os dados de um arquivo JSON de arrays, permitindo filtragem instantânea enquanto o usuário digita.
	Tecnologias: HTML, CSS e JavaScript vanilla (sem frameworks ou bibliotecas externas), garantindo máxima compatibilidade, leveza e simplicidade de manutenção.
	Público-alvo: servidores da Câmara, interessados em acompanhar a produção legislativa municipal. Logo, não é necessario simplificar a terminologia, para leigos.
Arquitetura
	O projeto adota uma arquitetura **Client-Side Static Application**. Não há processamento de servidor (Backend) para a renderização da interface. Toda a lógica de apresentação e manipulação de dados ocorre no navegador do cliente, consumindo uma base de dados estática em formato JSON.
	O design pattern fundamental é a **Separação de Preocupações (Separation of Concerns)**, onde estrutura (HTML), estilo (CSS), comportamento (JS) e dados (JSON) residem em camadas distintas de arquivos.
	Árvore de Diretórios
		A organização segue o padrão **"Assets-Centric"**, mantendo a raiz do projeto limpa e agrupando todos os recursos estáticos em um diretório dedicado.
		fica assim:
			/ (Raiz do Projeto)
			│
			├── index.html           # Ponto de entrada único (View/Estrutura)
			│
			├── assets/              # Repositório de recursos estáticos (Frontend)
			│   │
			│   ├── css/             # Camada de Estilização
			│   │   └── style.css    # Definições visuais e layout
			│   │
			│   ├── js/              # Camada Lógica (Controller)
			│   │   └── main.js      # Manipulação do DOM e consumo de dados
			│   │
			│   ├── data/            # Camada de Persistência (Leitura)
			│   │   └── dados.json   # Base de dados estática (ver a estrutura exata no arquivo spec-database.md)
			│   │
			│   └── img/             # Mídia e imagens do sistema
			│
			└── specs/               # Documentação e Contexto para IA
			    ├── spec-geral.md             # Visão macro e objetivos do projeto
			    ├── spec-features.md          # Lista de funcionalidades e comportamentos
			    ├── spec-database.md          # Estrutura do JSON e tipos de dados
			    └── spec-identidade-visual.md # Paleta de cores, tipografia e UX
		Definição dos Componentes
			index.html (View): Atua apenas como esqueleto semântico. Não contém lógica inline (<script>) nem estilos (<style>). É responsável por carregar os recursos da pasta assets e definir os containers onde o conteúdo dinâmico será injetado.
			assets/js/main.js (Controller): Responsável pela regra de negócio do frontend.
				Executa requisições assíncronas (fetch) para carregar o arquivo JSON.
				Processa e filtra os dados (busca nas ementas).
				Manipula o DOM para renderizar a tabela de resultados na tela.
			assets/data/dados.json (Model): Atua como um banco de dados read-only. O arquivo é baixado integralmente pelo cliente na primeira requisição, permitindo buscas instantâneas sem latência de rede subsequente.
				ver a estrutura exata no arquivo spec-database.md
			assets/css/style.css (Style): Centraliza toda a identidade visual, garantindo que o HTML permaneça agnóstico quanto à apresentação.
			specs/ (Contexto & Documentação): Contém os arquivos em Markdown que servem como "Regra da Verdade" (Single Source of Truth) para o desenvolvimento.
				spec-geral.md: Contexto amplo e propósito do software.
				spec-features.md: Detalha as funcionalidades específicas (ex: "Busca em tempo real", "Paginação", "Filtros por ano") e regras de comportamento da interface.
				spec-database.md: Schema do JSON e explicação dos campos.
				spec-identidade-visual.md: Guia de estilos (cores, fontes) para a UI.
	Hospedagem: GitHub Pages
	Github actions
		atualiza a database, conforme explicado no arquivo spec-database.md
	Fluxo de Dados
		1. O navegador carrega o `index.html` e solicita os arquivos de `assets/css` e `assets/js`.
		2. O script `main.js` inicia e dispara uma requisição `GET` para `assets/data/dados.json`.
		3. O conteúdo JSON é carregado na memória RAM do navegador.
		4. As interações do usuário (filtros, buscas) operam diretamente sobre os dados em memória, garantindo alta performance.
