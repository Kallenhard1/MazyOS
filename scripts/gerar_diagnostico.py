#!/usr/bin/env python3
"""
Gerador de diagnóstico em PDF — Etapa 3 (o 1-página por lead).

Pra cada lead quente, preenche o template branded da MarioLucash com o
diagnóstico real (achados do qualificador + score) e gera um PDF de 1
página pronto pra anexar na abordagem.

Uso:
    python gerar_diagnostico.py                       # leads quentes
    python gerar_diagnostico.py dados/prospects-qualificados.csv
    python gerar_diagnostico.py --classe quente,morno --limite 30

Saída: saidas/diagnosticos/<empresa>.pdf

Requer: pip install weasyprint
"""

import argparse
import csv
import datetime
import re
import sys
import unicodedata
from pathlib import Path

try:
    from weasyprint import HTML
except ImportError:
    sys.exit("WeasyPrint não instalado. Rode: pip install weasyprint")

RAIZ = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = RAIZ / "templates" / "diagnostico"
TEMPLATE = TEMPLATE_DIR / "diagnostico.html"

SOLUCAO = {
    "sem_site": "Um site profissional e rápido + perfil no Google Meu Negócio, "
                "pra vocês aparecerem exatamente quando alguém procura o que "
                "vocês fazem. É a base de tudo.",
    "quebrado": "Um site novo, leve e que funciona de verdade no celular, com "
                "o que o cliente precisa à mão e botão de contato direto.",
    "fraco":    "Modernizar o site (HTTPS, mobile, visual atual) e ligar ele ao "
                "Google e ao WhatsApp, pra cada visita virar contato.",
}


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "lead"


def tipo_solucao(status, https, mobile):
    if status == "sem_site":
        return SOLUCAO["sem_site"]
    if status == "nao_responde" or status.startswith("erro_http"):
        return SOLUCAO["quebrado"]
    return SOLUCAO["fraco"]


def to_int(v):
    try:
        return int(float(str(v).replace(",", ".")))
    except (TypeError, ValueError):
        return None


def achados_cliente(lead):
    """Só problemas digitais reais — nunca motivos internos de score."""
    f = []
    status = (lead.get("site_status") or "").strip()
    setor = (lead.get("setor") or "o que vocês fazem").strip()
    cidade = (lead.get("cidade") or "sua região").strip()
    if status == "sem_site":
        f.append(f"Não têm site — quem busca {setor} em {cidade} no Google "
                 "encontra o concorrente, não vocês")
    elif status == "nao_responde" or status.startswith("erro_http_5"):
        f.append("O site está fora do ar — quem tenta acessar não consegue")
    elif status.startswith("erro_http_4"):
        f.append("O site tem páginas com erro (dá problema ao abrir)")
    else:
        if lead.get("https") == "nao":
            f.append("Site sem HTTPS — o navegador mostra 'não seguro'")
        if lead.get("mobile") == "nao":
            f.append("Site não funciona bem no celular (maioria dos acessos)")
        ano = to_int(lead.get("ano_site"))
        if ano and ano <= datetime.date.today().year - 3:
            f.append(f"Site parece desatualizado (©{ano})")
    if (lead.get("tipo") or "").lower() == "b2b" and not (
            lead.get("linkedin") or "").strip():
        f.append("Sem LinkedIn — o comprador B2B pesquisa fornecedor lá")
    return f or ["Presença digital com espaço claro pra melhorar"]


def achados_html(lead):
    linhas = []
    for i, m in enumerate(achados_cliente(lead), 1):
        linhas.append(
            f'<div class="achado"><div class="mark">{i}</div>'
            f'<p>{m}</p></div>')
    return "\n".join(linhas)


def preencher(lead, template_html):
    repl = {
        "{{DATA}}": f"{datetime.date.today():%d/%m/%Y}",
        "{{NOME}}": lead.get("nome", "").strip(),
        "{{SETOR}}": (lead.get("setor") or "Negócio").strip(),
        "{{CIDADE}}": (lead.get("cidade") or "").strip(),
        "{{SCORE}}": str(lead.get("score", "")).strip(),
        "{{CLASSE}}": (lead.get("classificacao") or "").strip(),
        "{{ACHADOS}}": achados_html(lead),
        "{{SOLUCAO}}": tipo_solucao(
            (lead.get("site_status") or "").strip(),
            lead.get("https"), lead.get("mobile")),
    }
    html = template_html
    for k, v in repl.items():
        html = html.replace(k, v)
    return html


def main():
    ap = argparse.ArgumentParser(description="Gera diagnóstico PDF por lead")
    ap.add_argument("entrada", nargs="?", default="dados/prospects-qualificados.csv")
    ap.add_argument("--classe", default="quente")
    ap.add_argument("--limite", type=int, default=0)
    ap.add_argument("--saida-dir", default="saidas/diagnosticos")
    args = ap.parse_args()

    if not TEMPLATE.exists():
        sys.exit(f"Template não encontrado: {TEMPLATE}")
    entrada = Path(args.entrada)
    if not entrada.exists():
        sys.exit(f"CSV não encontrado: {entrada}")

    classes = {c.strip().lower() for c in args.classe.split(",") if c.strip()}
    with open(entrada, newline="", encoding="utf-8-sig") as f:
        leads = [r for r in csv.DictReader(f)
                 if (r.get("classificacao") or "").lower() in classes]
    if args.limite:
        leads = leads[:args.limite]
    if not leads:
        sys.exit(f"Nenhum lead nas classes {classes}.")

    template_html = TEMPLATE.read_text(encoding="utf-8")
    out_dir = Path(args.saida_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    import warnings
    warnings.filterwarnings("ignore")
    for lead in leads:
        html = preencher(lead, template_html)
        pdf = out_dir / f"diagnostico-{slug(lead.get('nome',''))}.pdf"
        # base_url = pasta do template, pra achar fonts/
        HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf(str(pdf))
        print(f"  -> {pdf}")
    print(f"\n{len(leads)} diagnósticos gerados em {out_dir}.")


if __name__ == "__main__":
    main()
