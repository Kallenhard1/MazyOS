# Sistema de Prospecção de Leads — Contexto para o Agente Local

> Documento de handoff para o agente Opus local. Descreve **tudo** que foi
> construído no MazyOS para prospecção de leads: a arquitetura, cada script,
> a skill `/prospectar`, o CRM, o espelho no Notion, e a evolução do uso do
> Google Places (pago) até a versão atual **100% gratuita**.
>
> Negócio: **MarioLucash** — freelancer de sites + automação para negócios
> locais. Foco: **B2C local + B2B**. Contexto vivo em `_memoria/` e
> `marketing/automacao-prospeccao.md`.

---

## 1. Visão geral

O objetivo é uma máquina semi-automática que transforma uma lista crua de
empresas em um funil de vendas com abordagem pronta — deixando para o humano
só o que importa: **decidir quem abordar e apertar enviar**.

Pipeline em 4 etapas, todas encadeadas por **um único formato CSV**:

```
[2] SOURCING        -> dados/prospects.csv          (lista crua)
[1] QUALIFICAÇÃO    -> dados/prospects-qualificados.csv  (ranqueada por score)
[3] ABORDAGEM       -> saidas/abordagens/ + saidas/diagnosticos/
[4] CRM             -> crm/pipeline.csv + crm/board.md + espelho no Notion
```

(A numeração reflete a ordem em que foram construídos; a ordem de execução é
sourcing → qualificação → abordagem → CRM.)

**Dependências:** tudo roda só com **Python 3 padrão** (biblioteca padrão),
exceto o gerador de diagnóstico em PDF, que precisa de `weasyprint`
(`pip install weasyprint`).

---

## 2. O formato CSV que cola tudo

Todos os scripts de sourcing gravam neste cabeçalho (em `dados/prospects.csv`):

```
nome,tipo,setor,cidade,telefone,email,site,nota,avaliacoes,instagram,linkedin
```

- `tipo`: `b2c` ou `b2b` (calibra score e mensagens)
- `nota` / `avaliacoes`: reputação (Google/OSM) — pode vir vazio
- `site`: vazio = forte sinal de oportunidade

O **qualificador** lê esse CSV e gera `dados/prospects-qualificados.csv`,
acrescentando as colunas calculadas:

```
score,classificacao,site_status,https,mobile,ano_site,motivos
```

Manter esse contrato é o que permite plugar qualquer fonte nova.

---

## 3. Etapa 2 — Sourcing (3 fontes)

### 3a. OpenStreetMap — `scripts/buscar_leads_osm.py` ⭐ GRÁTIS (padrão atual)
A versão atual recomendada. Busca negócios na **Overpass API** do
OpenStreetMap por categoria + cidade. **Sem chave, sem billing, sem cartão.**

- Mapeia ~20 categorias amigáveis → tags OSM (dict `CATEGORIAS`):
  cafe, padaria, restaurante, lanchonete, bar, mercado, petshop, veterinaria,
  salao, barbearia, academia, clinica, odontologia, farmacia, oficina,
  autopecas, hotel, advocacia, contabilidade, imobiliaria.
- Diz se o negócio tem `website`/`contact:website` cadastrado; puxa também
  `phone`/`contact:phone`, `email`, `contact:instagram`.
- Cobertura menor que a do Google, mas ilimitada e de graça — ideal pra
  começar sem verba. O que faltar de site, o qualificador confere ao vivo.

```bash
python scripts/buscar_leads_osm.py --cidade "Taubaté" --categorias cafe,padaria,restaurante
python scripts/buscar_leads_osm.py --cidade "Taubaté" --buscas dados/buscas-osm.csv
python scripts/buscar_leads_osm.py --cidade "Taubaté" --area-id 298561 --categorias cafe
```
Flags: `--cidade` (obrigatório), `--categorias` OU `--buscas <csv>` (colunas
`categoria,tipo`), `--tipo` (padrão b2c), `--area-id` (relação OSM p/
precisão), `--saida` (padrão dados/prospects.csv), `--append`.

Internamente: `montar_query()` gera Overpass QL com `area["name"=cidade]
["admin_level"="8"]`; `parse_elementos()` converte a resposta e faz dedup por
`(type,id)`, descartando POIs sem nome. Ambas as funções são testáveis sem
rede (foram validadas com amostra sintética no formato real da Overpass).

