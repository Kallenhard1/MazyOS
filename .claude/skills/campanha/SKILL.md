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

## Modo rotina (Claude Code na web / agendado)

Pra rodar SOZINHO de hora em hora até acabar os números, sem esperar a
confirmação manual de cada lote, usar o comando `rodar`:

```
python scripts/campanha.py rodar --tamanho 4
```

Ele **gera o lote E já marca como abordado** num passo só (avança o funil),
e devolve o arquivo pronto. A rotina, a cada disparo:
1. roda `campanha.py rodar`
2. se gerou lote → **enviar o arquivo pro Mario** (`SendUserFile`, status
   *proactive*, pra chegar no celular) com um resumo curto
3. se imprimiu "Campanha concluída" → **parar a rotina** (acabaram os números)

**Importante:** o `rodar` marca como abordado assumindo que o Mario vai
disparar aquele lote. Se algum não for enviado, é só reverter pra `novo` no
funil. Por isso a cadência tem que bater com a presença do Mario (ele recebe e
dispara cada lote). Respeitar a regra anti-ban: ~4 por hora.

**Como agendar de verdade:**
- **Sessão viva (hoje):** `/loop 1h` rodando o passo da rotina acima. Como o
  universo de WhatsApp é pequeno (uns 14), termina em poucas horas numa sessão.
- **Durável (todo dia):** criar um *trigger agendado* no Claude Code na web
  apontando pro prompt "rodar o próximo lote da campanha e me enviar". Ver
  https://code.claude.com/docs/en/claude-code-on-the-web. Bom pra quando
  entrar gente nova no funil (ex: depois das ligações dos fixos).

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
