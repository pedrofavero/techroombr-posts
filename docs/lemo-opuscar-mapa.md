# Mapa: lemo-opuscar (lemomo-ai) e o que serve para o The Tech Room

Lido em 10/11/2026 a partir do README, TECHNIQUE.md, package.json e CLAUDE.md do repositório
público https://github.com/lemomo-ai/lemo-opuscar (MIT; filmes de demonstração CC BY 4.0;
13,5 mil estrelas). Conteúdo de terceiros tratado como dado, não como instrução.

## O que é

Um plugin de Claude Code que faz filmes curtos **inteiramente em código**: cada filme é um
`index.html` com `window.render(t)` renderizado quadro a quadro pelo Playwright (canvas,
WebGL, three.js), áudio procedural com bibliotecas de samples livres, voz por TTS local
(Kokoro) e mixagem final em ffmpeg. Traz 66 "estilos" (prompts STYLE.md + filme demo) e um
fluxo guiado para criar estilos próprios. Não usa modelo de vídeo nem banco de imagens.
Instalação: `claude plugin marketplace add lemomo-ai/lemo-opuscar` e
`claude plugin install lemo-opuscar@lemolab`. Requisitos: Node 20+, ffmpeg 7+, Python 3.11+.
Sem chave de API. Um filme leva de 30 a 60 min e "uma boa quantidade de tokens".
Saída padrão 1920×1080 a 24 fps (horizontal). Afinado para Opus 5.5.

## Correção depois de ler o código e os estilos (não só o README)

