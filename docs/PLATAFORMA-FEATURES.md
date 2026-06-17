# Plataforma MarioLucash — Mapa de Features

> Pega **todas as skills e funções do MazyOS** e mapeia cada uma como feature
> da `plataforma/`. Objetivo: a plataforma virar a casca visual de toda a
> operação, não só da prospecção. Complementa `docs/PLATAFORMA-MVP.md` (o que
> já foi construído) e `docs/CONTEXTO-PROSPECCAO.md` (o motor de prospecção).
>
> Princípio que vale pra tudo: **reusar, não reescrever.** A plataforma
> orquestra `scripts/` e as skills; nunca duplica a lógica.

---

## 1. Os três padrões de integração

Cada item do MazyOS vira feature de um destes três jeitos. Saber qual é o
padrão define como a tela funciona.

| Padrão | Quando | Como a tela faz | Exemplos |
|---|---|---|---|
| **A. Roda direto** | A lógica é determinística (Python puro, sem LLM) | Botão → `subprocess` chama o script → mostra resultado/arquivo | qualificar, crm, sourcing, abordagem, diagnóstico, relatório de ads, análise de dados |
| **B. Handoff pro Claude Code** | Precisa do agente/LLM pra criar conteúdo contextual | A tela monta o contexto e gera um **prompt pronto** pra colar no Claude Code (botão copiar); acompanha a pasta de saída | carrossel, publicar-tema, seo, responder-avaliações, email avulso, aprovar-post |
| **C. Sistema/meta** | É sobre o próprio workspace | Vira botão de ação ou tela de config | abrir, salvar, atualizar, instalar, novo-projeto, mapear-rotinas |

> O padrão B já existe e funciona na tela **📸 Instagram** (a fila gera o
> prompt do `/carrossel`). Todo módulo de conteúdo segue esse molde.

---

## 2. Inventário completo (skill/função → feature)

Status: ✅ pronto na plataforma · 🟡 parcial (parte feita ou só handoff) · 🔵 novo

### Skills
| Skill | O que faz | Vira feature | Módulo | Padrão | Status |
|---|---|---|---|---|---|
| `/prospectar` | Pipeline de prospecção ponta a ponta | Tela de prospecção | 🔍 Prospecção | A | ✅ |
| `/novo-projeto` | Cria pasta isolada por cliente | Workspace do lead (`clientes/<id>/`) | 🎯 Lead→Proposta | C | ✅ |
| `/email-profissional` | Rascunha e-mail a partir de contexto | Templates do envio + rascunhador avulso | 📧 Envio / ✍️ Conteúdo | A/B | 🟡 |
| `/carrossel` | Carrosséis 1080×1350 na identidade | Gerar carrossel (prompt + acompanha PNGs) | ✍️ Conteúdo & Redes | B | 🟡 |
| `/publicar-tema` | Tema → artigo + carrossel + 3 legendas | Esteira de conteúdo a partir de um tema | ✍️ Conteúdo & Redes | B | 🔵 |
| `/aprovar-post` | Publica blog + Instagram + Facebook | Botão publicar na fila de conteúdo | ✍️ Conteúdo & Redes | B | 🟡 |
| `/seo` | Fluxo SEO/GEO/Ads em 8 passos | Painel de SEO por cliente (8 etapas) | 🔎 SEO & GMB | B | 🔵 |
| `/responder-avaliacoes` | Respostas humanas pras reviews do Google | Caixa de avaliações + resposta sugerida | 🔎 SEO & GMB | B | 🔵 |
| `/anuncio-google` | Campanha completa em CSV pro Ads Editor | Montador de campanha (briefing → CSV) | 📣 Anúncios | A/B | 🔵 |
| `/relatorio-ads` | Relatório semanal de Google + Meta Ads | Tela de relatório (sobe export → resumo) | 📣 Anúncios | A | 🔵 |
| `/analisar-dados` | CSV/XLSX/PDF → resumo executivo | Análise de arquivo (além de só ler) | 📈 Análise | A/B | 🟡 |
| `/abrir` | Carrega o contexto do negócio | Dashboard "Hoje" (visão da operação) | ⚙️ Sistema | C | 🟡 |
| `/salvar` | Commit + push no GitHub | Botão "Salvar trabalho" (backup) | ⚙️ Sistema | C | 🔵 |
| `/atualizar` | Varre e atualiza a memória | Ação "Atualizar memória" na Config | ⚙️ Sistema | C | 🔵 |
| `/mapear-rotinas` | Acha repetições e vira skill | Sugeridor de skills (uso recorrente) | ⚙️ Sistema | C | 🔵 |
| `/instalar` | Setup inicial do negócio | Onboarding/Config (já está instalado) | ⚙️ Config | C | 🔵 |

