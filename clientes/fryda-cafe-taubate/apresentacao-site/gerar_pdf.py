#!/usr/bin/env python3
"""
Gera os PDFs (apresentação + proposta) da versão "site grátis" via WeasyPrint.

Use este na nuvem / Claude Code na web, onde o Playwright/Chromium não baixa.
Localmente, o `gerar-pdf.js` (Playwright) dá a maior fidelidade. A fonte de
verdade são sempre os HTMLs.

Uso:
    python gerar_pdf.py            # gera os dois
    python gerar_pdf.py apresentacao.html Apresentacao-Fryda-Site.pdf

Requer: pip install weasyprint
"""

import sys
import warnings
from pathlib import Path

try:
    from weasyprint import HTML
except ImportError:
    sys.exit("WeasyPrint não instalado. Rode: pip install weasyprint")

base = Path(__file__).resolve().parent
ALVOS = [
    ("apresentacao.html", "Apresentacao-Fryda-Site.pdf"),
    ("proposta.html", "Proposta-Fryda-Site.pdf"),
]

warnings.filterwarnings("ignore")
args = sys.argv[1:]
if len(args) >= 2:
    ALVOS = [(args[0], args[1])]

for html_name, pdf_name in ALVOS:
    html = base / html_name
    if not html.exists():
        sys.exit(f"HTML não encontrado: {html}")
    HTML(filename=str(html), base_url=str(base)).write_pdf(str(base / pdf_name))
    print(f"PDF gerado: {pdf_name}")
