"""SEO & GMB (Fase 5). Casca sobre as skills /seo (8 passos) e
/responder-avaliacoes. Segue o padrão B: a plataforma organiza o fluxo por
alvo (próprio ou cliente), entrega o prompt pronto (handoff) e mostra o que a
skill já gerou. Quem pesquisa e escreve é o Claude Code.

Stateless de propósito: o status de cada passo é derivado da existência do
arquivo de saída (a skill escreve em marketing/seo/ ou clientes/<id>/seo/).
A plataforma só lê e dispara — não mantém banco paralelo.
"""
from pathlib import Path

from servicos.conteudo import listar_alvos  # reusa: próprio + clientes

ROOT = Path(__file__).resolve().parents[2]

# Os 8 passos da skill /seo, na ordem. `arquivo` = saída esperada;
# `comando` = atalho da skill pro handoff.
PASSOS = [
    {"n": 1, "id": "demanda", "nome": "Demanda",
     "desc": "O que as pessoas buscam no nicho (palavras-chave + intenção).",
     "arquivo": "01-pesquisa-demanda.md", "comando": "/seo passo 1"},
    {"n": 2, "id": "concorrencia", "nome": "Concorrência",
     "desc": "Quem domina as buscas e onde estão os gaps.",
     "arquivo": "02-analise-concorrencia.md", "comando": "/seo passo 2"},
    {"n": 3, "id": "gmb", "nome": "Google Meu Negócio",
     "desc": "Perfil completo pro Maps e Local Pack (resultado mais rápido).",
     "arquivo": "03-google-meu-negocio.md", "comando": "/seo gmb"},
    {"n": 4, "id": "onpage", "nome": "On-page",
     "desc": "Meta tags, schema e checklist técnico por página.",
     "arquivo": "04-otimizacao-on-page.md", "comando": "/seo passo 4"},
    {"n": 5, "id": "conteudo", "nome": "Conteúdo",
     "desc": "Plano de autoridade (vira insumo da esteira /publicar-tema).",
     "arquivo": "05-estrategia-conteudo.md", "comando": "/seo passo 5"},
    {"n": 6, "id": "ads", "nome": "Google Ads",
     "desc": "Campanhas prontas (vira CSV via /anuncio-google).",
     "arquivo": "06-google-ads.md", "comando": "/seo passo 6"},
    {"n": 7, "id": "monitoramento", "nome": "Monitoramento",
     "desc": "Checklist semanal / mensal / trimestral.",
     "arquivo": "07-checklist-monitoramento.md", "comando": "/seo passo 7"},
    {"n": 8, "id": "geo", "nome": "GEO (aparecer nas IAs)",
     "desc": "Ser citado por ChatGPT, Gemini, Perplexity no nicho.",
     "arquivo": "08-geo-otimizacao-ia.md", "comando": "/seo geo"},
]


def _pasta_seo(alvo):
    return ROOT / "marketing" / "seo" if alvo == "proprio" else (ROOT / "clientes" / alvo / "seo")


def _ctx_alvo(alvo):
    """Sufixo que o handoff usa pra mandar a skill salvar no lugar certo."""
    if alvo == "proprio":
        return ""
    return (f" (é pro cliente {alvo}: usar o briefing em clientes/{alvo}/ e "
            f"salvar a saída em clientes/{alvo}/seo/)")


def etapas(alvo):
    """Os 8 passos pro alvo, cada um com prompt pronto e status derivado
    da existência do arquivo de saída."""
    pasta = _pasta_seo(alvo)
    out = []
    for p in PASSOS:
        saida = pasta / p["arquivo"]
        feito = saida.exists()
        out.append({
            **p,
            "feito": feito,
            "prompt": p["comando"] + _ctx_alvo(alvo),
            "rel": saida.relative_to(ROOT).as_posix() if feito else None,
        })
    return out


def progresso(alvo):
    feitos = sum(1 for e in etapas(alvo) if e["feito"])
    return {"feitos": feitos, "total": len(PASSOS)}


# ---------- Avaliações (/responder-avaliacoes) ----------
def prompt_avaliacoes(alvo, reviews):
    """Monta o handoff do /responder-avaliacoes a partir das reviews coladas."""
    reviews = (reviews or "").strip()
    if not reviews:
        return ""
    alvo_txt = ("do meu negócio" if alvo == "proprio"
                else f"do cliente {alvo} (briefing em clientes/{alvo}/)")
    return (f"/responder-avaliacoes — responde estas avaliações do Google {alvo_txt}, "
            f"mantendo o tom da marca. Gera uma resposta sugerida pra cada uma:\n\n{reviews}")
