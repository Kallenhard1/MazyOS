# Plataforma MarioLucash — Plano do MVP

> Painel local que amarra a operação de prospecção→proposta→envio num
> workflow visual, pra não se perder nas etapas. Backend = scripts que já
> existem em `scripts/`; fonte de verdade = `crm/pipeline.csv`. Casca nova
> por cima. Documento de plano — aprovar antes de construir.
>
> Contexto: ver `docs/CONTEXTO-PROSPECCAO.md` (o que já existe) e
> `_memoria/` (negócio, tom, foco). Fase zero: fechar o 1º cliente.

---

## 1. Princípios

1. **Reusar, não reescrever.** A plataforma é uma casca sobre `scripts/`.
   Nada de duplicar lógica de score, abordagem ou CRM.
2. **CSV continua a verdade.** `crm/pipeline.csv` é a fonte; a tela só lê e
   chama os scripts. Notion segue como espelho de leitura.
3. **Humano aperta enviar.** Nenhum email/WhatsApp sai sozinho. A tela gera
   rascunho; o Mario revisa e dispara. (LGPD/ToS: volume moderado +
   personalização.)
4. **Local e simples.** Single-user, roda na máquina do Mario. Sem login,
   sem deploy, sem banco. `python app.py` → abre no navegador.
5. **MVP enxuto primeiro.** As 2 telas prioritárias antes de qualquer
   ambição (terminal de mockup, proposta automática vêm depois).

---

## 2. Stack e decisões

| Decisão | Escolha | Porquê |
|---|---|---|
| Linguagem | **Python 3** | Todos os scripts já são Python; zero context-switch |
| Web framework | **Flask** | Mínimo atrito, server-rendered, sem build/npm |
| Frontend | **HTML + HTMX + CSS** | Interatividade sem SPA; recarrega pedaços da página |
| Dados | **`crm/pipeline.csv`** (+ arquivos em `dados/`, `saidas/`) | Já é a verdade |
| Rodar scripts | `subprocess` chamando os `scripts/*.py` | Mesma lógica do terminal, sem reimplementar |
| Email | rascunho via **MCP Gmail** (fluxo atual) | Nunca enviar direto; revisão humana |
| Estilo visual | `identidade/design-guide.md` | Consistência com a marca |

**Dependência nova:** só `flask` (`pip install flask`). HTMX é um `<script>`
de CDN. Sem mais nada.

---

## 3. Arquitetura

```
plataforma/
  app.py                # Flask: rotas + chama os scripts via subprocess
  servicos/
    prospeccao.py       # wrappers: rodar OSM/qualificar/abordagem, listar saídas
    funil.py            # ler/editar pipeline.csv (usa crm.py por baixo)
    email_massa.py      # montar lote de emails a partir de emails.csv/leads
  templates/            # HTML (base + uma por tela)
    base.html           # layout com a sidebar
    prospeccao.html
    email_massa.html
    funil.html
  static/
    estilo.css          # paleta da marca (design-guide)
    app.js              # HTMX helpers
```

A plataforma **não** acessa CSV "na mão" onde já existe script: pra mudar
status de lead, chama `crm.py status ...`; pra qualificar, chama
`qualificar_leads.py`. Assim a regra de negócio mora num lugar só.

**Sidebar (todas as telas, ordem de entrega):**

```
🔍 Prospecção      ← MVP 1
📧 Envio em massa   ← MVP 1
📊 Funil / Leads    ← MVP 2
🎯 Lead → Proposta  ← Fase 3
⚙️  Config          ← Fase 3 (chaves, contato, identidade)
```

---

## 4. Telas — detalhe

### 🔍 Prospecção (MVP 1)
- **Form de sourcing:** cidade + categorias (ou usar `dados/buscas-osm.csv`)
  → botão "Buscar (OSM)" roda `buscar_leads_osm.py` e mostra o resumo
  (quantos leads, quantos sem site).
- **Botão "Qualificar":** roda `qualificar_leads.py`, mostra
  quentes/mornos/frios + top 5.
- **Botão "Gerar abordagem":** roda `gerar_abordagem.py` (com filtro de
  classe/limite) → link pros arquivos em `saidas/abordagens/`.
- **Painel de arquivos gerados:** lista `dados/` e `saidas/` com data,
  tamanho e link pra abrir/baixar — resolve o "ver e separar melhor os
  arquivos gerados".
- Saída de cada script aparece num log na tela (stdout do subprocess).

### 📧 Envio em massa (MVP 1)
- **Seleção de leads:** tabela do `pipeline.csv` com checkbox, filtro por
  status/score/setor. Marca quem vai receber.
