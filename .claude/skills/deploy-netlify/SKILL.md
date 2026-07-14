---
name: deploy-netlify
description: >
  Pega um HTML (de artifact ou de saidas/) e prepara a pasta de deploy pronta pra Netlify:
  index.html completo com doctype, meta tags, Open Graph, favicon, fontes locais e os dados
  estruturados que fazem o site passar na própria auditoria. Use quando o usuário disser
  "publicar na netlify", "preparar deploy", "subir o site", "pasta de deploy" ou /deploy-netlify.
---

# /deploy-netlify — Preparar pasta de deploy pra Netlify

Converte um HTML de trabalho num site real, pronto pra hospedar. Fecha a lacuna entre o
artifact (fragmento) e um site publicável.

## Dependências

- HTML de origem (ex: `saidas/site-<slug>.html`).
- `identidade/fontes/` (embutir fontes locais, sem depender de CDN).
- Netlify (a publicação em si é feita pelo usuário; a skill entrega a pasta pronta).

## O que a pasta de deploy precisa ter

Criar `saidas/deploy-<slug>/` com:

1. **index.html completo** — envelopar o HTML de trabalho com:
   - `<!DOCTYPE html>`, `<html lang="pt-BR">`, `<head>` com `<meta charset>` e viewport.
   - `<title>` e `<meta name="description">` reais.
   - **Open Graph** (og:title, og:description, og:image, og:url) pro link ficar bonito no WhatsApp.
   - Favicon (o logo caos, como .svg ou .png de `identidade/`).
   - Fontes via `@font-face` apontando pra `./fonts/` local.
2. **Dados estruturados (JSON-LD)** no `<head>` — o próprio site tem que passar na auditoria
   que o Mario vende. Escolher o `@type` certo: `Person`/`Organization` pro site do Mario,
   `LocalBusiness`/sub-tipo pro site de um cliente, com nome, url, sameAs, contato.
3. **fonts/** — cópia das fontes usadas.
4. **netlify.toml** simples (publish = ".") e um **_redirects** se precisar.

## Passos

1. Ler o HTML de origem e identificar título, descrição e tipo de negócio.
2. Montar `saidas/deploy-<slug>/index.html` com head completo + JSON-LD.
3. Copiar as fontes pra `saidas/deploy-<slug>/fonts/` e ajustar os caminhos.
4. Escrever `netlify.toml`.
5. Entregar as instruções de publicação:
   - Arrastar a pasta em app.netlify.com/drop, **ou**
   - `netlify deploy --prod --dir=saidas/deploy-<slug>` (se o Netlify CLI estiver logado).
6. Lembrar de apontar o domínio (mariolucash.com.br) nas configs da Netlify.

## Regras

- **O site do Mario tem que ser a vitrine do serviço:** JSON-LD sempre presente e válido.
- **Sem CDN externo:** fontes e assets locais (a Netlify serve tudo da pasta).
- Não inventar dados no JSON-LD (endereço, nota): só o que for verdadeiro.
- A publicação final é do usuário; a skill não tem acesso à conta Netlify. Entregar a pasta e o passo a passo.
