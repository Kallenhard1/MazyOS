"""Painel local do MarioLucash — casca web sobre os scripts de prospecção.

Rodar:  python plataforma/app.py   →   http://127.0.0.1:5000
Single-user, local, sem login. A fonte de verdade continua em crm/pipeline.csv
e dados/. Esta app só orquestra os scripts e mostra o que eles geram.
"""
from datetime import date
from pathlib import Path

from flask import (Flask, abort, redirect, render_template,
                   request, send_file, url_for)

from servicos import ads as adssvc
from servicos import arquivos as arq
from servicos import conteudo as cont
from servicos import email_massa as mail
from servicos import funil as fun
from servicos import lead as leadsvc
from servicos import pdf
from servicos import prospeccao as prosp
from servicos import seo as seosvc

ROOT = Path(__file__).resolve().parent.parent
app = Flask(__name__)

# diretórios que a rota de download pode servir (sandbox contra path traversal)
DIRS_PERMITIDOS = [(ROOT / d).resolve() for d in ("dados", "saidas", "crm", "clientes", "marketing")]


@app.get("/")
def home():
    return redirect(url_for("hoje"))


@app.get("/hoje")
def hoje():
    grupos, contagens = fun.por_estagio()
    return render_template(
        "hoje.html", ativa="hoje",
        hoje_data=date.today().strftime("%d/%m/%Y"),
        pendentes=fun.followups(),
        novos=grupos["novo"][:12],
        contagens=contagens, total=sum(contagens.values()),
        estagios=fun.ESTAGIOS, rotulos=fun.ROTULOS)


# ---------------- Prospecção ----------------
@app.get("/prospeccao")
def prospeccao():
    return render_template(
        "prospeccao.html", ativa="prospeccao",
        categorias=prosp.CATEGORIAS_OSM,
        resumo=prosp.resumo_qualificados(),
        grupos=prosp.listar_arquivos(),
    )


@app.post("/prospeccao/buscar")
def prospeccao_buscar():
    ok, saida = prosp.buscar_osm(
        request.form.get("cidade", ""),
        request.form.get("categorias", ""),
        usar_plano=request.form.get("usar_plano") == "on",
    )
    return render_template("partials/log.html", ok=ok, saida=saida, titulo="Sourcing (OSM)")


@app.post("/prospeccao/qualificar")
def prospeccao_qualificar():
    ok, saida = prosp.qualificar()
    return render_template(
        "partials/log.html", ok=ok, saida=saida, titulo="Qualificação",
        resumo=prosp.resumo_qualificados(),
    )


@app.post("/prospeccao/abordagem")
def prospeccao_abordagem():
    ok, saida = prosp.gerar_abordagem(
        request.form.get("classe", "morno"),
        int(request.form.get("limite") or 0),
    )
    return render_template("partials/log.html", ok=ok, saida=saida, titulo="Abordagem")


@app.get("/prospeccao/arquivos")
def prospeccao_arquivos():
    return render_template("partials/arquivos.html", grupos=prosp.listar_arquivos())


# ---------------- Envio em massa ----------------
@app.get("/envio")
def envio():
    return render_template(
        "envio.html", ativa="envio",
        leads=mail.carregar_leads(),
        email_assunto=mail.EMAIL_ASSUNTO_PADRAO,
        email_corpo=mail.EMAIL_CORPO_PADRAO,
        whatsapp=mail.WHATSAPP_PADRAO,
    )


def _tpls():
    return (request.form.get("assunto", ""), request.form.get("corpo", ""),
            request.form.get("whatsapp", ""))


@app.post("/envio/preview")
def envio_preview():
    ids = request.form.getlist("ids")
    previews = mail.montar_previews(ids, *_tpls())
    return render_template("partials/preview.html", previews=previews, n=len(ids))


@app.post("/envio/gerar")
def envio_gerar():
    resumo = mail.gerar_lote(request.form.getlist("ids"), *_tpls())
    return render_template("partials/lote.html", r=resumo)


# ---------------- Funil / Kanban ----------------
def _board_ctx(msg=None):
    grupos, contagens = fun.por_estagio()
    return {"estagios": fun.ESTAGIOS, "rotulos": fun.ROTULOS,
            "grupos": grupos, "contagens": contagens, "msg": msg}


@app.get("/funil")
def funil():
    return render_template("funil.html", ativa="funil",
                           pendentes=fun.followups(), **_board_ctx())


@app.post("/funil/atualizar")
def funil_atualizar():
    ok, saida = fun.mudar_status(
        request.form.get("id", ""),
        request.form.get("status", ""),
        request.form.get("nota", ""),
        fun.validar_followup(request.form.get("followup", "")),
    )
    return render_template("partials/board.html",
                           **_board_ctx(msg=saida if ok else "⚠️ " + saida))


