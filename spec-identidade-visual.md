# **Manual de Identidade Visual: SPLegis Busca**

Este documento define as diretrizes estéticas e comportamentais para a interface do SPLegis Busca. Qualquer novo elemento (popups, modais, tooltips, novos cards) deve seguir rigorosamente estes princípios para manter a coesão do universo visual **"Archival UI" / "Digital Stationery"**.

## **1. Conceito Central: "Gabinete de Arquivo"**

A interface não deve parecer um software digital moderno, mas sim um **arquivo físico bem preservado**. A metáfora visual é a de fichas de papel de alta gramatura, organizadas manualmente, com dados datilografados e anotações à mão.

**Pilares:**

*   **Tactilidade:** Nada é perfeitamente liso ou branco absoluto (#FFF).
*   **Permanência:** Fontes históricas e cores de tintas de arquivo.
*   **Imperfeição Orgânica:** Leves rotações e assimetrias que simulam o manuseio humano.
*   **Minimalismo:** Design limpo, sem modo noturno (Dark Mode não se aplica a papel).

## **2. A Física do Papel (Superfícies)**

Os elementos de container (fundo da tela, cartões, modais) devem obedecer às seguintes leis físicas:

### **2.1. Textura e Substrato**

*   **Fundo Geral:** Nunca use branco puro. Use tons de "Off-White" / Creme (#FAF9F6) ou Cinza-gelo.
*   **Granulação:** Aplique sempre uma textura de ruído PNG (`noise.png`) com `repeat` via `background-image` e `mix-blend-mode: multiply` com opacidade baixíssima (3-5%) para criar porosidade.
*   **Iridescência (Gradientes):** Os cartões não têm cor sólida. Eles possuem um gradiente linear muito sutil que varia a matiz. Use o identificador do projeto como seed para randomizar levemente a cor de fundo de cada cartão, garantindo unicidade.

### **2.2. Corte de Guilhotina (Bordas)**

*   **Contorno:** Bordas sólidas e finas (1px) em "Warm Gray" ou "Cinza Pedra" (ex: rgba(60, 50, 40, 0.08)), simulando corte intencional.
*   **Interatividade:** No hover, a borda escurece levemente.
*   **Assimetria:** Border-radius levemente imperfeito (ex: 2px) para evitar a aparência artificial de "app mobile".

### **2.3. Elevação (Layered Shadows)**

Evite sombras "drop-shadow" simples. Use o sistema de **Sombras Quentes em Camadas** para simular o "Lift" (papel levantado):

1.  **Umbra:** Sombra de contato (ex: `0 1px 2px rgba(60, 50, 40, 0.08)`).
2.  **Penumbra:** Sombra média.
3.  **Ambiente:** Sombra larga e transparente.

*Nota:* Não usar efeito de "pressão" (active) ao clicar, para não confundir com feedback de erro.

## **3. A Química da Tinta (Cores e Contraste)**

Abandone o preto digital (#000).

### **3.1. Regra de Mistura (Multiply)**

Todo texto colorido ou escuro deve ter `mix-blend-mode: multiply`. Isso simula a absorção física da tinta no papel.

### **3.2. Paleta de Tintas**

*   **Texto Principal (Warm Charcoal):** #2D2A26 ou #3E3B39. Um preto quente com base marrom/avermelhada, simulando tinta de impressora laser antiga ou Iron Gall Ink.
*   **Anotações Manuais:** Azul Caneta profundo ou Preto desbotado.
*   **Color Coding (Tipos Legislativos):** O colorido é funcional, usado apenas em rótulos e bordas.
    *   **PLO:** Tijolo / Terracota.
    *   **PDL:** Petróleo.
    *   **PR:** Verde.
    *   **PL:** Sem cor marcadora (Cor de papel envelhecido apenas).

### **3.3. Grifos (Marca-texto Realista)**

*   **Técnica:** `linear-gradient` inclinado simulando passagem manual.
*   **Altura Variável:** O grifo não cobre a linha toda; cobre apenas a parte inferior (ex: 45% a 60%), permitindo que a tinta preta do texto se sobressaia.
*   **Randomização:** A altura e inclinação do grifo variam levemente para cada palavra.

## **4. Tipografia (Estética "Academic / Technical")**

Contraste entre autoridade (serifa) e precisão técnica (monospace).

### **4.1. Conteúdo Narrativo (Ementas)**

*   **Fonte:** IM Fell Great Primer.
*   **Estilo:** Serifada, histórica. Traz a "Autoridade".

### **4.2. Dados Técnicos (Metadados)**

* **Fonte:** Special Elite  
* **Estilo:** Máquina de Escrever (Typewriter), monoespaçada, suja ("gritty").  
* **Uso:** Autores, palavras-chave, siglas de links (SPL, INT, BIB). Evoca burocracia e catalogação.  
* **Caixa:** Geralmente em UPPERCASE para dados curtos.

### **4.3. Elementos Humanos (Identificadores)**

*   **Fonte:** Reenie Beanie.
*   **Estilo:** Manuscrito grosso (marcador/caneta porosa).
*   **Specs:** Font-size 2.5rem, Line-height 0.8, Font-weight 600.
*   **Rotação:** Randômica e leve em cada cartão.

## **5. Componentes e Comportamentos**

### **5.1. Rotação Orgânica (A "Mesa de Trabalho")**

Para evitar a rigidez do grid digital, elementos podem ter rotações microscópicas e aleatórias (baseadas em seed para consistência).

* **Cards:** Rotação quase imperceptível (-0.5deg a 0.5deg).  
* **Chips e Carimbos:** Rotação leve (-2deg a 2deg).

### **5.2. Botões e Links**

* **Estilo:** Não use botões com fundo sólido ("pills"). Use apenas texto cru (Fonte Special Elite).  
* **Navegação:** Use códigos mnemônicos de 3 letras (SPL, INT) separados por barras (/).  
* **Interação:** No hover, o texto muda para a cor da tinta do projeto.

### **5.3. Status "Aprovado"**

*   **Espaçamento:** Grande vão entre o identificador e a ementa para acomodar o carimbo.

## **6. Resumo para Implementação**

| Elemento | Design |
| :---- | :---- |
| **Fundo** | Off-Wait (#FAF9F6) + Noise |
| **Texto Base** | Warm Charcoal (#2D2A26) + Multiply |
| **Sombra** | Tons Sépia/Quentes (rgba 60,50,40) |
| **Metadados** | Monospace Fina + Autores em Bold |
| **Chips** | Ghost (sem borda, sem fundo) |
| **Grifo** | Gradiente parcial (baixo), altura randomizada |
