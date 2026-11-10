---
name: reel
description: Produzir um reel do The Tech Room (posts/<slug>/reel.json, 25 a 40 s, 1080x1920) a partir de um carrossel já checado, escolhendo entre os estilos foto, lousa, caderno, planta e aquarela. Use quando pedirem reel, vídeo curto, ou ajuste de roteiro, estilo ou voz de um reel.
---

# Reel

Leia antes: `reels/GUIA.md` e os docstrings de `engine/render_reel.py` e `engine/reel_styles.py`.

## 1. Tema e estilo
- O reel parte de um carrossel já checado e usa SOMENTE fatos do `post.json` dele.
- Estilo pela categoria, nunca igual ao do reel anterior:

| Categoria | `style` | Cena-assinatura |
|---|---|---|
| NOTÍCIA, ESTUDO | (sem `style`: foto) | `hook` com número, `number`, `bars`, sempre com `fonte` |
| EXPLICA, COMO FUNCIONA | `lousa` | `corrige`: mito riscado, fato escrito |
| COMO FUNCIONA (máquinas, redes, chips) | `planta` | `draw` em ordem de desenho técnico |
| CURIOSIDADE, CONVERSA, ESTANTE | `caderno` | `draw`: o objeto se desenha |
| HISTÓRIA | `aquarela` ou `caderno` | `timeline`, `draw` |

## 2. Roteiro (`posts/<slug>/reel.json`)
- `"voice": "pt-BR-ThalitaMultilingualNeural"`, `"voice_rate": "+10%"`, `"captions": true`.
- **Som: só a voz.** Não inclua `music` nem `sfx`.
- 5 a 7 cenas; soma dos `say` entre 70 e 95 palavras.
- Funciona sem som. Cena 1 é o gancho (maior número ou afirmação central no primeiro quadro). Uma virada no meio.
- Todo número na tela com `fonte` na mesma cena. Numerais em dígitos.
- Na fala, evite siglas e nomes estrangeiros difíceis: descreva ("a agência de aviação americana").
- Última cena: `{"end": true, "title": "Fontes", "lines": [...3 fontes...], "say": "Fontes no primeiro comentário."}`.
- `legenda`: assunto por extenso, ressalvas do post, uma frase que dê motivo para enviar a alguém, "—",
  "Fontes no primeiro comentário.", 3 a 5 hashtags. `fontes_comentario`: fontes completas em um parágrafo.
- Formato foto: cada cena com `media` (`fotos/<slug>-n.jpg`) e `credit`; `"accent": "#FFC21A"`.
- Estilos desenhados: toda cena tem `anim`; sem foto. SVG da cena `draw`: só linhas simples (`path`, `line`, `rect`,
  `circle`, `text`), sem cor, `class='acc'` no destaque, textos curtos e longe dos traços. Nunca copie desenho,
  personagem ou logotipo de terceiros.

## 3. Conferir o visual (sem voz)
```bash
python3 engine/render_reel.py posts/<slug>/reel.json --fake-tts
```
Abra `posts/<slug>/_reel_prancha.jpg`. Corrija avisos de texto alto ou encostando na legenda. Depois apague as saídas:
`rm -f posts/<slug>/reel.mp4 posts/<slug>/reel_cover.jpg posts/<slug>/_reel_prancha.jpg posts/<slug>/reel_meta.json posts/<slug>/reel_legenda.txt posts/<slug>/reel_fontes.txt`

## 4. Checar os fatos
Skill `checagem-dupla`, no modo reel (reel.json contra o post.json checado).

## 5. Renderizar de verdade
- Na nuvem: `git add posts/<slug>/reel.json && git commit -m "reel: <slug>" && git pull --rebase origin main && git push`.
  O workflow `reel` leva 4 a 8 min e faz o commit "reel: render automático (<slug> )". Espere com `git fetch` e
  `git log FETCH_HEAD -6 --format=%s`; depois `git pull --rebase`.
- Em máquina local com rede aberta: `python3 engine/render_reel.py posts/<slug>/reel.json` gera o mp4 na hora
  (para ouvir). O vídeo que vai ao ar é sempre o do workflow.

## 6. Conferir a voz
- `posts/<slug>/reel_asr.txt` precisa trazer "números: todos ouvidos" e semelhança ≥ 90%.
- Leia o bloco OUVIDO: palavra-chave ouvida errado → reescreva no `say` como se fala e renderize de novo (até 2 vezes).
- Vídeo hospedado: `https://raw.githubusercontent.com/pedrofavero/techroombr-posts/media/<slug>-reel.mp4`.
- Entregue o mp4 para a pessoa ouvir: ninguém mais ouve o áudio.

## 7. Publicar
Skill `publicar`.

## Estilo novo
Novo estilo desenhado = uma entrada em `STYLES` de `engine/reel_styles.py` (fundo, tinta, destaque, fonte manuscrita,
espessura, rugosidade, som) + CSS `body.<nome> .tex`. Fontes manuscritas (OFL) em `engine/fonts/hand/`. Teste com
`--fake-tts` em todas as cenas (`hook`, `write`, `corrige`, `draw`, `number`, `bars`, `timeline`, `end`) e registre em `reels/GUIA.md`.
