# Plataforma — Fase 4: Conteúdo & Redes

> Plano de implementação do módulo de conteúdo. Junta `/carrossel`,
> `/publicar-tema` e `/aprovar-post` numa tela só, evoluindo a tela 📸
> Instagram (que já faz handoff de carrossel) pra cobrir conteúdo próprio
> **e de cliente**. Segue o padrão B (handoff pro Claude Code): a plataforma
> organiza, monta o prompt pronto e acompanha as saídas; quem cria e publica
> é o Claude Code. Aprovar antes de construir.
>
> Base: `docs/PLATAFORMA-FEATURES.md` (mapa) · `docs/PLATAFORMA-MVP.md`
> (padrões) · `plataforma/servicos/instagram.py` (molde que já existe).

---

## 1. Por que esse módulo agora

Depois de fechar cliente, a entrega recorrente é conteúdo: o marketing próprio
do Mario (prova social, meta 2 posts/semana) e a "estrutura de redes" que entra
nos pacotes. Hoje isso só existe meio na tela Instagram (carrossel próprio). A
Fase 4 transforma em um fluxo completo: **tema → peça → aprovação → publicação**,
reusando as três skills de conteúdo sem reescrever nada.

---

## 2. O que muda em relação ao que já existe

A tela 📸 Instagram (`servicos/instagram.py`) já faz: fila de temas, prompt de
`/carrossel`, prompt de `/publicar-tema`, e lista o que as skills geraram em
`marketing/conteudo/`. A Fase 4 **generaliza** isso:

| Hoje (Instagram) | Fase 4 (Conteúdo & Redes) |
|---|---|
| Só marketing próprio | Próprio **+ por cliente** (`clientes/<id>/conteudo/`) |
| Fila de temas | Fila com **status** (rascunho → aprovado → publicado) |
| Prompt de carrossel/tema | Os 3 fluxos: carrossel, esteira completa, **publicar** |
| Lista PNGs gerados | Galeria + ação de aprovar/publicar (`/aprovar-post`) |

A tela Instagram vira um caso (alvo = "próprio") do módulo maior.

---

## 3. As três features (uma por skill)

### 3a. Carrossel avulso — `/carrossel` (padrão B)
- Input: tema + alvo (próprio ou cliente X) + com/sem foto IA.
- A plataforma monta o **prompt pronto** (já faz: `prompt_carrossel`), com a
  identidade (`design-guide.md`, paleta âmbar/creme) e o tom
  (`preferencias.md`). Botão copiar.
- Acompanha os PNGs gerados pela skill na pasta de saída do alvo.

### 3b. Esteira de conteúdo — `/publicar-tema` (padrão B)
- Input: um tema.
- Gera o prompt `/publicar-tema <tema>` (já faz: `prompt_completo`), que entrega
  **artigo de blog + carrossel + 3 legendas amarradas**.
- A peça entra na fila como item com 3 saídas (blog, carrossel, legendas),
  cada uma com status próprio.

### 3c. Aprovar e publicar — `/aprovar-post` (padrão B, handoff de publicação)
- Quando a peça está pronta e revisada, botão **"Aprovar e publicar"** gera o
  handoff do `/aprovar-post` (blog draft→published, copia PNGs pro site,
  posta no Instagram + Facebook via Meta Graph API).
- Status do item vira `publicado` com data. Nada publica sozinho: o comando
  roda no Claude Code, com a revisão humana.

---

## 4. Arquitetura (segue o que já está montado)

```
plataforma/
  servicos/
    conteudo.py        # evolui instagram.py: fila c/ status, alvo, 3 prompts
  templates/
    conteudo.html      # tela única (filtro por alvo e por status)
app.py                 # rotas /conteudo, /conteudo/add, /conteudo/status, /conteudo/publicar
```

**Dados (fonte de verdade, fora da plataforma):**
- Próprio: `marketing/instagram-fila.json` (já existe) vira
  `marketing/conteudo-fila.json` com campos novos: `alvo`, `status`,
  `publicado_em`.
- Por cliente: `clientes/<id>/conteudo/` pras saídas; a fila guarda o `alvo`.
- Saídas das skills: `marketing/conteudo/` (próprio) e
  `clientes/<id>/conteudo/` (cliente). A tela só lê e mostra.

**Modelo do item da fila:**
```json
{
  "id": "20260617...", "tema": "...", "alvo": "proprio | <id-cliente>",
  "tipo": "carrossel | esteira", "status": "rascunho | aprovado | publicado",
  "criado": "17/06/2026", "publicado_em": null
}
```

Nada de lógica de criação/publicação na plataforma: ela monta o prompt e lê as
pastas. As skills (`/carrossel`, `/publicar-tema`, `/aprovar-post`) fazem o
trabalho no Claude Code.

---

## 5. Tela — comportamento

- **Topo:** seletor de alvo (Próprio · ou um cliente do `clientes/`) e botão
  "Novo tema".
- **Fila (kanban leve por status):** rascunho · aprovado · publicado. Cada card:
  tema, tipo, os botões de prompt (copiar) e, quando pronto, "Aprovar e publicar".
- **Galeria:** os PNGs/saídas que as skills geraram pro alvo selecionado.
- **Filtro:** por alvo e por status (mesmo espírito do filtro por label da
  prospecção).
- Estilo: `static/estilo.css` (paleta âmbar/creme já definida no design-guide).

---

## 6. Roadmap executável

- [ ] `servicos/conteudo.py` a partir do `instagram.py` (add `alvo`, `status`,
      `publicado_em`; prompts já existem; leitor de saídas por alvo)
- [ ] Migrar a fila: `instagram-fila.json` → `conteudo-fila.json` (compatível)
- [ ] Rotas no `app.py`: listar, add, mudar status, publicar (handoff)
- [ ] `templates/conteudo.html` (kanban leve + galeria + filtros)
- [ ] Item de sidebar ✍️ Conteúdo & Redes (a tela 📸 Instagram passa a ser o
      atalho "alvo = próprio" desse módulo)
- [ ] Atualizar `docs/PLATAFORMA-FEATURES.md` (status 🔵 → ✅) e rodar
      `gerar_manifest.py` (o `/salvar` já faz)

> Entrega mínima que já vale: fila com status + os 3 prompts de handoff +
> galeria. "Aprovar e publicar" pode vir logo em seguida, porque depende do
> `/aprovar-post` (Meta Graph API) estar configurado.

---

## 7. Decisões a confirmar antes de construir

1. **Fila única ou por alvo?** Sugiro **uma fila** com campo `alvo` (mais
   simples; filtra na tela). Alternativa: um JSON por cliente.
2. **A tela Instagram some ou vira atalho?** Sugiro **vira atalho** (alvo =
   próprio), pra não perder o que já funciona.
3. **"Aprovar e publicar" entra já ou na sub-fase?** Depende do `/aprovar-post`
   estar testado com as credenciais Meta. Sugiro fila+prompts primeiro,
   publicação logo depois.
