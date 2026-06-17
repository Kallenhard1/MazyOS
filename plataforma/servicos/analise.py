"""Análise (Fase 7). Casca sobre a skill /analisar-dados: lista os arquivos
analisáveis em dados/ e saidas/, monta o prompt pronto (handoff) e mostra os
resumos executivos que a skill gerou em saidas/analises/.

Padrão B: a plataforma organiza e entrega o prompt; quem lê o arquivo e escreve
o resumo é o Claude Code. O Leitor CSV (servicos/arquivos.py) já mostra a tabela;
isto adiciona a camada de interpretação.
"""
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FONTES = [ROOT / "dados", ROOT / "saidas"]
ANALISES = ROOT / "saidas" / "analises"
# o que a skill consegue analisar
EXT_OK = {".csv", ".xlsx", ".xls", ".pdf", ".txt", ".json", ".tsv"}


def arquivos_analisaveis():
    """Arquivos em dados/ e saidas/ que dá pra analisar (menos as próprias
    análises geradas)."""
    out = []
    for base in FONTES:
        if not base.exists():
            continue
        for p in sorted(base.rglob("*")):
            if not p.is_file() or p.suffix.lower() not in EXT_OK:
                continue
            if ANALISES in p.parents:  # não listar análises já feitas
                continue
            st = p.stat()
            out.append({
                "rel": p.relative_to(ROOT).as_posix(),
                "nome": p.name,
                "pasta": p.parent.relative_to(ROOT).as_posix(),
                "tam": f"{st.st_size / 1024:.0f} KB",
                "mod": datetime.fromtimestamp(st.st_mtime).strftime("%d/%m %H:%M"),
            })
    return out


def prompt_analise(rel, contexto):
    rel = (rel or "").strip()
    if not rel:
        return ""
    linhas = [f"/analisar-dados {rel}"]
    if (contexto or "").strip():
        linhas.append(f"Contexto: {contexto.strip()}")
    linhas.append("Salvar o resumo executivo em saidas/analises/.")
    return "\n".join(linhas)


def listar_analises():
    if not ANALISES.exists():
        return []
    return [{"nome": p.name, "rel": p.relative_to(ROOT).as_posix(),
             "mod": datetime.fromtimestamp(p.stat().st_mtime).strftime("%d/%m %H:%M")}
            for p in sorted(ANALISES.glob("*.md"), reverse=True)]
