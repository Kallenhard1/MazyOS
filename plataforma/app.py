"""Painel local do MarioLucash — casca web sobre os scripts de prospecção.

Rodar:  python plataforma/app.py   →   http://127.0.0.1:5000
Single-user, local, sem login. A fonte de verdade continua em crm/pipeline.csv
e dados/. Esta app só orquestra os scripts e mostra o que eles geram.
"""
from pathlib import Path

from flask import (Flask, abort, redirect, render_template, request,
                   send_file, url_for)

from servicos import arquivos as arq
from servicos import email_massa as mail
from servicos import funil as fun
from servicos import prospeccao as prosp

ROOT = Path(__file__).resolve().parent.parent
app = Flask(__name__)

# diretórios que a rota de download pode servir (sandbox contra path traversal)
DIRS_PERMITIDOS = [(ROOT / d).resolve() for d in ("dados", "saidas", "crm")]


@app.get("/")
def home():
    return redirect(url_for("prospeccao"))


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
        assunto_padrao=mail.ASSUNTO_PADRAO,
        corpo_padrao=mail.CORPO_PADRAO,
    )


@app.post("/envio/preview")
def envio_preview():
    ids = request.form.getlist("ids")
    assunto = request.form.get("assunto", "")
    corpo = request.form.get("corpo", "")
    por_id = {l.get("id"): l for l in mail.carregar_leads()}
    sel = [por_id[i] for i in ids if i in por_id][:3]
    previews = [mail.preencher(l, assunto, corpo) for l in sel]
    return render_template("partials/preview.html", previews=previews, n=len(ids))


@app.post("/envio/gerar")
def envio_gerar():
    ids = request.form.getlist("ids")
    resumo = mail.gerar_lote(
        ids, request.form.get("assunto", ""), request.form.get("corpo", ""))
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


@app.get("/funil/notion")
def funil_notion():
    return ('<div class="aviso" style="margin-top:10px">A sincronização com o '
            'Notion é feita pelo Claude via MCP (a app não acessa o Notion '
            'direto). Peça no chat: <em>"atualiza o Notion"</em> — ele lê o '
            'pipeline.csv, casa por nome e cria/atualiza os cards sem duplicar.</div>')


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
