---
name: platform-vision-workflow-mvp
description: Mario quer uma plataforma/CRM local com workflow visual em sidebar guiando da prospecção ao envio de email
metadata:
  type: project
---

Em 15/06/2026 o Mario definiu a próxima grande frente: construir uma **interface (plataforma) / CRM MVP local** que amarre tudo que já existe em `scripts/` num workflow visual com sidebar, pra ele não se perder nas etapas e ver sempre onde focar.

Fluxo desejado, etapa a etapa:
Prospecção → Leads → Funil (Quente/Morno/Frio) → Selecionar lead p/ proposta → Pesquisa das plataformas atuais do lead → Coleta inicial (automação via script+skill) → Pesquisa aprofundada manual (textos, imagens, logo, dor do cliente) → Mockup do site (terminal Claude Code embutido) → Iteração manual → Template de proposta personalizado (HTML existente + identidade escolhida + infos coletadas) → Tela final de validação (etapas em dropdown, botão "Mandar e-mail" ou "Ajustar" por etapa) → Envio de email personalizado (script gera template HTML, com subject/corpo/anexos editáveis).

**Duas telas prioritárias** (quer mesmo sem mockup pronto):
1. **Envio de emails em massa** — disparar pros leads adquiridos.
2. **Prospecção** — roda todos os scripts já feitos e visualiza/organiza melhor os arquivos gerados.

Escopo pedido: "CRM e MVP simples por agora". Telas separadas numa sidebar.

**Backlog (fora do escopo atual, registrado em 15/06/2026):** uma tela de
**criação de posts do Instagram** pro marketing próprio, reusando as skills
`/publicar-tema` e `/aprovar-post`. Entra depois do CRM/proposta estar de pé.

**Why:** centraliza a operação freelancer (fase zero, fechar 1º cliente) e remove o atrito de pular entre scripts/arquivos soltos.
**How to apply:** ao planejar, partir das 2 telas prioritárias; reusar `scripts/` (qualificar, abordagem, crm.py) como backend e o `pipeline.csv` como fonte de verdade. Ver [[CONTEXTO-PROSPECCAO]] em docs/. Cold email respeita LGPD/ToS (volume moderado + personalização).
