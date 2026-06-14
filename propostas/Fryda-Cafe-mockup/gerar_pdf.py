#!/usr/bin/env python3
"""
Gera o PDF da proposta a partir do template HTML.

Uso:
    python gerar_pdf.py                      # usa proposta.html -> proposta.pdf
    python gerar_pdf.py outro.html           # converte outro.html -> outro.pdf
    python gerar_pdf.py entrada.html saida.pdf

Requisitos:
    pip install weasyprint

As fontes ficam na pasta fonts/ e são referenciadas por caminho relativo
no @font-face do HTML, então o WeasyPrint as embute no PDF automaticamente.
"""

import sys
import warnings
from pathlib import Path

try:
    from weasyprint import HTML
except ImportError:
    sys.exit(
        "WeasyPrint não está instalado.\n"
        "Instale com:  pip install weasyprint"
    )


def gerar_pdf(html_path: Path, pdf_path: Path) -> None:
    if not html_path.exists():
        sys.exit(f"Arquivo HTML não encontrado: {html_path}")

    # base_url = pasta do HTML, pra resolver fonts/ e imagens relativas
    warnings.filterwarnings("ignore")
    HTML(filename=str(html_path), base_url=str(html_path.parent)).write_pdf(
        str(pdf_path)
    )
    print(f"PDF gerado: {pdf_path}")


def main() -> None:
    base = Path(__file__).resolve().parent
    args = sys.argv[1:]

    if len(args) == 0:
        html_path = base / "proposta.html"
        pdf_path = base / "proposta.pdf"
    elif len(args) == 1:
        html_path = Path(args[0]).resolve()
        pdf_path = html_path.with_suffix(".pdf")
    else:
        html_path = Path(args[0]).resolve()
        pdf_path = Path(args[1]).resolve()

    gerar_pdf(html_path, pdf_path)


if __name__ == "__main__":
    main()
