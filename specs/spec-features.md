display
	elementos
		cabeçalho
			mensagem do autor
				no topo de tudo, na extremidade direita, só uma mensagem discreta, sem link nem nada:
					Aceito sugestões! Kauê Negrão
			card de pesquisa
			log de resultados
				apenas o número de resultados e os termos pesquisados
					eg
						345 resultados                 EDUCAÇÂO + PLANO DIRETOR + SAÚDE
					os termos pesquisados devem ser grifados com o mesmo grifo que é usado para grifar nos cards de resultados
				atualizar quando carregar mais
				se Vazio: "Nenhum resultado encontrado "
		campo de informações
			Este, só aparece quando não há nada na barra de pesquisa.
			Texto de informações:
				Para abrir os projetos, clique nos botões que ficam no canto superior direito dos cards:
				SPL: SPLegis Consulta (o SPLegis público)
				INT: SPLegis intranet
				BIB: Biblioteca
				Caso haja uma norma decorrente do projeto, haverá botões para:
				PLP
				BIB: Biblioteca
				PREF: Repositório da Prefeitura (apenas no caso de Leis)
				TRUQUES DE PESQUISA
				O site permite um "truque" que facilita a busca por projetos ou normas diretamente pelo número. Veja:
				Em regra, os termos pesquisados são buscados em todos os campos: ementa, palavras-chave, tipo de projeto, número do projeto, ano do projeto, número e ano da norma decorrente (se houver).
				Assim, ao pesquisar por: educ 3
				São encontrados todos os projetos que tenham, em algum campo, o trecho de palavra educ e o número 3. Por exemplo, o PL 234/2025, que tenha a palavra chave EDUCAÇÃO.
				Porém, e aqui entra o truque, se o usuário começar a pesquisa por um número, o site interpretará como uma busca exata por projetos que tenham aquela numeração.
				Assim, ao pesquisar por: 3 educ
				São encontrados todos os projetos que sejam de número 3, e tenham, em algum campo, o trecho de palavra educ. Por exemplo, o PL 3/2025, que tenha a palavra chave EDUCAÇÃO.
				Adicionalmente, também há um truque para pesquisar normas por seu número exato. Para isso, basta começar a pesquisa pela letra n (ou N maiúsculo), seguido do número.
				Assim, ao pesquisar por: n18000
				Será encontrado o projeto que deu origem às normas que sejam de número 18000 (que, na prática, é só a Lei 18000).
				A vantagem dessa abordagem é que, em uma mesma barra de pesquisa, é possível pesquisar tanto projetos como normas.
				INFORMAÇÕES GERAIS
				Também, possível usar aspas para pesquisa exata. Por exemplo: "plano diretor", não encontra projetos que tenham essas duas palavras sepadas.
		campo de resultados
			cards de resultado
				layout de cada card
					linha superior
						na extremidade esquerda:
							identificador do projeto
						extremidade direita:
							os ícones de abertura de links, dispostos horizontalmente
								Links externos: quero que no card de resultado haja a opção de abrir o projeto em três plataformas externas. As plataformas são o SP elege pesquisa, o SP leges intranet, e o site da biblioteca.
									no card, coloque três ícones/botões pequenos
										Sugestões de ícones:
											SPLegis Consulta (público): globo
											SPLegis Intranet: cadeado
											Portal da biblioteca: livro
										posicionamento
											no canto superior direito
									A construção dos links de cada plataforma se dada a seguinte forma:
										Exemplo para o PL 1234/2025
											do splegis consulta:
												https://splegisconsulta.saopaulo.sp.leg.br/Pesquisa/DetailsMateriaTramitacaoLegislativa?tipo=1&numero=1234&ano=2025
											do portal:
												https://www.saopaulo.sp.leg.br/cgi-bin/wxis.bin/iah/scripts/?IsisScript=iah.xis&lang=pt&format=detalhado.pft&base=proje&form=A&nextAction=search&indexSearch=^nTw^lTodos%20os%20campos&exprSearch=P=PL12342025
										Exemplo para o PDL 123/2025
											do splegis consulta:
												https://splegisconsulta.saopaulo.sp.leg.br/Pesquisa/DetailsMateriaTramitacaoLegislativa?tipo=2&numero=123&ano=2025
											do portal:
												https://www.saopaulo.sp.leg.br/cgi-bin/wxis.bin/iah/scripts/?IsisScript=iah.xis&lang=pt&format=detalhado.pft&base=proje&form=A&nextAction=search&indexSearch=^nTw^lTodos%20os%20campos&exprSearch=P=PDL1232025
										Exemplo para o PR 12/2025
											do splegis consulta:
												https://splegisconsulta.saopaulo.sp.leg.br/Pesquisa/DetailsMateriaTramitacaoLegislativa?tipo=3&numero=12&ano=2025
											do portal:
												https://www.saopaulo.sp.leg.br/cgi-bin/wxis.bin/iah/scripts/?IsisScript=iah.xis&lang=pt&format=detalhado.pft&base=proje&form=A&nextAction=search&indexSearch=^nTw^lTodos%20os%20campos&exprSearch=P=PR122025
										Exemplo para o PLO 11/2025
											do splegis consulta:
												https://splegisconsulta.saopaulo.sp.leg.br/Pesquisa/DetailsMateriaTramitacaoLegislativa?tipo=4&numero=11&ano=2025
											do portal:
												https://www.saopaulo.sp.leg.br/cgi-bin/wxis.bin/iah/scripts/?IsisScript=iah.xis&lang=pt&format=detalhado.pft&base=proje&form=A&nextAction=search&indexSearch=^nTw^lTodos%20os%20campos&exprSearch=P=PLO112025
										Para o SPLegis Intranet, o que muda me relação ao SPLegis Consulta é só o início do link. Por exemplo, o PL 700 de 2025:
											no SPLegisconsulta
												https://splegisconsulta.saopaulo.sp.leg.br/Pesquisa/DetailsMateriaTramitacaoLegislativa?tipo=1&numero=700&ano=2025
											no SPLegis interno
												https://splegis.saopaulo.sp.leg.br/Pesquisa/DetailsMateriaTramitacaoLegislativa?tipo=1&numero=700&ano=2025
								abrir links na mesma guia
								ter a opção de abrir em nova guia
									ao clicar com botão do meio do mouse
									ou ao clicar com o botão direito do mouse (ou pressionar e segurar, se for no celular) e então isso abre o menu contextual padrão do navegador
								botões mais compactos:
									códigos mnemônicos de 3 ou 4 letras (SPL, INT, BIB)
					linha seguinte
						norma decorrente
							nem sempre existe
							forma de construção dos links:
								PLP
									Lei 18.378 de 2025
										https://app-plpconsulta-prd.azurewebsites.net/Forms/MostrarArquivo?TIPO=Lei&NUMERO=18378&ANO=2025&DOCUMENTO=Ficha
									Decreto-Legislativo 81 de 2025
										https://app-plpconsulta-prd.azurewebsites.net/Forms/MostrarArquivo?TIPO=DECLEG&NUMERO=81&ANO=2025&DOCUMENTO=Ficha
									Resolução 2 de 2025
										https://app-plpconsulta-prd.azurewebsites.net/Forms/MostrarArquivo?TIPO=RESCMSP&NUMERO=2&ANO=2025&DOCUMENTO=Ficha
								Biblioteca
									Lei 18.378 de 2025
										https://www.saopaulo.sp.leg.br/cgi-bin/wxis.bin/iah/scripts/?IsisScript=iah.xis&lang=pt&format=detalhado.pft&base=legis&nextAction=search&form=A&indexSearch=^nTw^lTodos%20os%20campos&&exprSearch=LEI18.378/2025
									Decreto-Legislativo 81 de 2025
										https://www.saopaulo.sp.leg.br/cgi-bin/wxis.bin/iah/scripts/?IsisScript=iah.xis&lang=pt&format=detalhado.pft&base=legis&nextAction=search&form=A&indexSearch=^nTw^lTodos%20os%20campos&&exprSearch=DLE81/2025
									Resolução 2 de 2025
										https://www.saopaulo.sp.leg.br/cgi-bin/wxis.bin/iah/scripts/?IsisScript=iah.xis&lang=pt&format=detalhado.pft&base=legis&nextAction=search&form=A&indexSearch=^nTw^lTodos%20os%20campos&&exprSearch=RESOLUCAO*DA*CMSP*2/(6)*2025
								Prefeitura
									Lei 18.378 de 2025
										https://legislacao.prefeitura.sp.gov.br/busca?nr_lei=18.378
									Decreto-Legislativo 81 de 2025
										não há
									Resolução 2 de 2025
										não há
								a Prefeitura só tem em caso de Lei, então tem que considerar que nem sempre estará presente o botão para a Prefeitura
					linha seguinte
						a ementa
							Ementas longas:
								não truncar
					linha seguinte
						nome dos proponentes
							Colocar o nome do proponente em destaque e o partido menor embaixo. Isso cria um ritmo de leitura melhor e limpa o layout.
							então, veja que precisará de um truque para pegar o nome do proponente e separar o nome da pessoa e o nome do partido, pois está tudo junto na database
					linha inferior
						a linha dos metadados (proponente e palavras chave)
						lado a lado:
							Separador visual — barra vertical fina
							chips de palavras chave
								chips que sejam mais elegantes, então não muito arredondado
								quando não há Palavras Chave, aparece assim na database: "SEM_PALAVRAS"
									nesse caso, não mostrar nenhuma palavra-chave no card. Não mostrar nada no campo de palavras chave
						o interessante da disposição lado a lado aqui é que ambas as categorias podem ter apenas um elemento ou dezenas de elementos, então estando lado a lado eles se distribuem da forma ideal a ocupar o mínimo de espaço
							Essa elasticidade bilateral é possível porque ambos os grupos — proponentes e palavras-chave — são tratados como sequências de elementos inline dentro do mesmo container flex. Não há divisão rígida "50%/50%" ou colunas fixas.
							O separador vertical funciona como marco divisório móvel — ele simplesmente aparece entre o último autor e a primeira palavra-chave, independentemente de onde isso ocorra no fluxo. A altura da linha cresce apenas o necessário para acomodar o conteúdo real de cada projeto, evitando espaço reservado ocioso que penalizaria registros mais concisos.
						usar cor cinza claro para os metadados
							para ser mais fácil de diferenciar do texto da ementa
						linha divisória leve, que separa da ementa
						tamanho da fonte
							a fonte aqui é menor que a da ementa
							digamos que a ementa é 100%, então
								promovente
									75%
								palavras chave
									62,5%
					não precisa aparecer
						o ano separadamente
							Ie, o ano já aparece na identificação do projeto, que fica no canto superior esquerdo, então não precisa aparecer novamente
			botão de carregar mais
	Estado Inicial da Página (antes de qualquer busca)
		nenhum card de resultado exibido até a primeira busca válida
		ao abrir o site, quero que o cursor já para para a barra. Ie, a barra já é ativada
		como é uma página para uso interno, não precisa de nenhuma texto Identificando a página
		ao abrir a página, o usuário verá apenas a barra de pesquisa no topo da tela, com um texto discreto acima dela, com a mensagem do autor, e embaixo da barra o campo de informações
	existe uma feature que é o seguinte  (sticky headers): a barra de pesquisa fica fixa em cima, então mesmo que a página seja rolada, a barra fica aparecendo no topo da tela
		não quero essa feature. Quero que um rolar de página normal.
	espaçamentos
		Faça bem compacta a parte do topo da página (entorno da barra de busca, cabeçalho)
			o primeiro card de resultado deve ficar bem próximo da barra de pesquisa
		interface compacta, aproveitando bem o espaço da tela
			espaço reduzido entre os cards
	Exibição de Resultados
		Mostrar 25 primeiros resultados
			Limite de 25 resultados garante fluidez em celulares medianos
			ainda não sei quantos reusltados por página vou mostrar, então quero que fique em uma váriável única do código, para eu poder facilmente mudar e fazer testes
		ordenação dos resultados:
			apresentar na ordem da database, que já está em ordem cronológica
		O que fazer quando há >25 resultados?
			Botão "Carregar Mais"
				Quando chegar ao fim dos resultados, esconda ou desabilite o botão
		Grifo nos resultados quero que nos cards de resultado apareça grifado os trechos que correspondem a pesquisa
			grifos em todos os campos que surgir o termo
				inclusive no de identificação do projeto e da norma
			possível problema: como a busca é no searchable concatenado, você perde a informação de “onde” o match ocorreu
				possível solução:
					Para grifar corretamente , após filtrar os projetos, rode uma busca secundária nas colunas individuais para marcar os trechos. Custo baixo porque só nos projetos que passaram no filtro (máximo algumas centenas).
			estética do grifo:
				cores
					a cada termo de pesquisa uma cor diferente
						assim, ela pode bater o olho nos resultados buscando uma cor específica
						na linha que aparece em baixo da caixa de pesquisa, que informa quantos resultados foram encontrados e indica quais os termos pesquisados, grifar ali também, para o usuário já saber qual cor será usada para grifar cada termo
						usar sempre a mesma sequência de cores:
							ciano
							amarelo
							verde
							magenta
							laranja
							roxo
							vermelho
							marrom
							a partir daí, faça todos os grifos cinza
			não grifar:
				palavras com menos de 3 letras
					exceto se
						dentro de expressão entre aspas duplas, pois aí a expressão inteira será grifada como um bloco só
						ou no contexto de uma pesquisa numérica, caso em que será grifado apenas o número do projeto ou norma
			atenção para evitar problemas com:
				Consistência entre normalização e grifo
					Problema:
						- A busca ocorre sobre texto normalizado (sem acento, lowercase)
						- O grifo precisa ocorrer sobre o texto original
						- Risco de:
							* grifar trecho errado
							* quebrar palavras com acentos
				Caracteres Especiais: Regex pode quebrar com caracteres especiais nos termos
				atenção para problema que observei em testes: quando grifa uma substring, cria um espaço entre a substring grifada e o resto da palavra
