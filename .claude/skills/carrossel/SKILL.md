---
name: carrossel
description: Produzir um carrossel de Instagram do The Tech Room (posts/<slug>/post.json renderizado em 7 a 9 páginas 1080x1350). Use quando pedirem um post, carrossel, pauta do dia, ou ajuste em um carrossel existente.
---

# Carrossel

## 1. Escolher o tema
- Leia `posts/historico.csv` (últimas 9 linhas para a rotação de categorias; o arquivo todo para não repetir tema).
- NOTÍCIA: fato dos últimos 7 dias, com uma fonte primária + uma de imprensa de referência. ESTUDO: paper dos
  últimos 30 dias; vá ao paper; diga amostra, efeito e o que NÃO prova; marque preprint e conflito de interesse.
- Demais categorias: HISTÓRIA, ESTANTE, CURIOSIDADE, COMO FUNCIONA, EXPLICA, CONVERSA.
- Teste: daria uma boa história num jantar? Um leigo entende? Tem fonte para cada frase? Tem foto real plausível?
- Guarde as URLs de todas as fontes abertas: a checagem dupla precisa delas.

## 2. Fotos (2 a 3 por post, só fotografia documental real)
- Busque no Unsplash (MCP, se conectado). Rejeite 3D, render, ilustração, "AI generated".
- Crie `fila/<slug>-<n>.txt`: linha 1 = `urls.raw` + `&w=1600&fit=max&q=85&fm=jpg`; linha 2 = `# Fotógrafo / Unsplash — link`.
- `git add fila && git commit -m "fila: fotos <slug>" && git push`. A Action `fotos` grava `fotos/<slug>-<n>.jpg`
  em 1 a 4 min; espere com `git fetch` + `git ls-tree -r FETCH_HEAD --name-only`, depois `git pull --rebase`.
- Em máquina local dá para baixar direto para `fotos/` com curl; mantenha o `fila/*.txt` como registro do crédito.

## 3. Escrever `posts/<slug>/post.json`
Campos: `slug`, `categoria`, `theme` (dark | paper | night), `display` (sans | serif), `masthead` "The Tech Room",
`handle` "@techroombr", `slides[]`, `legenda`. Tipos de página: docstring de `engine/render_natgeo.py`.
- Capa (`cover`): título até 60 caracteres com fato + virada; `dek` de 1 a 2 frases.
- Uma ideia por página; cada página faz sentido sozinha.
- Varie os blocos conforme a categoria: ESTUDO pede `stat`/`chart`/`card`; COMO FUNCIONA pede `diagram`/`steps`;
  HISTÓRIA pede `timeline`/`quote`; ESTANTE pede `card`/`compare`; NOTÍCIA pede `compare` "o que se sabe / não se sabe".
- Penúltima página: `inner` "Para levar" com 3 itens em `check`. Última: `sources` com 3 a 5 fontes + linha "Fotos".
- Foto real na capa e em pelo menos uma página interna (`photo` + `caption` "Foto: Nome / Unsplash").
- Legenda: 1 frase que amplia; 2 a 3 de contexto; 1 pergunta; linha "—"; "Fontes no último slide."; 5 a 8 hashtags.

## 4. Renderizar e conferir
```bash
python3 engine/render_natgeo.py posts/<slug>/post.json
```
- "AVISO: página N estourou" → corte texto e renderize de novo.
- Abra `posts/<slug>/_prancha.jpg` e confira: nada cortado, nada sobre o @techroombr, texto legível sobre a foto,
  destaque (`==x==`) legível (sobre foto, prefira `**negrito**`).

## 5. Checar e entregar
- Rode a skill `checagem-dupla`. Corrija, renderize, repita até limpar.
- `git add posts/<slug> fila fotos && git commit -m "post: <slug>" && git pull --rebase origin main && git push`.
- Agendamento e publicação: skill `publicar` (fila própria em `fila-publicacao/`).
