"""Conteúdo & Redes (Fase 4). Evolui o instagram.py: fila ÚNICA com `alvo`
(próprio ou um cliente) e `status` (rascunho → aprovado → publicado).

A plataforma NÃO cria nem publica conteúdo — isso é das skills do Claude Code
(/carrossel, /publicar-tema, /aprovar-post). Aqui a gente organiza a fila,
entrega o prompt pronto (handoff) e mostra o que as skills já geraram.
"""
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILA = ROOT / "marketing" / "conteudo-fila.json"
FILA_ANTIGA = ROOT / "marketing" / "instagram-fila.json"  # migra a fila do Insta
CONTEUDO_PROPRIO = ROOT / "marketing" / "conteudo"
CLIENTES = ROOT / "clientes"
IMG_EXT = {".png", ".jpg", ".jpeg", ".webp"}
STATUSES = ["rascunho", "aprovado", "publicado"]
ROTULO_STATUS = {"rascunho": "Rascunho", "aprovado": "Aprovado", "publicado": "Publicado"}


def _migrar_se_preciso():
    """Primeira vez: aproveita a fila antiga do Instagram (alvo=próprio)."""
    if FILA.exists() or not FILA_ANTIGA.exists():
        return
    try:
        antigos = json.loads(FILA_ANTIGA.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        antigos = []
    for i in antigos:
        i.setdefault("alvo", "proprio")
        i.setdefault("tipo", "carrossel")
        i.setdefault("status", "rascunho")
        i.setdefault("publicado_em", None)
    _salvar(antigos)


def ler_fila():
    _migrar_se_preciso()
    if not FILA.exists():
        return []
    try:
        return json.loads(FILA.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return []


def _salvar(itens):
    FILA.parent.mkdir(parents=True, exist_ok=True)
    FILA.write_text(json.dumps(itens, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------- alvos (próprio + clientes) ----------
def listar_alvos():
    alvos = [{"id": "proprio", "nome": "Próprio (marketing)"}]
    if CLIENTES.exists():
        for d in sorted(CLIENTES.iterdir()):
            if not d.is_dir():
                continue
            nome = d.name
            est = d / "estado.json"
            if est.exists():
                try:
                    nome = json.loads(est.read_text(encoding="utf-8")).get("nome") or d.name
                except (ValueError, OSError):
                    pass
            alvos.append({"id": d.name, "nome": nome})
    return alvos


def _pasta_saida(alvo):
    return CONTEUDO_PROPRIO if alvo == "proprio" else (CLIENTES / alvo / "conteudo")


# ---------- prompts (handoff pro Claude Code) ----------
def prompt_carrossel(tema, alvo):
    if alvo == "proprio":
        ctx = ("Segue a identidade (identidade/design-guide.md, preto/creme/âmbar) "
               "e o tom de _memoria/preferencias.md (direto, caloroso).")
    else:
        ctx = (f"É pro cliente {alvo}: usar a identidade e o briefing em "
               f"clientes/{alvo}/. Salvar em clientes/{alvo}/conteudo/.")
    return f"Cria um carrossel pro Instagram sobre: {tema}. {ctx} Legenda pronta no final."


def prompt_completo(tema, alvo):
    base = f"/publicar-tema {tema}"
    return base if alvo == "proprio" else f"{base} (cliente {alvo}, salvar em clientes/{alvo}/)"


def prompt_publicar(tema, alvo):
    base = f"/aprovar-post {tema}"
    return base if alvo == "proprio" else f"{base} (cliente {alvo})"


# ---------- operações da fila ----------
def add_item(tema, alvo, tipo):
    tema = (tema or "").strip()
    alvo = (alvo or "proprio").strip()
    tipo = tipo if tipo in ("carrossel", "esteira") else "carrossel"
    if tema:
        itens = ler_fila()
        itens.insert(0, {
            "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
            "tema": tema, "alvo": alvo, "tipo": tipo, "status": "rascunho",
            "criado": datetime.now().strftime("%d/%m/%Y"), "publicado_em": None})
        _salvar(itens)
    return alvo


def remover(item_id):
    _salvar([i for i in ler_fila() if i.get("id") != item_id])


def mudar_status(item_id, novo):
    if novo not in STATUSES:
        return
    itens = ler_fila()
    for i in itens:
        if i.get("id") == item_id:
            i["status"] = novo
            i["publicado_em"] = (datetime.now().strftime("%d/%m/%Y")
                                 if novo == "publicado" else None)
            break
    _salvar(itens)


# ---------- montagem pra tela ----------
def fila_da_tela(alvo):
    """Itens do alvo, agrupados por status, com os prompts prontos."""
    grupos = {s: [] for s in STATUSES}
    for i in ler_fila():
        if i.get("alvo", "proprio") != alvo:
            continue
        i["p_carrossel"] = prompt_carrossel(i["tema"], alvo)
        i["p_completo"] = prompt_completo(i["tema"], alvo)
        i["p_publicar"] = prompt_publicar(i["tema"], alvo)
        grupos.get(i.get("status", "rascunho"), grupos["rascunho"]).append(i)
    return grupos


def listar_conteudo(alvo):
    """Pastas geradas pelas skills pro alvo, com as imagens."""
    base = _pasta_saida(alvo)
    if not base.exists():
        return []
    out = []
    for d in sorted(base.iterdir(), reverse=True):
        if not d.is_dir():
            continue
        arqs = [p for p in sorted(d.rglob("*")) if p.is_file()]
        out.append({
            "nome": d.name,
            "imgs": [p.relative_to(ROOT).as_posix() for p in arqs if p.suffix.lower() in IMG_EXT],
            "outros": [p.relative_to(ROOT).as_posix() for p in arqs if p.suffix.lower() not in IMG_EXT],
        })
    return out