Busca
	Campo de texto livre que busca em todos campos simultaneamente. Os campos estarão concatenados na coluna searchable, que onde a busca acontece efetivamente
	ignora acentos, case etc
		Case-insensitive (ignora maiúsculas/minúsculas)
		Normalizar acentos: quero que a pesquisa independa da presença de acentos
	Debounce de 300ms (só busca depois que parar de digitar)
		Debounce: reinicie o timer a cada tecla; só execute a busca quando parar.
		Bypass do Debounce no "Enter":
			O debounce de 300ms é ótimo para quem está digitando, mas se o usuário digitar rápido e bater a tecla Enter, ele espera uma resposta imediata.
			Sugestão: Adicione um listener para a tecla Enter (ou "Ir" no mobile) que cancela o timer do debounce e chama a função de busca instantaneamente. Isso dá uma sensação de "snappiness" (rapidez).
	Busca apenas após usuário digitar 3+ caracteres
		exceto se busca numérica
		A contagem de 3 caracteres deve ser após trim() e removendo aspas (ou contar o conteúdo “efetivo”).
		Se o usuário apagar para menos de 3, limpe os resultados imediatamente (estado “pronto para buscar”).
		se, após o debounce, houver menos de 3 caracteres na pesquisa (e não caracterizar uma pesquisa numérica), então, no log de resultados exibir a mensagem "Digite pelo menos 3 caracteres para pesquisar"
	Busca nativa com .includes() é suficiente para 31k registros
	se o usuário digita Múltiplos Termos
		eg, digita:
			transporte mobilidade 2024
		a pesquisa é tipo AND. Mostra só projetos que contêm TODOS os termos
		Cada termo pode estar em colunas diferentes
		a ordem dos termos não importa
			ou seja
				se pesquisa: aplicativo transporte
				encontra se hover o texto: transporte por aplicativo
	Busca por substring
		termo parcial encontra palavra completa
		- Exemplo: "educ" encontra "educação", "educacional"
	Botão de Limpar Busca
		Limpa campo de busca
		Remove resultados
		Volta ao estado inicial
		Útil para mobile (evita apagar manualmente)
		ao clicar em LIMPAR, deve o foco ir para a caixa de pesquisa
			para que o usuário já possa começar a digitar novamente, sem precisar clicar na barra novamente
	Controle do Teclado Virtual (Mobile)
		Em celulares, o teclado ocupa metade da tela. Se o usuário tocar em "Pesquisar/Ir", o teclado deve fechar para mostrar os resultados.
			Sugestão: Use input type="search" e enterkeyhint="search". Ao detectar o evento de submit/enter, invoque .blur() no campo de input para esconder o teclado automaticamente.
		também, ao clicar na tela, fora do teclado (e fora da barra), o teclado deve fechar, o toque na tela indica que o usuário quer olhar os resultados, então é bom o teclado sair da frente, para abrir mais espaço
	truque: pesquisa numérica de projetos e normas.
		descrição:
			O site permite um "truque" que facilita a busca por projetos ou normas diretamente pelo número. Veja:
			Em regra, os termos pesquisados são buscados em todos os campos: ementa, palavras-chave, tipo de projeto, número do projeto, ano do projeto, número e ano da norma decorrente (se houver).
			Assim, ao pesquisar por: educ 3
			São encontrados todos os projetos que tenham, em algum campo, o trecho de palavra educ e o número 3. Por exemplo, o PL 234/2025, que tenha a palavra chave EDUCAÇÃO.
			Porém, e aqui entra o truque, se o usuário começar a pesquisa por um número, o site interpretará como uma busca exata por projetos que tenham aquela numeração.
			Assim, ao pesquisar por: 3 educ
			São encontrados todos os projetos que sejam de número 3, e tenham, em algum campo, o trecho de palavra educ. Por exemplo, o PL 3/2025, que tenha a palavra chave EDUCAÇÃO.
			Adicionalmente, também há um truque para pesquisar normas por seu número exato. Para isso, basta começar a pesquisa pela letra n (ou N maiúsculo), seguido do número.
			Assim, ao pesquisar por: n18000
			Será encontrado o projeto que deu origem às normas que sejam de número 18000 (que, na prática, é só a Lei 18000).
	Parsing da query com aspas + múltiplos termos: é a parte mais propensa a bugs. Teste exaustivamente com casos edge (aspas no meio, múltiplas frases, aspas não fechadas, termos com aspas dentro — raro).
