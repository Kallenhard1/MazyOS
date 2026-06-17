#!/usr/bin/env python3
"""
Gera o PDF da apresentação via WeasyPrint (roda na nuvem / Claude Code na web).

Use este quando estiver numa sessão remota, onde o Playwright/Chromium não
baixa. Localmente, o `gerar-pdf.js` (Playwright) dá a maior fidelidade.
A fonte de verdade é sempre o `apresentacao.html`.

Uso:
    python gerar_pdf.py
    python gerar_pdf.py apresentacao.html Apresentacao-Fryda-MarioLucash.pdf

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
args = sys.argv[1:]
html = Path(args[0]) if len(args) >= 1 else base / "apresentacao.html"
pdf = Path(args[1]) if len(args) >= 2 else base / "Apresentacao-Fryda-MarioLucash.pdf"

if not html.exists():
    sys.exit(f"HTML não encontrado: {html}")

warnings.filterwarnings("ignore")
HTML(filename=str(html), base_url=str(html.parent)).write_pdf(str(pdf))
print(f"PDF gerado: {pdf}")
