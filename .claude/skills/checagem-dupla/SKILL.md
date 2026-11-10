---
name: checagem-dupla
description: Checagem independente de fatos de um carrossel ou reel do The Tech Room contra as fontes, feita por um subagente que não usa conhecimento próprio. Use sempre antes de agendar ou publicar qualquer conteúdo, e depois de qualquer edição que mude número, data, nome, citação ou atribuição.
---

# Checagem dupla

Quem escreveu não checa. Lance um subagente (Agent, tipo general-purpose) para cada peça.

## Carrossel
Briefing do subagente:
- O caminho `posts/<slug>/post.json` para ele ler (todas as páginas e a `legenda`).
- A lista de URLs de TODAS as fontes usadas, com o que conferir em cada uma.
- Instrução: abrir cada fonte e verificar, frase por frase, todo número, data, nome, citação e atribuição.
  Usar SOMENTE o que as fontes dizem. Fonte bloqueada ou fora do ar = "não verificável", não "erro"; não repetir a tentativa.
  Apontar também afirmação sem apoio em nenhuma fonte e contradição entre fontes.
- Formato da resposta: `página N: afirmação — o que a fonte diz — gravidade (erro / imprecisão / sem fonte / não verificável)`,
  só os problemas; no fim, quais fontes abriu e um veredito de uma linha.

## Reel
Briefing: ler `posts/<slug>/reel.json` e `posts/<slug>/post.json`; confirmar, cena por cena, que todo número, data,
nome e atribuição do reel (fala, tela, legenda, comentário de fontes) é igual ao post.json já checado e que nenhuma
simplificação mudou o sentido. Mesmo formato de resposta.

## O que fazer com o resultado
- "erro" ou "sem fonte": corrija ou remova a afirmação, renderize de novo.
- "imprecisão": corrija quando muda o sentido (ex.: "uma medição" × "uma consulta"; "casos leves" × "corte mais baixo").
- "não verificável": só mantém se outra fonte independente aberta sustenta; senão, remova.
- Depois de corrigir, mande o MESMO subagente reconferir só as frases alteradas. Repita até "limpo".
- Não ficou limpo: NÃO agende; entregue para aprovação manual explicando o problema.
- Na entrega, liste como [CONFERIR] o que só foi confirmado em fonte secundária e as fontes primárias que não abriram.

## Erros que já apareceram
- Síntese que a fonte não faz: ligar dois fatos com "por causa de", ou atribuir a uma fonte o que veio de outra.
- Número certo, rótulo errado (sensibilidade com corte diferente virou "casos leves").
- Data de uma fonte usada como se todas concordassem (1991 × 1994 para a mesma regra).
- "Segundo X" quando X só relata o que Y disse.
