"""Instagram (marketing próprio). A plataforma NÃO cria o conteúdo — isso é
trabalho das skills do Claude Code (/carrossel, /publicar-tema, /aprovar-post).
Aqui a gente organiza a fila de temas, entrega o prompt pronto pra rodar no
terminal (handoff) e mostra o conteúdo que as skills já geraram.
"""
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILA = ROOT / "marketing" / "instagram-fila.json"
CONTEUDO = ROOT / "marketing" / "conteudo"
IMG_EXT = {".png", ".jpg", ".jpeg", ".webp"}


def ler_fila():
    if not FILA.exists():
        return []
    try:
        return json.loads(FILA.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return []


def _salvar(itens):
    FILA.parent.mkdir(parents=True, exist_ok=True)
    FILA.write_text(json.dumps(itens, ensure_ascii=False, indent=2), encoding="utf-8")


def add_tema(tema):
    tema = (tema or "").strip()
    if tema:
        itens = ler_fila()
        itens.insert(0, {
            "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
            "tema": tema, "criado": datetime.now().strftime("%d/%m/%Y")})
        _salvar(itens)
    return fila_para_tela()


def remover(item_id):
    _salvar([i for i in ler_fila() if i.get("id") != item_id])
    return fila_para_tela()


def prompt_carrossel(tema):
    return (f"Cria um carrossel pro Instagram sobre: {tema}. Segue a identidade "
            "(identidade/design-guide.md — preto/creme/âmbar) e o tom de "
            "_memoria/preferencias.md (direto, caloroso). Legenda pronta no final.")


def prompt_completo(tema):
    return f"/publicar-tema {tema}"


def fila_para_tela():
    itens = ler_fila()
    for i in itens:
        i["p_carrossel"] = prompt_carrossel(i["tema"])
        i["p_completo"] = prompt_completo(i["tema"])
    return itens


def listar_conteudo():
    """Pastas geradas pelas skills em marketing/conteudo/, com as imagens."""
    if not CONTEUDO.exists():
        return []
    out = []
    for d in sorted(CONTEUDO.iterdir(), reverse=True):
        if not d.is_dir():
            continue
        arqs = [p for p in sorted(d.rglob("*")) if p.is_file()]
        imgs = [p.relative_to(ROOT).as_posix() for p in arqs
                if p.suffix.lower() in IMG_EXT]
        outros = [p.relative_to(ROOT).as_posix() for p in arqs
                  if p.suffix.lower() not in IMG_EXT]
        out.append({"nome": d.name, "imgs": imgs, "outros": outros})
    return out
