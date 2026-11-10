---
name: publicar
description: Agendar, publicar, segurar ou cancelar carrosséis e reels do The Tech Room no Instagram (Metricool para carrosséis, API própria e fila-publicacao para reels) e manter posts/historico.csv. Use quando pedirem para agendar, publicar agora, segurar, reagendar, conferir o que está na fila ou diagnosticar uma publicação que falhou.
---

# Publicar

Publicar é público e não tem ensaio. Só publique ou agende com a checagem dupla limpa e com pedido explícito.
Antes de qualquer coisa, veja o que já está agendado para o dia (Metricool e `fila-publicacao/`) para não empilhar nem duplicar.

## Carrossel pelo Metricool (padrão da rotina)
- Precisa do conector/MCP do Metricool. blogId `7436094`, fuso `America/Sao_Paulo`.
- `createScheduledPost`: `media` = `https://raw.githubusercontent.com/pedrofavero/techroombr-posts/main/posts/<slug>/01.png` … em ordem
  (confirme HTTP 200 antes); `text` = legenda; `providers` instagram; `instagramData {"type":"POST"}`; `autoPublish true`.
- Padrão de horário: 10:00 e 18:30, sempre para o dia seguinte ou depois (o intervalo é a janela para segurar).
- Imagem mudou depois de agendar: reenvie a lista de `media` com `updateScheduledPost` (o Metricool copia a mídia;
  use a URL com o hash do commit no lugar de `main` para furar o cache). O `id` muda a cada update; o `uuid` não.
- Segurar: `updateScheduledPost` com `draft true` e `autoPublish false`. Não existe apagar pela API.

## Reel (e carrossel) pela API própria
- Agendar: crie `fila-publicacao/<AAAA-MM-DD>-reel-<slug>.json` com
  `{"type": "reel", "slug": "<slug>", "when": "<AAAA-MM-DD>T12:30:00-03:00"}` (`"type": "carousel"` também vale);
  commit `fila: reel <slug>`; pull --rebase; push. O workflow `publicar` roda aos minutos 05 e 35 e publica o que venceu.
- O reel precisa já estar renderizado pelo workflow `reel` (vídeo no branch `media`) e com `reel_asr.txt` aprovado.
- Segurar: acrescente `"hold": true` ao arquivo. Liberar: remova o `hold` e ponha um `when` futuro.
- Publicar agora (só com pedido explícito): Actions → `publicar` → `carousel` ou `reel` + slug; ou Actions → `reel`
  com `publicar = agora`. Fontes do reel vão sozinhas no primeiro comentário.
- Se o mesmo conteúdo estiver agendado no Metricool, tire de lá antes: senão sai duas vezes.

## Histórico
`posts/historico.csv`, colunas `data,categoria,titulo,slug,fontes,status,publicacao,metricool_url`. Uma linha por item.
Reel: categoria `REEL (<categoria>, <estilo>)`, slug `<slug>-reel`. Status: `agendado (silêncio = aprovado)`,
`segurado`, `publicado`. A publicação pela API marca `publicado` e grava o permalink sozinha.
Commit `historico: <slugs>`.

## Diagnóstico
- Actions → `publicar` → `debug`: token válido? escopo `instagram_content_publish`? → `me`: conta certa? → `limit`: cota.
- Job que morre em 2 s sem rodar passo: cobrança da conta do GitHub, não código.
- Erro 190: token inválido; gerar outro no painel da Meta (`SETUP.md`) e atualizar o secret `IG_ACCESS_TOKEN`.
- Erro 100 "nonexisting field": campo que não existe no login unificado (`graph.facebook.com`); ajuste em `engine/publish_ig.py`.
- Vídeo recusado: confira 1080×1920, H.264 + AAC, até 90 s, URL pública respondendo 200.

## Medir (semanal)
Pelo Metricool ou Insights, por post: envios ÷ alcance, tempo médio assistido (reels), salvamentos (carrosséis),
% de não seguidores. O que ficar acima da mediana do perfil se repete; mude uma variável por vez.