- **Editor do email:** assunto + corpo + anexos, com variáveis
  (`{nome}`, `{setor}`, `{cidade}`) preenchidas por lead. Preview ao vivo.
- **Anexos:** opção de anexar o diagnóstico PDF do lead (de
  `saidas/diagnosticos/`) quando existir.
- **Ação:** "Gerar rascunhos no Gmail" → cria um draft por lead via MCP
  (nunca envia). Leads sem email → mostra a mensagem de WhatsApp pra copiar.
- Backend reusa `gerar_abordagem.py` (mesma calibragem b2c/b2b e os
  `achados_cliente` — só problemas reais, nunca motivo interno de score).

### 📊 Funil / Leads (MVP 2)
- **Kanban** por estágio (novo→abordado→conversa→proposta→fechado/perdido),
  alimentado pelo `pipeline.csv`.
- Arrastar/мudar status → chama `crm.py status`. Editar nota e follow-up.
- **Follow-ups de hoje** em destaque (atrasados com ⚠️).
- Botão "Espelhar no Notion" (sincronização que hoje é manual).

### 🎯 Lead → Proposta (Fase 3 — a parte ambiciosa)
Fluxo guiado, etapa a etapa, com a tela final de validação em dropdown:
1. Pesquisa das plataformas atuais do lead (qualificador + busca)
2. Coleta inicial automática (script + skill)
3. Coleta aprofundada manual (textos, imagens, logo, dor) — upload/notas
4. **Mockup do site:** abrir o terminal do Claude Code já no contexto do
   lead (reusa o fluxo de mockup tipo `clientes/fryda-cafe-taubate/site/`)
5. Iteração manual
6. Gerar proposta personalizada a partir do template
   (`clientes/fryda-cafe-taubate/site/proposta.html` + `gerar_pdf.py`) com a
   identidade escolhida e as infos coletadas
7. **Tela de validação:** cada etapa num dropdown com status; botão
   "Mandar e-mail para o cliente" ou "Ajustar" por etapa
> Fase 3 é bem maior (terminal embutido, geração de proposta, orquestração
> de estado por lead). Fica pra depois do MVP provar valor.

---

## 5. Roadmap executável

**Fase MVP 1 — as 2 telas prioritárias** (entrega que já dá pra usar)
- [ ] Esqueleto Flask + `base.html` com a sidebar + `estilo.css` da marca
- [ ] Serviço `prospeccao.py` (rodar scripts via subprocess, capturar log)
- [ ] Tela Prospecção (sourcing + qualificar + abordagem + painel de arquivos)
- [ ] Serviço `email_massa.py` (montar lote a partir do pipeline + emails.csv)
- [ ] Tela Envio em massa (seleção + editor + preview + gerar rascunhos)
- [ ] README de como rodar (`python plataforma/app.py`)

**Fase MVP 2 — Funil visual**
- [ ] Serviço `funil.py` sobre `crm.py`
- [ ] Tela Kanban + mudar status + follow-ups
- [ ] Botão de espelhar no Notion

**Fase 3 — Lead → Proposta** (planejar em detalhe quando chegar a hora)
- [ ] Workflow guiado por lead + estado por etapa
- [ ] Terminal de mockup no contexto do lead
- [ ] Geração de proposta (template + identidade + infos)
- [ ] Tela de validação com dropdown e ação de envio

**Backlog — fora do escopo atual** (registrado, não planejado)
- [ ] 📸 **Criação de posts do Instagram** — tela pra gerar/aprovar conteúdo
  do marketing próprio. Reusaria as skills que já existem
  (`/publicar-tema` pra criar carrossel, `/aprovar-post` pra publicar via
  Meta Graph API). Entra depois do CRM/proposta estar de pé.

> **Mapa completo das próximas features:** ver `docs/PLATAFORMA-FEATURES.md`,
> que pega todas as skills e funções do MazyOS (conteúdo, SEO, anúncios,
> análise, sistema) e mapeia cada uma como feature da plataforma, com os
> padrões de integração (roda direto / handoff pro Claude Code / sistema).

---

## 6. Decisões — TRAVADAS (15/06/2026)

1. **Envio de email:** ✅ **Só rascunho no Gmail** (via MCP). Nada de envio
   direto no MVP — humano revisa e dispara. Seguro p/ LGPD/ToS.
2. **Paleta da marca:** ✅ **Monocromática** (preto/branco do logo) por
   enquanto, até o `design-guide.md` fixar cor de destaque.
3. **Nome da pasta:** ✅ `plataforma/`.
4. **Escopo do MVP 1:** ✅ **Prospecção + Envio em massa**. Funil kanban
   vai pro MVP 2.

Plano aprovado nessas condições — pronto pra construir o MVP 1.
