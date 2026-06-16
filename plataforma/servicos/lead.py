"""Workspace do lead (Fase 3). Ao 'trabalhar a proposta' de um lead do funil,
cria clientes/<slug>/ com briefing.md (dados do lead) e estado.json (status de
cada etapa do fluxo). Segue a convenção do CLAUDE.md (cliente novo → pasta
própria, autossuficiente). Tudo versionável no Git.
"""
import csv
import json
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "crm" / "pipeline.csv"
CLIENTES = ROOT / "clientes"
ENVIO = ROOT / "saidas" / "envio"

# As etapas do fluxo Lead → Proposta, na ordem. (chave, rótulo, descrição)
ETAPAS = [
    ("pesquisa", "Pesquisa das plataformas atuais",
     "O que o lead já tem online hoje (site, redes, Google)."),
    ("coleta", "Coleta de informações",
     "Textos, imagens, logo e a dor do cliente — base da proposta."),
    ("mockup", "Mockup do site",
     "Prompt pro Claude Code criar o mockup em site/ e iterar."),
    ("proposta", "Geração da proposta",
     "Preenche o template e gera a proposta em PDF."),
    ("validacao", "Validação e envio",
     "Revisar tudo e disparar o e-mail com a proposta anexa."),
]
ETAPA_ROTULO = {k: r for k, r, _ in ETAPAS}


