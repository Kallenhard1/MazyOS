#!/usr/bin/env python3
"""
Campanha de abordagem — roda os leads em lotes, respeitando as regras.

Regras (pra não queimar o número):
  - WhatsApp só pra CELULAR (fixo não tem WhatsApp). Detecta pelo 9 do celular.
  - Em LOTES pequenos (padrão 4), pra mandar espaçado (3-4/hora).
  - Marca no funil só DEPOIS de enviar (comando `marcar`).
  - Roda ATÉ ACABAR os números: quando não há pendente, avisa que terminou.
  - Nada é enviado automaticamente: o script PREPARA, você dispara (wa.me).

Subcomandos:
    status                       panorama (móveis/fixos, contatados, pendentes)
    whatsapp [--tamanho N]       gera o PRÓXIMO lote de N celulares pendentes
    whatsapp --ondas [--tamanho N]   plano inteiro em ondas (até acabar tudo)
    marcar [--nota "..."]        marca o último lote como abordado (canal zap)
    ligacao                      roteiro de ligação dos fixos pendentes

Fonte de verdade: crm/pipeline.csv. Reusa a lógica do crm.py.
Sem dependências externas: só a biblioteca padrão do Python 3.
"""
import argparse
import json
import re
import sys
import urllib.parse
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import crm  # reusa carregar/salvar/COLS/HOJE/FOLLOWUP_PADRAO

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / crm.ARQUIVO_PADRAO
ENVIO = ROOT / "saidas" / "envio"
ESTADO = ROOT / "dados" / ".campanha-lote.json"

MSG = ("Oi! Tudo bem? Sou o Mario Lucas, sou de Taubaté e mexo com sites e "
       "presença digital. Reparei que quem procura {setor} em {cidade} no "
       "Google acaba não achando o {nome}, e isso é cliente indo pro "
       "concorrente. Montei um diagnóstico rápido (de graça) do que dá pra "
       "melhorar. Posso te mandar? Sem compromisso!")


# ---------- telefone ----------
def _e164(tel):
    primeiro = re.split(r"[;/]", tel or "")[0]
    d = re.sub(r"\D", "", primeiro).lstrip("0")
    if not d:
        return ""
    if d.startswith("55") and len(d) >= 12:
        return d
    if len(d) in (10, 11):
        return "55" + d
    return d if d.startswith("55") else "55" + d


def is_movel(tel):
    n = _e164(tel)
    return len(n) == 13 and n[4] == "9"


def wa_link(tel, msg):
    n = _e164(tel)
    return f"https://wa.me/{n}?text={urllib.parse.quote(msg)}" if n else ""


def msg_lead(l):
    return MSG.format(setor=(l.get("setor") or "seu segmento"),
                      cidade=(l.get("cidade") or "sua região"),
                      nome=(l.get("nome") or ""))


# ---------- seleção ----------
def carregar():
    return crm.carregar(PIPELINE)


def novo(l):
    return (l.get("status") or "novo") == "novo"


def pend_zap(leads):
    return [l for l in leads if novo(l) and is_movel(l.get("telefone", ""))]


def pend_fixo(leads):
    return [l for l in leads if novo(l) and (l.get("telefone") or "").strip()
            and not is_movel(l.get("telefone", ""))]


def escrever_lote(leads, titulo):
    ENVIO.mkdir(parents=True, exist_ok=True)
    ts = crm.HOJE.strftime("%Y%m%d")
    path = ENVIO / f"whatsapp-{ts}-{crm.datetime.datetime.now():%H%M%S}.md"
    linhas = [f"# {titulo} ({len(leads)} celulares)", ""]
    for l in leads:
        msg = msg_lead(l)
        linhas += [f"## {l['nome']}  ·  {l.get('setor','')}  ·  {l['telefone']}", ""]
        wa = wa_link(l["telefone"], msg)
        if wa:
            linhas += [f"[💬 Abrir no WhatsApp (mensagem pronta)]({wa})", ""]
        linhas += ["```", msg, "```", ""]
    path.write_text("\n".join(linhas), encoding="utf-8")
    return path


