---
name: campanha
description: >
  Roda a campanha de abordagem dos leads em lotes, respeitando as regras de
  WhatsApp (só celular, lotes pequenos, espaçado, marca no funil depois).
  Repete até acabar os números. Use quando o usuário disser "rodar campanha",
  "/campanha", "abordar os leads", "próximo lote", "continuar a campanha" ou
  "roteiro de ligação".
---

# /campanha — Campanha de abordagem em lotes

Orquestra o `scripts/campanha.py` pra abordar o funil sem queimar o número.
Motor determinístico (o script faz tudo); aqui é a condução. **Nada é enviado
automaticamente** — o script prepara, o Mario revisa e dispara, e só então
marca no funil. Roda **até acabar os números** (quando não há pendente, para).

## Antes

Ler `_memoria/preferencias.md` (tom). Fonte de verdade: `crm/pipeline.csv`.
Regras do WhatsApp: só celular, lotes de ~4, espaçar 3-4/hora, revisar cada
mensagem, marcar depois de enviar.

## Ciclo (repetir até zerar)

1. **Status:** `python scripts/campanha.py status`. Mostrar o panorama
   (celulares pendentes, fixos, sem contato).
2. **Condição de parada:** se "celulares pendentes" = 0, avisar
   *"Acabaram os números da campanha de WhatsApp"* e **parar o ciclo**. Oferecer
   o roteiro de ligação dos fixos (passo 5) se ainda não foi feito.
3. **Próximo lote:** `python scripts/campanha.py whatsapp --tamanho 4`. Mostrar
   o arquivo gerado em `saidas/envio/` e lembrar: mandar espaçado (3-4/hora),
   revisar cada um antes de enviar.
4. **Marcar depois de enviar:** quando o Mario confirmar que disparou o lote,
   `python scripts/campanha.py marcar`. Aí volta ao passo 1 pro próximo lote.

> Cadência: um lote por vez, com intervalo. Pra automatizar o lembrete de hora
> em hora, dá pra envolver com `/loop 1h /campanha` — o loop para sozinho
> quando o status zerar (passo 2).

## Roteiro de ligação (fixos)

5. `python scripts/campanha.py ligacao` gera o roteiro pros telefones fixos
   (que não têm WhatsApp). O objetivo da ligação é **pegar o celular/WhatsApp
   do dono** pra mandar o diagnóstico — cada fixo convertido entra na campanha
   de WhatsApp. Depois de conseguir um número, adicionar ao funil.

## Plano completo de uma vez (opcional)

`python scripts/campanha.py whatsapp --ondas --tamanho 4` gera o plano inteiro
dividido em ondas (todos os pendentes), num arquivo só, pra quem prefere ver
tudo de uma vez em vez de lote a lote.

## Regras

- Nunca enviar WhatsApp/e-mail automaticamente. O script só prepara o `wa.me`;
  o humano abre, revisa e manda.
- Só marcar `marcar` depois que o Mario confirmar o envio do lote.
- Respeitar o espaçamento (3-4/hora). Lotes grandes = risco de ban.
- Fixo não recebe WhatsApp: vai pro roteiro de ligação, não pro lote.
