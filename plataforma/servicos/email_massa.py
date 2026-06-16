"""Camada de envio em massa. Lê os leads do funil (crm/pipeline.csv) e monta a
abordagem por lead a partir de DOIS templates separados — um de e-mail, um de
WhatsApp — calibrados por canal. GERA O LOTE, nunca envia: o passo final (criar
rascunhos no Gmail) é feito pelo Claude via MCP, lendo o lote-*.csv. Quem tem
e-mail entra no lote de e-mail; quem não tem vira mensagem de WhatsApp.
"""
import csv
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "crm" / "pipeline.csv"
ENVIO_DIR = ROOT / "saidas" / "envio"

VARIAVEIS = ["nome", "setor", "cidade", "telefone"]

# --- Template de E-MAIL (formal-leve, com assunto e assinatura) ---
EMAIL_ASSUNTO_PADRAO = "{nome}: sua presença digital na internet"
EMAIL_CORPO_PADRAO = (
    "Oi, pessoal do {nome}!\n\n"
    "Sou o Mario Lucas, trabalho com sites e automação para negócios de "
    "{cidade}. Dei uma olhada na presença digital de vocês e acho que dá "
    "pra trazer mais cliente com alguns ajustes simples.\n\n"
    "Posso te mandar um diagnóstico rápido de 1 página, sem compromisso?\n\n"
    "Um abraço,\nMario Lucas\n"
    "mariolucasdasilvabarbosa@gmail.com · Instagram @mariolucash"
)

# --- Template de WHATSAPP (curto, informal, sem assunto/assinatura) ---
WHATSAPP_PADRAO = (
    "Oi! Tudo bem? Sou o Mario Lucas, mexo com sites e automação aqui na "
    "região. Dei uma olhada na presença digital do {nome} e acho que dá pra "
    "trazer mais cliente com uns ajustes simples. Posso te mandar um "
    "diagnóstico rápido (de graça)? Sem compromisso!"
)


def carregar_leads():
    if not PIPELINE.exists():
        return []
    with open(PIPELINE, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def aplicar_vars(texto, lead):
    t = texto or ""
    for k in VARIAVEIS:
        t = t.replace("{" + k + "}", (lead.get(k) or "").strip())
    return t


def preencher(lead, assunto_tpl, corpo_tpl, wpp_tpl):
    """Devolve o item já preenchido, escolhendo o canal pelo e-mail do lead."""
    tem_email = bool((lead.get("email") or "").strip())
    base = {"nome": lead.get("nome", ""), "telefone": (lead.get("telefone") or "").strip()}
    if tem_email:
        return {**base, "canal": "email", "email": lead["email"].strip(),
                "assunto": aplicar_vars(assunto_tpl, lead),
                "corpo": aplicar_vars(corpo_tpl, lead)}
    return {**base, "canal": "whatsapp", "msg": aplicar_vars(wpp_tpl, lead)}


def montar_previews(ids, assunto_tpl, corpo_tpl, wpp_tpl, limite=3):
    por_id = {l.get("id"): l for l in carregar_leads()}
    sel = [por_id[i] for i in ids if i in por_id][:limite]
    return [preencher(l, assunto_tpl, corpo_tpl, wpp_tpl) for l in sel]


def gerar_lote(ids, assunto_tpl, corpo_tpl, wpp_tpl):
    """Escreve lote-<ts>.csv (e-mail) e whatsapp-<ts>.md (WhatsApp). Resumo p/ tela."""
    por_id = {l.get("id"): l for l in carregar_leads()}
    sel = [por_id[i] for i in ids if i in por_id]
    if not sel:
        return {"erro": "Nenhum lead selecionado."}

    emails, zaps = [], []
    for l in sel:
        p = preencher(l, assunto_tpl, corpo_tpl, wpp_tpl)
        if p["canal"] == "email":
            emails.append({"to": p["email"], "subject": p["assunto"], "body": p["corpo"]})
        else:
            zaps.append(p)

    ENVIO_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    resumo = {"total": len(sel), "com_email": len(emails), "sem_email": len(zaps)}

    lote_csv = ENVIO_DIR / f"lote-{ts}.csv"
    with open(lote_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["to", "subject", "body"])
        w.writeheader()
        w.writerows(emails)
    resumo["lote_csv"] = lote_csv.relative_to(ROOT).as_posix()

    if zaps:
        wpp = ENVIO_DIR / f"whatsapp-{ts}.md"
        linhas = [f"# WhatsApp — {len(zaps)} leads sem e-mail", ""]
        for p in zaps:
            linhas += [f"## {p['nome']}  ·  {p['telefone'] or 'sem telefone'}",
                       "", "```", p["msg"], "```", ""]
        wpp.write_text("\n".join(linhas), encoding="utf-8")
        resumo["wpp_md"] = wpp.relative_to(ROOT).as_posix()

    return resumo
