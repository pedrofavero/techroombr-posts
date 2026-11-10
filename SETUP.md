# Setup do pipeline — The Tech Room

Guia dos passos que só o dono das contas consegue fazer. Depois disso, tudo roda sozinho.

## 1. Destravar o GitHub Actions

A Action `fotos` falha desde 05/11/2026 (o job morre em ~2 s, sem runner). Em repositório
público os minutos são gratuitos e ilimitados, então a causa provável é cobrança pendente
na conta dona do repositório.

1. github.com → foto do perfil → **Settings → Billing and plans**. Regularize qualquer
   aviso de pagamento recusado (Copilot, Codespaces, armazenamento de pacotes).
2. No repositório → **Settings → Actions → General** → "Allow all actions" e, em
   *Workflow permissions*, **Read and write permissions**.
3. Teste: **Actions → fotos → Run workflow**. Se passar de 10 segundos, destravou.

## 2. App da Meta (Instagram API with Instagram Login)

Esta é a API que publica carrossel e reel de graça, sem limite mensal e sem Página do
Facebook. O limite da Meta é 100 publicações por 24 h.

### 2.0 Antes de começar

A conta @techroombr precisa estar **Profissional** e **pública**. No app do Instagram:
**Configurações e privacidade → Tipo de conta e ferramentas → Mudar para conta
profissional** (escolha Criador). E em **Privacidade da conta**, deixe desmarcado
"Conta privada". Conta privada é recusada até para teste.

### 2.1 Criar o app (a ordem das telas importa)

O produto Instagram só aparece em app do tipo **Empresa**, e só se chega nesse tipo
passando pelo caso de uso **Outro**. Não existe caso de uso chamado "Instagram".

1. Abra **developers.facebook.com/apps** e faça login com o Facebook do Pedro.
   Se for a primeira vez, o site pede para registrar a conta de desenvolvedor:
   aceite os termos e confirme o e-mail ou telefone.
2. Botão **Criar app** (canto superior direito).
3. Tela **Detalhes do app**: preencha **Nome do app** (ex.: "Tech Room Publisher") e
   **E-mail de contato do app** → **Avançar**.
4. Tela **Caso de uso** ("O que você quer que seu app faça?"): marque **Outro**
   (*Other*) → **Avançar**. Ignore as opções de mensagens, login e anúncios.
5. Tela **Tipo de app**: marque **Empresa** (*Business*) → **Avançar**.
   **Este é o passo que libera o Instagram.** Se você marcar "Consumidor" ou
   "Nenhum", o card do Instagram nunca vai aparecer.
6. Tela **Portfólio comercial** (se aparecer): pode escolher **Não conectar** agora.
   Só é exigido para publicar o app, e não vamos publicar.
7. **Criar app** → confirme a senha do Facebook se for pedida.

Conferência: você cai no painel do app, com o nome dele no topo e um menu à esquerda
com "Painel", "Configurações do app", "Funções do app", "Análise do app".

### 2.2 Adicionar o produto Instagram

8. No **Painel** do app, role a página para baixo até a lista de produtos
   ("Adicione produtos ao seu app"). Procure o card **Instagram** → **Configurar**
   (*Set up*).
9. O menu da esquerda ganha um item **Instagram**. Clique nele e depois em
   **Configuração da API com login do Instagram**
   (*API setup with Instagram login*).

Se não houver card Instagram na lista de produtos, o app foi criado com o tipo errado.
Não dá para converter: volte ao passo 2 e crie outro app (é gratuito; o limite é 15 apps).

### 2.3 Gerar o token

10. Na tela **Configuração da API com login do Instagram**, a primeira seção é
    **1. Gerar tokens de acesso** (*Generate access tokens*). Clique em
    **Adicionar conta** (*Add account*).
11. Abre um **pop-up do instagram.com** pedindo login. Entre com @techroombr e
    **Permitir**. Se nada abrir, o navegador bloqueou o pop-up: libere e clique de novo.
12. De volta ao painel, a conta aparece listada com o **ID da conta do Instagram**
    (número longo) e um botão **Gerar token**. Copie os dois:
    - ID → `IG_USER_ID`
    - token → `IG_ACCESS_TOKEN`

### 2.4 Pegar a chave secreta

13. Na mesma tela, role até **3. Configurar o login comercial do Instagram** →
    **Configurações de login comercial** (*Business login settings*).
    Ali aparecem **ID do app do Instagram** e **Chave secreta do app do Instagram**.
    Copie a chave secreta → `IG_APP_SECRET`. (Serve só para renovar o token sozinho.)

Permissões que o app já traz nesse caso de uso: `instagram_business_basic`,
`instagram_business_content_publish`, `instagram_business_manage_comments`. Se houver uma
lista de permissões com chaves para ligar, ligue também `instagram_business_manage_insights`
(é para o relatório semanal; sem ela o resto funciona).

Revisão do app (*App Review*) **não** é necessária para publicar na própria conta
adicionada no painel: isso é Acesso Padrão (*Standard Access*).

## 3. Pexels (b-roll dos reels, gratuito)

pexels.com/api → **Get started** → criar conta → copiar a chave → `PEXELS_API_KEY`.

## 4. Salvar os secrets no repositório

GitHub → repositório → **Settings → Secrets and variables → Actions → New repository secret**:

| Secret | De onde vem |
|---|---|
| `IG_USER_ID` | passo 2 |
| `IG_ACCESS_TOKEN` | passo 2 (renovado sozinho a cada 50 dias) |
| `IG_APP_SECRET` | passo 2 |
| `PEXELS_API_KEY` | passo 3 |

## 5. Conferir

Com os secrets salvos, rode no Actions o workflow **publicar → me** (ou localmente
`IG_USER_ID=... IG_ACCESS_TOKEN=... python3 engine/publish_ig.py me`). Deve imprimir o
usuário @techroombr e a contagem de seguidores.

## Problemas comuns no passo 2

**Abriu "Adicionar pessoas ao seu aplicativo" com Administrador / Desenvolvedor / Testador.**
Essa é a tela **Funções do app → Funções** (*App roles*), que serve para dar acesso a
pessoas ao painel. Não é ela que gera o token. O botão certo fica em
**Instagram → Configuração da API com login do Instagram → 1. Gerar tokens de acesso →
Adicionar conta**, e ele abre um **pop-up do instagram.com** pedindo login da conta.
Se nada abriu, o navegador bloqueou o pop-up.

**Só existe a opção "Testador do Instagram".** Significa que o app ficou no fluxo antigo
(login via Facebook). Nesse caso: adicione @techroombr como *Testador do Instagram*, depois
abra o app do Instagram com essa conta → **Configurações → Apps e sites → Convites de
testadores** → **Aceitar**. Só depois o painel deixa gerar o token.

**A conta não aparece para ser adicionada.** Ela precisa ser Profissional (Criador ou
Empresa) e **pública**. Conta privada é recusada mesmo para teste.