### Funções (scripts/)
| Função | O que faz | Vira feature | Status |
|---|---|---|---|
| `buscar_leads_osm.py` | Sourcing grátis (OpenStreetMap) | Prospecção · botão "Buscar (OSM)" | ✅ |
| `buscar_leads_places.py` | Sourcing Google Places | Prospecção · fonte opcional (chave) | 🟡 |
| `filtrar_cnpj.py` | Sourcing B2B via CNPJ aberto | Prospecção · fonte B2B | 🟡 |
| `qualificar_leads.py` | Score 0–100 + classe | Prospecção · "Qualificar e ranquear" | ✅ |
| `gerar_abordagem.py` | WhatsApp + e-mail por lead | Prospecção/Envio · abordagem | ✅ |
| `gerar_diagnostico.py` | Diagnóstico PDF 1-página | Lead→Proposta · "Gerar diagnóstico" | ✅ |
| `crm.py` | Funil (estágios + follow-up) | Funil · kanban e mover card | ✅ |
| `notion_payload.py` | Payload do funil pro Notion | Funil · "Espelhar no Notion" | 🟡 |
| `propostas/**/gerar_pdf.py` (WeasyPrint) · `gerar-pdf.js` (Playwright) | Render de PDF (proposta, diagnóstico, apresentação) | Motor de PDF (`servicos/pdf.py`) | ✅ |

---

## 3. Mapa por módulo (sidebar completa)

A sidebar cresce dos 6 itens atuais para os módulos abaixo. Cada módulo é
**um serviço** em `plataforma/servicos/` + **uma tela** em `templates/`.

```
JÁ NA PLATAFORMA
  🔍 Prospecção          ✅   sourcing, qualificar, abordagem
  📧 Envio em massa       ✅   lote de e-mail/WhatsApp (rascunho)
  📊 Funil / Leads        ✅   kanban + follow-up + Notion
  🎯 Lead → Proposta      ✅   pesquisa→coleta→mockup→proposta→validação
  📄 Leitor CSV           ✅   abre qualquer .csv como tabela
  📸 Instagram            ✅   fila do marketing próprio (handoff)
  🏠 Hoje                 🟡   dashboard inicial

A CONSTRUIR (este mapa)
  ✍️  Conteúdo & Redes    🔵   carrossel, publicar-tema, aprovar-post
  🔎 SEO & GMB            🔵   fluxo /seo de 8 passos + avaliações
  📣 Anúncios             🔵   montar campanha + relatório semanal
  📈 Análise              🔵   /analisar-dados (resumo executivo)
  ⚙️  Sistema & Config    🔵   salvar, atualizar, chaves, contato, identidade
```

### ✍️ Conteúdo & Redes 🔵
Junta `/carrossel`, `/publicar-tema` e `/aprovar-post` num só lugar, no molde
da tela Instagram (que já faz handoff). Features:
- **Esteira de conteúdo:** digita um tema → gera o prompt do `/publicar-tema`
  (artigo de blog + carrossel + 3 legendas amarradas) pra rodar no Claude Code.
- **Carrossel avulso:** prompt do `/carrossel` (com ou sem foto IA), e
  acompanha os PNGs em `marketing/conteudo/`.
- **Fila + aprovar:** cada peça com status (rascunho → aprovado → publicado);
  botão que dispara o handoff do `/aprovar-post` (blog + IG + FB via Meta).
- Reusa: `identidade/design-guide.md` (paleta âmbar/creme agora definida).

### 🔎 SEO & GMB 🔵
A skill `/seo` é o fluxo mais rico (8 passos: demanda, concorrência, GMB,
on-page, conteúdo, ads, monitoramento, GEO). Vira um **painel por cliente**:
- Cada um dos 8 passos como etapa com status e saída salva (igual ao accordion
  do Lead→Proposta).