### 3b. Google Places — `scripts/buscar_leads_places.py` (pago/free tier)
**A primeira fonte construída.** Busca no Google Maps por consulta
(ex.: "cafeteria em Taubaté") e já traz site, telefone, nota e nº de
avaliações. Cobertura excelente, mas **precisa de `GOOGLE_MAPS_API_KEY`**
(conta no Google Cloud com a Places API; free tier ~US$200/mês de crédito).

```bash
export GOOGLE_MAPS_API_KEY="..."
python scripts/buscar_leads_places.py --buscas dados/buscas-exemplo.csv
python scripts/buscar_leads_places.py "cafeteria em Taubaté" --tipo b2c --setor Cafeteria
```
Flags: `consulta` posicional OU `--buscas <csv>` (`consulta,tipo,setor`),
`--tipo`, `--setor`, `--saida`, `--append`, `--paginas` (máx 3 = 60
resultados/busca), `--key`. Usa Text Search (paginado, token leva ~2s) +
Place Details (`name,website,formatted_phone_number,rating,user_ratings_total`).

**Por que saiu de cena como padrão:** exige cartão/conta de billing, e o
momento do negócio é sem verba. Ficou como **upgrade opcional** pra mais
cobertura. Foi a motivação para buscar a alternativa gratuita (OSM).

### 3c. CNPJ aberto — `scripts/filtrar_cnpj.py` (B2B em escala) GRÁTIS
Filtra os **dados abertos de CNPJ da Receita Federal** por CNAE + UF +
município + situação ativa. Acha até a empresa que não está em mapa nenhum —
o melhor para B2B industrial. Baixar o dump em
https://dadosabertos.rfb.gov.br/CNPJ/.

```bash
python scripts/filtrar_cnpj.py --dir ./cnpj --cnae 6920,6201 --uf SP \
    --municipio "TAUBATE,SAO JOSE DOS CAMPOS" --limite 500
```
Flags: `--dir` (pasta dos CSVs, padrão `cnpj`), `--cnae` (prefixos por
vírgula), `--uf`, `--municipio` (nomes — exige Municipios.csv — ou códigos),
`--situacao` (padrão `02`=ativa), `--limite`, `--saida`, `--tipo` (padrão b2b).

Roda em **2 passagens** (baixo uso de memória): (1) filtra Estabelecimentos e
guarda os CNPJs básicos que batem; (2) varre Empresas só para pegar a razão
social desses. Usa Municipios.csv para traduzir código→nome. Layout da
Receita: CSV `;`, latin-1, sem cabeçalho (Estabelecimentos: situacao=col5,
cnae=11, uf=19, municipio=20, ddd1=21, tel1=22, email=27). **Não traz site**
(o CNPJ não tem) — todos saem com `site` vazio; o qualificador confere depois.
Validado com amostra sintética no layout real.

> **Recomendação atual de sourcing sem gastar nada:**
> OpenStreetMap (B2C local) + CNPJ aberto (B2B). Google Places só se quiser
> mais cobertura e tiver a chave.

Planos de busca de exemplo: `dados/buscas-osm.csv` e `dados/buscas-exemplo.csv`.

---

## 4. Etapa 1 — Qualificação e score — `scripts/qualificar_leads.py`

O coração do sistema. Lê o CSV de leads, **checa a saúde do site de cada
empresa ao vivo** (concorrente em paralelo via ThreadPoolExecutor) e devolve
a lista ranqueada por um **score de oportunidade 0–100**.

```bash
python scripts/qualificar_leads.py dados/prospects.csv
python scripts/qualificar_leads.py entrada.csv saida.csv --workers 12 --timeout 8
```

Checagem do site (`site_status`): `sem_site`, `nao_responde`,
`erro_http_4xx/5xx`, ou `ok`; além de `https` (sim/nao), `mobile`
(tem meta viewport?) e `ano_site` (maior ano encontrado no HTML).

Score = **NEED** (fraqueza digital) + **FIT** (vale a pena / consegue pagar):
- sem site +45 · fora do ar +35 · erro 4xx +25 · sem HTTPS +12 · não mobile
  +12 · site velho (©≤ano-3) +8
