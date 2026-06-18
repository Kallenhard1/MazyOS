# Plataforma — Migração pra SQLite + base multiusuário

> Plano de arquitetura pra trocar a persistência de arquivos planos (CSV/JSON)
> por um **SQLite local**, preparando o terreno pra **multiusuário**. Documento
> de plano: aprovar/revisar antes de construir. Escrito em 18/06/2026.
>
> Contexto desta decisão: ver também `docs/PLATAFORMA-MVP.md` (que assumia
> "sem banco", premissa agora revista) e `docs/PLATAFORMA-FEATURES.md`.

---

## 1. Por que agora (e por que SQLite)

A conversa que originou este plano deixou duas coisas claras:

1. **A lentidão de editar lead NÃO era o storage.** Era o `subprocess` que
   subia um Python novo a cada edição (~205ms). Isso **já foi resolvido** numa
   etapa anterior: `funil.py` agora chama a lógica do `crm.py` em processo
   (edição caiu pra ~1.7ms). Ou seja, **velocidade não é mais o motivo** da
   migração.
2. **O motivo real é multiusuário.** Decidiu-se levar a plataforma pra
   multiusuário. Com isso, o modelo "carrega CSV inteiro → reescreve CSV
   inteiro" quebra de verdade: dois usuários editando ao mesmo tempo = um
   sobrescreve o outro, sem trava de linha nem transação.

**SQLite é o degrau certo** (não overengineering): é local, zero servidor,
embutido na stdlib do Python (`sqlite3`), e com **WAL mode** aguenta leitura
concorrente + escrita serializada por bastante tempo. Só vale trocar por
Postgres/MySQL quando houver múltiplos processos de app servindo junto ou
volume alto de leads — longe disso hoje.

### O que a migração preserva (inegociável)

O modelo de arquivos planos tinha duas virtudes que **não podem sumir**:

- **Claude lê os dados como texto.** Workflows como "atualiza o Notion" ou
  "quem está atrasado" hoje leem o `pipeline.csv` direto.
- **Versionamento no Git.** O `/salvar` comita o estado e o histórico mostra o
  que mudou.

Solução: o `.sqlite` vira a fonte de verdade de runtime (no `.gitignore`), mas
um comando **`export`** gera snapshots CSV/JSON versionáveis (pro Git e pro
Claude ler). Mesma ideia do `manifest.json`: artefato derivado, regenerável.

---

## 2. Princípios

1. **Uma fonte de verdade de runtime: o SQLite.** Fim do "reescreve o arquivo
   inteiro". Escritas viram `UPDATE`/`INSERT` de uma linha, em transação.
2. **Git guarda código + snapshots, não o banco vivo.** `.sqlite` no
   `.gitignore`; `crm/pipeline.csv` (e amigos) passam a ser **exports**
   gerados, mantidos no Git como backup legível.
3. **A camada de dados fica num lugar só.** Hoje a lógica já está centralizada
   em `scripts/crm.py` (funções puras `mudar_status_lead`, `editar_lead_dados`,
   `carregar`, `salvar`). A migração troca o miolo de `carregar`/`salvar` por
   acesso ao banco — o resto do código nem percebe.
4. **Migração reversível e incremental.** Importa do CSV/JSON pro banco; se der
   ruim, o export volta a ser a verdade. Migrar uma entidade por vez.
5. **Multiusuário é fase seguinte, não esta.** O banco é pré-requisito. Auth,
   sessão e deploy vêm depois (seção 7).

---

## 3. O que está disperso hoje (inventário a migrar)

| Dado | Onde hoje | Formato | Vira tabela |
|---|---|---|---|
| Funil/CRM (leads) | `crm/pipeline.csv` | CSV | `leads` |
| Estado de cada cliente | `clientes/<slug>/estado.json` | JSON | `clientes` (+ `etapas`) |
| Fila de conteúdo | `marketing/conteudo-fila.json` | JSON | `conteudo` |
| Prospects qualificados | `dados/prospects-qualificados.csv` | CSV | fica em CSV (entrada de pipeline, read-only) |

> `briefing.md`, `notas.md`, `pesquisa.md`, `proposta.html`, PDFs e assets
> **continuam arquivos** dentro de `clientes/<slug>/` — são documentos, não
> registros. O banco guarda só dado estruturado consultável/editável.

Pontos do código que tocam esses dados (mapear antes de mexer):
- `scripts/crm.py` — `carregar`/`salvar`/`achar` + funções de negócio.
- `plataforma/servicos/funil.py` — lê `pipeline.csv`, agrupa por estágio.
- `plataforma/servicos/lead.py` — lê/escreve `estado.json`, lista workspaces.
- `plataforma/servicos/email_massa.py` — lê `pipeline.csv` pros lotes.
- `plataforma/servicos/conteudo.py` — lê/escreve `conteudo-fila.json`.
- `plataforma/servicos/arquivos.py` — leitor genérico de CSV (segue lendo os
  exports e os CSVs de entrada; não precisa de banco).

---

## 4. Esquema inicial (rascunho)