# ---------- comandos ----------
def cmd_status(args):
    leads = carregar()
    zap_total = [l for l in leads if is_movel(l.get("telefone", ""))]
    fixo_total = [l for l in leads if (l.get("telefone") or "").strip()
                  and not is_movel(l.get("telefone", ""))]
    pz, pf = pend_zap(leads), pend_fixo(leads)
    sem = [l for l in leads if not (l.get("telefone") or "").strip()]
    print(f"Funil: {len(leads)} leads")
    print(f"  📱 Celular (WhatsApp): {len(zap_total)}  | pendentes: {len(pz)}  | já abordados: {len(zap_total)-len(pz)}")
    print(f"  ☎️  Fixo (ligação):     {len(fixo_total)}  | pendentes: {len(pf)}")
    print(f"  ⚪ Sem contato:        {len(sem)}")
    if not pz:
        print("\n✅ Acabaram os celulares pendentes. Campanha de WhatsApp concluída.")


def cmd_whatsapp(args):
    leads = carregar()
    pz = pend_zap(leads)
    if not pz:
        print("✅ Acabaram os celulares pendentes. Campanha de WhatsApp concluída.")
        return
    if args.ondas:
        ondas = [pz[i:i + args.tamanho] for i in range(0, len(pz), args.tamanho)]
        ENVIO.mkdir(parents=True, exist_ok=True)
        path = ENVIO / f"campanha-whatsapp-ondas-{crm.HOJE:%Y%m%d}.md"
        linhas = [f"# Campanha WhatsApp — {len(pz)} celulares em {len(ondas)} ondas",
                  "", "> Mande **uma onda por vez**, com ~1h de intervalo. "
                  "Depois de cada onda, marque no funil.", ""]
        for n, onda in enumerate(ondas, 1):
            linhas += [f"## Onda {n} ({len(onda)})  ·  enviar +{n-1}h", ""]
            for l in onda:
                msg = msg_lead(l)
                linhas += [f"- **{l['nome']}** ({l.get('setor','')})  ·  {l['telefone']}",
                           f"  [💬 WhatsApp]({wa_link(l['telefone'], msg)})", ""]
        path.write_text("\n".join(linhas), encoding="utf-8")
        print(f"Plano completo: {len(pz)} celulares em {len(ondas)} ondas de {args.tamanho}.")
        print(f"  -> {path.relative_to(ROOT)}")
        return
    batch = pz[:args.tamanho]
    path = escrever_lote(batch, "WhatsApp — próximo lote")
    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    ESTADO.write_text(json.dumps({"ids": [l["id"] for l in batch],
                                  "arquivo": path.relative_to(ROOT).as_posix()},
                                 ensure_ascii=False), encoding="utf-8")
    print(f"Lote gerado: {len(batch)} celulares. Restam {len(pz)-len(batch)} pendentes.")
    print(f"  -> {path.relative_to(ROOT)}")
    print("Mande espaçado (3-4/hora). Depois rode: python scripts/campanha.py marcar")


def cmd_marcar(args):
    if not ESTADO.exists():
        print("Nenhum lote pendente de marcação. Rode 'whatsapp' antes.")
        return
    info = json.loads(ESTADO.read_text(encoding="utf-8"))
    ids = set(info.get("ids", []))
    leads = carregar()
    n = _marcar(leads, ids, args.nota or "abordado por WhatsApp (campanha)")
    crm.salvar(PIPELINE, leads)
    ESTADO.unlink()
    print(f"{n} leads marcados como abordado. Rode 'whatsapp' pro próximo lote.")


def _marcar(leads, ids, nota):
    """Marca uma lista de ids como abordado/whatsapp (mesma regra do crm)."""
    fu = (crm.HOJE + timedelta(days=crm.FOLLOWUP_PADRAO["abordado"])).isoformat()
    n = 0
    for l in leads:
        if l["id"] in ids:
            l["status"] = "abordado"
            l["ultimo_contato"] = crm.HOJE.isoformat()
            l["canal"] = "whatsapp"
            l["proximo_followup"] = fu
            carimbo = f"[{crm.HOJE:%d/%m}] {nota}"
            l["notas"] = (l["notas"] + " | " + carimbo).strip(" |") if l.get("notas") else carimbo
            n += 1
    return n


