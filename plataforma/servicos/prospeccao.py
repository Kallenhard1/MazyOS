"""Camada de prospecção: roda os scripts que já existem em scripts/ via
subprocess e lê os arquivos que eles geram. Nenhuma lógica de negócio nova
mora aqui — só orquestra e apresenta. Fonte de verdade segue em dados/ e crm/.
"""
import csv
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DADOS = ROOT / "dados"
SAIDAS = ROOT / "saidas"

# categorias amigáveis aceitas pelo buscar_leads_osm.py (pra montar o form)
CATEGORIAS_OSM = [
    "cafe", "restaurante", "lanchonete", "bar", "padaria", "mercado",
    "petshop", "veterinaria", "salao", "barbearia", "academia", "clinica",
    "odontologia", "farmacia", "oficina", "hotel", "advocacia",
    "contabilidade", "imobiliaria",
]


def _run(args, timeout=600):
    """Roda `python <args...>` na raiz do projeto. Devolve (ok, saida_texto)."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    try:
        p = subprocess.run(
            [sys.executable, *args],
            cwd=ROOT, env=env, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout,
        )
        out = (p.stdout or "").strip()
        if p.stderr and p.stderr.strip():
            out += "\n\n[stderr]\n" + p.stderr.strip()
        return p.returncode == 0, (out or "(sem saída)")
    except subprocess.TimeoutExpired:
        return False, "Tempo esgotado — o script demorou demais."
    except Exception as e:  # noqa: BLE001
        return False, f"Falha ao executar: {e}"


def buscar_osm(cidade, categorias="", usar_plano=False):
    cidade = (cidade or "").strip()
    if not cidade:
        return False, "Informe a cidade."
    args = ["scripts/buscar_leads_osm.py", "--cidade", cidade]
    if usar_plano:
        args += ["--buscas", "dados/buscas-osm.csv"]
    elif categorias.strip():
        args += ["--categorias", categorias.strip()]
    else:
        return False, "Escolha categorias ou marque 'usar plano de busca'."
    return _run(args)


def qualificar(entrada="dados/prospects.csv"):
    if not (ROOT / entrada).exists():
        return False, f"Não achei {entrada}. Rode o sourcing antes."
    return _run(["scripts/qualificar_leads.py", entrada])


def gerar_abordagem(classe="morno", limite=0):
    args = ["scripts/gerar_abordagem.py", "--classe", classe]
    if limite:
        args += ["--limite", str(int(limite))]
    return _run(args)


def resumo_qualificados():
    """Conta classes e pega o top 5 do prospects-qualificados.csv (já ordenado)."""
    f = DADOS / "prospects-qualificados.csv"
    if not f.exists():
        return None
    with open(f, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    counts = {"quente": 0, "morno": 0, "frio": 0}
    for r in rows:
        c = (r.get("classificacao") or "").lower()
        if c in counts:
            counts[c] += 1
    return {"total": len(rows), "counts": counts, "top": rows[:5]}


def listar_arquivos():
    """Lista os arquivos gerados em dados/ e saidas/ (nome, link, tamanho, data)."""
    grupos = []
    fontes = [
        ("dados", DADOS),
        ("saidas/abordagens", SAIDAS / "abordagens"),
        ("saidas/diagnosticos", SAIDAS / "diagnosticos"),
        ("saidas/envio", SAIDAS / "envio"),
    ]
    for label, d in fontes:
        if not d.exists():
            continue
        itens = []
        for p in sorted(d.rglob("*"), key=lambda x: x.name.lower()):
            if p.is_file():
                st = p.stat()
                itens.append({
                    "nome": p.name,
                    "rel": p.relative_to(ROOT).as_posix(),
                    "tam": _humano(st.st_size),
                    "mod": datetime.fromtimestamp(st.st_mtime).strftime("%d/%m %H:%M"),
                })
        if itens:
            grupos.append({"label": label, "itens": itens})
    return grupos


def _humano(n):
    for u in ("B", "KB", "MB"):
        if n < 1024:
            return f"{n:.0f} {u}"
        n /= 1024
    return f"{n:.1f} GB"
