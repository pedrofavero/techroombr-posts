# The Tech Room — posts

Repositório de apoio da publicação @techroombr. Nenhum arquivo aqui precisa ser editado à mão.

| Pasta | O que é |
|---|---|
| `engine/` | Molde NatGeo (`natgeo.html`) e renderizador (`render_natgeo.py`) |
| `fila/` | Pedidos de foto: `slug.txt` com a URL do Unsplash na primeira linha |
| `fotos/` | Fotos baixadas pela Action (`slug.jpg`) |
| `posts/<slug>/` | Conteúdo do post (`post.json`), páginas renderizadas (`01.png`…`06.png`), `legenda.txt` |

Fluxo: Claude escolhe a foto no Unsplash → grava `fila/slug.txt` → a Action baixa para `fotos/` → Claude renderiza as páginas → publica em `posts/` → após "aprovado", o Metricool agenda usando as URLs públicas de `posts/`.

Fotos: licença Unsplash. Crédito ao fotógrafo na página de fontes de cada post.