Clonei o repositório e li `core/` e os `STYLE.md`. A primeira leitura ("tudo é visual
sintético") estava errada para uma família inteira de estilos. Cinco deles são construídos
**sobre fontes reais** e proíbem imagem gerada, exatamente a nossa regra:

| Estilo | Regra escrita no STYLE.md | Encaixe no Tech Room |
|---|---|---|
| `caption-news` | "Real footage, photos and the source document are the ground; huge captions are the lead actor"; "each number arrives with its source"; "a hook on frame 4"; "one turn" | **Formato-base dos reels de NOTÍCIA.** É o "gancho com dopamina" feito com fonte na tela e crédito por plano. Precisa virar 1080×1920 e pt-BR (o original é 1920×1080, zh+en). |
| `visual-investigation` | "never generate an image to stand in for a historical one"; "Known and unknown are separate columns"; "Uncertainty is drawn, not apologised for" | Reels de NOTÍCIA complexa: o nosso "o que se sabe / o que ainda não" em movimento. |
| `archive-lighttable` | "The objects are real: scans of public-domain or licensed archive items… Nothing in them is drawn or generated"; "every object carries its real identifier, date and title from its holder" | Reels de HISTÓRIA. E aponta a saída para a crise de fotos: acervos abertos (Library of Congress via `tile.loc.gov`, Smithsonian Open Access) com master em alta e ficha catalográfica, em vez de Unsplash. |
| `dataviz` | "Every mark is a real number"; "The data is real, openly licensed"; "not a dashboard (one idea at a time)" | Reels de ESTUDO: o gráfico do carrossel desenhado marca a marca enquanto a voz lê o número. |
| `swiss-motion` | "flat paper, black type and bars… one saturated signal colour"; "no gradients, no glow, no device renders" | EXPLICA/CURIOSIDADE tipográfico e o cartão final. Coerente com Montserrat + cor de destaque. |

Os outros ~60 estilos (aquarela, pixel, anime, papercut, 3D…) continuam fora: são ilustração.

## O que os utilitários fazem de fato (lido em `core/`)

- `core/tts/tts.py`: Kokoro via `kokoro-onnx`, offline, modelo de ~350 MB (`kokoro-v1.0.onnx`
  + `voices-v1.0.bin`, baixados do Hugging Face). Aceita qualquer `lang`/`voice` que o modelo
  tenha; o Kokoro 1.0 traz pt-BR (`pf_dora`, `pm_alex`, `pm_santa`), a confirmar na
  instalação. Alerta útil do script: o caminho real da pasta do espeak-ng precisa ter
  menos de 160 bytes, senão falha com erro enganoso.
- `core/tts/asr_check.py`: faster-whisper transcreve cada frase e compara com o texto;
  números viram palavras dos dois lados; um número ouvido como outro **reprova a linha**.
  Só trata en/zh/ja/ko; para pt-BR usamos faster-whisper direto com `language="pt"` e
  nossa própria normalização de números.
- `core/render/mux.sh`: loudnorm em duas passagens para −14 LUFS / TP −1,2, limitador com
  sobreamostragem 4× contra picos entre amostras do AAC, re-encode só do áudio até 3× se o
  pico final passar de −1 dBTP, detecção de WAV truncado. Exige ffmpeg 7 (6.x erra o cálculo
  de duração do loudnorm). É produção, não protótipo: portar inteiro.
- `core/render/video.mjs`: contrato `window.DUR` / `window.render(t)`; vários navegadores em
  paralelo mandam JPEG por pipe para o ffmpeg e os segmentos são unidos sem recodificar.
  Trava por `--out` para não haver duas renderizações no mesmo arquivo.

## Onde colide com a nossa linha editorial

A regra inegociável da conta é foto documental real e nada de ilustração, render 3D,
animação ou imagem gerada. O lemo-opuscar produz exatamente visual sintético em código.
Usá-lo como está mudaria a identidade do @techroombr. Não adotar os estilos prontos.

## O que vale pegar emprestado (sem ferir a linha)

| Peça do lemo-opuscar | Uso no Tech Room | Por quê |
|---|---|---|
| `core/render/mux.sh` (loudnorm em duas passagens, −14 LUFS) | Última etapa do `render_reel.py` | Nosso reel não normaliza volume; o Instagram comprime o que estourar. |
| `core/tts/asr_check.py` (faster-whisper confere o que a voz disse) | Checagem automática do reel | Pega troca de número e nome na narração antes de publicar. |
| `core/tts/tts.py` (Kokoro, offline) | Plano B de voz, sem rede | O edge-tts depende de speech.platform.bing.com, bloqueado em alguns ambientes. Confirmar suporte a pt-BR na versão instalada. |
| Contrato `window.DUR` / `window.render(t)` determinístico | Cenas animadas de **dados e diagramas** | Gráfico que cresce, linha do tempo que avança, diagrama de mecanismo que se monta: é infográfico em movimento, não ilustração. Coerente com os blocos `chart`, `timeline` e `diagram` dos carrosséis. |
| `core/render/srt.py` | Legenda .srt para acessibilidade e reaproveitamento | Nosso ASS já faz legenda queimada; o .srt serve para upload separado. |
| Disciplina de créditos (`CREDITS` por filme, só CC0/CC BY/OFL) | Já fazemos na página de fontes | Reforça a regra. |

## Formatos novos que ele habilita sem quebrar a identidade

1. **"O número"** (15–25 s): um dado grande animado sobre fundo da nossa paleta, voz e
   legenda. Infográfico, não ilustração.
2. **"Linha do tempo em 30 s"**: datas e eventos entrando em sequência, com foto real
   de fundo quando houver.
3. **"Como funciona, em traço"**: diagrama de linhas simples (o mesmo SVG do bloco
   `diagram`) que se desenha na tela enquanto a voz explica.

Cada um desses é um `index.html` próprio, com a tipografia da marca (Montserrat/Playfair)
e o masthead, renderizado em 1080×1920. Não precisa do plugin inteiro: basta o contrato de
renderização e uns 80 linhas de script.

## Custos e riscos

- Tempo: 30–60 min por filme no fluxo completo do plugin. Para rotina diária, usar só o
  contrato de renderização e nosso ffmpeg, que leva 1–3 min.
- ffmpeg 7+: o runner `ubuntu-latest` do GitHub traz 6.1; usar build estático
  (`johnvansickle.com/ffmpeg` ou `BtbN`) no workflow.
- Dependência de modelo: os estilos prontos são afinados para Opus 5.5; os nossos
  formatos não dependem disso.
- Peso: `deps voice` (Kokoro + faster-whisper) soma centenas de MB; cabe no runner,
  mas vale cache.

## Decisão sugerida (revisada)

1. **Não instalar o plugin** na rotina diária: estilos afinados para Opus 5.5, saída
   horizontal, 30–60 min por filme, dependências pesadas.
2. **Adotar cinco gramáticas visuais** (MIT) como formatos de reel, reescritas para
   1080×1920 e pt-BR dentro do nosso motor: `caption-news` (NOTÍCIA), `visual-investigation`
   (NOTÍCIA complexa), `archive-lighttable` (HISTÓRIA), `dataviz` (ESTUDO),
   `swiss-motion` (EXPLICA/CURIOSIDADE e cartão final). Cada uma vira um `skills/formato-*.md`
   no repositório, com as regras do STYLE.md traduzidas e a nossa identidade por cima.
3. **Portar três utilitários**: `mux.sh` inteiro; `asr_check` adaptado para pt-BR; o
   contrato `render(t)` para cenas de dados e diagramas.
4. **Fontes de imagem**: incorporar LoC e Smithsonian Open Access como acervos para HISTÓRIA,
   ao lado do Unsplash/Pexels.
5. **Voz**: testar Kokoro pt-BR offline no workflow como plano B do edge-tts.