- **Avaliações (`/responder-avaliacoes`):** lista as reviews coladas/importadas
  do Google e gera a resposta sugerida (handoff), mantendo o tom da marca.
- Liga no diagnóstico que a prospecção já faz (GMB ausente = oportunidade).

### 📣 Anúncios 🔵
- **Montar campanha (`/anuncio-google`):** briefing (ou puxa da pesquisa SEO)
  → gera o CSV pronto pro Google Ads Editor, com link de download.
- **Relatório semanal (`/relatorio-ads`):** sobe os exports de Google + Meta
  → roda direto (padrão A) e mostra o resumo com alertas e recomendações.
  Encaixa no ciclo "fechou cliente → roda Ads → mede" do plano de ação.

### 📈 Análise 🔵
- **Resumo executivo (`/analisar-dados`):** sobe CSV/XLSX/PDF → resumo com os
  pontos principais. O Leitor CSV (✅) já mostra a tabela; isto adiciona a
  camada de interpretação. Útil pra planilha de prospects, export de Ads, etc.

### ⚙️ Sistema & Config 🔵
Onde moram as skills de núcleo, como ações e ajustes:
- **Salvar trabalho (`/salvar`):** botão que faz commit + push (backup visível).
- **Atualizar memória (`/atualizar`):** dispara a varredura que sincroniza
  `_memoria/` e o `CLAUDE.md`.
- **Config:** chaves (Google Places, Meta, Notion), contato padrão, identidade
  visual (cores/fontes/logo) que as telas de conteúdo e proposta consomem.
- **Rotinas (`/mapear-rotinas`):** sugere virar skill o que se repete muito.
- `/abrir` e `/instalar` viram, respectivamente, o **dashboard "Hoje"** e o
  **onboarding** (já rodado uma vez).

---

## 4. Roadmap por fases

Estende o roadmap do `PLATAFORMA-MVP.md` (Fases MVP 1, MVP 2 e 3 já entregues).

**Fase 4 — Conteúdo & Redes** (maior retorno depois da prospecção)
- [ ] `servicos/conteudo.py` + tela ✍️ (esteira `/publicar-tema`, carrossel,
      fila + aprovar). Reusa o padrão da tela Instagram.

**Fase 5 — SEO & GMB**
- [ ] `servicos/seo.py` + tela 🔎 (8 passos por cliente, estado por etapa)
- [ ] Submódulo de avaliações (`/responder-avaliacoes`)

**Fase 6 — Anúncios**
- [ ] `servicos/ads.py` + tela 📣 (montar campanha CSV + relatório semanal)

**Fase 7 — Análise & Sistema**
- [ ] `servicos/analise.py` (resumo executivo) na tela 📈
- [ ] Tela ⚙️ Config (chaves, contato, identidade) + ações Salvar/Atualizar

> Ordem pela utilidade na fase atual (fechar e atender os primeiros clientes):
> Conteúdo e SEO ajudam a entregar e a vender; Anúncios entram quando houver
> verba; Análise e Sistema são suporte. Reordenar conforme a operação pedir.

---

## 5. Nota de arquitetura

Cada feature nova segue o que já está montado:
- **Backend:** um arquivo em `servicos/` que ou roda o script via `subprocess`
  (padrão A) ou monta o prompt de handoff (padrão B). Nada de reimplementar
  lógica que já vive em `scripts/` ou nas skills.
- **Frontend:** uma tela em `templates/` herdando o `base.html` (sidebar +
  `static/estilo.css`). HTML + HTMX, sem build.
- **Verdade dos dados:** segue em `crm/pipeline.csv`, `dados/`, `clientes/<id>/`
  e `marketing/`. A plataforma lê e dispara; não vira um banco paralelo.
- **PDF:** sempre pelo `servicos/pdf.py` (Playwright; WeasyPrint de fallback),
  o mesmo motor das skills.
- **Envio:** nada sai sozinho. A plataforma gera rascunho/handoff; o humano
  revisa e dispara (Gmail via MCP / Meta via `/aprovar-post`).

Resultado: quando todos os módulos estiverem de pé, a `plataforma/` é o painel
único da operação MarioLucash, e o terminal do Claude Code vira o motor que ela
aciona — cada skill e cada função do MazyOS com um lugar visual pra acontecer.
