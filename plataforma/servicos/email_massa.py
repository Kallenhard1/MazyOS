"""Camada de envio em massa. Lê os leads do funil (crm/pipeline.csv), monta o
e-mail por lead a partir de um template com variáveis e GERA O LOTE — nunca
envia. O passo final (criar rascunhos no Gmail) é feito pelo Claude via MCP,
lendo o lote-*.csv. Leads sem e-mail viram mensagem de WhatsApp pra copiar.
"""
import csv
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "crm" / "pipeline.csv"
ENVIO_DIR = ROOT / "saidas" / "envio"

VARIAVEIS = ["nome", "setor", "cidade", "telefone"]

ASSUNTO_PADRAO = "{nome}: sua presença digital na internet"
CORPO_PADRAO = (
    "Oi, pessoal do {nome}!\n\n"
    "Sou o Mario Lucas, trabalho com sites e automação para negócios de "
    "{cidade}. Dei uma olhada na presença digital de vocês e acho que dá "
    "pra trazer mais cliente com alguns ajustes simples.\n\n"
    "Posso te mandar um diagnóstico rápido de 1 página, sem compromisso?\n\n"
    "Um abraço,\nMario Lucas\n"
    "mariolucasdasilvabarbosa@gmail.com · Instagram @mariolucash"
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


def preencher(lead, assunto_tpl, corpo_tpl):
    return {
        "nome": lead.get("nome", ""),
        "email": (lead.get("email") or "").strip(),
        "telefone": (lead.get("telefone") or "").strip(),
        "assunto": aplicar_vars(assunto_tpl, lead),
        "corpo": aplicar_vars(corpo_tpl, lead),
    }


def gerar_lote(ids, assunto_tpl, corpo_tpl):
    """Escreve saidas/envio/lote-<ts>.csv (com e-mail) e whatsapp-<ts>.md
    (sem e-mail). Devolve um resumo pra tela."""
    por_id = {l.get("id"): l for l in carregar_leads()}
    sel = [por_id[i] for i in ids if i in por_id]
    if not sel:
        return {"erro": "Nenhum lead selecionado."}

    com_email, sem_email = [], []
    for l in sel:
        p = preencher(l, assunto_tpl, corpo_tpl)
        if p["email"]:
            com_email.append({"to": p["email"], "subject": p["assunto"], "body": p["corpo"]})
        else:
            sem_email.append(p)

    ENVIO_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    resumo = {"total": len(sel), "com_email": len(com_email), "sem_email": len(sem_email)}

    lote_csv = ENVIO_DIR / f"lote-{ts}.csv"
    with open(lote_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["to", "subject", "body"])
        w.writeheader()
        w.writerows(com_email)
    resumo["lote_csv"] = lote_csv.relative_to(ROOT).as_posix()

    if sem_email:
        wpp = ENVIO_DIR / f"whatsapp-{ts}.md"
        linhas = [f"# WhatsApp — {len(sem_email)} leads sem e-mail", ""]
        for p in sem_email:
            linhas += [f"## {p['nome']}  ·  {p['telefone'] or 'sem telefone'}",
                       "", "```", p["corpo"], "```", ""]
        wpp.write_text("\n".join(linhas), encoding="utf-8")
        resumo["wpp_md"] = wpp.relative_to(ROOT).as_posix()

    return resumo
