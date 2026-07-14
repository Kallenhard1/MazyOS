---
name: site-cliente
description: >
  Cria um site ou landing page pra cliente, na identidade do próprio cliente, pronto pra
  converter e pra nova busca (legível por pessoas e por IA). Use quando o usuário disser
  "fazer site pra [cliente]", "landing page", "criar site do cliente", "página de captura" ou /site-cliente.
---

# /site-cliente — Site e landing page pra cliente

Entrega um site rápido e bonito na cara do cliente, já preparado pra ser encontrado.

## Dependências

- **Estilo base:** `identidade/design-guide.md` (fallback quando o cliente não tem identidade forte).
- **Fontes locais:** `identidade/fontes/` quando for gerar versão impressa/print.
- **Deploy:** encadear com `/deploy-netlify` pra preparar a pasta publicável.
- **Contexto:** `_memoria/empresa.md`, `_memoria/preferencias.md`.

## O que pedir (se não vier no pedido)

1. **Cliente + ramo** e o **objetivo** do site (captar reserva, orçamento, cadastro, venda).
2. **Marca do cliente** — cores, fonte, logo, prints do site atual se houver.
3. **Conteúdo real** — serviços, contato, endereço, provas (só o que for verdadeiro).
4. **Uma página ou várias?** Padrão: uma landing de rolagem que converte.

## Passos

1. Definir a paleta e a tipografia espelhando a marca do cliente (design-guide como fallback).
2. Montar a landing: herói com promessa clara → prova/serviços → como funciona → CTA (WhatsApp/reserva) → rodapé.
3. Escrever a copy no tom do MarioLucash (direto, caloroso), mas na voz do cliente.
4. Deixar o site **legível pra nova busca**: conteúdo real, semântico, e (na etapa de deploy) os dados estruturados do negócio.
5. Salvar em `saidas/site-<slug>.html` e, pra publicar, chamar `/deploy-netlify`.

## Regras

- **Sem travessão (—)** no texto. Copy honesta: nada de número ou prova inventada.
- Responsivo de verdade: nada de scroll horizontal; imagens `max-width:100%`.
- Botão de conversão (WhatsApp/reserva) visível em todo lugar.
- A identidade é a do **cliente**; o design-guide MarioLucash só entra como fallback de qualidade.
- **Guarda-corpo:** a preparação técnica pra IA (dados estruturados) é entregue, não explicada na peça.
