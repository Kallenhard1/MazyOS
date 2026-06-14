# Automação de prospecção — motor de leads B2B

> Plano pra transformar prospecção manual em pipeline semi-automático.
> Filosofia MazyOS: closed loop — busca → qualifica → aborda → mede →
> realimenta. A máquina faz o trabalho repetível; o humano faz a relação.

---

## Por que mirar B2B muda o jogo

| | B2C local (café, clínica) | B2B (indústria, atacado, serviço pro outro negócio) |
|---|---|---|
| Ticket | R$ 900–3.000 | R$ 5.000–15.000+ |
| Dor digital | "não apareço no Google" | "comprador me pesquisa antes de cotar e não me acha" |
| Recorrência | manutenção R$ 99/mês | manutenção + LinkedIn + catálogo + automação maior |
| Ciclo de venda | curto (dias) | mais longo (semanas), mas LTV muito maior |

O comprador B2B **pesquisa fornecedor antes de aprovar** (Google, LinkedIn,
site). Ausência digital dói mais — logo a venda é mais fácil de justificar.
Um único cliente B2B paga o que 5 cafés pagariam. O caso StarCad (template
da proposta) é exatamente esse perfil.

**Alvos B2B bons pra começar:** indústrias pequenas/médias, distribuidoras
e atacados, fornecedores de serviço (contabilidade, jurídico, logística,
manutenção industrial, equipamentos), empresas com 25+ anos e site de 2010.

---

## Fontes de lead B2B (Brasil) — por ordem de poder

1. **Dados abertos de CNPJ (Receita Federal)** — a mina de ouro B2B.
   Base pública e gratuita. Dá pra filtrar por **CNAE (setor), município,
   porte, situação ativa** e puxar nome, CNPJ, endereço, telefone, data de
   abertura, capital social. Segmentação cirúrgica e legal.
   - Acesso: dump oficial da Receita, ou serviços tipo casadosdados / cnpj.biz.
2. **Google Maps / Places API** — ótimo pra quem tem ponto físico
   (atacado, indústria, oficinas). Free tier generoso (~US$ 200/mês de
   crédito). Dá nome, categoria, telefone, **se tem site**, nota e nº de
   avaliações.
3. **LinkedIn** — onde está o decisor B2B. Busca manual (grátis) ou Sales
   Navigator (pago) pra achar dono/sócio/compras.
4. **Associações comerciais, sindicatos e catálogos setoriais** — listas
   de associados, já segmentadas por setor.

---

## O pipeline (o que automatizar)

```
[1] Sourcing        → dados/prospects.csv (lista bruta)
[2] Qualificação    → script enriquece: tem site? site ruim? GMB? LinkedIn?
[3] Scoring         → nota 0–100, classifica quente/morno/frio
[4] Diagnóstico     → gera 1-página/PDF por lead quente (reusa gerar_pdf.py)
[5] Outreach        → gera mensagem personalizada + rascunho no Gmail
[6] CRM/tracking    → pipeline (Notion ou o próprio RivalFlow)
[7] Follow-up       → sequência de 2–3 toques, com lembrete automático
```

### O que a máquina faz (automatizável de verdade)
- Puxar e padronizar a lista de leads
- **Checar a saúde do site de cada lead**: existe? responde? tem HTTPS?
  é responsivo/mobile? data da última atualização? → esse é o filtro que
  separa quente de frio em escala
- Calcular o score e ranquear (foco: empresa ativa + boas avaliações +
  presença digital fraca = lead quentíssimo)
- Gerar o diagnóstico e o rascunho de abordagem personalizado por lead
- Registrar tudo no CRM e lembrar do follow-up

### O que continua humano (de propósito)
- O **envio final** e a conversa. Relação B2B é pessoal; disparo em massa
  não-solicitado queima a marca e esbarra na LGPD. A máquina prepara, o
  Mario aperta enviar depois de revisar.

---

## Ordem de construção sugerida

1. **Qualificador de leads** (`qualificar_leads.py`) — lê o CSV, checa o
   site de cada empresa e devolve a lista ranqueada. É o coração: faz
   qualquer fonte de lead virar prioridade clara. Funciona independente
   de como a lista foi montada.
2. **Sourcing** — escolher a fonte (CNPJ aberto pra B2B segmentado, ou
   Places API pra ponto físico) e automatizar a coleta pro CSV.
3. **Diagnóstico + outreach em massa** — gerar o 1-página e o rascunho de
   e-mail por lead quente, criando os drafts no Gmail pro Mario revisar.
4. **CRM** — pipeline no Notion ou dogfood do RivalFlow pra rastrear
   status e follow-up.

---

## Roadmap das 4 etapas

Foco de cliente definido: **B2C local + B2B** — misturar negócios locais
(venda rápida, gera caixa) com B2B (ticket alto, LTV maior). O mesmo
pipeline serve os dois; muda só a fonte de lead e alguns pesos do score.

### Etapa 1 — Qualificador de leads ✅ (implementado)
- **Arquivo:** `scripts/qualificar_leads.py`
- **Entrada:** `dados/prospects.csv` (lista bruta de qualquer fonte)
- **O que faz:** checa a saúde do site de cada empresa (existe? responde?
  HTTPS? mobile? está velho?), cruza com sinais de "vale a pena" (nota,
  nº de avaliações, B2B) e gera um **score de oportunidade 0–100** +
  classificação quente/morno/frio + os motivos.
- **Saída:** `dados/prospects-qualificados.csv` (ranqueado) e um resumo
  em `dados/prospects-qualificados.md`.
- **Dependências:** nenhuma além de Python 3 (usa só a biblioteca padrão).

