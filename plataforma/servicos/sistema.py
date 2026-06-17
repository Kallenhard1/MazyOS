"""Sistema & Config (Fase 7). Onde moram as skills de núcleo (padrão C: sobre o
próprio workspace) e os ajustes da operação.

A plataforma não guarda config própria: lê das fontes de verdade
(_memoria/empresa.md, identidade/design-guide.md, CLAUDE.md) e mostra. As ações
de sistema (/salvar, /atualizar, /mapear-rotinas) são handoff — rodam no Claude
Code, com a revisão humana. Editar config = editar o arquivo-fonte (a tela
aponta qual).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EMPRESA = ROOT / "_memoria" / "empresa.md"
DESIGN = ROOT / "identidade" / "design-guide.md"
CLAUDEMD = ROOT / "CLAUDE.md"

# Ações de núcleo — cada uma roda como skill no Claude Code (handoff).
ACOES = [
    {"comando": "/salvar", "nome": "Salvar trabalho",
     "desc": "Commit + push no GitHub (backup). Regenera o manifesto antes.",
     "fonte": "github"},
    {"comando": "/atualizar", "nome": "Atualizar memória",
     "desc": "Varre o workspace e sincroniza _memoria/ e o CLAUDE.md.",
     "fonte": "memoria"},
    {"comando": "/mapear-rotinas", "nome": "Sugerir rotinas",
     "desc": "Acha o que se repete e sugere virar skill nova.",
     "fonte": "skills"},
]


def _texto(arquivo):
    try:
        return arquivo.read_text(encoding="utf-8")
    except OSError:
        return ""


def contato():
    """A linha de contato canônica do _memoria/empresa.md (o '... usar sempre
    em proposta, apresentação e material de cliente')."""
    for linha in _texto(EMPRESA).splitlines():
        if "Contato" in linha and ("WhatsApp" in linha or "@" in linha):
            return linha.split(":**", 1)[-1].split(":", 1)[-1].strip() if ":" in linha else linha.strip()
    return ""


def identidade():
    """Cores (label + hex) e logo do design-guide.md, pra um preview rápido."""
    txt = _texto(DESIGN)
    cores = []
    for label, hexv in re.findall(r"\*\*([^*]+?):\*\*\s*`(#[0-9A-Fa-f]{3,8})`", txt):
        cores.append({"label": label.strip(), "hex": hexv})
    logo = "identidade/logo.jpg" if (ROOT / "identidade" / "logo.jpg").exists() else None
    return {"cores": cores, "logo": logo}


def integracoes():
    """O checklist 'Ferramentas conectadas' do CLAUDE.md → lista com status."""
    out = []
    dentro = False
    for linha in _texto(CLAUDEMD).splitlines():
        if linha.startswith("## Ferramentas conectadas"):
            dentro = True
            continue
        if dentro:
            if linha.startswith("## "):
                break
            m = re.match(r"\s*-\s*\[([ xX])\]\s*(.+)", linha)
            if m:
                nome = m.group(2).split("—")[0].split("(")[0].strip()
                out.append({"nome": nome, "conectado": m.group(1).lower() == "x"})
    return out
