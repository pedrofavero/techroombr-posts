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

## Decisão sugerida

Não instalar o plugin no pipeline. Copiar três ideias: normalização de volume, checagem
por ASR e o contrato `render(t)` para cenas de dados. Testar primeiro o Kokoro em pt-BR
como voz alternativa ao edge-tts.