Performance
	Renderização client-side (JavaScript nativo, sem bibliotecas externas necessárias)
	enquanto carrega as databases, mostrar indicador de carregamento?
		não mostrar e já permitir ao usuário ir digitando
			ie, tentar aproveitar os segundos que o usuário leva para digitar para concluir o carregamento das databases
			então, a sistemática é:
				usuário abre a página
					já começa o carregamento da database
					não é apresentada nenhuma mensagem de "carregando..." ou algo assim. A aparência é de que já está tudo pronto para usar.
					o usuário já pode interagir normalmente com a página
				usuário digita na barra de pesquisa
				a pesquisa é acionada
					ie,
						o usuário digitou o número mínimo de caracteres ou iniciou com uma pesquisa numérica
						e deu o tempo de debounce
				se
					as bases já estão carregadas:
						segue normalmente com a pesquisa
					as bases não estão carregadas:
						apresenta uma mensagem de "Carregando..."
							a mensagem aparece no log de resultados
	Cache do JSON
		Problema
			- A cada reload da página, o navegador baixa novamente ~2–3MB de dados
			- Impacto direto em tempo de carregamento e consumo de banda
		Estratégia Geral
			- Persistir os dados no navegador do usuário
			- Reutilizar dados já carregados e processados em visitas futuras
			- Invalidar automaticamente o cache quando o JSON for atualizado
		Solução: Cache HTTP padrão (Nativo do Navegador).
			O navegador gerencia automaticamente a verificação de arquivos atualizados via ETags e Last-Modified fornecidos pelo GitHub Pages.
			Se o arquivo não mudou no servidor (ex: histórico antigo), o servidor retorna 304 Not Modified (0 bytes de download), e o navegador usa a cópia local instantaneamente.
			Se o arquivo mudou (ex: atual.json), o navegador baixa a nova versão automaticamente.
	Tratamento de Erros de Carregamento
		Fallback:
			Se fetch falhar → mensagem de erro amigável + botão “Tentar novamente”.
				No erro final: mensagem "Erro ao carregar dados. Verifique sua conexão ou tente novamente." + botão "Recarregar" que chama a função de load novamente.
