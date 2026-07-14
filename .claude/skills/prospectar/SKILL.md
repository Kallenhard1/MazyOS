---
name: prospectar
description: >
  Dispara a esteira de venda completa a partir de um nome + site de empresa: roda a auditoria
  de visibilidade em IA (a prova do problema), gera a proposta comercial e escreve a mensagem
  de abordagem no tom do Mario. Use quando o usuário disser "prospectar [empresa]", "abordar
  [cliente]", "rodar a esteira de venda", "montar tudo pra [empresa]" ou /prospectar.
---

# /prospectar — Esteira de venda de ponta a ponta

Orquestra as peças de venda numa sequência só. Pega um alvo e devolve prova + proposta + abordagem.

## Dependências

- Skill `/auditoria-ia` (a prova do problema).
- Skill `/proposta` (o PDF comercial).
- `_memoria/empresa.md`, `_memoria/preferencias.md` (tom da abordagem).

## O que pedir (se não vier no pedido)

1. **Nome + site** da empresa-alvo.
2. **Tipo de negócio** (define os campos que a IA procura).
3. **Um exemplo de busca real no Modo IA** (fortalece a auditoria; se não tiver, seguir com o que der).
4. **Canal da abordagem** (WhatsApp, e-mail, DM) e pra quem (dono, marketing, gestor de tráfego).

## Passos

1. **Auditoria** — rodar `/auditoria-ia` para o alvo. Guardar os achados reais.
2. **Proposta** — rodar `/proposta` usando o diagnóstico da auditoria como base da página 01.
3. **Mensagem de abordagem** — escrever uma mensagem curta no tom MarioLucash:
   - Abre com a dor concreta (sem entregar o método), não com "olá, tudo bem?".
   - Referencia a auditoria como isca ("montei um diagnóstico rápido do que a IA vê sobre vocês").
   - Um CTA só: agendar 30 min ou receber o material.
4. Entregar os 3 artefatos: link da auditoria, PDF da proposta, e a mensagem pronta pra colar.

## Regras

- **Nunca revelar o método** em nenhuma das peças. Só sintoma, nunca a cura.
- **Sem travessão (—)**; mensagem curta, humana, sem cara de template nem de IA.
- Provas e números só se forem verificáveis de verdade (vêm da auditoria).
- Não prometer posição no ranking nem resultado garantido. Prometer diagnóstico e trabalho.
- Se faltar dado do alvo (site fora do ar, sem exemplo de busca), avisar e seguir com o que dá.
