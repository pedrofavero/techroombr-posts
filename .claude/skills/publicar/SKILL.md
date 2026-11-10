---
name: publicar
description: Agendar, publicar, segurar, reagendar ou cancelar carrosséis e reels do The Tech Room no Instagram pela fila própria (fila-publicacao/ + workflow publicar) e manter posts/historico.csv. Use quando pedirem para agendar, publicar agora, segurar, mudar horário, conferir o que está na fila ou diagnosticar uma publicação que falhou.
---

# Publicar

Publicar é público e não tem ensaio. Só publique ou agende com a checagem dupla limpa e com pedido explícito.
Tudo sai pela API oficial do Instagram; o Metricool não é mais usado para publicar.

## Agendar
Um arquivo por item em `fila-publicacao/`:

```json
{"type": "carousel", "slug": "<slug>", "when": "2026-11-12T10:00:00-03:00"}
```
- `type`: `carousel` (publica `posts/<slug>/NN.png` + `legenda.txt` como estiverem no `main` na hora) ou `reel`
  (publica o vídeo já renderizado pelo workflow `reel`; fontes vão sozinhas no primeiro comentário).
- `when` sempre com fuso (`-03:00`). Nome do arquivo: `<AAAA-MM-DD>-<ordem>-<carrossel|reel>-<slug>.json`.
- Padrão do dia: carrossel 10:00, reel 12:30, carrossel 18:30. Nunca para hoje na rotina: o dia de intervalo é a janela para segurar.
- Antes: liste `fila-publicacao/*.json` para não empilhar nem repetir. Reel precisa de `reel_asr.txt` com "números: todos ouvidos".
- `git add fila-publicacao && git commit -m "fila: <slugs>" && git pull --rebase origin main && git push`.
- O workflow `publicar` roda a cada 10 minutos (o agendador do GitHub pode atrasar alguns minutos). Conferir sem
  publicar: `python3 engine/publish_ig.py due --dry-run`.

## Segurar, liberar, mudar
- Segurar: acrescente `"hold": true` ao arquivo; commit e push.
- Liberar: remova o `hold` e ponha um `when` futuro.
- Mudar horário: edite o `when`. Cancelar de vez: apague o arquivo.
- Mudar o conteúdo de um item já na fila: edite, renderize e faça push; a fila publica o que estiver no `main`.

## Publicar agora (só com pedido explícito)
Actions → `publicar` → `carousel` ou `reel` + slug; ou Actions → `reel` com `publicar = agora`.
Se o item também estiver na fila, apague o arquivo ou ponha `hold` antes: senão sai duas vezes.

## Histórico
`posts/historico.csv`, colunas `data,categoria,titulo,slug,fontes,status,publicacao,metricool_url` (a última coluna
guarda o link do Instagram). Uma linha por item. Reel: categoria `REEL (<categoria>, <estilo>)`, slug `<slug>-reel`.
Status: `agendado (silêncio = aprovado)`, `segurado`, `publicado`. A publicação marca `publicado`, grava o permalink
e move o arquivo para `fila-publicacao/feito/` sozinha. Commit `historico: <slugs>`.

## Diagnóstico
- Actions → `publicar` → `debug`: token válido? escopo `instagram_content_publish`? → `me`: conta certa? → `limit`: cota.
- Item venceu e não saiu: veja a última execução do workflow `publicar`. Sem execução = agendador do GitHub atrasou;
  dispare `due` à mão.
- Job que morre em 2 s sem rodar passo: cobrança da conta do GitHub, não código.
- Erro 190: token inválido; gerar outro no painel da Meta (`SETUP.md`) e atualizar o secret `IG_ACCESS_TOKEN`.
- Erro 100 "nonexisting field": campo que não existe no login unificado (`graph.facebook.com`); ajuste em `engine/publish_ig.py`.
- Vídeo recusado: confira 1080×1920, H.264 + AAC, até 90 s, URL pública respondendo 200.

## Medir (semanal)
Por post: envios ÷ alcance, tempo médio assistido (reels), salvamentos (carrosséis), % de não seguidores. Hoje esses
números vêm dos Insights do app ou do conector do Metricool (só leitura); o token do repositório não tem a permissão
`instagram_manage_insights`. O que ficar acima da mediana do perfil se repete; mude uma variável por vez.
