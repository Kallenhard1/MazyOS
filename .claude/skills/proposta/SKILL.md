---
name: proposta
description: >
  Gera uma proposta comercial em PDF na estrutura do Mario (capa → diagnóstico → a entrega
  em fases/frentes → como trabalho → por que agora → próximos passos), com as fontes da marca
  embutidas e espelhando o visual do cliente. Use quando o usuário disser "fazer proposta",
  "proposta pra [cliente]", "gerar PDF da proposta", "apresentação comercial" ou /proposta.
---

# /proposta — Proposta comercial em PDF

Transforma um serviço + um cliente numa proposta PDF pronta pra apresentar ou enviar.
Segue o molde já validado (StarCad, Fryda, Nacional Inn).

## Dependências

- **Template-modelo:** `saidas/proposta-nacional-inn-print.html` (clonar a estrutura).
- **Fontes:** `identidade/fontes/Fraunces.ttf` (títulos) + `identidade/fontes/Inter.ttf` (corpo), via `@font-face`.
- **Gerador de PDF:** `node scripts/html-para-pdf.js <entrada.html> <saida.pdf>`.
- **Contexto:** `_memoria/empresa.md`, `_memoria/preferencias.md`; marca do cliente (cores/logo).

## O que pedir (se não vier no pedido)

1. **Cliente + assunto** (nome, ramo).
2. **Serviço proposto** (qual dos 4, ou combinação).
3. **Diagnóstico** — a dor concreta (se houver auditoria feita, puxar dela).
4. **Marca do cliente** — cor principal e, se tiver, logo. Serve pra espelhar o visual.
5. **Preços?** Perguntar. Se o usuário não quiser, montar sem valores ("definido por fase, na reunião").

## Passos

1. Clonar `proposta-nacional-inn-print.html` para `saidas/proposta-<slug>-print.html`.
2. Trocar só o conteúdo, mantendo a estrutura de 6 páginas A4:
   - **Capa** (painel na cor do cliente + título grande) com "Apresentado por MarioLucash".
   - **01 · Diagnóstico** — cards numerados com a dor real (+ faixa de stats se houver dados).
   - **02 · A entrega** — fases ou frentes com bullets do que entra.
   - **03 · Como eu trabalho** — pilares (acesso autorizado, nada quebra, vocês aprovam) + "o que está incluso".
   - **04 · Por que agora** — a urgência (first-mover quando for visibilidade em IA).
   - **05 · Próximos passos** — 3 passos + fecho + contato + rodapé confidencial.
3. Ajustar a paleta do `:root` pra espelhar a marca do cliente (mantendo Fraunces + Inter).
4. Gerar o PDF: `node scripts/html-para-pdf.js saidas/proposta-<slug>-print.html saidas/proposta-<slug>.pdf`.
5. Conferir que saiu com o nº de páginas certo (sem sobra) e entregar o caminho do PDF.

## Regras (guarda-corpos)

- **Nunca revelar o método técnico** (dados estruturados / JSON-LD / schema). Só a dor e o resultado.
- **Sem travessão (—)** no texto. Ver `_memoria/preferencias.md`.
- **Nunca inventar** número, prazo ou resultado não medido. Sem preço = "definido na reunião".
- Rodapé sempre: "material independente, não afiliado a [cliente]" e "confidencial".
- Contato: WhatsApp (12) 98159-2576 · mariolucas@mariolucash.com.br · mariolucash.com.br.
- Peça de cliente espelha a marca do cliente; a assinatura é sempre MarioLucash.
