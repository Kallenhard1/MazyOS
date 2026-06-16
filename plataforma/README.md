# Painel MarioLucash (MVP 1)

Casca web local sobre os scripts de prospecção. Não reescreve nada — orquestra
`scripts/` e mostra o que eles geram. Fonte de verdade segue em `crm/pipeline.csv`
e `dados/`. Veja o plano completo em [`docs/PLATAFORMA-MVP.md`](../docs/PLATAFORMA-MVP.md).

## Rodar localmente

### Pré-requisitos
- **Python 3** instalado (`python --version` — testado no 3.13).
- Estar na **raiz do projeto** (`MazyOS/`). Os scripts são chamados a partir
  daí, então rode sempre de lá — não de dentro de `plataforma/`.

### Passo a passo
```bash
# 1. (opcional, recomendado) ambiente virtual isolado
python -m venv .venv
.venv\Scripts\activate        # Windows (PowerShell/CMD)
# source .venv/bin/activate   # Git Bash / Linux / macOS

# 2. instalar a única dependência nova
pip install flask

# 3. subir o painel (a partir da raiz MazyOS/)
python plataforma/app.py
```

Vai aparecer:
```
Painel MarioLucash → http://127.0.0.1:5000  (Ctrl+C pra parar)
```

### Abrir e parar
- Abra **http://127.0.0.1:5000** no navegador (cai direto na tela de Prospecção).
- Pra **parar**, volte ao terminal e aperte **Ctrl + C**.
- O modo debug está ligado: salvou um arquivo, o servidor recarrega sozinho.

### Deu problema?
- **`ModuleNotFoundError: flask`** → faltou `pip install flask` (ou ativar o venv).
- **`No such file or directory: scripts/...`** ao rodar um botão → você subiu o
  app de dentro de `plataforma/`. Suba da raiz `MazyOS/`.
- **Porta 5000 ocupada** → edite o final do `app.py` (`app.run(..., port=5001)`)
  e abra na porta nova.
- **Sourcing/qualificação travando** → precisam de internet (consultam o
  OpenStreetMap e os sites dos leads). Sem rede, esses botões dão erro no log.

## Telas (MVP 1)

- **🔍 Prospecção** — roda sourcing (OSM), qualificação e abordagem pelos
  botões; mostra o resumo (quentes/mornos) e lista os arquivos gerados.
- **📧 Envio em massa** — seleciona leads do funil e escreve **dois templates
  separados** (e-mail e WhatsApp) com variáveis (`{nome}`, `{setor}`,
  `{cidade}`, `{telefone}`), pré-visualiza por canal e **gera o lote**. Não
  envia: quem tem e-mail vai pro `saidas/envio/lote-*.csv` (vira rascunho no
  Gmail quando você pede ao Claude *"cria os rascunhos do lote"*); quem não tem
  vira `saidas/envio/whatsapp-*.md` pra copiar.

- **📄 Leitor CSV** — abre qualquer `.csv` de `dados/`, `saidas/` ou `crm/`
  como tabela dentro do painel (filtro por linha, cabeçalho fixo, link de
  download). Só leitura. Atalho "ver tabela" também aparece nos arquivos da
  tela de Prospecção.
- **📊 Funil / Leads** (MVP 2) — kanban dos 6 estágios
  (novo→abordado→conversa→proposta→fechado/perdido) alimentado por
  `crm/pipeline.csv`. Mover um lead chama o `crm.py` (carimba contato + nota +
  follow-up automático). Painel de follow-ups do dia (atrasados com ⚠️) e botão
  "Espelhar no Notion" (handoff: a sync é feita pelo Claude via MCP).

- **🎯 Lead → Proposta** (Fase 3, em construção) — "Trabalhar proposta" num
  card do funil cria `clientes/<id>/` (briefing.md + estado.json + notas.md) e
  abre a tela do lead com as 5 etapas (pesquisa → coleta → mockup → proposta →
  validação) em accordion, cada uma com status e nota. **Já entregue: 3.0**
  (templates e-mail/WhatsApp separados) **+ 3.1** (workspace + estado) **+ 3.2**
  (pesquisa automática do site atual reusando o checador + coleta manual:
  notas.md e upload de imagens/logo pra `assets/`) **+ 3.3** (handoff do mockup:
  gera um prompt pronto — com briefing, notas e achados — pra colar no terminal
  do Claude Code, botão copiar, e acompanha a pasta `site/`) **+ 3.4** (gera a
  proposta: diagnóstico vindo da pesquisa + preços editáveis dos 3 pacotes →
  `proposta.html` branded A4) **+ 3.5** (validação: checklist das etapas + botão
  "Mandar e-mail" que monta o envio com a proposta anexa em `saidas/envio/` →
  rascunho no Gmail via Claude/MCP). **Fase 3 completa.**
  PDF: o weasyprint precisa do runtime GTK (não instalado), então por ora o PDF
  sai pelo navegador — abra a `proposta.html` e use Ctrl+P → Salvar como PDF.

Instagram (backlog) segue na sidebar como próximo depois da Fase 3.

## Como funciona por baixo

`app.py` (rotas) → `servicos/prospeccao.py` e `servicos/email_massa.py`
chamam os scripts via `subprocess` / leem os CSVs. Frontend é HTML + HTMX
(sem build). Estilo monocromático em `static/estilo.css` (paleta da marca
ainda sem cor de destaque — parte do preto/branco do logo).

## Segurança

Local, single-user, sem login. A rota de download (`/arquivo`) é restrita a
`dados/`, `saidas/` e `crm/`. Nenhum e-mail/WhatsApp é disparado pela app —
sempre passa por revisão humana + Claude/MCP.