```sql
PRAGMA journal_mode = WAL;          -- leitura concorrente + escrita serializada
PRAGMA foreign_keys = ON;

CREATE TABLE leads (
  id              TEXT PRIMARY KEY,  -- slug atual (nome-cidade)
  nome            TEXT NOT NULL,
  tipo            TEXT,
  setor           TEXT,
  cidade          TEXT,
  telefone        TEXT,
  email           TEXT,
  site            TEXT,
  score           INTEGER,
  classificacao   TEXT,             -- quente/morno/frio
  status          TEXT NOT NULL DEFAULT 'novo',
  ultimo_contato  TEXT,             -- ISO date
  proximo_followup TEXT,            -- ISO date
  canal           TEXT,
  notas           TEXT,
  criado_em       TEXT DEFAULT (datetime('now')),
  atualizado_em   TEXT DEFAULT (datetime('now'))
);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_followup ON leads(proximo_followup);

CREATE TABLE clientes (
  slug         TEXT PRIMARY KEY,    -- = clientes/<slug>/
  lead_id      TEXT REFERENCES leads(id),
  etapa_atual  TEXT,
  estado_json  TEXT,                -- blob do estado.json durante a transição
  atualizado_em TEXT DEFAULT (datetime('now'))
);

CREATE TABLE conteudo (
  id        TEXT PRIMARY KEY,
  alvo      TEXT NOT NULL,          -- 'proprio' ou slug do cliente
  tema      TEXT NOT NULL,
  tipo      TEXT DEFAULT 'carrossel',
  status    TEXT DEFAULT 'ideia',
  criado_em TEXT DEFAULT (datetime('now'))
);
CREATE INDEX idx_conteudo_alvo ON conteudo(alvo);
```

> `clientes.estado_json` é uma muleta de transição: guarda o JSON inteiro pra
> não ter que normalizar todas as etapas de uma vez. Normalizar `etapas` numa
> tabela própria depois, se valer.

---

## 5. Camada de acesso

Criar `plataforma/servicos/db.py` (ou `scripts/db.py`, compartilhado):

- `conectar()` — abre o SQLite com `row_factory = sqlite3.Row`, garante WAL e
  `foreign_keys`. Caminho do banco: `dados/mazyos.sqlite` (gitignored).
- `init_db()` — cria as tabelas se não existirem (idempotente).
- Funções de CRUD por entidade que **devolvem dicts** com as mesmas chaves que
  o código já espera (`COLS` do crm.py), pra trocar o miolo sem reescrever
  quem chama.

O truque pra migração suave: manter a **assinatura** de `carregar(arquivo)` e
`salvar(arquivo, leads)` no `crm.py`, mas reimplementar por dentro com SQLite
(o parâmetro `arquivo` passa a ser ignorado ou usado só pra export). Assim
`funil.py`, `email_massa.py` etc. continuam funcionando sem alteração.

---

## 6. Passo a passo da migração

1. **`db.py` + `init_db()`** — banco e tabelas, sem ligar nada ainda.
2. **Script `scripts/migrar_para_sqlite.py`** — lê `pipeline.csv`,
   `conteudo-fila.json` e os `estado.json` e popula o banco. Idempotente
   (rodar de novo não duplica).
3. **Comando `export`** — gera `crm/pipeline.csv` (e os JSONs) a partir do
   banco. Roda no `/salvar` (igual o `gerar_manifest.py`), pra manter o
   snapshot versionado e legível pelo Claude.
4. **Trocar `crm.py`** — `carregar`/`salvar` passam a bater no SQLite. Rodar a
   bateria de testes do funil (status, editar, followups, board).
5. **Migrar `conteudo.py` e `lead.py`** pro banco, um de cada vez.
6. **`.gitignore`** — adicionar `dados/mazyos.sqlite*` (inclui `-wal`/`-shm`).
7. **Atualizar docs** — `PLATAFORMA-MVP.md` (premissa "sem banco" caiu),
   `PLATAFORMA-FEATURES.md`, e o `CLAUDE.md` (regra: fonte de verdade vira o
   banco; `/salvar` roda o export antes de comitar).

Cada passo é um commit atômico. Dá pra parar em qualquer um e continuar depois.

---

## 7. Multiusuário (fase seguinte, fora deste plano)

O banco é só o pré-requisito. Pra multiusuário de verdade ainda falta:

- **Auth** — login simples (usuário/senha ou OAuth Google), sessão Flask.
- **Coluna de dono/responsável** nas tabelas, se cada usuário vê o seu funil.
- **Deploy** — sair do `127.0.0.1` pra um host (a app deixa de ser "local").
  Aí entra HTTPS, variável de ambiente pra secret, backup do `.sqlite`.
- **Concorrência real** — com WAL o SQLite segura bem um servidor único. Se um
  dia rodar em múltiplos processos/instâncias, aí sim avaliar Postgres.

Decisão registrada: **não** ir pra Postgres/MySQL agora. SQLite cobre a
operação atual e o primeiro passo de multiusuário com folga.

---

## 8. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Perder a leitura direta pelo Claude | Comando `export` mantém CSV/JSON no Git |
| Migração corromper dados | Importa de cópia; CSV original fica como backup até validar |
| `import crm` colidir com a pasta `crm/` | Já tratado: carregar por caminho via `importlib` (ver `funil.py`) |
| Banco binário no Git | `.gitignore` no `.sqlite*`; só o export versiona |
| Datas/encoding | Tudo ISO (`YYYY-MM-DD`) e UTF-8, como já é hoje |