- reputação forte (≥4.3★ e ≥50 aval.) +20 · boa (≥4.0 e ≥20) +12 · alguma +5
- tem telefone +5 · é B2B +5 (ticket maior)

Classificação: **quente ≥60 · morno 35–59 · frio <35**.

Saída: `dados/prospects-qualificados.csv` (ranqueado) + `...-qualificados.md`
(resumo com top quentes). Importante: o campo `motivos` mistura razões de
NEED (mostráveis ao cliente) e de FIT (internas) — por isso as etapas
seguintes **derivam os achados do cliente dos campos estruturados**, nunca do
`motivos` cru.

---

## 5. Etapa 3 — Abordagem + Diagnóstico

### 5a. Mensagens — `scripts/gerar_abordagem.py`
Para cada lead quente, gera **WhatsApp + e-mail personalizados**, calibrados
por `tipo` (b2c/b2b) e pelos achados reais.

```bash
python scripts/gerar_abordagem.py
python scripts/gerar_abordagem.py dados/prospects-qualificados.csv --classe quente,morno --limite 50
```
- `gancho()` cria a frase-âncora a partir do `site_status` (sem site → "quem
  busca {setor} em {cidade} acha o concorrente"; etc.).
- `achados_cliente()` lista **só problemas digitais reais** — nunca expõe
  motivos internos de score ("ticket maior", "reputação forte").
- Saídas: `saidas/abordagens/abordagens.md` (revisar/copiar p/ WhatsApp) e
  `saidas/abordagens/emails.csv` (`to,subject,body` — ponte pro Gmail).
- Assinatura usa: `mariolucasdasilvabarbosa@gmail.com` · Instagram `@mariolucash`.

### 5b. Diagnóstico PDF — `scripts/gerar_diagnostico.py` (requer weasyprint)
PDF de **1 página, branded MarioLucash** (monocromático — paleta da marca
ainda não definida; combina com o logo preto/branco) com score, achados e
solução. Template: `templates/diagnostico/diagnostico.html` (+ `fonts/`).

```bash
python scripts/gerar_diagnostico.py --classe quente --limite 30
```
Saída: `saidas/diagnosticos/diagnostico-<empresa>.pdf`. Usa os mesmos
`achados_cliente()` (só problemas reais).

### 5c. Rascunhos no Gmail (via MCP, sem script)
O `create_draft` do Gmail está conectado (`mcp__Gmail__create_draft`). Quando
houver leads com e-mail no `emails.csv`, o agente lê o CSV e cria os rascunhos
(`to`, `subject`, `body`), um por linha. **Nunca envia** — só rascunho; o
humano revisa e dispara. (CNPJ traz e-mail; Places/OSM normalmente não — para
esses, usar a mensagem de WhatsApp.)

---

## 6. Etapa 4 — CRM — `scripts/crm.py`

Funil local **versionado no Git** (a fonte de verdade), sem dependências.

```bash
python scripts/crm.py importar dados/prospects-qualificados.csv --classe quente
python scripts/crm.py status "Contabilidade Prisma" abordado --canal whatsapp --nota "mandei zap"
python scripts/crm.py followups --ate +3d
python scripts/crm.py board
python scripts/crm.py list --status conversa,proposta
```
- Estágios: **novo → abordado → conversa → proposta → fechado/perdido**.
- `status` carimba `ultimo_contato=hoje` e define follow-up automático por
  estágio (abordado +3d, conversa +2d, proposta +4d) — ou `--followup +Nd|data`.
- `followups` lista quem cobrar (marca atrasados com ⚠️).
- `board` gera o kanban em `crm/board.md`.
- Dados em `crm/pipeline.csv` (versionado). `importar` casa por `id`
  (slug nome+cidade) e não duplica.

### Espelho no Notion (board visual, via MCP)
Base **"Prospecção — MarioLucash"** já criada:
- URL: https://app.notion.com/p/2ae35c0bfb2a4828b592e534a4b2cbaf
- `data_source_id`: `2b3cc55d-f52a-473a-a751-10014632e7bd`
- Propriedades: Empresa (title), Status (select c/ cores por estágio), Tipo,
  Setor, Cidade, Telefone, Email, Site, Score, `date:Follow-up:start`, Canal, Notas.

Sincronização **manual e unidirecional** (CSV é a verdade; Notion é leitura):
o agente lê `crm/pipeline.csv`, casa por nome (Empresa) com
`notion-search` na data source, **cria** os novos e **atualiza** os mudados —
sem duplicar. Disparar com "atualiza o Notion" ou ao fim de `/prospectar`.

---

## 7. A skill `/prospectar` — `.claude/skills/prospectar/SKILL.md`

Orquestra o pipeline inteiro como um comando. Gatilhos: "prospectar",
"/prospectar", "buscar clientes", "qualificar leads", "rodar a prospecção".
Passos: **0** sourcing (oferece OSM grátis primeiro, depois Places, depois
CNPJ) → **1** qualificar → **2** abordagem+diagnóstico → **3** rascunhos no
Gmail (opcional) → **4** CRM → **5** espelhar no Notion. Regras embutidas:
nunca enviar nada sem revisão humana; calibrar por b2c/b2b; manter o tom de
`_memoria/preferencias.md` (direto, sem jargão de guru).

---

## 8. Como rodar tudo (fluxo completo, gratuito)

```bash
# 2) Sourcing gratuito
python scripts/buscar_leads_osm.py --cidade "Taubaté" --buscas dados/buscas-osm.csv  # B2C
python scripts/filtrar_cnpj.py --dir ./cnpj --cnae 6920 --uf SP                       # B2B

# 1) Qualifica e ranqueia
python scripts/qualificar_leads.py dados/prospects.csv

# 3) Abordagem + diagnóstico dos quentes
python scripts/gerar_abordagem.py
python scripts/gerar_diagnostico.py            # requer weasyprint
#    -> "cria os rascunhos do emails.csv" (Gmail via MCP)

# 4) CRM + Notion
python scripts/crm.py importar dados/prospects-qualificados.csv
python scripts/crm.py board
python scripts/crm.py followups
#    -> "atualiza o Notion"
```

---

## 9. Mapa de arquivos

| Caminho | Papel |
|---|---|
| `scripts/buscar_leads_osm.py` | Sourcing OSM (grátis, padrão) |
| `scripts/buscar_leads_places.py` | Sourcing Google Places (precisa de chave) |
| `scripts/filtrar_cnpj.py` | Sourcing B2B via CNPJ aberto (grátis) |
| `scripts/qualificar_leads.py` | Qualificação + score 0–100 |
| `scripts/gerar_abordagem.py` | WhatsApp + e-mail por lead |
| `scripts/gerar_diagnostico.py` | Diagnóstico PDF 1-página (weasyprint) |
| `scripts/crm.py` | Funil/CRM local + board |
| `templates/diagnostico/` | HTML + fontes do diagnóstico |
| `dados/buscas-osm.csv`, `dados/buscas-exemplo.csv` | Planos de busca exemplo |
| `crm/pipeline.csv`, `crm/board.md` | Funil (verdade) + kanban |
| `.claude/skills/prospectar/SKILL.md` | Skill que orquestra tudo |
| `marketing/automacao-prospeccao.md` | Plano/roadmap das 4 etapas |

---

## 10. Notas, limitações e próximos passos

- **Testado x não testado:** a lógica offline (parsing, score sem rede,
  CNPJ, CRM, geração de mensagens/PDF) foi validada de ponta a ponta. As
  chamadas que dependem de rede externa (OSM/Overpass, Google Places, checagem
  ao vivo de sites no qualificador) foram validadas em estrutura/erro, mas
  precisam rodar na máquina do Mario com internet aberta.
- **LGPD/ToS:** cold outreach B2B segmentado e relevante é ok; spam em massa
  não. Não raspar Google/LinkedIn direto (ToS). Volume moderado +
  personalização. Ver `marketing/automacao-prospeccao.md`.
- **Evolução resumida:** começou com Google Places (pago) → sem verba →
  adicionou CNPJ aberto (B2B grátis) → criou OpenStreetMap como fonte B2C
  gratuita (padrão atual) → empacotou tudo na skill `/prospectar` com CRM e
  espelho no Notion.
- **Próximos possíveis:** sync bidirecional com o Notion (precisa de token +
  script); dogfood do CRM no próprio RivalFlow; definir a paleta da marca para
  colorir o diagnóstico; rodar com leads reais e calibrar pesos do score.
