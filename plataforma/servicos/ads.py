"""Anúncios (Fase 6). Casca sobre as skills /anuncio-google (monta a campanha
em CSV pro Google Ads Editor) e /relatorio-ads (resumo executivo dos exports).

Padrão B (handoff): a plataforma monta o briefing / a seleção de exports e
entrega o prompt pronto. Quem gera os CSVs e escreve o relatório é o Claude
Code. A plataforma só lê dados/ e mostra o que as skills geraram em
marketing/campanhas/ (próprio) ou clientes/<id>/campanhas/ (cliente).
"""
from datetime import datetime
from pathlib import Path

from servicos import arquivos as arq
from servicos.conteudo import listar_alvos  # reusa: próprio + clientes

ROOT = Path(__file__).resolve().parents[2]

# objetivo da campanha (vira a 1ª linha do briefing do /anuncio-google)
OBJETIVOS = [
    {"id": "leads", "nome": "Gerar leads (ligações, WhatsApp, formulário)"},
    {"id": "site", "nome": "Visitas ao site"},
    {"id": "local", "nome": "Alcance local (Google Maps)"},
]


def _pasta_campanhas(alvo):
    return (ROOT / "marketing" / "campanhas" if alvo == "proprio"
            else ROOT / "clientes" / alvo / "campanhas")


def _pasta_seo(alvo):
    return ROOT / "marketing" / "seo" if alvo == "proprio" else (ROOT / "clientes" / alvo / "seo")


def seo_base(alvo):
    """Arquivos da pesquisa SEO que servem de insumo pro /anuncio-google."""
    pasta = _pasta_seo(alvo)
    nomes = ["06-google-ads.md", "01-pesquisa-demanda.md"]
    return [(pasta / n).relative_to(ROOT).as_posix() for n in nomes if (pasta / n).exists()]


# ---------- Montar campanha (/anuncio-google) ----------
def prompt_campanha(alvo, objetivo, orcamento, regiao, obs):
    obj = next((o["nome"] for o in OBJETIVOS if o["id"] == objetivo), OBJETIVOS[0]["nome"])
    linhas = ["/anuncio-google", f"Objetivo: {obj}"]
    if (orcamento or "").strip():
        linhas.append(f"Orçamento diário: {orcamento.strip()}")
    if (regiao or "").strip():
        linhas.append(f"Região: {regiao.strip()}")
    if (obs or "").strip():
        linhas.append(f"Observações: {obs.strip()}")
    base = seo_base(alvo)
    if base:
        linhas.append("Usar como base a pesquisa SEO já feita: " + ", ".join(base))
    if alvo != "proprio":
        linhas.append(f"É pro cliente {alvo}: usar o briefing em clientes/{alvo}/ "
                      f"e salvar a campanha em clientes/{alvo}/campanhas/.")
    return "\n".join(linhas)


def listar_campanhas(alvo):
    """Pastas de campanha geradas pela skill (google-ads-<data>/), com os CSVs."""
    base = _pasta_campanhas(alvo)
    if not base.exists():
        return []
    out = []
    for d in sorted(base.iterdir(), reverse=True):
        if not d.is_dir() or d.name == "relatorios":
            continue
        csvs = [p.relative_to(ROOT).as_posix() for p in sorted(d.glob("*.csv"))]
        out.append({"nome": d.name, "csvs": csvs})
    return out


# ---------- Relatório semanal (/relatorio-ads) ----------
def exports_disponiveis():
    """CSVs em dados/ que parecem export de Ads (google/meta), pra referência."""
    todos = arq.listar_csvs()
    chaves = ("google-ads", "meta-ads", "google_ads", "meta_ads", "ads")
    marcados = [c for c in todos if any(k in c["nome"].lower() for k in chaves)]
    return {"ads": marcados, "todos": todos}


def prompt_relatorio(alvo, rels):
    rels = [r for r in (rels or []) if r.strip()]
    if not rels:
        return ""
    cab = "/relatorio-ads" + ("" if alvo == "proprio" else f" (cliente {alvo})")
    return cab + "\n" + "\n".join(rels)


def listar_relatorios(alvo):
    """Relatórios .md gerados pela skill em campanhas/relatorios/."""
    base = _pasta_campanhas(alvo) / "relatorios"
    if not base.exists():
        return []
    return [{"nome": p.name, "rel": p.relative_to(ROOT).as_posix(),
             "mod": datetime.fromtimestamp(p.stat().st_mtime).strftime("%d/%m %H:%M")}
            for p in sorted(base.glob("*.md"), reverse=True)]
