#!/usr/bin/env python3
"""
Gera o manifesto que conecta o MazyOS à plataforma.

Varre as skills (`.claude/skills/`) e as funções (`scripts/`), e escreve
`plataforma/manifest.json` — a lista viva do que o MazyOS tem. É assim que a
plataforma "sabe" o que existe, e como a gente detecta skill/função nova que
ainda não virou feature (campo `mapeado`, cruzando com
`docs/PLATAFORMA-FEATURES.md`).

A skill `/salvar` roda isto antes de cada commit, pra plataforma e MazyOS
nunca saírem de sincronia.

Uso:
    python scripts/gerar_manifest.py

Sem dependências externas: só a biblioteca padrão do Python 3.
"""

import ast
import datetime
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / ".claude" / "skills"
SCRIPTS_DIR = ROOT / "scripts"
FEATURES_DOC = ROOT / "docs" / "PLATAFORMA-FEATURES.md"
SAIDA = ROOT / "plataforma" / "manifest.json"


def primeira_frase(texto, limite=160):
    texto = re.sub(r"\s+", " ", (texto or "").strip())
    corte = re.split(r"(?<=[.;])\s", texto, maxsplit=1)[0]
    return (corte[:limite]).strip()


def desc_skill(skill_md):
    """Extrai a description do frontmatter YAML do SKILL.md."""
    try:
        txt = skill_md.read_text(encoding="utf-8")
    except OSError:
        return ""
    m = re.search(r"description:\s*(.*?)(?:\n[a-zA-Z_]+:|\n---)", txt, re.S)
    if not m:
        return ""
    corpo = m.group(1).replace(">", " ").replace("|", " ")
    return primeira_frase(corpo)


def desc_script(py):
    """Primeira linha do docstring do módulo."""
    try:
        doc = ast.get_docstring(ast.parse(py.read_text(encoding="utf-8")))
    except (OSError, SyntaxError):
        doc = None
    return primeira_frase((doc or "").splitlines()[0] if doc else "")


def coletar_skills():
    if not SKILLS_DIR.exists():
        return []
    out = []
    for d in sorted(SKILLS_DIR.iterdir()):
        md = d / "SKILL.md"
        if d.is_dir() and md.exists():
            out.append({"nome": d.name, "descricao": desc_skill(md)})
    return out


def coletar_scripts():
    out = []
    for py in sorted(SCRIPTS_DIR.glob("*.py")):
        if py.stem == "gerar_manifest":
            continue
        out.append({"nome": py.name, "descricao": desc_script(py)})
    return out


def main():
    features_txt = FEATURES_DOC.read_text(encoding="utf-8") if FEATURES_DOC.exists() else ""
    skills = coletar_skills()
    scripts = coletar_scripts()

    for s in skills:
        s["mapeado"] = f"/{s['nome']}" in features_txt or s["nome"] in features_txt
    for s in scripts:
        s["mapeado"] = s["nome"] in features_txt

    nao_mapeados = ([f"/{s['nome']}" for s in skills if not s["mapeado"]]
                    + [s["nome"] for s in scripts if not s["mapeado"]])

    manifesto = {
        "gerado_em": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "resumo": {
            "skills": len(skills),
            "scripts": len(scripts),
            "nao_mapeados": len(nao_mapeados),
        },
        "skills": skills,
        "scripts": scripts,
        "nao_mapeados_na_plataforma": nao_mapeados,
    }
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2),
                     encoding="utf-8")

    print(f"Manifesto: {len(skills)} skills, {len(scripts)} scripts -> {SAIDA}")
    if nao_mapeados:
        print("Ainda não viraram feature na plataforma (ver docs/PLATAFORMA-FEATURES.md):")
        for n in nao_mapeados:
            print(f"  - {n}")
    else:
        print("Tudo mapeado como feature. MazyOS e plataforma em sincronia.")


if __name__ == "__main__":
    main()