@app.post("/funil/editar")
def funil_editar():
    ok, saida = fun.editar_lead(request.form.get("id", ""), request.form)
    return render_template("partials/board.html",
                           **_board_ctx(msg=saida if ok else "⚠️ " + saida))


@app.get("/funil/notion")
def funil_notion():
    return ('<div class="aviso" style="margin-top:10px">A sincronização com o '
            'Notion é feita pelo Claude via MCP (a app não acessa o Notion '
            'direto). Peça no chat: <em>"atualiza o Notion"</em> — ele lê o '
            'pipeline.csv, casa por nome e cria/atualiza os cards sem duplicar.</div>')


@app.post("/funil/trabalhar")
def funil_trabalhar():
    estado, criado = leadsvc.criar_workspace(
        request.form.get("id", ""), request.form.get("obs", ""))
    if not estado:
        abort(404)
    branch = (request.form.get("branch", "").strip()
              or f"cliente/{estado['id']}")
    return render_template(
        "partials/trabalhar.html", estado=estado, criado=criado, branch=branch,
        lead_url=url_for("lead_ver", slug=estado["id"]))


# ---------------- Lead → Proposta (Fase 3) ----------------
@app.get("/lead")
def lead_index():
    return render_template("lead_index.html", ativa="lead",
                           workspaces=leadsvc.listar_workspaces())


def _lead_ctx(slug, estado):
    """Contexto compartilhado pelas telas/partials do lead."""
    return {"estado": estado, "etapas_meta": leadsvc.ETAPAS,
            "notas": leadsvc.ler_notas(slug), "assets": leadsvc.listar_assets(slug),
            "site": leadsvc.listar_site(slug),
            "prop": leadsvc.arquivos_proposta(slug),
            "dprop": leadsvc.dados_proposta(slug)}


def _etapas(slug, estado):
    return render_template("partials/etapas.html", **_lead_ctx(slug, estado))


@app.get("/lead/<slug>")
def lead_ver(slug):
    estado = leadsvc.ler_estado(slug)
    if not estado:
        abort(404)
    return render_template("lead.html", ativa="lead", **_lead_ctx(slug, estado))


@app.post("/lead/<slug>/etapa/<etapa>")
def lead_etapa(slug, etapa):
    estado = leadsvc.atualizar_etapa(
        slug, etapa, request.form.get("status"), request.form.get("nota", ""))
    if not estado:
        abort(404)
    return _etapas(slug, estado)


@app.post("/lead/<slug>/pesquisa")
def lead_pesquisa(slug):
    estado = leadsvc.rodar_pesquisa(slug)
    if not estado:
        abort(404)
    return _etapas(slug, estado)


@app.post("/lead/<slug>/mockup")
def lead_mockup(slug):
    estado = leadsvc.gerar_prompt_mockup(slug)
    if not estado:
        abort(404)
    return _etapas(slug, estado)


@app.post("/lead/<slug>/proposta")
def lead_proposta(slug):
    if leadsvc.salvar_config_proposta(slug, request.form) is None:
        abort(404)
    lead = leadsvc.achar_lead(slug)
    d = leadsvc.dados_proposta(slug)
    html = render_template(
        "proposta_base.html", nome=lead.get("nome", ""),
        setor=lead.get("setor", ""), cidade=lead.get("cidade", ""),
        data=date.today().strftime("%d/%m/%Y"), **d)
    res = leadsvc.escrever_proposta(slug, html)
    if not res:
        abort(404)
    return _etapas(slug, res["estado"])


@app.post("/lead/<slug>/enviar")
def lead_enviar(slug):
    resumo = leadsvc.montar_envio_proposta(slug)
    if resumo is None:
        abort(404)
    return _etapas(slug, leadsvc.ler_estado(slug))


@app.post("/lead/<slug>/diagnostico")
def lead_diagnostico(slug):
    d = leadsvc.dados_diagnostico(slug)
    if d is None:
        abort(404)
    html = render_template("diagnostico_pdf.html", **d)
    ok, engine = pdf.gerar(html, leadsvc.diagnostico_pdf_path(slug))
    leadsvc.registrar_diagnostico(slug, engine if ok else "falhou")
    return _etapas(slug, leadsvc.ler_estado(slug))


@app.post("/lead/<slug>/notas")
def lead_notas(slug):
    if leadsvc.salvar_notas(slug, request.form.get("texto", "")) is None:
        abort(404)
    return _etapas(slug, leadsvc.ler_estado(slug))


