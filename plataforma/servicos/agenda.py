"""Agenda / scheduler do painel — Fase nova.

Tarefas agendadas que viram AVISO quando chega a hora; você clica Confirmar.
Três tipos:
  - lembrete: só um aviso (ex: "ligar pro fixo X")
  - evento:   algo com data (ex: "reunião com o Fryda")
  - comando:  ao confirmar, RODA um comando da whitelist (ex: próximo lote
              da campanha) e mostra o resultado. Humano sempre confirma.

Recorrência simples (horária/diária/semanal): ao confirmar, a tarefa avança
pra próxima ocorrência em vez de sumir. Estado em dados/agenda.json.

Segurança: só roda comandos da whitelist COMANDOS — nunca shell arbitrário.
"""
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AGENDA = ROOT / "dados" / "agenda.json"

# comandos que o botão Confirmar pode disparar (whitelist)
COMANDOS = {
    "campanha": {
        "rotulo": "Próximo lote da campanha (WhatsApp)",
        "cmd": ["python", "scripts/campanha.py", "rodar", "--tamanho", "4"],
    },
    "followups": {
        "rotulo": "Listar follow-ups de hoje",
        "cmd": ["python", "scripts/crm.py", "followups"],
    },
}
RECORRENCIAS = {
    "nenhuma": None, "horaria": timedelta(hours=1),
    "diaria": timedelta(days=1), "semanal": timedelta(weeks=1),
}
TIPOS = ("lembrete", "evento", "comando")


def ler():
    if not AGENDA.exists():
        return []
    try:
        return json.loads(AGENDA.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return []


def _salvar(ts):
    AGENDA.parent.mkdir(parents=True, exist_ok=True)
    AGENDA.write_text(json.dumps(ts, ensure_ascii=False, indent=2), encoding="utf-8")


def _quando(t):
    try:
        return datetime.fromisoformat(t["quando"])
    except (ValueError, KeyError):
        return datetime.max


def add(titulo, quando, tipo, recorrencia="nenhuma", comando="", detalhe=""):
    titulo = (titulo or "").strip()
    quando = (quando or "").strip()
    if not titulo or not quando:
        return
    ts = ler()
    ts.append({
        "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
        "titulo": titulo, "quando": quando,
        "tipo": tipo if tipo in TIPOS else "lembrete",
        "recorrencia": recorrencia if recorrencia in RECORRENCIAS else "nenhuma",
        "comando": comando if comando in COMANDOS else "",
        "detalhe": (detalhe or "").strip(),
        "status": "pendente",
        "criado": datetime.now().strftime("%d/%m/%Y %H:%M"),
    })
    _salvar(ts)


def remover(tid):
    _salvar([t for t in ler() if t.get("id") != tid])


def agendar_campanha(intervalo="horaria"):
    """Atalho: agenda o próximo lote da campanha de forma recorrente."""
    add("Disparar próximo lote da campanha",
        datetime.now().isoformat(timespec="minutes"),
        "comando", recorrencia=intervalo, comando="campanha",
        detalhe="Confirme pra gerar 4 mensagens prontas e marcar no funil.")


def confirmar(tid):
    """Confirma uma tarefa. Se for comando, roda; se recorrente, reagenda."""
    ts = ler()
    saida = None
    for t in ts:
        if t.get("id") != tid:
            continue
        if t.get("tipo") == "comando" and t.get("comando") in COMANDOS:
            saida = _rodar(t["comando"])
        rec = RECORRENCIAS.get(t.get("recorrencia", "nenhuma"))
        if rec:
            prox = _quando(t)
            agora = datetime.now()
            while prox <= agora:
                prox += rec
            t["quando"] = prox.isoformat(timespec="minutes")
            t["ultima"] = agora.strftime("%d/%m %H:%M")
        else:
            t["status"] = "feito"
        break
    _salvar(ts)
    return saida


def _rodar(chave):
    info = COMANDOS.get(chave)
    if not info:
        return {"ok": False, "rotulo": chave, "texto": "comando não permitido"}
    try:
        r = subprocess.run(info["cmd"], cwd=ROOT, capture_output=True,
                           text=True, timeout=180)
        texto = (r.stdout or "") + (("\n" + r.stderr) if r.stderr else "")
        return {"ok": r.returncode == 0, "rotulo": info["rotulo"], "texto": texto.strip()}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "rotulo": info["rotulo"], "texto": str(e)}


def vencidas(now=None):
    now = now or datetime.now()
    return sorted([t for t in ler()
                   if t.get("status", "pendente") == "pendente" and _quando(t) <= now],
                  key=_quando)


def proximas(now=None):
    now = now or datetime.now()
    return sorted([t for t in ler()
                   if t.get("status", "pendente") == "pendente" and _quando(t) > now],
                  key=_quando)


def n_vencidas():
    return len(vencidas())
