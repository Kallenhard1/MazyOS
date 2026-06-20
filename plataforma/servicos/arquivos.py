"""Leitor de CSV do painel. Lista os .csv gerados pela operação e lê um deles
como tabela (cabeçalho + linhas), com sandbox contra path traversal. Só leitura.
"""
import csv
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIRS = [ROOT / "dados", ROOT / "saidas", ROOT / "crm"]
LIMITE_LINHAS = 5000  # trava de segurança pra não estourar a página


def listar_csvs():
    """Todos os .csv dentro de dados/, saidas/ e crm/."""
    out = []
    for d in DIRS:
        if not d.exists():
            continue
        for p in sorted(d.rglob("*.csv"), key=lambda x: x.name.lower()):
            st = p.stat()
            out.append({
                "rel": p.relative_to(ROOT).as_posix(),
                "nome": p.name,
                "pasta": p.parent.relative_to(ROOT).as_posix(),
                "mod": datetime.fromtimestamp(st.st_mtime).strftime("%d/%m %H:%M"),
            })
    return out


def _seguro(rel):
    """Resolve `rel` só se for um .csv real dentro dos diretórios permitidos."""
    if not rel:
        return None
    full = (ROOT / rel).resolve()
    if full.suffix.lower() != ".csv" or not full.is_file():
        return None
    if not any(str(full).startswith(str(d.resolve())) for d in DIRS):
        return None
    return full


def ler_csv(rel, limite=LIMITE_LINHAS):
    """Lê um CSV permitido → dict com headers, linhas e metadados. None se inválido."""
    full = _seguro(rel)
    if not full:
        return None
    with open(full, newline="", encoding="utf-8-sig") as f:
        linhas = list(csv.reader(f))
    if not linhas:
        return {"rel": rel, "nome": full.name, "headers": [], "linhas": [],
                "total": 0, "truncado": False}
    headers, corpo = linhas[0], linhas[1:]
    total = len(corpo)
    return {
        "rel": rel,
        "nome": full.name,
        "headers": headers,
        "linhas": corpo[:limite],
        "total": total,
        "truncado": total > limite,
    }
