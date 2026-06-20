#!/usr/bin/env python3
"""
CRM de prospecção — Etapa 4 (fecha o ciclo).

Pipeline simples e versionado pra rastrear cada lead do primeiro contato ao
fechamento, com lembrete de follow-up. Sem dependências externas.

Estágios: novo → abordado → conversa → proposta → fechado (ou perdido)

Comandos:
    # traz os leads qualificados pro funil (novos entram como 'novo')
    python crm.py importar dados/prospects-qualificados.csv --classe quente

    # move um lead de estágio (casa por id ou parte do nome)
    python crm.py status "Contabilidade Prisma" abordado --canal whatsapp \\
        --nota "mandei o diagnóstico no zap"

    # quem precisa de follow-up hoje (ou até daqui a N dias)
    python crm.py followups
    python crm.py followups --ate +3d

    # gera o quadro kanban em crm/board.md
    python crm.py board

    # lista o funil (tudo ou por estágio)
    python crm.py list --status conversa,proposta

Arquivo do funil: crm/pipeline.csv (versionável no Git).
"""

import argparse
import csv
import datetime
import re
import sys
import unicodedata
from pathlib import Path

ESTAGIOS = ["novo", "abordado", "conversa", "proposta", "fechado", "perdido"]
# follow-up padrão (em dias) ao entrar no estágio, se não informado
FOLLOWUP_PADRAO = {"abordado": 3, "conversa": 2, "proposta": 4}
COLS = ["id", "nome", "tipo", "setor", "cidade", "telefone", "email", "site",
        "score", "classificacao", "status", "ultimo_contato",
        "proximo_followup", "canal", "notas"]
# campos de dados editáveis sem mexer em id/score/status
EDITAVEIS = ["nome", "tipo", "setor", "cidade", "telefone", "email", "site"]
ARQUIVO_PADRAO = "crm/pipeline.csv"
HOJE = datetime.date.today()


