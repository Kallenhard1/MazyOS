"""Geração de PDF via Chromium (Playwright) — o mesmo motor das skills do MazyOS
(/carrossel, proposta, apresentação). Renderiza o HTML real no navegador, então
flexbox, grid, web fonts e cores de fundo saem com qualidade de impressão (o que
o weasyprint/xhtml2pdf não davam).

Requer Node.js + a dependência `playwright` instalada em `plataforma/`
(`npm install` lá dentro) e o Chromium baixado uma vez
(`npx playwright install chromium`). Se o Node não estiver disponível, cai pro
xhtml2pdf (puro Python) como último recurso. Devolve (ok, engine).
"""
import shutil
import subprocess
import tempfile
from pathlib import Path

_RENDER = Path(__file__).resolve().parent / "pdf_render.js"


def _via_playwright(html, destino, base_url):
    """Renderiza via Node + Playwright. O HTML vai pra um arquivo temporário;
    quando há base_url (uma pasta), grava o temporário lá dentro pra que caminhos
    relativos (fonts/, imagens) resolvam via file://."""
    node = shutil.which("node")
    if not node or not _RENDER.exists():
        return False

    if base_url:
        tmp = Path(base_url) / "._pdf_tmp.html"
    else:
        f = tempfile.NamedTemporaryFile(
            "w", suffix=".html", delete=False, encoding="utf-8")
        f.close()
        tmp = Path(f.name)

    # Caminhos absolutos: o Node roda com cwd em servicos/, então passar
    # relativos gravaria o PDF no lugar errado.
    tmp = tmp.resolve()
    destino = Path(destino).resolve()

    try:
        tmp.write_text(html, encoding="utf-8")
        res = subprocess.run(
            [node, str(_RENDER), str(tmp), str(destino)],
            cwd=str(_RENDER.parent),
            capture_output=True, text=True, timeout=120,
        )
        return (res.returncode == 0
                and destino.exists() and destino.stat().st_size > 0)
    except Exception:  # noqa: BLE001
        return False
    finally:
        try:
            tmp.unlink()
        except OSError:
            pass


def gerar(html, destino, base_url=None):
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)

    # 1) Playwright/Chromium — qualidade de navegador (motor das skills)
    if _via_playwright(html, destino, base_url):
        return True, "playwright"

    # 2) xhtml2pdf — fallback puro Python, sem libs nativas
    try:
        from xhtml2pdf import pisa
        with open(destino, "wb") as fp:
            res = pisa.CreatePDF(html, dest=fp)
        if not res.err and destino.exists() and destino.stat().st_size > 0:
            return True, "xhtml2pdf"
    except Exception:  # noqa: BLE001
        pass

    return False, ""
