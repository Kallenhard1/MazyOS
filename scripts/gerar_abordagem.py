#!/usr/bin/env python3
"""
Gerador de abordagem — Etapa 3 (outreach personalizado).

Lê os leads já qualificados e gera, pra cada lead quente, uma mensagem de
WhatsApp e um e-mail personalizados — calibrados por tipo (b2c/b2b) e pelo
diagnóstico real de cada empresa (o que o qualificador encontrou).

Nada é enviado: o script só PREPARA. Saída:
    saidas/abordagens/abordagens.md   -> revisar e copiar/colar (WhatsApp)
    saidas/abordagens/emails.csv      -> to,subject,body (ponte pro Gmail)

Pra virar rascunho no Gmail: peça ao Claude "cria os rascunhos do
emails.csv" — ele lê o CSV e cria os drafts via MCP do Gmail pra você
revisar e enviar.

Uso:
    python gerar_abordagem.py
    python gerar_abordagem.py dados/prospects-qualificados.csv
    python gerar_abordagem.py --classe quente,morno --limite 50

Sem dependências externas: usa só a biblioteca padrão do Python 3.
"""

import argparse
import csv
import sys
from pathlib import Path

ASSINATURA_EMAIL = (
    "Mario Lucas\n"
    "Sites e automação para negócios locais\n"
    "mariolucasdasilvabarbosa@gmail.com · Instagram @mariolucash"
)


def to_float(v):
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return None


def to_int(v):
    f = to_float(v)
    return int(f) if f is not None else None


def gancho(lead):
    """Frase-âncora do diagnóstico, calibrada por status do site e tipo."""
    setor = (lead.get("setor") or "seu segmento").strip()
    cidade = (lead.get("cidade") or "sua região").strip()
    tipo = (lead.get("tipo") or "b2c").strip().lower()
    status = (lead.get("site_status") or "").strip()

    if status == "sem_site":
        if tipo == "b2b":
            return (f"quando um cliente pesquisa {setor} em {cidade} antes "
                    "de fechar com um fornecedor, não encontra vocês online")
        return (f"quem procura {setor} em {cidade} no Google não encontra "
                "vocês — acaba achando o concorrente que tem site")
    if status == "nao_responde" or status.startswith("erro_http_5"):
        return "o site de vocês está fora do ar — quem tenta acessar não consegue"
    if status.startswith("erro_http_4"):
        return "o site de vocês está com páginas quebradas (dá erro ao abrir)"
    if lead.get("https") == "nao":
        return ("o site de vocês aparece como 'não seguro' no navegador "
                "(falta o cadeado HTTPS), o que espanta cliente")
    if lead.get("mobile") == "nao":
        return ("o site de vocês não funciona bem no celular, que é de onde "
                "vem a maioria dos acessos hoje")
    return "dá pra melhorar bastante a presença digital de vocês"


def reputacao_frag(lead):
    nota, aval = to_float(lead.get("nota")), to_int(lead.get("avaliacoes"))
    if nota and aval and aval >= 20:
        return f"Vi que vocês têm ótimas avaliações ({nota:g}★). "
    return ""


def achados_cliente(lead):
    """Só os achados que fazem sentido MOSTRAR pro cliente (problemas
    digitais reais) — nunca os motivos internos de score (ticket, fit)."""
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
        import datetime as _dt
        if ano and ano <= _dt.date.today().year - 3:
            f.append(f"Site parece desatualizado (©{ano})")
    if (lead.get("tipo") or "").lower() == "b2b" and not (
            lead.get("linkedin") or "").strip():
        f.append("Sem LinkedIn — o comprador B2B pesquisa fornecedor lá")
    return f or ["Presença digital com espaço claro pra melhorar"]


def msg_whatsapp(lead):
    nome = lead.get("nome", "").strip()
    tipo = (lead.get("tipo") or "b2c").strip().lower()
    rep = reputacao_frag(lead)
    g = gancho(lead)
    if tipo == "b2b":
        return (
            f"Olá! Sou o Mario Lucas, trabalho com presença digital pra "
            f"empresas. {rep}Reparei que {g}. "
            f"Montei um diagnóstico rápido do {nome} com alguns pontos que "
            f"costumam pesar na hora do cliente escolher fornecedor. "
            f"Posso te enviar? É sem compromisso."
        )
    return (
        f"Oi! Tudo bem? Sou o Mario Lucas, mexo com sites e automação aqui "
        f"na região. {rep}Reparei que {g}. "
        f"Fiz um diagnóstico rápido (de graça) do que dá pra melhorar e "
        f"trazer mais cliente pro {nome}. Posso te mandar? Sem compromisso!"
    )


