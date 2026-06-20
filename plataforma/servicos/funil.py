"""Camada do funil (CRM). Lê crm/pipeline.csv agrupado por estágio e muda o
estágio de um lead chamando o scripts/crm.py (mesma regra do terminal:
carimba último contato, follow-up automático por estágio, nota com data).
Pipeline.csv continua a fonte de verdade.
"""
import csv
import datetime
import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "crm" / "pipeline.csv"


def _carregar_crm():
    """Importa scripts/crm.py por caminho (evita colidir com a pasta de dados
    crm/) pra reusar a lógica em processo, sem subir subprocess a cada edição."""
    spec = importlib.util.spec_from_file_location(
        "crm_logica", ROOT / "scripts" / "crm.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_crm = _carregar_crm()
ESTAGIOS = ["novo", "abordado", "conversa", "proposta", "fechado", "perdido"]
ROTULOS = {
    "novo": "⚪ Novo", "abordado": "📨 Abordado", "conversa": "💬 Conversa",
    "proposta": "📄 Proposta", "fechado": "✅ Fechado", "perdido": "❌ Perdido",
}
HOJE = datetime.date.today()


def _int(v):
    try:
        return int(float(str(v).replace(",", ".")))
    except (TypeError, ValueError):
        return 0


def carregar():
    if not PIPELINE.exists():
        return []
    with open(PIPELINE, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def por_estagio():
    """Retorna (grupos, contagens). Grupos: estágio -> leads ordenados por score."""
    from servicos import email_massa as _mail
    from servicos import zap
    leads = carregar()
    grupos = {e: [] for e in ESTAGIOS}
    for l in leads:
        l["wa"] = zap.link(l.get("telefone", ""),
                           _mail.aplicar_vars(_mail.WHATSAPP_PADRAO, l))
        grupos.get(l.get("status") or "novo", grupos["novo"]).append(l)
    for e in ESTAGIOS:
        grupos[e].sort(key=lambda l: _int(l.get("score")), reverse=True)
    contagens = {e: len(grupos[e]) for e in ESTAGIOS}
    return grupos, contagens


def _parse_data(s):
    try:
        return datetime.date.fromisoformat((s or "").strip())
    except ValueError:
        return None


def followups(ate=None):
    """Leads com follow-up vencido/até a data, fora de fechado/perdido."""
    limite = _parse_data(ate) or HOJE
    pend = []
    for l in carregar():
        d = _parse_data(l.get("proximo_followup"))
        if d and l.get("status") not in ("fechado", "perdido") and d <= limite:
            pend.append({**l, "_data": d, "_atrasado": d < HOJE})
    pend.sort(key=lambda l: l["_data"])
    return pend


def mudar_status(lead_id, novo, nota="", followup=""):
    """Move o lead de estágio (mesma regra do crm.py, agora em processo). (ok, saida)."""
    if novo not in ESTAGIOS:
        return False, "Estágio inválido."
    if not (lead_id or "").strip():
        return False, "Lead sem id."
    return _crm.mudar_status_lead(str(PIPELINE), lead_id.strip(), novo,
                                  nota=nota.strip(), followup=followup.strip())


EDITAVEIS = _crm.EDITAVEIS


def editar_lead(lead_id, campos):
    """Edita dados de um lead (id/score/estágio intactos). Em processo, sem
    subprocess. Só envia os campos editáveis presentes. Retorna (ok, saida)."""
    lead_id = (lead_id or "").strip()
    if not lead_id:
        return False, "Lead sem id."
    dados = {k: (campos.get(k) or "").strip() for k in EDITAVEIS if k in campos}
    return _crm.editar_lead_dados(str(PIPELINE), lead_id, dados)


def validar_followup(s):
    """Aceita vazio, +Nd/+Nw ou AAAA-MM-DD. Devolve a string válida ou ''."""
    s = (s or "").strip()
    if not s or re.match(r"^\+\d+[dw]$", s) or _parse_data(s):
        return s
    return ""
