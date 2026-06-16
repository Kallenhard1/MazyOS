# Fase 3 — Lead → Proposta (plano)

> A parte ambiciosa da plataforma: pegar um lead do funil e levá-lo, num
> workflow guiado, até a proposta personalizada e o e-mail de envio. Documento
> de plano — aprovar antes de construir. Continua do [MVP](PLATAFORMA-MVP.md);
> backend reusa `scripts/`, `crm/pipeline.csv` e o motor de proposta em
> `propostas/Fryda-Cafe-mockup/` (`proposta.html` + `gerar_pdf.py`, weasyprint).

---

## 1. Princípios (herdados + novos)

- **Reusar.** Proposta = `proposta.html` + `gerar_pdf.py`. Pesquisa = qualificador.
  Envio = tela de Envio em massa. Nada reescrito.
- **Estado por lead vive em `clientes/<slug>/`** — segue a convenção do
  `CLAUDE.md` (cliente novo → pasta com `briefing.md`). Versionável no Git.
- **Mockup é handoff, não terminal embutido.** Rodar o Claude Code *dentro* da
  página não é viável; o painel prepara o workspace + um prompt pronto pra
  colar no terminal do Claude Code. (Ver decisão 1.)
- **Humano valida e aperta enviar.** A tela final só dispara rascunho via Claude/MCP.

---

## 2. Sub-fases (entrega incremental)

### 3.0 — Separar template de e-mail × WhatsApp  ⟵ pedido explícito
Hoje `email_massa.py` usa um corpo só pros dois canais. Separar:
- `TEMPLATE_EMAIL` (assunto + corpo, formal-leve, com assinatura) e
  `TEMPLATE_WHATSAPP` (curto, informal, sem assunto/assinatura).
- Na tela **Envio em massa**: dois editores (E-mail | WhatsApp), cada um com
  suas variáveis (`{nome}`, `{setor}`, `{cidade}`).
- `gerar_lote`: e-mail usa o template de e-mail; quem não tem e-mail usa o de
  WhatsApp no `whatsapp-*.md`. Preview mostra o canal certo por lead.
- Base também pra personalizar a abordagem na proposta.

### 3.1 — Workspace do lead + estado por etapa
- Ação "Trabalhar proposta" num card do funil → cria `clientes/<slug>/` com
  `briefing.md` (dados do lead) e `estado.json` (status de cada etapa).
- Nova tela **Lead** com as etapas como accordion/dropdown, cada uma com
  status (⬜ pendente / ✅ ok) e botão "Ajustar". Estado persiste no JSON.

### 3.2 — Pesquisa + coleta
- **Automático:** rodar o qualificador no site atual do lead + resumo do que
  ele já tem online (status do site, redes).
- **Manual:** área pra colar textos, anexar imagens/logo e descrever a dor do
  cliente. Tudo salvo em `clientes/<slug>/` (assets/ + notas.md).

### 3.3 — Mockup do site (handoff Claude Code)
- O painel monta um **brief** a partir do briefing + coleta e gera um **prompt
  pronto** ("crie o mockup do site do <lead> em clientes/<slug>/site/ …").
- Botão "copiar prompt" → você cola no terminal do Claude Code e itera.
  A tela acompanha a pasta `site/` (lista os arquivos gerados).

### 3.4 — Geração da proposta
- Copia `proposta.html` → `clientes/<slug>/proposta.html`, preenche nome,
  diagnóstico, pilares, preços e contato com os dados coletados, roda
  `gerar_pdf.py` → `proposta.pdf`. Preview do PDF na tela.

### 3.5 — Tela de validação + envio
- Cada etapa num dropdown com seu status; "Ajustar" volta pra etapa.
- Tudo ok → botão **"Mandar e-mail para o cliente"**: monta o lote (reusa
  Envio) com o template de e-mail + a **proposta.pdf anexa** → rascunho via
  Claude/MCP. Nunca envia sozinho.

---

## 3. Roadmap

- [x] **3.0** Separar templates e-mail/WhatsApp (Envio em massa) ✅
- [x] **3.1** Workspace `clientes/<slug>/` + estado.json + tela Lead (etapas) ✅
- [x] **3.2** Pesquisa automática + coleta manual (assets, dor) ✅
- [x] **3.3** Brief + prompt de mockup (handoff) + acompanhar `site/` ✅
- [x] **3.4** Gerar proposta (proposta.html branded + tentativa de PDF) ✅
      _PDF automático (weasyprint) precisa do runtime GTK, ainda não instalado
      nesta máquina → por ora o PDF sai via navegador (Ctrl+P → Salvar como PDF)._
- [x] **3.5** Tela de validação (checklist) + envio com proposta anexa ✅

**Fase 3 concluída (15/06/2026).** Falta só o PDF automático (weasyprint/GTK).

---

## 4. Decisões — TRAVADAS (15/06/2026)

1. **Mockup:** ✅ **Handoff** — o painel prepara o workspace + um prompt pronto
   pra colar no terminal do Claude Code. Nada de terminal embutido.
2. **Estado do lead:** ✅ `clientes/<slug>/estado.json` + `briefing.md`
   (segue o `CLAUDE.md`).
3. **Primeira fatia:** ✅ **3.0 + 3.1** primeiro (separação de templates +
   workspace/tela do Lead), depois empilho 3.2→3.5.

Plano aprovado — construindo 3.0 + 3.1.

---

## 5. Anotado para próximas fases (15/06/2026)

Pedidos do Mario, fora do escopo da 3.x atual — planejar quando chegar a hora:

1. ✅ **Branch padronizada por cliente.** "Trabalhar proposta" abre um **modal
   com form** (branch + observação) que cria a pasta `clientes/<id>/`
   padronizada e gera o comando `git checkout -b cliente/<slug>` pra copiar —
   **handoff**, a app não toca no git. _Feito 15/06/2026._
2. ✅ **Kanban drag-and-drop.** Arrastar cards entre os estágios (chama o mesmo
   `/funil/atualizar`). O select "mover / editar" segue pra quando precisar de
   nota/follow-up. _Feito 15/06/2026._
3. ✅ **Filtro por label na visão de leads.** Botões quente / morno / frio /
   todos no topo do funil filtram os cards (client-side, sobrevive aos
   re-renders). _Feito 15/06/2026._
4. ✅ **Terminal → Handoff.** Tentamos um painel-espelho (tail de log via `tee`),
   mas o Mario preferiu o **handoff** puro: a plataforma gera o prompt/comando e
   ele roda no terminal local do Claude Code, que fica exatamente como é. O
   espelho foi **removido**; o handoff do mockup já vive na etapa 3.3 (botão
   "copiar prompt") e o handoff do git no modal (item 1). _Decidido 15/06/2026._