def email_assunto(lead):
    nome = lead.get("nome", "").strip()
    setor = (lead.get("setor") or "").strip()
    cidade = (lead.get("cidade") or "").strip()
    if (lead.get("tipo") or "b2c").lower() == "b2b":
        return f"{nome} — pontos sobre a presença digital de vocês"
    alvo = f"quem procura {setor} em {cidade}".strip()
    return f"{nome}: como aparecer pra {alvo}"


def email_corpo(lead):
    nome = lead.get("nome", "").strip()
    rep = reputacao_frag(lead)
    g = gancho(lead)
    achados = achados_cliente(lead)
    itens = "\n".join(f"  • {a}" for a in achados)
    pontos = f"\n\nNo diagnóstico rápido que fiz, os pontos principais foram:\n{itens}"
    saudacao = "Olá!" if (lead.get("tipo") or "b2c").lower() == "b2b" else f"Oi, pessoal do {nome}!"
    return (
        f"{saudacao}\n\n"
        f"Sou o Mario Lucas, trabalho com sites e automação para negócios "
        f"da região. {rep}Dei uma olhada na presença digital de vocês e "
        f"reparei que {g}.{pontos}\n\n"
        f"Preparei um diagnóstico de 1 página com o que dá pra resolver "
        f"(e quanto isso costuma trazer de retorno). Posso te enviar, sem "
        f"compromisso nenhum — se fizer sentido, a gente conversa.\n\n"
        f"Um abraço,\n{ASSINATURA_EMAIL}"
    )


def main():
    ap = argparse.ArgumentParser(description="Gera abordagens (WhatsApp + e-mail)")
    ap.add_argument("entrada", nargs="?", default="dados/prospects-qualificados.csv")
    ap.add_argument("--classe", default="quente",
                    help="classes a incluir (quente,morno,frio)")
    ap.add_argument("--limite", type=int, default=0)
    ap.add_argument("--saida-dir", default="saidas/abordagens")
    args = ap.parse_args()

    entrada = Path(args.entrada)
    if not entrada.exists():
        sys.exit(f"CSV não encontrado: {entrada}\n"
                 "Rode antes: python scripts/qualificar_leads.py dados/prospects.csv")
    classes = {c.strip().lower() for c in args.classe.split(",") if c.strip()}

    with open(entrada, newline="", encoding="utf-8-sig") as f:
        leads = [r for r in csv.DictReader(f)
                 if (r.get("classificacao") or "").lower() in classes]
    if args.limite:
        leads = leads[:args.limite]
    if not leads:
        sys.exit(f"Nenhum lead nas classes {classes}.")

    out_dir = Path(args.saida_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # markdown pra revisão humana
    md = ["# Abordagens geradas", "",
          f"> {len(leads)} leads · classes: {', '.join(sorted(classes))}", ""]
    # csv ponte pro Gmail (só quem tem e-mail)
    emails = []
    for l in leads:
        nome = l.get("nome", "").strip()
        contato = l.get("telefone", "").strip() or "—"
        email = (l.get("email") or "").strip()
        wpp = msg_whatsapp(l)
        assunto = email_assunto(l)
        corpo = email_corpo(l)
        md += [
            f"## {nome}  ·  {l.get('tipo','')}  ·  score {l.get('score','')}",
            f"**Contato:** {contato}"
            + (f"  ·  **E-mail:** {email}" if email else "  ·  _sem e-mail_"),
            "", "**WhatsApp:**", "", "```", wpp, "```", "",
            "**E-mail:**", "", f"*Assunto:* {assunto}", "", "```", corpo, "```",
            "", "---", "",
        ]
        if email:
            emails.append({"to": email, "subject": assunto, "body": corpo})

    (out_dir / "abordagens.md").write_text("\n".join(md), encoding="utf-8")
    with open(out_dir / "emails.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["to", "subject", "body"])
        w.writeheader()
        w.writerows(emails)

    print(f"{len(leads)} abordagens geradas.")
    print(f"  -> {out_dir/'abordagens.md'}  (revisar / WhatsApp)")
    print(f"  -> {out_dir/'emails.csv'}  ({len(emails)} com e-mail, ponte pro Gmail)")
    print("\nPra criar os rascunhos no Gmail: peça ao Claude "
          "'cria os rascunhos do emails.csv'.")


if __name__ == "__main__":
    main()
