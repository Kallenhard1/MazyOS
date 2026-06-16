"""Geração de PDF resiliente. Tenta o weasyprint (melhor qualidade, mas precisa
do runtime GTK nativo); se não der, cai pro xhtml2pdf (100% Python, roda no
Windows sem libs nativas). Devolve (ok, engine). O HTML passado deve ser
amigável ao xhtml2pdf (layout em tabelas, sem flexbox) pra render bem no fallback.
"""
from pathlib import Path


def gerar(html, destino, base_url=None):
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)

    # 1) weasyprint — qualidade máxima, se o GTK estiver instalado
    try:
        from weasyprint import HTML
        HTML(string=html, base_url=base_url).write_pdf(str(destino))
        return True, "weasyprint"
    except Exception:  # noqa: BLE001
        pass

    # 2) xhtml2pdf — fallback puro Python
    try:
        from xhtml2pdf import pisa
        with open(destino, "wb") as f:
            res = pisa.CreatePDF(html, dest=f)
        if not res.err and destino.exists() and destino.stat().st_size > 0:
            return True, "xhtml2pdf"
    except Exception:  # noqa: BLE001
        pass

    return False, ""
