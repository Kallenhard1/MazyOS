---
name: auditoria-ia
description: >
  Cria uma "prova do problema" de visibilidade em IA pra prospectar clientes: inspeciona
  os dados estruturados do site de um negócio (o que a IA do Google/Gemini realmente lê),
  compara com concorrentes, e gera uma página de auditoria editorial pronta pra apresentar
  ou mandar no WhatsApp — com CTA pro plano de automação do Mario.
  Use quando o usuário disser "auditoria de IA", "prova do problema", "diagnóstico de
  visibilidade", "prospectar [empresa]", "analisar o site do [cliente]", ou /auditoria-ia.
---

# /auditoria-ia — Auditoria de Visibilidade em IA (prova do problema)

Ferramenta de **venda**. Pega um negócio → inspeciona de verdade o que a IA enxerga no
site dele → entrega uma página de auditoria que faz o gestor querer resolver, e ancora o
CTA no plano de automação do Mario.

O valor está em ser **real e irrefutável**: os achados vêm de inspeção de verdade, nunca
inventados. E o **método fica escondido** — a página nomeia a doença (dados estruturados
ausentes), nunca a cura (nada de JSON-LD, schema.org, "como implementar").

---

## Dependências

- **Logo e contato do Mario:** já embutidos no exemplo (`exemplo-nacional-inn.html`). Não trocar.
- **Contexto do negócio:** `_memoria/empresa.md`, `_memoria/preferencias.md` (calibrar tom).
- **Output vai em:** `saidas/auditoria-ia-<slug-do-cliente>.html`
- **Modelo pra clonar:** `.claude/skills/auditoria-ia/exemplo-nacional-inn.html`

---

## O que pedir ao usuário (se não vier no pedido)

1. **Nome + site** do negócio-alvo (ex: "Rede Nacional Inn — nacionalinn.com.br").
2. **Tipo de negócio** (hotel, restaurante, clínica, loja, imobiliária...). Define quais
   campos a IA procura.
3. **Um exemplo de busca real no Modo IA** — o print ou o texto que o cliente vê quando
   pesquisa. É o que dá realismo ao bloco 01. Se não tiver, pedir; sem isso a prova é fraca.
4. *(opcional)* 1–3 **concorrentes** pra comparar (reforça o argumento first-mover).

---

## Passo 1 — Inspecionar (a evidência real)

Rodar no site-alvo E nos concorrentes, lendo como um robô do Google lê:

```bash
UA="Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
curl -sL --max-time 25 -A "$UA" "<URL_DA_PAGINA>" -o /tmp/pg.html
echo "blocos ld+json: $(grep -c 'application/ld+json' /tmp/pg.html)"
grep -oiE '"@type"\s*:\s*"[^"]+"' /tmp/pg.html | sort | uniq -c
grep -oiE '"(aggregateRating|ratingValue|priceRange|geo|latitude|amenityFeature|starRating|address|telephone|openingHours)"' /tmp/pg.html | sort | uniq -c
```

Inspecionar a **página do serviço/produto** (ex: página de um hotel, não só a home) — é
onde o dado importa. Anotar quais campos existem e quais faltam. Registrar os `@type`
que aparecem (quase sempre só `SiteNavigationElement`, `ItemList`, `Organization`,
`BreadcrumbList` — nada que descreva o negócio em si).

**Regra de honestidade:** só marcar "ausente" o que a inspeção confirmar ausente. Se o
site tiver um campo, dizer que tem. Uma prova honesta aguenta o gestor de tráfego checar;
uma inflada, não.

## Passo 2 — Mapear os campos que a IA procura (por tipo de negócio)

Camada base (LocalBusiness) — vale pra quase todos:
- "Isto é um [tipo]" (o @type do estabelecimento) · Endereço estruturado · Localização no
  mapa (geo) · Nota e volume de avaliações · Faixa de preço · Telefone / contato direto ·
  Horário de funcionamento.

Extras por tipo:
- **Hotel / pousada:** comodidades (piscina, café, wi-fi, pet), classificação em estrelas, check-in/out.
- **Restaurante:** cardápio, tipo de cozinha, aceita reserva, faixa de preço.
- **Clínica / consultório:** especialidades, convênios, profissionais.
- **Loja / e-commerce:** produtos, preço, disponibilidade, avaliações do produto.
- **Imobiliária:** imóveis, faixa de preço, área de atuação.

Montar o checklist do bloco 02 com esses campos, marcando ✗ (Ausente) o que faltar.

## Passo 3 — Gerar a página

Clonar `exemplo-nacional-inn.html` e trocar **só os blocos de conteúdo** — CSS, logo,
tipografia, cores, contato e estrutura permanecem idênticos:

- `<title>` e nome do negócio nos títulos.
- **Bloco 01** — a query real e a resposta de IA reproduzida, com as fontes que descrevem
  o negócio hoje (OTAs/agregadores). Manter o rótulo "Reprodução ilustrativa".
- **Bloco 02** — o checklist com os campos reais ausentes + a caixa "o que o site de fato
  declara" (os `@type` genéricos achados). A frase-veredito adaptada ao tipo.
- **Bloco 03** — stats first-mover: nº de sites inspecionados, quantos têm ficha completa
  (quase sempre 0), "1º lugar disponível". Só afirmar "0" se os concorrentes forem checados.
- **Bloco 04 + CTA** — manter o CTA do plano de automação e os botões do Mario.

Salvar em `saidas/auditoria-ia-<slug>.html` e publicar como Artifact (favicon 🔍).
Lembrar o usuário que o link nasce privado — compartilhar pelo menu da página.

---

## Guarda-corpos (não violar)

- **Nunca** revelar o método: sem "JSON-LD", "schema markup", "schema.org", nomes de
  `@type` como receita, nem passo-a-passo de implementação. Só sintoma, nunca solução.
- **Nunca** inventar número de tráfego, receita ou % de ganho que não foi medido. Usar
  enquadramento qualitativo quando não houver dado.
- **Nunca** se passar pela empresa-alvo. É uma auditoria independente do Mario *sobre* o
  negócio — o rodapé deixa isso explícito ("não afiliado a...").
- Preços/notas do bloco 01 vêm do print real do cliente — pedir pra ele conferir antes de enviar.

## Depois de entregar

Oferecer os próximos passos da esteira de venda: **proposta comercial**, **menu de
automações** e **plano técnico** (guardado, não vai pro cliente).