def cmd_rodar(args):
    """Modo ROTINA: gera o próximo lote E já marca como abordado, num passo só.
    É o que a rotina (loop/agendamento) chama de hora em hora, avançando o funil
    até acabar os celulares. O lote sai pronto pra você revisar e disparar."""
    leads = carregar()
    pz = pend_zap(leads)
    if not pz:
        print("✅ Acabaram os celulares pendentes. Campanha de WhatsApp concluída.")
        return
    batch = pz[:args.tamanho]
    path = escrever_lote(batch, "WhatsApp — lote da rotina (revisar e disparar)")
    _marcar(leads, {l["id"] for l in batch},
            "lote da rotina (revisar e disparar no WhatsApp)")
    crm.salvar(PIPELINE, leads)
    restam = len(pz) - len(batch)
    print(f"Lote da rotina: {len(batch)} celulares (marcados como abordado). "
          f"Restam {restam} pendentes.")
    print(f"  -> {path.relative_to(ROOT)}")
    if restam == 0:
        print("✅ Esse foi o último. Campanha de WhatsApp concluída.")


ROTEIRO = """# Roteiro de ligação — fixos do funil

> Objetivo da ligação NÃO é vender no telefone. É **pegar o WhatsApp do dono**
> pra mandar o diagnóstico. Cada fixo que vira contato de WhatsApp entra na
> campanha. Ligue em horário comercial, fora do pico do almoço.

## O que falar

**Abertura:** "Oi, bom dia! Falo com o responsável? Aqui é o Mario, sou de
Taubaté e trabalho com presença digital pra negócios daqui."

**Gancho:** "Liguei porque reparei que quem procura {SEU SETOR} em Taubaté no
Google não acha vocês fácil, e isso é cliente indo pro concorrente. Vocês têm
site hoje?"

**Descoberta:** "Como o cliente novo costuma achar vocês? Só indicação e
Instagram, ou tem mais alguma coisa?"

**Ponte (o gol):** "Montei um diagnóstico rápido, de 1 página, mostrando o que
dá pra melhorar. Posso te mandar no WhatsApp pra você ver com calma? Qual o
número?" → ANOTE O CELULAR.

**Encerramento:** "Fechado, te mando ainda hoje. Sem compromisso, qualquer
dúvida é só chamar. Obrigado!"

## Se vier objeção
- *"Não tenho interesse":* "Tranquilo! Posso te mandar só o diagnóstico mesmo
  assim? Se não fizer sentido, é só ignorar." (ainda assim tenta o WhatsApp)
- *"Já tenho quem cuida":* "Show. O diagnóstico serve até pra comparar. Te mando?"
- *"Tô sem tempo agora":* "Rapidinho, só o WhatsApp que eu te mando por lá."

## Lista pra ligar (marque o resultado)
"""


def cmd_ligacao(args):
    leads = carregar()
    fixos = pend_fixo(leads)
    if not fixos:
        print("Nenhum fixo pendente.")
        return
    ENVIO.mkdir(parents=True, exist_ok=True)
    path = ENVIO / f"roteiro-ligacao-{crm.HOJE:%Y%m%d}.md"
    linhas = [ROTEIRO]
    for l in fixos:
        linhas.append(f"- [ ] **{l['nome']}** ({l.get('setor','')}) · {l['telefone']}  "
                      f"→ celular: __________  · resultado: __________")
    linhas += ["", f"_Total: {len(fixos)} fixos pra ligar. Cada WhatsApp "
               "conseguido, adicione ao funil e ele entra na campanha._"]
    path.write_text("\n".join(linhas), encoding="utf-8")
    print(f"Roteiro de ligação: {len(fixos)} fixos -> {path.relative_to(ROOT)}")


def main():
    ap = argparse.ArgumentParser(description="Campanha de abordagem em lotes")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status").set_defaults(func=cmd_status)
    pw = sub.add_parser("whatsapp"); pw.add_argument("--tamanho", type=int, default=4)
    pw.add_argument("--ondas", action="store_true"); pw.set_defaults(func=cmd_whatsapp)
    pr = sub.add_parser("rodar"); pr.add_argument("--tamanho", type=int, default=4)
    pr.set_defaults(func=cmd_rodar)
    pm = sub.add_parser("marcar"); pm.add_argument("--nota", default=""); pm.set_defaults(func=cmd_marcar)
    sub.add_parser("ligacao").set_defaults(func=cmd_ligacao)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