### Etapa 2 — Sourcing (coleta de leads) ✅ (implementado)
- **GRÁTIS via OpenStreetMap** (`scripts/buscar_leads_osm.py`): busca por
  categoria + cidade na Overpass API, sem chave nem billing. Diz se o
  negócio tem site cadastrado. Cobertura menor que o Google, mas ilimitada
  e de graça — a melhor opção pra começar sem verba. Plano de busca em
  `dados/buscas-osm.csv` (categoria, tipo).
- **B2C local + B2B via Google Places** (`scripts/buscar_leads_places.py`):
  busca por consulta ("cafeteria em Taubaté", "contabilidade em Taubaté")
  e já traz se a empresa tem site, telefone, nota e nº de avaliações.
  Plano de busca em CSV (`dados/buscas-exemplo.csv`: consulta, tipo, setor).
  Precisa de chave da Places API em `GOOGLE_MAPS_API_KEY` (free tier).
- **B2B em escala via CNPJ aberto** (`scripts/filtrar_cnpj.py`): filtra os
  CSVs públicos da Receita por CNAE + UF + município + situação ativa, junta
  a razão social e despeja no formato do qualificador. Roda em 2 passagens
  (baixo uso de memória). Baixar em https://dadosabertos.rfb.gov.br/CNPJ/.
  Diferença-chave: o CNPJ acha até empresa sem nenhuma presença online
  (que o Places nem lista) — ideal pro B2B industrial.
- **Saída:** ambos gravam no mesmo formato; encadeia direto na Etapa 1.

  Fluxo completo:
  ```
  # B2C local + B2B com ponto físico (precisa da chave Places)
  export GOOGLE_MAPS_API_KEY="..."
  python scripts/buscar_leads_places.py --buscas dados/buscas-exemplo.csv

  # B2B em escala por setor (precisa baixar o dump da Receita)
  python scripts/filtrar_cnpj.py --dir ./cnpj --cnae 6920,6201 --uf SP

  # qualifica e ranqueia (Etapa 1)
  python scripts/qualificar_leads.py dados/prospects.csv
  ```

### Etapa 3 — Diagnóstico + outreach ✅ (implementado)
- **Mensagens** (`scripts/gerar_abordagem.py`): pra cada lead quente gera
  WhatsApp + e-mail personalizados, calibrados por `tipo` e pelos achados
  reais do qualificador. Só mostra problemas digitais ao cliente (nunca os
  motivos internos de score). Saída:
  - `saidas/abordagens/abordagens.md` — revisar e copiar/colar (WhatsApp)
  - `saidas/abordagens/emails.csv` — `to,subject,body` (ponte pro Gmail)
- **Diagnóstico 1-página** (`scripts/gerar_diagnostico.py` +
  `templates/diagnostico/`): PDF branded MarioLucash por lead quente, com
  score, achados e solução. Reaproveita o WeasyPrint. Saída em
  `saidas/diagnosticos/`.
- **Rascunhos no Gmail:** pedir ao Claude "cria os rascunhos do emails.csv"
  → ele lê o CSV e cria os drafts via MCP do Gmail. Nada é enviado: o Mario
  revisa e dispara. (CNPJ traz e-mail; Places não — pra leads sem e-mail,
  usar a mensagem de WhatsApp.)

### Etapa 4 — CRM de prospecção ✅ (implementado)
- **CRM local versionado** (`scripts/crm.py`): funil em `crm/pipeline.csv`
  com estágios novo → abordado → conversa → proposta → fechado/perdido,
  follow-up automático por estágio e board kanban em `crm/board.md`.
  Zero dependência; integra direto com o qualificador.
  - `crm.py importar <qualificados.csv> --classe quente`
  - `crm.py status "<nome>" abordado --canal whatsapp --nota "..."`
  - `crm.py followups [--ate +3d]` · `crm.py board` · `crm.py list`
- **Opção visual (Notion):** dá pra espelhar o funil num board do Notion
  via MCP (pedir ao Claude "joga o funil no Notion"). Bom pra ter UI e
  lembretes nativos.
- **Opção estratégica (RivalFlow):** dogfood — usar o CRM do próprio
  produto pra gerir a prospecção. Vira case de venda ("rodo meu negócio
  nele"). Fica pra quando o RivalFlow estiver no ar pro uso diário.

---

## Pipeline completo (as 4 etapas encadeadas)

```bash
# 2) sourcing — escolha a fonte
export GOOGLE_MAPS_API_KEY="..."
python scripts/buscar_leads_places.py --buscas dados/buscas-exemplo.csv  # B2C+B2B
python scripts/filtrar_cnpj.py --dir ./cnpj --cnae 6920 --uf SP          # B2B escala

# 1) qualifica e ranqueia
python scripts/qualificar_leads.py dados/prospects.csv

# 3) abordagem + diagnóstico dos quentes
python scripts/gerar_abordagem.py
python scripts/gerar_diagnostico.py
#    -> "Claude, cria os rascunhos do emails.csv"  (Gmail via MCP)

# 4) CRM — funil e follow-up
python scripts/crm.py importar dados/prospects-qualificados.csv
python scripts/crm.py board
python scripts/crm.py followups
```

Da lista crua ao acompanhamento do fechamento, com humano só onde importa:
a decisão de abordar e o envio.


---

## Cuidados (LGPD + ToS)
- Cold outreach B2B segmentado e relevante é aceitável; **spam em massa não**.
- Volume moderado + personalização real > disparo genérico em escala.
- Não scrapear Google Maps/LinkedIn direto (viola ToS) — usar APIs oficiais
  e dados públicos (CNPJ).
- Dado de empresa (CNPJ, telefone comercial) tem tratamento mais flexível
  que dado pessoal, mas registrar a base legal (legítimo interesse) e
  oferecer opt-out já na primeira mensagem.
