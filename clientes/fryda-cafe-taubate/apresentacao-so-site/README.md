# Apresentação & Proposta — versão "Só site" (sem Google Meu Negócio)

Versão **só site**, oferecida **de graça** como primeiro cliente em troca de
depoimento/case. Sem Google Meu Negócio, sem Ads, sem gestão de redes. O foco é
uma coisa só, bem feita: a casa digital do Fryda no ar.

Identidade visual do **Fryda** (creme/marrom/vermelho do carrossel, Playfair +
Jost + Great Vibes + logo real do Fryda).

> Variações irmãs:
> - `../apresentacao-site/` — versão grátis **site + Google Meu Negócio**
> - `../apresentacao/` — versão **com preço** (pacote R$ 5.000 com Ads, GMB e redes)

## Arquivos
- `apresentacao.html` — deck de 5 páginas (fonte de verdade)
- `proposta.html` — proposta formal de 1 página (fonte de verdade)
- `Apresentacao-Fryda-Site.pdf` · `Proposta-Fryda-Site.pdf` — PDFs gerados
- `fotos/` — logo do Fryda + logo MarioLucash · `fonts/` — Playfair, Jost, Great Vibes

## Gerar os PDFs
- **Local (preferido, Playwright):** `NODE_PATH="<.../node_modules>" node gerar-pdf.js`
- **Nuvem (fallback, WeasyPrint):** `python gerar_pdf.py`

Os dois HTMLs são a fonte de verdade; manter os geradores em sincronia.
