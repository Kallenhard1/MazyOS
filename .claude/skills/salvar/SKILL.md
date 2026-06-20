---
name: salvar
description: >
  Salva o trabalho do MazyOS no GitHub (commit + push). Na primeira vez configura o repositório
  remoto. Use quando o usuário disser "salvar", "salva no github", "commit", "push", "/salvar"
  ou pedir backup do trabalho.
---

# /salvar — Salvar no GitHub

Skill de uma função só: garantir que o trabalho do usuário está no GitHub. Fácil pra quem nunca usou git.

## Workflow

### Primeira vez (repositório não inicializado)

Detectar com `git rev-parse --is-inside-work-tree`. Se falhar:

1. Perguntar:
   > "Esse é o primeiro syncar. Você já tem um repositório criado no GitHub pra esse workspace?
   > 1. Sim, me passa a URL (ex: https://github.com/usuario/nome.git)
   > 2. Não, vou criar agora — me dá um nome pro repositório (ex: meu-mazyos)"

2. **Se opção 1:** rodar `git init`, `git add .`, `git commit -m "Setup inicial do MazyOS"`, `git branch -M main`, `git remote add origin <URL>`, `git push -u origin main`.

3. **Se opção 2:** verificar se o `gh` CLI está instalado (`gh --version`). 
   - Se sim: rodar `git init`, criar commit inicial, e `gh repo create <nome> --private --source=. --push`.
   - Se não: instruir o usuário a instalar `gh` (https://cli.github.com/) ou criar o repo manualmente em github.com/new e voltar com a URL.

### Commits seguintes (já configurado)

1. **Sincronizar a plataforma com o MazyOS.** Rodar
   `python scripts/gerar_manifest.py` pra atualizar `plataforma/manifest.json`
   (a lista viva de skills e funções que a plataforma lê). Se a saída listar
   algo em "não viraram feature ainda", avisar o usuário que tem skill ou
   função nova sem feature na plataforma e oferecer mapear em
   `docs/PLATAFORMA-FEATURES.md` antes de seguir.

2. Rodar `git status`. Se não tiver mudanças, responder "Tá tudo sincronizado, sem mudança nova" e parar.

3. Mostrar o `git status` curto pro usuário e perguntar:
   > "Vou comitar tudo isso. Quer descrever a mudança em uma frase ou usa o resumo automático?"

4. Se o usuário fornecer mensagem, usar. Se não, gerar uma mensagem baseada nos arquivos alterados (1 linha, formato: "Atualiza X" ou "Adiciona Y" ou "Cria proposta pra cliente Z").

5. `git add .` → `git commit -m "<mensagem>"` → `git push`.

6. Confirmar com link do repositório (extrair de `git remote get-url origin`):
   > "Sincronizado. Ver no GitHub: <URL>"

## Regras

- O `/salvar` é o ponto onde MazyOS e plataforma se sincronizam: sempre
  regenerar `plataforma/manifest.json` (passo 1) antes de comitar. O manifesto
  é gerado, nunca editado à mão.
- Nunca usar `--force` sem o usuário pedir explicitamente
- Nunca rodar `git reset --hard` ou outras destrutivas sem confirmação clara
- Se o push falhar por divergência (alguém comitou no remoto), avisar o usuário e oferecer `git pull --rebase` antes de tentar de novo
- Se o usuário ainda não tiver `git` configurado (`user.name` / `user.email`), perguntar e configurar com `git config --global` na primeira vez
