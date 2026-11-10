# Reels — ativo desde 10/11/2026 (pipeline v2)

## Fluxo

1. Escrever `posts/<slug>/reel.json` (campos no docstring de `engine/render_reel.py`) e dar push.
2. O workflow **reel** renderiza no GitHub Actions (voz, legendas palavra a palavra, cenas animadas), confere a narração
   com Whisper e hospeda o vídeo em `https://raw.githubusercontent.com/pedrofavero/techroombr-posts/media/<slug>-reel.mp4`.
   No repositório ficam só `reel_cover.jpg`, `_reel_prancha.jpg`, `reel_legenda.txt`, `reel_fontes.txt`, `reel_meta.json`
   e `reel_asr.txt` (roteiro x o que foi ouvido).
3. Publicar: **Actions → reel → Run workflow** com `publicar = agora`, ou enfileirar em
   `fila-publicacao/<nome>.json` (`{"type":"reel","slug":"…","when":"2026-11-12T12:00:00-03:00"}`), que o workflow
   **publicar** dispara no horário. As fontes vão no primeiro comentário.

A renderização só funciona no Actions: a voz (edge-tts) e os modelos (Kokoro, Whisper) precisam de rede aberta.
Localmente, `--fake-tts` gera o vídeo mudo para conferir o visual.

## Peças

- Voz: edge-tts (`pt-BR-FranciscaNeural`, `AntonioNeural`, `ThalitaMultilingualNeural`); plano B offline Kokoro (`pf_dora`, `pm_alex`).
- Cenas: foto com Ken Burns, b-roll (`videos/<x>.mp4`, via workflow `videos` + `PEXELS_API_KEY`), e `anim`
  (número, barras, linha do tempo) no contrato `window.render(t)` do toolbox.
- Áudio final: `toolbox/mux.sh` (−14 LUFS, duas passagens). Conferência: `engine/asr_check_pt.py`; número do roteiro
  não ouvido bloqueia a publicação pelo workflow.
- `reels/musica/`: trilhas livres (mp3) para o campo `music`. Sem arquivo, o reel sai só com voz.
- Origem e licença das peças emprestadas do lemo-opuscar: `toolbox/README.md`.
