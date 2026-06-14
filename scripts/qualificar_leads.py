#!/usr/bin/env python3
"""
Qualificador de leads — o coração da automação de prospecção.

Lê uma lista bruta de empresas (CSV), checa a saúde do site de cada uma e
devolve a lista RANQUEADA por um score de oportunidade (0–100). Quanto mais
alto o score, mais a empresa precisa do nosso serviço E mais vale a pena
abordar.

Filosofia do score:
    NEED (fraqueza digital)  -> sem site, site quebrado, sem HTTPS, não
                                responsivo, site velho = oportunidade
    FIT  (vale a pena)       -> boas avaliações, negócio ativo, B2B (ticket
                                maior) = consegue pagar e se importa

Uso:
    python qualificar_leads.py
    python qualificar_leads.py dados/prospects.csv
    python qualificar_leads.py entrada.csv saida.csv
    python qualificar_leads.py --workers 12 --timeout 8

Entrada (CSV) — colunas reconhecidas (todas opcionais menos 'nome'):
    nome, tipo (b2b/b2c), setor, cidade, telefone, site,
    nota, avaliacoes, instagram, linkedin

Saída:
    <saida>.csv  -> mesma lista + colunas calculadas, ordenada por score
    <saida>.md   -> resumo dos leads quentes pra bater o olho

Sem dependências externas: usa só a biblioteca padrão do Python 3.
"""

import argparse
import csv
import datetime
import re
import ssl
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ANO_ATUAL = datetime.date.today().year
UA = "Mozilla/5.0 (compatible; MazyOS-LeadCheck/1.0; +prospeccao)"

# sinônimos de cabeçalho aceitos -> nome canônico
ALIASES = {
    "nome": "nome", "empresa": "nome", "razao_social": "nome",
    "tipo": "tipo", "segmento": "tipo",
    "setor": "setor", "categoria": "setor", "cnae": "setor",
    "cidade": "cidade", "municipio": "cidade",
    "telefone": "telefone", "fone": "telefone", "whatsapp": "telefone",
    "site": "site", "website": "site", "url": "site",
    "nota": "nota", "rating": "nota", "avaliacao": "nota",
    "avaliacoes": "avaliacoes", "reviews": "avaliacoes",
    "num_avaliacoes": "avaliacoes", "n_avaliacoes": "avaliacoes",
    "instagram": "instagram", "insta": "instagram",
    "linkedin": "linkedin",
}


def to_float(v):
    if v is None:
        return None
    v = str(v).strip().replace(",", ".")
    m = re.search(r"\d+(\.\d+)?", v)
    return float(m.group()) if m else None


def to_int(v):
    f = to_float(v)
    return int(f) if f is not None else None


def normalizar_url(site):
    site = (site or "").strip()
    if not site or site.lower() in ("-", "n/a", "nao", "não", "none"):
        return ""
    if not re.match(r"^https?://", site, re.I):
        site = "http://" + site
    return site


def checar_site(url, timeout):
    """Retorna dict com status do site. Sem rede/erro -> marca o motivo."""
    res = {"site_status": "", "https": "", "mobile": "", "ano_site": ""}
    url = normalizar_url(url)
    if not url:
        res["site_status"] = "sem_site"
        return res

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE  # checamos existência, não a cadeia SSL
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            final = r.geturl()
            html = r.read(250_000).decode("utf-8", "ignore")
            res["site_status"] = "ok"
            res["https"] = "sim" if final.lower().startswith("https") else "nao"
            res["mobile"] = "sim" if re.search(
                r'name=["\']?viewport', html, re.I) else "nao"
            anos = [int(a) for a in re.findall(r"\b(20\d{2})\b", html)
                    if 2000 <= int(a) <= ANO_ATUAL]
            if anos:
                res["ano_site"] = str(max(anos))
    except urllib.error.HTTPError as e:
        # site existe mas responde com erro (403/404/500...)
        res["site_status"] = f"erro_http_{e.code}"
        res["https"] = "sim" if url.lower().startswith("https") else "nao"
    except (urllib.error.URLError, TimeoutError, ssl.SSLError, OSError):
        res["site_status"] = "nao_responde"
    except Exception:
        res["site_status"] = "erro"
    return res


