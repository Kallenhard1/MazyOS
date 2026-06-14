---
name: prospectar
description: >
  Roda o pipeline completo de prospecção do MarioLucash: qualifica leads,
  ranqueia por oportunidade, gera abordagem (WhatsApp + e-mail) e diagnóstico
  PDF dos quentes, e alimenta o CRM com follow-up. Use quando o usuário disser
  "prospectar", "/prospectar", "buscar clientes", "qualificar leads", "rodar a
  prospecção", "gerar abordagem pros leads" ou pedir pra trabalhar a lista de
  prospects.
---

# /prospectar — Pipeline de prospecção ponta a ponta

Orquestra os scripts em `scripts/` pra transformar uma lista de leads em
funil com abordagem pronta. Leia `_memoria/empresa.md` e
`_memoria/preferencias.md` antes pra manter tom e contexto. Foco atual:
**B2C local + B2B** (ver `marketing/automacao-prospeccao.md`).

As 4 etapas: **sourcing → qualificação → abordagem/diagnóstico → CRM.**
Humano decide o que abordar e aperta enviar; o resto é automático.

## Antes de rodar

- Scripts usam só Python 3 (padrão). O diagnóstico PDF precisa de
  `weasyprint` (`pip install weasyprint`).
- Conferir onde está a lista de leads. Se o usuário não tiver uma, ir pra
  Etapa 0 (sourcing).

## Workflow

### Passo 0 — Sourcing (só se não houver lista)
Perguntar a fonte e o alvo (cidade/setor). Então:
- **B2C local + B2B com ponto físico (Google Places):** precisa de
  `GOOGLE_MAPS_API_KEY`. Montar/usar um plano de busca CSV
  (`consulta,tipo,setor`, ver `dados/buscas-exemplo.csv`) e rodar:
  `python scripts/buscar_leads_places.py --buscas dados/buscas.csv`
- **B2B em escala (CNPJ aberto):** precisa do dump da Receita baixado.
  `python scripts/filtrar_cnpj.py --dir ./cnpj --cnae <cods> --uf <UF>`
- Ambos gravam em `dados/prospects.csv` (formato do qualificador).

Se o usuário já tem a lista, pular pro Passo 1.

### Passo 1 — Qualificar e ranquear
```
python scripts/qualificar_leads.py dados/prospects.csv
```
Gera `dados/prospects-qualificados.csv` (+ `.md`). Mostrar ao usuário o
resumo: quantos quentes/mornos e o top 5. Confirmar antes de seguir.

### Passo 2 — Abordagem + diagnóstico dos quentes
```
python scripts/gerar_abordagem.py
python scripts/gerar_diagnostico.py      # requer weasyprint
```
Saídas em `saidas/abordagens/` (abordagens.md + emails.csv) e
`saidas/diagnosticos/`. Avisar que as mensagens só expõem problemas
digitais reais (nunca os motivos internos de score).

### Passo 3 — Rascunhos no Gmail (opcional)
Se houver leads com e-mail em `saidas/abordagens/emails.csv`, oferecer:
ler o CSV e criar os rascunhos via MCP do Gmail (`mcp__Gmail__create_draft`,
um por linha: `to`, `subject`, `body`). **Nunca enviar** — só rascunho, o
usuário revisa e dispara. Leads sem e-mail: usar a mensagem de WhatsApp do
`abordagens.md`.

### Passo 4 — Alimentar o CRM
```
python scripts/crm.py importar dados/prospects-qualificados.csv --classe quente
python scripts/crm.py board
python scripts/crm.py followups
```
Mostrar o resumo do funil. Lembrar dos comandos do dia a dia:
- `crm.py status "<nome>" abordado --canal whatsapp --nota "..."`
- `crm.py followups` (quem cobrar hoje) · `crm.py board` (kanban)

### Passo 5 — Espelhar no Notion (board visual)
A fonte de verdade é o `crm/pipeline.csv`; o Notion é board de leitura.
Sincronizar via MCP:
- Base: **Prospecção — MarioLucash**
  - data_source_id: `2b3cc55d-f52a-473a-a751-10014632e7bd`
  - URL: https://app.notion.com/p/2ae35c0bfb2a4828b592e534a4b2cbaf
- Ler `crm/pipeline.csv`. Para cada lead, casar pelo nome (Empresa) com o
  que já existe no Notion (`notion-search` na data source):
  - **não existe** → `notion-create-pages` (parent = data_source_id)
  - **existe e mudou** → `notion-update-page` (status, follow-up, notas…)
- Propriedades: Empresa, Status, Tipo, Setor, Cidade, Telefone, Email,
  Site, Score, `date:Follow-up:start`, Canal, Notas.
- **Não duplicar:** sempre conferir os existentes antes de criar.
- Disparar só quando o usuário pedir ("atualiza o Notion") ou ao fim de um
  `/prospectar`, confirmando antes.

## Ao terminar

- Resumir o que rodou: nº de leads, quentes, abordagens/diagnósticos
  gerados, estado do funil.
- Espelhar o funil no **Notion** (Passo 5) e oferecer: pros leads quentes
  que viraram conversa, criar a proposta com o template
  (`propostas/Fryda-Cafe-mockup/gerar_pdf.py` como base).
- Se algo no fluxo mudou de forma duradoura (nova fonte, novo critério de
  score), seguir a regra de "Manter contexto atualizado" do `CLAUDE.md`.

## Regras

- Não enviar nada automaticamente (WhatsApp ou e-mail) — sempre revisão
  humana antes. Cold outreach: volume moderado + personalização (LGPD/ToS,
  ver `marketing/automacao-prospeccao.md`).
- Calibrar a mensagem por `tipo` (b2c/b2b) — os scripts já fazem; ao editar
  textos, manter o tom de `_memoria/preferencias.md` (direto, sem jargão).
- Contato do Mario nas peças: mariolucasdasilvabarbosa@gmail.com · @mariolucash.
