# toolbox — peças do lemo-opuscar usadas pelo The Tech Room

Arquivos copiados sem alteração de https://github.com/lemomo-ai/lemo-opuscar (commit `9eb7739`, licença MIT em
`LICENSE-lemo-opuscar`). Mantemos só o que serve à linha editorial (foto real + infográfico; nada de ilustração gerada).

| Arquivo | Origem | Uso aqui |
|---|---|---|
| `mux.sh` | `core/render/mux.sh` | Masterização do reel: loudnorm em duas passagens (−14 LUFS), limitador e conferência de pico. Chamado por `engine/render_reel.py` quando há ffmpeg 7+. |
| `tts.py` | `core/tts/tts.py` | Referência da voz offline Kokoro. O motor chama o Kokoro direto (pt-BR: `pf_dora`, `pm_alex`) como plano B do edge-tts. |
| `asr_check.py` | `core/tts/asr_check.py` | Referência (só en/zh/ja/ko). A conferência em português está em `engine/asr_check_pt.py`. |
| `srt.py` | `core/render/srt.py` | Referência para legenda .srt. |

Do toolbox também vem o **contrato de animação** `window.DUR` / `window.render(t)`: as cenas `anim` do reel
(número, barras, linha do tempo) são páginas HTML determinísticas renderizadas quadro a quadro.

`modelos/` (Kokoro, ~350 MB) não vai para o git: o workflow `reel` baixa e guarda em cache.
