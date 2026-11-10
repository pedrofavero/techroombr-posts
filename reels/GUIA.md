# Guia de reels — The Tech Room (pesquisa de 10/11/2026)

Carrosséis não mudam. Este guia vale só para reels.

## 1. O que o Instagram diz que pesa (e o que é palpite)

Fontes: cinco guias de 2026 (Dataslayer, SocialPilot, Hootsuite, PostEverywhere, Highstyle) que citam Adam Mosseri
e a página "Instagram Ranking Explained". Nenhuma fonte primária do Instagram foi aberta diretamente; tratar como relato.

| Ponto | Quem afirma | Como usamos |
|---|---|---|
| Os três sinais principais: tempo assistido, curtidas por alcance e **envios por alcance** (Mosseri, jan. 2025) | Instagram, relatado por 4 guias | Roteiro curto, sem enrolação; uma frase na legenda que dê motivo para mandar a alguém |
| Envios pesam mais para alcançar quem **não** segue; curtidas, para quem já segue | Instagram, relatado por 3 guias | Tema com cara de "preciso mostrar isso a alguém" |
| Menos alcance: marca d'água de outros apps, baixa resolução, reel mudo, bordas, **reel que é quase só texto**, conteúdo repostado | Lista do próprio Instagram, relatada pelo PostEverywhere | 1080×1920, sempre com voz e trilha, foto ou vídeo real em tela, nada reaproveitado de terceiros |
| "Quanto mais curto, melhor" (Mosseri, sem data) | Instagram, relatado pelo Hootsuite | Alvo de 25 a 40 s |
| Hashtag não é alavanca de distribuição; legenda com palavras-chave ajuda a busca | Instagram (hashtags) + autores (palavras-chave) | 3 a 5 hashtags; primeira frase da legenda com o assunto por extenso |
| Trial Reels: mostra primeiro a não seguidores | Instagram, relatado por todos | Usar para testar formato novo (publicação manual; a API não cobre) |
| Janela do gancho (0,2 s, 1,7 s, 3 s), duração ideal, "envio vale 3 a 5 curtidas", "10 reposts em 30 dias" | Só autores; números divergem e não têm fonte | Não tratar como regra. Medir no nosso próprio perfil |

## 2. Formato da casa (gramática "caption-news" do lemo-opuscar, adaptada para 9:16 e pt-BR)

1. **Funciona sem som.** Cada cena se entende só com imagem e legenda; a voz dá ritmo.
2. **Gancho no primeiro quadro.** Cena `anim: hook`: o maior número ou a afirmação central num bloco amarelo, já em 0,1 s.
3. **Uma virada.** O gancho é respondido por um fato que muda o sentido dele ("mas a IA não mede a pressão").
4. **Evidência em tela.** Todo número aparece com selo `FONTE` na mesma cena (`anim.fonte`); crédito da foto no canto.
5. **Nada parado.** Cortes secos na grade de 0,5 s; a foto troca de enquadramento a cada ~2,5 s; contadores rolam; barras crescem.
6. **Legenda é o ator principal.** Blocos de até 3 palavras, caixa alta, entram com "slam"; palavra falada em amarelo.
7. **Som.** Voz + trilha procedural a 120 BPM (gerada em código, sem direitos de terceiros) + efeitos nas ações de tela.
   Master em −14 LUFS.
8. **Fecho curto.** Cartão de fontes de 2 a 3 s; fontes completas no primeiro comentário.

Ordem de um fato: imagem (sensação) → número no cartão → de onde veio → consequência.

## 3. Repertório de estilos (campo `style` do reel.json)

Decisão de 10/11/2026: nos **reels** valem estilos desenhados, sem foto. Os carrosséis continuam só com fotografia real.

| Estilo | Visual | Encaixa em | Cena-assinatura |
|---|---|---|---|
| `foto` (padrão) | fotografia real, legenda gigante, bloco amarelo | NOTÍCIA, ESTUDO | `hook` com número, `number`, `bars` |
| `lousa` | quadro-negro, giz branco e um giz amarelo | EXPLICA, COMO FUNCIONA | `corrige`: escreve o mito, risca, escreve o fato |
| `caderno` | papel creme pontilhado, nanquim e lápis vermelho | CURIOSIDADE, CONVERSA, ESTANTE | `draw`: o objeto se desenha traço a traço |
| `planta` | cianotipia azul, linha técnica branca, grade | COMO FUNCIONA (máquinas, redes, chips) | `draw` em ordem de desenho técnico |
| `aquarela` | papel de algodão, manchas translúcidas | HISTÓRIA, ESTANTE | `timeline` e `draw` com `class="wash"` |

Regras dos estilos desenhados (vêm dos STYLE.md de chalkboard, whiteboard, blueprint e watercolor do lemo-opuscar):
tudo o que aparece é **escrito ou traçado na tela**, nunca surge pronto; uma só cor de destaque, reservada ao que a
lição acompanha; o desenho é o mais simples que carrega a ideia (linhas, não ilustração detalhada); nenhum desenho,
personagem ou layout copiado de terceiros. Nunca dois reels seguidos no mesmo estilo.
Ainda proibido em qualquer estilo: imagem gerada por IA, render 3D, robô, cérebro brilhante.

## 4. Ferramentas (todas gratuitas)

| Função | Ferramenta | Observação |
|---|---|---|
| Render | GitHub Actions (repositório público) + Playwright + ffmpeg 7 | ~4 min por reel |
| Voz | edge-tts: `pt-BR-AntonioNeural` (masculina), `pt-BR-ThalitaMultilingualNeural` | Plano B offline: Kokoro (`pm_alex`, `pf_dora`) |
| Animação | contrato `window.render(t)` do lemo-opuscar (MIT) | cenas `hook`, `number`, `bars`, `timeline` |
| Som | `engine/reel_audio.py` + `toolbox/sfx.py` | trilha e efeitos gerados em código |
| Master | `toolbox/mux.sh` | −14 LUFS, duas passagens |
| Conferência | faster-whisper (pt) em `engine/asr_check_pt.py` | número não ouvido bloqueia a publicação |
| Foto | Unsplash (Action `fotos`) | já em uso |
| Vídeo de apoio | Pexels (Action `videos`) | falta o secret `PEXELS_API_KEY` |
| Acervo histórico | Library of Congress, Smithsonian Open Access, NASA, Wikimedia Commons (só CC0, domínio público, CC BY) | para HISTÓRIA |

## 5. Como medir (toda semana)

No Metricool ou nos Insights, por reel: envios ÷ alcance, tempo médio assistido, % de não seguidores.
Manter o que ficar acima da mediana do perfil; trocar gancho e duração do que ficar abaixo. Um teste por vez.