def slug(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def gerar_id(lead):
    base = slug(lead.get("nome", ""))
    cidade = slug((lead.get("cidade") or "").split("/")[0])
    return f"{base}-{cidade}".strip("-") or base or "lead"


def parse_data(s, base=None):
    base = base or HOJE
    s = (s or "").strip()
    if not s:
        return None
    m = re.match(r"^\+(\d+)([dw])$", s)
    if m:
        n = int(m.group(1)) * (7 if m.group(2) == "w" else 1)
        return base + datetime.timedelta(days=n)
    try:
        return datetime.date.fromisoformat(s)
    except ValueError:
        return None


def carregar(arq):
    p = Path(arq)
    if not p.exists():
        return []
    with open(p, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def salvar(arq, leads):
    p = Path(arq)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
        w.writeheader()
        for ld in leads:
            w.writerow({c: ld.get(c, "") for c in COLS})


def achar(leads, busca):
    busca = busca.strip().lower()
    exatos = [l for l in leads if l.get("id", "").lower() == busca]
    if exatos:
        return exatos
    return [l for l in leads if busca in (l.get("nome", "")).lower()]


# ---------- lógica (reutilizável pelo CLI e pela plataforma) ----------
def mudar_status_lead(arquivo, busca, novo_status, nota="", canal="", followup=""):
    """Move um lead de estágio (carimba contato, follow-up, nota). Pura, sem
    argparse/print: retorna (ok, mensagem). Usada pelo CLI e pela plataforma."""
    hoje = datetime.date.today()
    if novo_status not in ESTAGIOS:
        return False, f"Estágio inválido. Use: {', '.join(ESTAGIOS)}"
    leads = carregar(arquivo)
    achados = achar(leads, busca)
    if not achados:
        return False, f"Nenhum lead casa com '{busca}'."
    if len(achados) > 1:
        ids = "\n".join(f"  {l['id']}  ({l['nome']})" for l in achados)
        return False, "Vários leads casam — seja específico (use o id):\n" + ids
    l = achados[0]
    l["status"] = novo_status
    l["ultimo_contato"] = hoje.isoformat()
    if canal:
        l["canal"] = canal
    if nota:
        carimbo = f"[{hoje:%d/%m}] {nota}"
        l["notas"] = (l["notas"] + " | " + carimbo).strip(" |") if l["notas"] else carimbo
    # follow-up: explícito, padrão do estágio, ou limpa se encerrou
    if followup:
        d = parse_data(followup, base=hoje)
        l["proximo_followup"] = d.isoformat() if d else ""
    elif novo_status in FOLLOWUP_PADRAO:
        l["proximo_followup"] = (hoje + datetime.timedelta(
            days=FOLLOWUP_PADRAO[novo_status])).isoformat()
    elif novo_status in ("fechado", "perdido"):
        l["proximo_followup"] = ""
    salvar(arquivo, leads)
    return True, f"{l['nome']} → {novo_status} (follow-up: {l['proximo_followup'] or '—'})"


def editar_lead_dados(arquivo, busca, campos):
    """Edita os dados de um lead (só os campos EDITAVEIS presentes e diferentes).
    `campos`: dict campo->valor. Pura: retorna (ok, mensagem)."""
    leads = carregar(arquivo)
    achados = achar(leads, busca)
    if not achados:
        return False, f"Nenhum lead casa com '{busca}'."
    if len(achados) > 1:
        ids = "\n".join(f"  {l['id']}  ({l['nome']})" for l in achados)
        return False, "Vários leads casam — seja específico (use o id):\n" + ids
    l = achados[0]
    mudou = [k for k in EDITAVEIS
             if campos.get(k) is not None and campos[k] != l.get(k, "")]
    if not mudou:
        return True, "Nada alterado."
    for k in mudou:
        l[k] = campos[k]
    salvar(arquivo, leads)
    return True, f"{l['nome']} atualizado ({', '.join(mudou)})."


# ---------- comandos ----------
def cmd_importar(args):
    leads = carregar(args.arquivo)
    existentes = {l["id"] for l in leads}
    classes = ({c.strip().lower() for c in args.classe.split(",")}
               if args.classe else None)
    novos = 0
    for row in carregar(args.fonte):
        if classes and (row.get("classificacao") or "").lower() not in classes:
            continue
        rid = gerar_id(row)
        if rid in existentes:
            continue
        existentes.add(rid)
        leads.append({
            "id": rid, "nome": row.get("nome", ""), "tipo": row.get("tipo", ""),
            "setor": row.get("setor", ""), "cidade": row.get("cidade", ""),
            "telefone": row.get("telefone", ""), "email": row.get("email", ""),
            "site": row.get("site", ""), "score": row.get("score", ""),
            "classificacao": row.get("classificacao", ""),
            "status": "novo", "ultimo_contato": "", "proximo_followup": "",
            "canal": "", "notas": "",
        })
        novos += 1
    salvar(args.arquivo, leads)
    print(f"{novos} leads novos importados. Funil agora: {len(leads)} leads.")


def cmd_status(args):
    ok, msg = mudar_status_lead(args.arquivo, args.busca, args.novo_status,
                                nota=args.nota, canal=args.canal,
                                followup=args.followup)
    print(msg)
    if not ok:
        sys.exit(1)


def cmd_followups(args):
    leads = carregar(args.arquivo)
    limite = parse_data(args.ate) or HOJE
    pend = [l for l in leads if l.get("proximo_followup")
            and l["status"] not in ("fechado", "perdido")
            and parse_data(l["proximo_followup"]) and
            parse_data(l["proximo_followup"]) <= limite]
    pend.sort(key=lambda l: l["proximo_followup"])
    if not pend:
        print(f"Nenhum follow-up até {limite:%d/%m/%Y}. 🎉")
        return
    print(f"Follow-ups até {limite:%d/%m/%Y} ({len(pend)}):\n")
    for l in pend:
        d = parse_data(l["proximo_followup"])
        atraso = " ⚠️ ATRASADO" if d < HOJE else ""
        contato = l.get("telefone") or l.get("email") or "—"
        print(f"  [{l['proximo_followup']}] {l['nome']} ({l['status']}) "
              f"· {contato}{atraso}")
        if l.get("notas"):
            print(f"       {l['notas']}")


def cmd_board(args):
    leads = carregar(args.arquivo)
    por_estagio = {e: [l for l in leads if l.get("status") == e] for e in ESTAGIOS}
    linhas = ["# Funil de prospecção — MarioLucash", "",
              f"> Atualizado em {HOJE:%d/%m/%Y} · {len(leads)} leads no total", ""]
    resumo = " · ".join(f"**{e}** {len(por_estagio[e])}" for e in ESTAGIOS)
    linhas += [resumo, ""]
    for e in ESTAGIOS:
        grupo = sorted(por_estagio[e],
                       key=lambda l: to_int(l.get("score")), reverse=True)
        linhas.append(f"## {e.capitalize()} ({len(grupo)})")
        if not grupo:
            linhas += ["", "_vazio_", ""]
            continue
        linhas += ["", "| Score | Empresa | Tipo | Cidade | Contato | Follow-up | Notas |",
                   "|---:|---|---|---|---|---|---|"]
        for l in grupo:
            contato = l.get("telefone") or l.get("email") or "—"
            linhas.append(
                f"| {l.get('score','')} | {l['nome']} | {l.get('tipo','')} | "
                f"{l.get('cidade','')} | {contato} | "
                f"{l.get('proximo_followup','') or '—'} | {l.get('notas','') or '—'} |")
        linhas.append("")
    out = Path(args.saida)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(linhas), encoding="utf-8")
    print(f"Board gerado: {out}")
    print(resumo.replace("**", ""))


def to_int(v):
    try:
        return int(float(str(v).replace(",", ".")))
    except (TypeError, ValueError):
        return 0


def cmd_list(args):
    leads = carregar(args.arquivo)
    if args.status:
        alvo = {s.strip().lower() for s in args.status.split(",")}
        leads = [l for l in leads if l.get("status") in alvo]
    leads.sort(key=lambda l: to_int(l.get("score")), reverse=True)
    if not leads:
        print("Funil vazio (ou nenhum lead nesse estágio).")
        return
    for l in leads:
        print(f"  [{l.get('score',''):>3}] {l.get('status',''):<9} "
              f"{l['nome']} — {l.get('cidade','')}")


def cmd_editar(args):
    """Edita os dados de um lead (nome, telefone, e-mail, site...). Só altera
    os campos passados; id/score/status/estágio ficam intactos."""
    campos = {k: getattr(args, k) for k in EDITAVEIS}
    ok, msg = editar_lead_dados(args.arquivo, args.busca, campos)
    print(msg)
    if not ok:
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description="CRM de prospecção MazyOS")
    ap.add_argument("--arquivo", default=ARQUIVO_PADRAO, help="CSV do funil")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("importar", help="traz leads qualificados pro funil")
    p.add_argument("fonte")
    p.add_argument("--classe", default="quente")
    p.set_defaults(func=cmd_importar)

    p = sub.add_parser("status", help="muda o estágio de um lead")
    p.add_argument("busca"); p.add_argument("novo_status")
    p.add_argument("--nota", default=""); p.add_argument("--canal", default="")
    p.add_argument("--followup", default="", help="+3d, +2w ou AAAA-MM-DD")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("followups", help="quem cobrar")
    p.add_argument("--ate", default="", help="hoje (padrão) ou +Nd")
    p.set_defaults(func=cmd_followups)

    p = sub.add_parser("board", help="gera o kanban em markdown")
    p.add_argument("--saida", default="crm/board.md")
    p.set_defaults(func=cmd_board)

    p = sub.add_parser("list", help="lista o funil")
    p.add_argument("--status", default="")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("editar", help="edita dados de um lead (nome, telefone…)")
    p.add_argument("busca")
    for c in EDITAVEIS:
        p.add_argument(f"--{c}", default=None)
    p.set_defaults(func=cmd_editar)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
