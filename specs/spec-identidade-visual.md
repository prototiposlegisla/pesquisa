# **Manual de Identidade Visual: SPLegis Busca**

Este documento define as diretrizes estéticas e comportamentais para a interface do SPLegis Busca. Qualquer novo elemento (popups, modais, tooltips, novos cards) deve seguir rigorosamente estes princípios para manter a coesão do universo visual **"Archival UI" / "Digital Stationery"**.

## **1\. Conceito Central: "Gabinete de Arquivo"**

A interface não deve parecer um software digital moderno, mas sim um **arquivo físico bem preservado**. A metáfora visual é a de fichas de papel de alta gramatura, organizadas manualmente, com dados datilografados e anotações à mão.

**Pilares:**

* **Tactilidade:** Nada é perfeitamente liso ou branco absoluto (\#FFF).  
* **Permanência:** Fontes históricas e cores de tintas de arquivo.  
* **Imperfeição Orgânica:** Leves rotações e assimetrias que simulam o manuseio humano.

## **2\. A Física do Papel (Superfícies)**

Os elementos de container (fundo da tela, cartões, modais) devem obedecer às seguintes leis físicas:

### **2.1. Textura e Substrato**

* **Fundo Geral:** Nunca use branco puro. Use tons de creme/off-white (\#FAF9F6).  
* **Granulação:** Aplique sempre uma textura de ruído SVG (feTurbulence) via mix-blend-mode: multiply com opacidade baixíssima (3-5%) para criar porosidade.  
* **Iridescência (Gradientes):** Os cartões não têm cor sólida. Eles possuem um gradiente linear muito sutil (135deg) que varia a matiz (ex: de um bege quente para um bege frio, ou vinho pálido para vinho acinzentado). Isso simula a incidência complexa da luz sobre o papel.

### **2.2. Corte de Guilhotina (Bordas)**

* **Contorno:** Bordas sólidas e finas (1px), em cores muito discretas (rgba(0,0,0,0.05)).  
* **Assimetria:** Nunca use border-radius perfeito em todos os cantos. Use valores variados para simular o corte de papel imperfeito.  
  * *Exemplo:* border-radius: 2px 5px 2px 3px;

### **2.3. Elevação (Layered Shadows)**

Evite sombras "drop-shadow" simples. Use o sistema de **Sombras em Camadas** para simular a oclusão de ambiente:

1. **Umbra:** Sombra de contato, escura e nítida.  
2. **Penumbra:** Sombra média, difusa.  
3. **Ambiente:** Sombra larga e muito transparente.

## **3\. A Química da Tinta (Cores e Contraste)**

Não usamos cores digitais (hexadecimais chapados). Usamos o conceito de **"Deep Inks"**.

### **3.1. Regra de Mistura (Multiply)**

Todo texto escuro ou colorido sobre o papel deve ter mix-blend-mode: multiply. A tinta não flutua sobre o papel; ela é absorvida por ele, escurecendo o substrato.

### **3.2. Paleta de Tintas**

* **Texto Principal (Iron Gall):** \#1F2937 (Cinza Chumbo/Carvão). Nunca preto absoluto.  
* **Anotações Manuais (Ballpoint):** \#1a237e (Azul Caneta Bic profundo).  
* **Color Coding (Tipos Legislativos):**  
  * **PLO:** Vinho Bordeaux (\#951D36).  
  * **PDL:** Azul Maastricht (\#001C3D).  
  * **PR:** Verde Hunter (\#1A4122).  
  * **PL:** Neutro (Cinza Chumbo).

### **3.3. Grifos (Marca-texto Vintage)**

Para destacar termos de busca, use gradientes suaves que simulam canetas marca-texto.

* **Técnica:** Fundo com gradiente linear angulado (100deg) \+ mix-blend-mode: multiply. O texto mantém a cor original, sendo apenas "tingido" pelo fundo.

## **4\. Tipografia (O Stack "Arquivo Histórico")**

A tipografia é dividida por função tecnológica/histórica:

### **4.1. Conteúdo Narrativo (Ementas, Títulos Longos)**

* **Fonte:** IM Fell Great Primer  
* **Estilo:** Serifada, histórica (séc. XVII), textura de impressão rústica ("ink spread"), bordas irregulares.  
* **Uso:** Traz peso histórico e autoridade ao texto da lei.  
* **Alinhamento:** Sempre à esquerda (*Ragged Right*). Nunca justificado.

### **4.2. Dados Técnicos e Interface (Botões, Metadados)**

* **Fonte:** Special Elite  
* **Estilo:** Máquina de Escrever (Typewriter), monoespaçada, suja ("gritty").  
* **Uso:** Autores, palavras-chave, siglas de links (SPL, INT, BIB). Evoca burocracia e catalogação.  
* **Caixa:** Geralmente em UPPERCASE para dados curtos.

### **4.3. Elementos Humanos (Identificadores)**

* **Fonte:** Reenie Beanie  
* **Estilo:** Manuscrito, caneta esferográfica.  
* **Uso:** Números dos projetos. Simula que o arquivista anotou o número à mão na ficha.

## **5\. Componentes e Comportamentos**

### **5.1. Rotação Orgânica (A "Mesa de Trabalho")**

Para evitar a rigidez do grid digital, elementos podem ter rotações microscópicas e aleatórias (baseadas em seed para consistência).

* **Cards:** Rotação quase imperceptível (-0.5deg a 0.5deg).  
* **Chips e Carimbos:** Rotação leve (-2deg a 2deg).

### **5.2. Botões e Links**

* **Estilo:** Não use botões com fundo sólido ("pills"). Use apenas texto cru (Fonte Special Elite).  
* **Navegação:** Use códigos mnemônicos de 3 letras (SPL, INT) separados por barras (/).  
* **Interação:** No hover, o texto muda para a cor da tinta do projeto.

### **5.3. Palavras-Chave (Chips)**

* **Estilo:** "Datilografia Solta". Sem bordas, sem fundo. Apenas o texto flutuando no rodapé do cartão.  
* **Disposição:** Alinhadas à esquerda, com leve rotação individual em cada termo para simular a batida da máquina de escrever.

## **6\. Resumo para Implementação (Cheat Sheet)**

| Elemento | Fonte | Cor | Efeito Especial |
| :---- | :---- | :---- | :---- |
| **Ementa** | IM Fell Great Primer | Cinza Chumbo | Multiply, Ragged Right |
| **Autor/Partido** | Special Elite | Cinza Chumbo | Uppercase, Multiply |
| **Número Proj.** | Reenie Beanie | Azul Caneta | Rotação, Tamanho Grande |
| **Links** | Special Elite | Preto Suave | Siglas 3 letras, Hover Colorido |
| **Keywords** | Special Elite | Cinza Pedra | Rotação individual, Sem borda |
| **Card (Papel)** | \- | Gradiente Tints | Borda Irregular, Ruído, Sombra Layered |

## **7. Elementos Especiais: Status Legal**

### **7.1. O "Carimbo de Borracha" (Indicadores de Status)**

Para projetos convertidos em lei (APROVADO), o carimbo aparece no início da linha da norma.

*   **Posição:** Primeiro elemento da linha, à esquerda.
*   **Design:** Caixa alta, borda pesada sólida ou dupla texturizada.
*   **Química:** `mix-blend-mode: multiply` (CRUCIAL).
*   **Cor:** Vermelho Carimbo (#b91c1c).

### **7.2. Campo Norma (Lei Convertida)**

Localizado numa linha dedicada logo abaixo do Identificador do Projeto e acima da Ementa.

*   **Estrutura da Linha:** [CARIMBO] + [Número/Ano] + [Botões].
*   **Sem Prefixos:** Não usar rótulos como "Norma:" ou setas separadoras.
*   **Número/Ano:** Fonte *Reenie Beanie* (Manuscrito).
*   **Links:** Botões (PLP, BIB, PREF) na sequência, mesma estética do topo.


