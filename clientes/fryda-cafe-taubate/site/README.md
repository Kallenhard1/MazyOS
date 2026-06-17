# Proposta Fryda Café — template HTML → PDF

Template de proposta comercial (padrão StarCad/Mazzeo IA) adaptado pra
marca do Fryda Café. Editável em HTML, exportável em PDF com um comando.

## Arquivos

- `proposta.html` — o template (6 páginas A4). É só editar esse arquivo.
- `gerar_pdf.py` — converte o HTML em PDF.
- `fonts/` — fontes embutidas no PDF (Playfair Display, Jost, Great Vibes).
- `proposta.pdf` — saída gerada pelo script.
- `index.html` / `en.html` — mockups do site do Fryda (separados da proposta).

## Como gerar o PDF

Instalar o WeasyPrint uma vez:

```bash
pip install weasyprint
```

Gerar o PDF:

```bash
python gerar_pdf.py                 # proposta.html -> proposta.pdf
python gerar_pdf.py outro.html      # outro.html    -> outro.pdf
python gerar_pdf.py in.html out.pdf # nomes custom
```

## Reaproveitar pra outro cliente

1. Copiar `proposta.html` pra `propostas/<Cliente>.html`
2. Trocar nome, diagnóstico, pilares, preços e contato no HTML
3. Rodar `python gerar_pdf.py propostas/<Cliente>.html`

> Dica de manutenção: as fontes são referenciadas por caminho relativo
> (`fonts/...`) no `@font-face`, então o PDF sempre sai com a tipografia
> certa, em qualquer máquina, sem depender de internet.
