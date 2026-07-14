# Identidade visual

> Como a marca MarioLucash aparece em tudo que o MazyOS gera.
> As skills de conteúdo, carrossel, proposta e slide leem esse arquivo antes de criar qualquer visual.
> Em peça de CLIENTE, espelhar a marca do cliente; este guia vale pras peças da marca própria.

---

## Cores

- **Fundo principal (dark):** `#0C0C08` (ground) · painel `#13130E`
- **Fundo claro / papel:** `#F1F0EA` · cards claros `#F8F7F2`
- **Cor de destaque / CTA:** verde `#3EA972` (escuro `#0B8A47`) · acento claro `#8FC7A6`
- **Texto principal:** `#ECEAE0` no dark · `#16160F` no claro
- **Fundo alternativo / cards:** `#181812` (dark) · `#F8F7F2` (claro)
- **Alarme (só pra marcar ausências/erros):** argila `#B23A26` (dark `#E0704F`)
- **Premium/proposta:** chocolate `#33291E` + dourado `#D8B45C` + creme `#F4EEE1`
- **Cor proibida:** gradiente arco-íris, roxo-para-azul de IA, qualquer cor "neon de template".

---

## Tipografia

- **Títulos e destaques:** **Fraunces** (serif editorial, quente) — arquivo `identidade/fontes/Fraunces.ttf`
- **Corpo, subtítulos e botões:** **Inter** — arquivo `identidade/fontes/Inter.ttf`
- **Labels / eyebrows:** Inter (ou mono `ui-monospace` no estilo terminal) em CAIXA ALTA com letter-spacing largo
- **Peso do título:** 560 (Fraunces) a 800 (Inter bold)

---

## Estilo geral

Editorial, calmo, premium. Duas vozes visuais:
- **Terminal / TUI** (fundo escuro, mono, janela de terminal, statusbar) — pra marca pessoal MarioLucash.
- **Espelho do cliente** — em proposta/auditoria, adota a paleta e o tom visual da marca do cliente.

---

## Elementos-chave

- Bordas: 1px finas
- Border-radius dos cards: 12–18px (5mm no print)
- Botões: pill (100px) ou radius 8px, verde de CTA
- Sombras: suaves e discretas (nunca pesadas)

---

## O que NUNCA fazer

- Travessão (—) no texto (regra de escrita, vale no visual também)
- Template genérico de IA, clip-art, emoji decorativo
- Gradiente arco-íris ou paleta neon
- Fonte de sistema quando a peça é impressa/PDF: embutir Fraunces + Inter

---

## Logo

- **Arquivo:** `identidade/caos-logo-02.svg` (o emaranhado dentro do círculo)
- **Também:** `caos-logo-01.svg/.png`, `caos-logo-02.png`
- **Versão pra fundo escuro:** o emaranhado em creme/dourado; embutido como `currentColor` nos HTMLs
- **Significado:** o emaranhado = dados desestruturados / o caos que o Mario organiza
- **Onde usar:** header de propostas e sites, capa (marca d'água grande), slide final de carrossel
- **Tamanho sugerido:** 30–34px em headers; grande e translúcido como textura de fundo

---

## Fontes e scripts

- Fontes da marca em `identidade/fontes/` (Fraunces.ttf, Inter.ttf)
- Gerar PDF a partir de HTML: `node scripts/html-para-pdf.js entrada.html saida.pdf`

## Observações adicionais

Peças de referência já feitas em `saidas/`: auditoria de IA, proposta (web + PDF), site pessoal (versão terminal e versão clientes).
