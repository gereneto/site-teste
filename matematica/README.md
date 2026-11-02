# taioe-matematica

Estudos para uma série de livros de história da matemática, publicados em **taioe.com.br/matematica**. Pasta `matematica` dentro de `taioe/`.

Worker da Cloudflare só com arquivos estáticos, como os outros sites da Taioé (contrato da origem no README do `taioe-hub`): publica só o prefixo `/matematica`, pela route `taioe.com.br/matematica*`.

## Como está organizado

```
conteudo/index.md                 capa (/matematica/)
conteudo/NN-slug/index.md         abertura de um estudo (/matematica/slug/)
conteudo/NN-slug/NN-parte.md      partes do estudo, em ordem (/matematica/slug/parte/)
ferramentas/gerar.py              gera public/matematica/ a partir de conteudo/
public/matematica/estilo.css      aparência (cores e fonte do hub)
public/matematica/fontes/         Nunito (OFL)
public/_headers                   CSP e demais cabeçalhos
wrangler.jsonc                    Worker e route
```

O texto se escreve em Markdown em `conteudo/`. Os números `NN` dão a ordem e não entram no endereço. O título de cada página é o primeiro `# ` do arquivo. Depois de mexer em `conteudo/`:

```bash
python ferramentas/gerar.py
```

e fazer commit de `conteudo/` e de `public/` juntos (o deploy não roda build).

Para ver no computador: `python -m http.server 8790 -d public` e abrir http://localhost:8790/matematica/.

## Regras herdadas do hub

- Sem scripts nem estilos inline, sem scripts de terceiros, sem cookies (a CSP de `_headers` impede).
- As páginas levam `noindex`: são estudos de trabalho.
- O acesso pelo admin é um link em `/admin/`, que vem de `dados/paginas/admin.json` do `taioe-infra`.

## Deploy

Workers Builds, a cada push na `main`: comando de build vazio, deploy com `npx wrangler deploy`. Nas outras branches, `npx wrangler versions upload`.
