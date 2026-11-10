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

Pré-requisito: @techroombr precisa ser conta **Profissional** (Criador ou Empresa) e
**pública**. No app do Instagram: Configurações → Tipo de conta e ferramentas.

### Criar o app (a ordem importa)

A opção de Instagram só aparece se o app for do tipo **Empresa**. O caminho é:

1. developers.facebook.com/apps → **Criar app** (*Create app*).
2. Tela de caso de uso / "o que seu app faz": escolha **Outro** (*Other*) → **Avançar**.
   Não existe um caso de uso chamado "Instagram" nessa lista.
3. Tela de tipo: escolha **Empresa** (*Business*) → **Avançar**. É este passo que libera
   o produto Instagram.
4. Nome do app ("Tech Room Publisher") e e-mail de contato → **Criar app**.
5. No painel do app, role até o card **Instagram** → **Configurar** (*Set up*).
   Isso adiciona sozinho a **Configuração da API com login do Instagram**
   (*API setup with Instagram login*) no menu da esquerda.

Se o app já criado não tiver o card Instagram, ele foi criado com outro tipo: crie um novo,
é gratuito e leva dois minutos.

### Pegar as credenciais

Menu da esquerda → **Instagram → Configuração da API com login do Instagram**:

- Seção **1. Gerar tokens de acesso** (*Generate access tokens*) → **Adicionar conta** →
  faça login com @techroombr e autorize. Depois disso aparecem o **ID da conta** e o botão
  de gerar token. Copie os dois → `IG_USER_ID` e `IG_ACCESS_TOKEN`.
- Seção **3. Configurar o login comercial do Instagram** → **Configurações de login
  comercial** (*Business login settings*): ali ficam o **ID do app do Instagram** e a
  **Chave secreta do app do Instagram** → `IG_APP_SECRET` (usada só para renovar o token).

Permissões necessárias (aparecem no caso de uso do app): `instagram_business_basic`,
`instagram_business_content_publish`, `instagram_business_manage_comments` e, para o
relatório semanal, `instagram_business_manage_insights`.

Revisão do app (App Review) **não** é necessária para publicar na própria conta adicionada
no painel: isso é Acesso Padrão (*Standard Access*).

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
