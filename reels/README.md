# Reels

- `fila-video/<slug>-<n>.txt`: pedido de b-roll (linha 1: busca em inglês no Pexels; linha 2: portrait|landscape). A Action `videos` grava `videos/<slug>-<n>.json` (crédito, URL do Pexels, URL do clipe na release `clips`).
- `videos/<slug>-<n>.mp4`: clipe baixado da release para renderizar (não vai para o git).
- `posts/<slug>/reel.json`: roteiro do reel (ver docstring de `engine/render_reel.py`). `python3 engine/render_reel.py posts/<slug>/reel.json` gera `reel.mp4`, `reel_cover.jpg`, `reel_legenda.txt` e `_reel_prancha.jpg`.
- `posts/<slug>/reel.mp4` vai para a release `reels` (URL pública para o Metricool): `https://github.com/pedrofavero/techroombr-posts/releases/download/reels/<slug>.mp4`.
- `reels/musica/`: trilhas livres de direitos (mp3) para usar no campo `music` do reel.json. Sem arquivo, o reel sai sem áudio.
