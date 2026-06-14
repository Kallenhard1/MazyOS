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

## Cuidados (LGPD + ToS)
- Cold outreach B2B segmentado e relevante é aceitável; **spam em massa não**.
- Volume moderado + personalização real > disparo genérico em escala.
- Não scrapear Google Maps/LinkedIn direto (viola ToS) — usar APIs oficiais
  e dados públicos (CNPJ).
- Dado de empresa (CNPJ, telefone comercial) tem tratamento mais flexível
  que dado pessoal, mas registrar a base legal (legítimo interesse) e
  oferecer opt-out já na primeira mensagem.
