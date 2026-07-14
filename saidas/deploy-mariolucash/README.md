# mariolucash.com.br — site pronto pra deploy

Site estático autossuficiente do Mario Lucas (automação e IA). Zero dependência externa: fontes de sistema, imagens locais, tudo self-contained.

## Conteúdo da pasta

| Arquivo | O que é |
|---|---|
| `index.html` | O site completo (head com meta/OG, dados estruturados, estilo e script inline) |
| `favicon.svg` | Ícone da aba (logo caos) |
| `og.png` | Imagem de preview do link (WhatsApp, redes) — 1200×630 |
| `sitemap.xml` · `robots.txt` | Para os buscadores |
| `netlify.toml` | Config de deploy (publish = raiz) |

## Migrar pro repositório mariolucash

O conteúdo desta pasta é a **raiz** do site. Passos:

```bash
git clone https://github.com/Kallenhard1/mariolucash.git
cp -r saidas/deploy-mariolucash/* mariolucash/
cd mariolucash
git add .
git commit -m "site inicial mariolucash.com.br"
git push
```

## Publicar na Netlify

**Opção A — conectar o repo (recomendado, deploy automático a cada push):**
1. app.netlify.com → Add new site → Import from Git → escolher `Kallenhard1/mariolucash`
2. Build command: (vazio) · Publish directory: `.`
3. Deploy. A cada `git push`, a Netlify republica sozinha.

**Opção B — arrastar e soltar:**
- app.netlify.com/drop → arrastar esta pasta inteira.

**Opção C — CLI:**
```bash
netlify deploy --prod --dir=.
```

## Apontar o domínio

Na Netlify: Site settings → Domain management → Add custom domain → `mariolucash.com.br`.
Seguir as instruções de DNS (apontar para a Netlify) no seu registrador do domínio.

## Confirmar antes de publicar

- **Instagram:** o JSON-LD e as metatags referenciam `instagram.com/mariolucash`. Se o @ for outro, ajustar em `index.html` (campos `sameAs`).
- **og.png:** o preview usa `https://mariolucash.com.br/og.png` (URL absoluta). Só funciona depois que o domínio estiver no ar.
- **Dados estruturados:** depois de publicado, testar em search.google.com/test/rich-results — o próprio site tem que passar (é a prova viva do serviço de Visibilidade em IA).
