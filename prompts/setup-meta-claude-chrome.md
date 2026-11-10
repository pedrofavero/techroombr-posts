# Prompt para o Claude no Chrome — terminar a configuração do app da Meta

Cole o bloco abaixo no Claude in Chrome, com o navegador logado no Facebook do dono do app.
Resultado esperado: os três valores `IG_USER_ID`, `IG_ACCESS_TOKEN` e `IG_APP_SECRET`.

---

Você está no meu navegador, com minhas sessões já logadas. Objetivo: terminar a configuração
de um app que EU JÁ CRIEI no Meta for Developers, para publicar no Instagram pela
"Instagram API with Instagram Login", e me entregar três valores no final.

Contexto: a conta é @techroombr, profissional e pública. Não quero revisão de app
(App Review) nem publicar o app — vou usar Acesso Padrão na minha própria conta.

Faça nesta ordem, me dizendo em uma linha o que você vê em cada etapa:

1. Abra https://developers.facebook.com/apps e liste os apps existentes com nome e ID.
   Se houver mais de um, me pergunte qual usar antes de continuar.
2. Entre no app e confira o tipo em "Configurações do app → Básico". Preciso que seja
   do tipo **Empresa** (Business). Se for outro tipo, PARE e me avise: não dá para
   converter, eu crio outro app do zero.
3. Vá ao "Painel" e role até a lista de produtos. Se o card **Instagram** ainda não
   estiver adicionado, clique em **Configurar** (Set up) nele.
4. No menu da esquerda, abra **Instagram → Configuração da API com login do Instagram**
   (API setup with Instagram login). Se o que existir for "Configuração da API com login
   do Facebook", PARE e me avise.
5. Na seção **1. Gerar tokens de acesso**, clique em **Adicionar conta**. Deve abrir um
   pop-up do instagram.com. Se o navegador bloquear, libere o pop-up e tente de novo.
   Se a tela pedir senha ou código de verificação, PARE e me chame para digitar.
   ATENÇÃO: não use "Funções do app" nem "Adicionar pessoas ao seu aplicativo" — essa
   tela é de permissões de painel e NÃO gera token.
6. Autorizada a conta, volte ao painel e copie o **ID da conta do Instagram** que
   aparece listado (número longo).
7. Clique em **Gerar token** e copie o token inteiro, sem abreviar.
8. Role até **3. Configurar o login comercial do Instagram** → **Configurações de login
   comercial** e copie a **Chave secreta do app do Instagram** (clique em "Mostrar" se
   estiver oculta).
9. Se houver uma lista de permissões nessa página, confirme que estão ativas:
   instagram_business_basic, instagram_business_content_publish,
   instagram_business_manage_comments e, se existir, instagram_business_manage_insights.
   Não peça acesso avançado para nenhuma delas.
10. Me entregue no chat, exatamente nesta ordem e sem cortar nenhum caractere:
    IG_USER_ID = ...
    IG_ACCESS_TOKEN = ...
    IG_APP_SECRET = ...

Regras durante toda a tarefa:
- Não clique em "Enviar para revisão", "Publicar app" ou "Solicitar acesso avançado".
- Não adicione pessoas ao app nem altere funções.
- Não publique, comente ou curta nada no Instagram.
- Não cole esses valores em nenhum site além do que eu pedir explicitamente.
- Se qualquer tela divergir do que descrevi, pare, descreva o que está vendo e pergunte.

---

## Parte opcional: salvar os secrets no GitHub

Só rode depois de ter os três valores em mãos.

Agora abra https://github.com/pedrofavero/techroombr-posts/settings/secrets/actions
e crie três repository secrets com **New repository secret**, usando exatamente estes
nomes e os valores que você acabou de obter:
IG_USER_ID, IG_ACCESS_TOKEN, IG_APP_SECRET.
Depois me confirme que os três aparecem na lista. Não exponha os valores em nenhum
outro site e não os escreva em issues, commits ou comentários.
