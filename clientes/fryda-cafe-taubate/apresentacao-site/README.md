# Apresentação & Proposta — versão "Site grátis" (primeiro cliente)

Versão **só site + Google Meu Negócio**, oferecida **de graça** como primeiro
cliente em troca de depoimento/case. Sem Ads, sem gestão de redes.

Identidade visual do **Fryda** (creme/marrom/vermelho do carrossel, Playfair +
Jost + Great Vibes + logo real do Fryda), diferente da versão com preço que usa
a marca do MarioLucash.

> A versão **com preço** (pacote R$ 5.000 com Ads, GMB e redes) continua em
> `../apresentacao/apresentacao.html`. Esta aqui é o pontapé grátis.

## Arquivos
- `apresentacao.html` — deck de 5 páginas (fonte de verdade)
- `proposta.html` — proposta formal de 1 página (fonte de verdade)
- `Apresentacao-Fryda-Site.pdf` · `Proposta-Fryda-Site.pdf` — PDFs gerados
- `fotos/` — logo do Fryda + logo MarioLucash · `fonts/` — Playfair, Jost, Great Vibes

## Gerar os PDFs
- **Local (preferido, Playwright):** `NODE_PATH="<.../node_modules>" node gerar-pdf.js`
- **Nuvem (fallback, WeasyPrint):** `python gerar_pdf.py`

Os dois HTMLs são a fonte de verdade; manter os geradores em sincronia.