@app.post("/lead/<slug>/asset")
def lead_asset(slug):
    leadsvc.salvar_asset(slug, request.files.get("arquivo"))
    estado = leadsvc.ler_estado(slug)
    if not estado:
        abort(404)
    return _etapas(slug, estado)


# ---------------- Leitor de CSV ----------------
@app.get("/leitor")
def leitor():
    rel = request.args.get("rel", "")
    return render_template(
        "leitor.html", ativa="leitor",
        csvs=arq.listar_csvs(),
        dados=arq.ler_csv(rel) if rel else None,
        rel=rel,
    )


@app.get("/leitor/tabela")
def leitor_tabela():
    return render_template("partials/tabela_csv.html", dados=arq.ler_csv(request.args.get("rel", "")))


# ---------------- Conteúdo & Redes (Fase 4) ----------------
def _conteudo_fila(alvo):
    return render_template("partials/conteudo_fila.html",
                           grupos=cont.fila_da_tela(alvo), alvo=alvo,
                           rotulos=cont.ROTULO_STATUS)


@app.get("/conteudo")
def conteudo():
    alvo = request.args.get("alvo", "proprio")
    return render_template("conteudo.html", ativa="conteudo", alvo=alvo,
                           alvos=cont.listar_alvos(),
                           grupos=cont.fila_da_tela(alvo),
                           rotulos=cont.ROTULO_STATUS,
                           conteudo=cont.listar_conteudo(alvo))


@app.post("/conteudo/add")
def conteudo_add():
    alvo = cont.add_item(request.form.get("tema", ""),
                         request.form.get("alvo", "proprio"),
                         request.form.get("tipo", "carrossel"))
    return _conteudo_fila(alvo)


@app.post("/conteudo/remover")
def conteudo_remover():
    cont.remover(request.form.get("id", ""))
    return _conteudo_fila(request.form.get("alvo", "proprio"))


@app.post("/conteudo/status")
def conteudo_status():
    cont.mudar_status(request.form.get("id", ""), request.form.get("status", ""))
    return _conteudo_fila(request.form.get("alvo", "proprio"))


# atalho: a antiga tela Instagram vira "alvo = próprio" do módulo de conteúdo
@app.get("/instagram")
def instagram():
    return redirect(url_for("conteudo", alvo="proprio"))


# ---------------- SEO & GMB (Fase 5) ----------------
@app.get("/seo")
def seo():
    alvo = request.args.get("alvo", "proprio")
    return render_template("seo.html", ativa="seo", alvo=alvo,
                           alvos=cont.listar_alvos(),
                           etapas=seosvc.etapas(alvo),
                           prog=seosvc.progresso(alvo))


@app.post("/seo/avaliacoes")
def seo_avaliacoes():
    prompt = seosvc.prompt_avaliacoes(request.form.get("alvo", "proprio"),
                                      request.form.get("reviews", ""))
    return render_template("partials/seo_avaliacoes.html", prompt=prompt)


# ---------------- Anúncios (Fase 6) ----------------
@app.get("/ads")
def ads():
    alvo = request.args.get("alvo", "proprio")
    return render_template("ads.html", ativa="ads", alvo=alvo,
                           alvos=cont.listar_alvos(),
                           objetivos=adssvc.OBJETIVOS,
                           base_seo=adssvc.seo_base(alvo),
                           campanhas=adssvc.listar_campanhas(alvo),
                           exports=adssvc.exports_disponiveis(),
                           relatorios=adssvc.listar_relatorios(alvo))


@app.post("/ads/campanha")
def ads_campanha():
    prompt = adssvc.prompt_campanha(
        request.form.get("alvo", "proprio"), request.form.get("objetivo", ""),
        request.form.get("orcamento", ""), request.form.get("regiao", ""),
        request.form.get("obs", ""))
    return render_template("partials/ads_prompt.html", prompt=prompt)


@app.post("/ads/relatorio")
def ads_relatorio():
    prompt = adssvc.prompt_relatorio(request.form.get("alvo", "proprio"),
                                     request.form.getlist("rels"))
    return render_template("partials/ads_prompt.html", prompt=prompt,
                           vazio="Marque pelo menos um export acima.")


# ---------------- Download de arquivos (sandbox) ----------------
@app.get("/arquivo")
def arquivo():
    rel = request.args.get("rel", "")
    full = (ROOT / rel).resolve()
    if not full.is_file() or not any(
            str(full).startswith(str(d)) for d in DIRS_PERMITIDOS):
        abort(404)
    return send_file(full)


if __name__ == "__main__":
    print("Painel MarioLucash → http://127.0.0.1:5000  (Ctrl+C pra parar)")
    app.run(debug=True, port=5000)