def _leads():
    if not PIPELINE.exists():
        return []
    with open(PIPELINE, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def achar_lead(lead_id):
    return next((l for l in _leads() if l.get("id") == lead_id), None)


def _pasta(slug):
    return CLIENTES / slug


def _estado_path(slug):
    return _pasta(slug) / "estado.json"


def existe(slug):
    return _estado_path(slug).exists()


def ler_estado(slug):
    p = _estado_path(slug)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _salvar_estado(slug, estado):
    _estado_path(slug).write_text(
        json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")


def criar_workspace(lead_id, obs=""):
    """Cria clientes/<id>/ padronizado (briefing.md + estado.json + notas.md).
    Idempotente: se já existe, só devolve o estado atual. `obs` (opcional) entra
    no topo do notas.md. Retorna (estado, criado_agora)."""
    lead = achar_lead(lead_id)
    if not lead:
        return None, False
    slug = lead_id
    if existe(slug):
        return ler_estado(slug), False

    pasta = _pasta(slug)
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "assets").mkdir(exist_ok=True)

    estado = {
        "id": slug,
        "nome": lead.get("nome", ""),
        "criado": date.today().isoformat(),
        "etapas": {k: {"status": "pendente", "nota": ""} for k, _, _ in ETAPAS},
    }
    _salvar_estado(slug, estado)
    (pasta / "briefing.md").write_text(_briefing_md(lead), encoding="utf-8")
    obs_bloco = (f"\n## Observação inicial\n\n{obs.strip()}\n" if obs.strip() else "")
    (pasta / "notas.md").write_text(
        f"# Notas de coleta — {lead.get('nome','')}\n\n"
        "> Cole aqui textos, links e a dor do cliente. Imagens/logo em assets/.\n"
        + obs_bloco,
        encoding="utf-8")
    return estado, True


def atualizar_etapa(slug, etapa, status=None, nota=None):
    estado = ler_estado(slug)
    if not estado or etapa not in estado["etapas"]:
        return None
    if status in ("pendente", "ok"):
        estado["etapas"][etapa]["status"] = status
    if nota is not None:
        estado["etapas"][etapa]["nota"] = nota.strip()
    _salvar_estado(slug, estado)
    return estado


def progresso(estado):
    total = len(ETAPAS)
    ok = sum(1 for e in estado["etapas"].values() if e.get("status") == "ok")
    return ok, total


def listar_workspaces():
    """Leads que já têm workspace, com progresso."""
    if not CLIENTES.exists():
        return []
    out = []
    for p in sorted(CLIENTES.iterdir()):
        if (p / "estado.json").exists():
            est = ler_estado(p.name)
            ok, total = progresso(est)
            out.append({"id": est["id"], "nome": est["nome"],
                        "ok": ok, "total": total})
    return out


# ---------------- 3.2 — Pesquisa (automática) ----------------
def _scripts_mod(nome):
    """Importa um módulo de scripts/ sob demanda (reusa a lógica existente)."""
    import importlib
    import sys
    sp = str(ROOT / "scripts")
    if sp not in sys.path:
        sys.path.insert(0, sp)
    return importlib.import_module(nome)


_RESUMO_SITE = {
    "sem_site": "não tem site (oportunidade máxima)",
    "ok": "site no ar",
    "nao_responde": "site fora do ar",
}


def rodar_pesquisa(slug, timeout=8):
    """Checa o site atual do lead (reusa checar_site + achados_cliente) e grava
    o resultado no estado.json e em pesquisa.md. Marca a etapa como concluída."""
    lead = achar_lead(slug)
    estado = ler_estado(slug)
    if not lead or not estado:
        return None
    ql = _scripts_mod("qualificar_leads")
    ga = _scripts_mod("gerar_abordagem")
    check = ql.checar_site(lead.get("site"), timeout)
    achados = ga.achados_cliente({**lead, **check})

    status = check.get("site_status", "")
    estado["etapas"]["pesquisa"].update({
        "status": "ok",
        "nota": _RESUMO_SITE.get(status, status or "—"),
        "resultado": {
            "site": lead.get("site") or "",
            "site_status": status,
            "https": check.get("https", ""),
            "mobile": check.get("mobile", ""),
            "ano_site": check.get("ano_site", ""),
            "achados": achados,
            "quando": date.today().isoformat(),
        },
    })
    _salvar_estado(slug, estado)
    (_pasta(slug) / "pesquisa.md").write_text(
        _pesquisa_md(lead, check, achados), encoding="utf-8")
    return estado


def _pesquisa_md(lead, check, achados):
    linhas = [
        f"# Pesquisa — {lead.get('nome','')}", "",
        f"- **Site:** {lead.get('site') or '— (sem site)'}",
        f"- **Status:** {check.get('site_status','')}",
        f"- **HTTPS:** {check.get('https','') or '—'} · "
        f"**Mobile:** {check.get('mobile','') or '—'} · "
        f"**Ano:** {check.get('ano_site','') or '—'}",
        "", "## Achados (problemas digitais reais)", "",
    ]
    linhas += [f"- {a}" for a in achados]
    return "\n".join(linhas) + "\n"


# ---------------- 3.4 — Geração da proposta ----------------
PRECOS_PADRAO = {"essencial": "900", "profissional": "1.800",
                 "completo": "3.000", "manutencao": "99"}
CAMPOS_PROPOSTA = ["diagnostico", "essencial", "profissional", "completo", "manutencao"]


def dados_proposta(slug):
    """Valores pra pré-preencher o form da proposta (config salva ou defaults).
    O diagnóstico parte dos achados da pesquisa."""
    estado = ler_estado(slug)
    lead = achar_lead(slug)
    if not estado or not lead:
        return None
    cfg = estado["etapas"]["proposta"].get("config", {})
    achados = estado["etapas"]["pesquisa"].get("resultado", {}).get("achados", [])
    if achados:
        diag = (f"Pontos pra melhorar na presença digital de {lead.get('nome','')}:\n"
                + "\n".join(f"• {a}" for a in achados))
    else:
        diag = (f"{lead.get('nome','')} tem espaço claro pra crescer a presença "
                "digital e atrair mais cliente — rode a etapa de Pesquisa pra detalhar.")
    d = {"diagnostico": cfg.get("diagnostico") or diag}
    for k, v in PRECOS_PADRAO.items():
        d[k] = cfg.get(k) or v
    return d


def salvar_config_proposta(slug, config):
    estado = ler_estado(slug)
    if not estado:
        return None
    estado["etapas"]["proposta"]["config"] = {
        k: (config.get(k) or "").strip() for k in CAMPOS_PROPOSTA}
    _salvar_estado(slug, estado)
    return estado


def escrever_proposta(slug, html):
    """Grava clientes/<slug>/proposta.html, tenta o PDF (weasyprint) e marca a
    etapa. Retorna {pdf_ok, pdf_msg, estado}."""
    if not existe(slug):
        return None
    (_pasta(slug) / "proposta.html").write_text(html, encoding="utf-8")
    pdf_ok, pdf_msg = _tentar_pdf(html, _pasta(slug) / "proposta.pdf")
    estado = ler_estado(slug)
    estado["etapas"]["proposta"].update({
        "status": "ok", "nota": "proposta gerada", "pdf": pdf_ok})
    _salvar_estado(slug, estado)
    return {"pdf_ok": pdf_ok, "pdf_msg": pdf_msg, "estado": estado}


def _tentar_pdf(html, pdf_path):
    try:
        from weasyprint import HTML
        HTML(string=html).write_pdf(str(pdf_path))
        return True, "PDF gerado."
    except Exception:  # noqa: BLE001
        return False, ("PDF automático indisponível nesta máquina (weasyprint "
                       "precisa do runtime GTK). Abra a proposta.html e use "
                       "Ctrl+P → Salvar como PDF.")


def arquivos_proposta(slug):
    return {"html": (_pasta(slug) / "proposta.html").exists(),
            "pdf": (_pasta(slug) / "proposta.pdf").exists()}


# ---------------- 3.5 — Validação + envio ----------------
def montar_envio_proposta(slug):
    """Monta o e-mail (ou WhatsApp) de envio da proposta, com a proposta como
    anexo, e grava o arquivo de lote em saidas/envio/. Não envia — o rascunho é
    criado pelo Claude via MCP. Retorna o resumo (também salvo no estado)."""
    lead = achar_lead(slug)
    estado = ler_estado(slug)
    if not lead or not estado:
        return None
    arq = arquivos_proposta(slug)
    if not arq["html"]:
        return {"erro": "Gere a proposta antes (etapa 4)."}

    nome = lead.get("nome", "")
    email = (lead.get("email") or "").strip()
    anexo = f"clientes/{slug}/proposta.{'pdf' if arq['pdf'] else 'html'}"
    assunto = f"Proposta de site para {nome}"
    corpo = (
        f"Oi, pessoal do {nome}!\n\n"
        "Conforme conversamos, segue em anexo a proposta com os pacotes, "
        "prazos e valores. Qualquer dúvida me chama — dá pra ajustar o que "
        "fizer sentido pra vocês.\n\n"
        "Um abraço,\nMario Lucas\n"
        "mariolucasdasilvabarbosa@gmail.com · Instagram @mariolucash")

    ENVIO.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    if email:
        arquivo = ENVIO / f"proposta-{slug}-{ts}.csv"
        with open(arquivo, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["to", "subject", "body", "anexo"])
            w.writeheader()
            w.writerow({"to": email, "subject": assunto, "body": corpo, "anexo": anexo})
        resumo = {"canal": "email", "email": email}
    else:
        arquivo = ENVIO / f"proposta-{slug}-{ts}.md"
        arquivo.write_text(
            f"# Enviar proposta — {nome}\n\n"
            f"**WhatsApp:** {lead.get('telefone','') or 'sem telefone'}\n"
            f"**Anexo:** {anexo}\n\n```\n"
            f"Oi! Segue a proposta do site que preparei pra vocês 👇 "
            f"(qualquer dúvida me chama)\n```\n", encoding="utf-8")
        resumo = {"canal": "whatsapp", "telefone": lead.get("telefone", "")}

    resumo["arquivo"] = arquivo.relative_to(ROOT).as_posix()
    resumo["anexo"] = anexo
    estado["etapas"]["validacao"].update(
        {"status": "ok", "nota": f"envio montado ({resumo['canal']})", "envio": resumo})
    _salvar_estado(slug, estado)
    return resumo


# ---------------- 3.3 — Mockup (handoff Claude Code) ----------------
def listar_site(slug):
    d = _pasta(slug) / "site"
    if not d.exists():
        return []
    return [p.relative_to(d).as_posix() for p in sorted(d.rglob("*")) if p.is_file()]


def gerar_prompt_mockup(slug):
    """Monta um prompt pronto pra colar no terminal do Claude Code, a partir do
    que já foi coletado. Salva em prompt-mockup.md e no estado.json."""
    lead = achar_lead(slug)
    estado = ler_estado(slug)
    if not lead or not estado:
        return None
    prompt = _prompt_mockup(lead, slug, ler_notas(slug),
                            estado["etapas"]["pesquisa"].get("resultado", {}).get("achados", []),
                            listar_assets(slug))
    (_pasta(slug) / "prompt-mockup.md").write_text(prompt, encoding="utf-8")
    estado["etapas"]["mockup"]["prompt"] = prompt
    _salvar_estado(slug, estado)
    return estado


def _prompt_mockup(lead, slug, notas, achados, assets):
    nome = lead.get("nome", "")
    setor = lead.get("setor", "o negócio")
    cidade = lead.get("cidade", "")
    achados_txt = "\n".join(f"- {a}" for a in achados) or "- (rode a etapa de Pesquisa pra detectar)"
    assets_txt = "\n".join(f"- assets/{a}" for a in assets) or "- (nenhum asset enviado ainda)"
    notas_txt = (notas or "").strip() or "(sem notas de coleta ainda — preencha a etapa de Coleta)"
    return (
        f"Crie um mockup de site (landing page de uma página) para o cliente "
        f"abaixo, dentro da pasta `clientes/{slug}/site/` (gere `index.html` e os "
        f"assets que precisar).\n\n"
        f"**Cliente:** {nome} — {setor} em {cidade}.\n\n"
        f"**Dores / contexto coletado (notas.md):**\n{notas_txt}\n\n"
        f"**Problemas digitais hoje (pesquisa):**\n{achados_txt}\n\n"
        f"**Imagens disponíveis em `clientes/{slug}/assets/`:**\n{assets_txt}\n\n"
        f"**Diretrizes:**\n"
        f"- Marca monocromática (preto/branco), seguindo `identidade/design-guide.md`. "
        f"Não inventar cor de destaque.\n"
        f"- Use de referência de estrutura/qualidade o mockup em "
        f"`propostas/Fryda-Cafe-mockup/index.html` (hero, seções, CTA, WhatsApp "
        f"flutuante), adaptando ao segmento de {setor}.\n"
        f"- Página única, responsiva (mobile-first), rápida, sem dependências pesadas.\n"
        f"- Conteúdo real a partir das notas — nada de lorem ipsum. CTA claro "
        f"(WhatsApp / contato).\n"
        f"- Resolva os problemas apontados na pesquisa.\n\n"
        f"Itere comigo até ficar bom. Quando terminar, me avise pra eu seguir "
        f"pra proposta."
    )


# ---------------- 3.2b — Diagnóstico em PDF ----------------
_SOLUCAO = {
    "sem_site": "Um site profissional e rápido + perfil no Google Meu Negócio, "
                "pra vocês aparecerem exatamente quando alguém procura o que "
                "vocês fazem. É a base de tudo.",
    "quebrado": "Um site novo, leve e que funciona de verdade no celular, com o "
                "que o cliente precisa à mão e botão de contato direto.",
    "fraco": "Modernizar o site (HTTPS, mobile, visual atual) e ligar ele ao "
             "Google e ao WhatsApp, pra cada visita virar contato.",
}


def dados_diagnostico(slug):
    """Contexto do diagnóstico a partir do resultado da Pesquisa. None se a
    pesquisa ainda não rodou."""
    lead = achar_lead(slug)
    estado = ler_estado(slug)
    if not lead or not estado:
        return None
    res = estado["etapas"]["pesquisa"].get("resultado")
    if not res:
        return None
    status = res.get("site_status", "")
    if status == "sem_site":
        sol = _SOLUCAO["sem_site"]
    elif status == "nao_responde" or status.startswith("erro_http"):
        sol = _SOLUCAO["quebrado"]
    else:
        sol = _SOLUCAO["fraco"]
    return {
        "nome": lead.get("nome", ""), "setor": lead.get("setor", ""),
        "cidade": lead.get("cidade", ""), "score": lead.get("score", ""),
        "achados": res.get("achados", []), "solucao": sol,
        "data": date.today().strftime("%d/%m/%Y"),
    }


def registrar_diagnostico(slug, engine):
    estado = ler_estado(slug)
    if not estado or not estado["etapas"]["pesquisa"].get("resultado"):
        return None
    estado["etapas"]["pesquisa"]["resultado"]["diag_engine"] = engine
    _salvar_estado(slug, estado)
    return estado


def diagnostico_pdf_path(slug):
    return _pasta(slug) / "diagnostico.pdf"


# ---------------- 3.2 — Coleta (manual) ----------------
def ler_notas(slug):
    p = _pasta(slug) / "notas.md"
    return p.read_text(encoding="utf-8") if p.exists() else ""


def salvar_notas(slug, texto):
    if not existe(slug):
        return None
    (_pasta(slug) / "notas.md").write_text(texto or "", encoding="utf-8")
    return True


def listar_assets(slug):
    d = _pasta(slug) / "assets"
    if not d.exists():
        return []
    return [p.name for p in sorted(d.iterdir()) if p.is_file()]


def salvar_asset(slug, filestorage):
    """Salva um upload em clientes/<slug>/assets/. Retorna o nome salvo ou None."""
    from werkzeug.utils import secure_filename
    if not existe(slug) or not filestorage or not filestorage.filename:
        return None
    nome = secure_filename(filestorage.filename)
    if not nome:
        return None
    d = _pasta(slug) / "assets"
    d.mkdir(exist_ok=True)
    filestorage.save(str(d / nome))
    return nome


def _briefing_md(lead):
    linhas = [
        f"# Briefing — {lead.get('nome','')}", "",
        f"- **Tipo:** {lead.get('tipo','')}",
        f"- **Setor:** {lead.get('setor','')}",
        f"- **Cidade:** {lead.get('cidade','')}",
        f"- **Telefone:** {lead.get('telefone','') or '—'}",
        f"- **E-mail:** {lead.get('email','') or '—'}",
        f"- **Site atual:** {lead.get('site','') or '— (sem site)'}",
        f"- **Score:** {lead.get('score','')} ({lead.get('classificacao','')})",
        f"- **Status no funil:** {lead.get('status','')}",
        "", "## Notas do funil", "",
        lead.get("notas", "") or "_sem notas_", "",
    ]
    return "\n".join(linhas)