def pontuar(lead, check):
    """Score de oportunidade 0–100 + classificação + motivos."""
    score = 0
    motivos = []
    status = check["site_status"]
    tipo = (lead.get("tipo") or "b2c").strip().lower()

    # ---- NEED: fraqueza digital ----
    if status == "sem_site":
        score += 45
        motivos.append("não tem site (oportunidade máxima)")
    elif status == "nao_responde" or status.startswith("erro_http_5"):
        score += 35
        motivos.append("site fora do ar / não responde")
    elif status.startswith("erro_http_4"):
        score += 25
        motivos.append("site com erro (página quebrada)")
    elif status == "ok":
        if check["https"] == "nao":
            score += 12
            motivos.append("site sem HTTPS (inseguro)")
        if check["mobile"] == "nao":
            score += 12
            motivos.append("site não é responsivo (ruim no celular)")
        ano = to_int(check["ano_site"])
        if ano and ano <= ANO_ATUAL - 3:
            score += 8
            motivos.append(f"site parece desatualizado (©{ano})")
        if check["https"] == "sim" and check["mobile"] == "sim" and not (
                ano and ano <= ANO_ATUAL - 3):
            motivos.append("site moderno — menos urgência")

    # ---- FIT: vale a pena / consegue pagar ----
    nota = to_float(lead.get("nota"))
    aval = to_int(lead.get("avaliacoes"))
    if nota is not None and aval is not None:
        if nota >= 4.3 and aval >= 50:
            score += 20
            motivos.append(f"reputação forte ({nota}★, {aval} avaliações)")
        elif nota >= 4.0 and aval >= 20:
            score += 12
            motivos.append(f"boa reputação ({nota}★, {aval} avaliações)")
        elif aval >= 1:
            score += 5
    if (lead.get("telefone") or "").strip():
        score += 5
    if tipo == "b2b":
        score += 5
        motivos.append("B2B (ticket maior)")
        if not (lead.get("linkedin") or "").strip():
            motivos.append("sem LinkedIn (decisor B2B pesquisa lá)")

    score = max(0, min(100, score))
    if score >= 60:
        classe = "quente"
    elif score >= 35:
        classe = "morno"
    else:
        classe = "frio"
    return score, classe, "; ".join(motivos) if motivos else "—"


def ler_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        leads = []
        for row in reader:
            lead = {}
            for k, v in row.items():
                if k is None:
                    continue
                canon = ALIASES.get(k.strip().lower())
                if canon:
                    lead[canon] = v
            if (lead.get("nome") or "").strip():
                leads.append(lead)
    return leads


def escrever_csv(path, leads):
    cols = ["score", "classificacao", "nome", "tipo", "setor", "cidade",
            "telefone", "site", "site_status", "https", "mobile",
            "ano_site", "nota", "avaliacoes", "motivos"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for ld in leads:
            w.writerow(ld)


def escrever_md(path, leads):
    quentes = [l for l in leads if l["classificacao"] == "quente"]
    mornos = [l for l in leads if l["classificacao"] == "morno"]
    frios = [l for l in leads if l["classificacao"] == "frio"]
    linhas = [
        "# Leads qualificados",
        "",
        f"> Gerado em {datetime.date.today():%d/%m/%Y} · "
        f"{len(leads)} leads · 🔥 {len(quentes)} quentes · "
        f"🟡 {len(mornos)} mornos · ⚪ {len(frios)} frios",
        "",
        "## 🔥 Quentes — abordar primeiro",
        "",
        "| Score | Empresa | Tipo | Cidade | Por que é oportunidade |",
        "|---:|---|---|---|---|",
    ]
    for l in quentes[:25]:
        linhas.append(
            f"| {l['score']} | {l['nome']} | {l.get('tipo','')} | "
            f"{l.get('cidade','')} | {l['motivos']} |")
    if not quentes:
        linhas.append("| — | _nenhum lead quente nessa leva_ | | | |")
    linhas += ["", f"_Mornos: {len(mornos)} · Frios: {len(frios)} "
               "(ver CSV completo)._", ""]
    Path(path).write_text("\n".join(linhas), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Qualificador de leads MazyOS")
    ap.add_argument("entrada", nargs="?", default="dados/prospects.csv")
    ap.add_argument("saida", nargs="?", default=None)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--timeout", type=int, default=8)
    args = ap.parse_args()

    entrada = Path(args.entrada)
    if not entrada.exists():
        sys.exit(f"CSV de entrada não encontrado: {entrada}")
    saida = Path(args.saida) if args.saida else entrada.with_name(
        entrada.stem + "-qualificados.csv")

    leads = ler_csv(entrada)
    if not leads:
        sys.exit("Nenhum lead válido no CSV (precisa ao menos da coluna 'nome').")

    print(f"Qualificando {len(leads)} leads (checando sites)...")
    checks = list(ThreadPoolExecutor(max_workers=args.workers).map(
        lambda l: checar_site(l.get("site"), args.timeout), leads))

    for lead, check in zip(leads, checks):
        lead.update(check)
        score, classe, motivos = pontuar(lead, check)
        lead["score"], lead["classificacao"], lead["motivos"] = (
            score, classe, motivos)

    leads.sort(key=lambda l: l["score"], reverse=True)
    escrever_csv(saida, leads)
    md = saida.with_suffix(".md")
    escrever_md(md, leads)

    n_q = sum(1 for l in leads if l["classificacao"] == "quente")
    n_m = sum(1 for l in leads if l["classificacao"] == "morno")
    print(f"Pronto. {n_q} quentes, {n_m} mornos.")
    print(f"  -> {saida}")
    print(f"  -> {md}")
    print("\nTop 5:")
    for l in leads[:5]:
        print(f"  [{l['score']:>3}] {l['classificacao']:<6} {l['nome']} "
              f"— {l['motivos']}")


if __name__ == "__main__":
    main()
