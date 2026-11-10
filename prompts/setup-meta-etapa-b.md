# Prompt 3 para o Claude no Chrome — Etapa B: login unificado (pode alterar)

Decisão: seguir pelo **API setup with Unified login** no app Tech Room Publisher
(ID 1636459114687717). Token SUAT, sem expiração. O passo 2 (aceitar o convite de
testador) precisa ser feito no celular pelo dono da conta; o Claude vai parar e avisar.

---

Continuando. Agora você PODE criar e salvar configuração no app Tech Room Publisher
(ID 1636459114687717), só dentro do que está descrito aqui. Me conte o que vê a cada passo.

1. **Funções do app → Funções**. Clique em "Adicionar pessoas". No modal, escolha a função
   **Testador do Instagram** e informe o nome de usuário `techroombr`. Confirme.
   Se a interface pedir uma conta do Facebook em vez de um nome de usuário do Instagram,
   procure uma aba/seção específica "Testadores do Instagram" nessa mesma página; é por
   nome de usuário do Instagram.
2. PARE e me avise: eu preciso aceitar o convite no app do Instagram
   (Configurações → Apps e sites → Convites de testadores → Aceitar). Só continue quando
   eu disser "aceitei".
3. Volte a **Instagram → API setup with Unified login**. Em "1. Configure seu app",
   clique em **Criar nova configuração**. Aceite os valores propostos (Variação: Geral;
   Token: SUAT; Expiração: Nunca; Ativo obrigatório: Conta do Instagram). Se a tela pedir
   para marcar permissões, deixe marcadas instagram_basic, instagram_content_publish e
   instagram_manage_comments; desmarque ads_management, ads_read e
   instagram_manage_messages se for possível desmarcar (se não for, deixe como está).
   Salve. Me diga o **ID da configuração** (config_id) se aparecer.
4. Em "URL de redirecionamento", clique em **Registrar um novo URL de redirecionamento**,
   cole exatamente `https://github.com/pedrofavero/techroombr-posts/` e **Salvar**.
5. Expanda "2. Gerar tokens de acesso" e clique em **Adicionar conta**. Vai abrir uma
   janela de login da Meta/Instagram: entre com @techroombr, escolha o portfólio
   **The Tech Room**, marque a conta do Instagram @techroombr quando pedir os ativos e
   autorize. Se pedir senha ou código, PARE e me chame.
6. De volta ao painel, copie o **ID da conta do Instagram** listado e clique em
   **Gerar token**; copie o token inteiro.
7. Vá em **Configurações do app → Básico** e copie o **ID do Aplicativo** e a
   **Chave Secreta** (clique em Mostrar).
8. Me entregue, sem cortar nenhum caractere:
   IG_USER_ID = ...
   IG_ACCESS_TOKEN = ...
   IG_APP_ID = ...
   IG_APP_SECRET = ...

Não faça: enviar para revisão, solicitar acesso avançado, ativar webhooks, publicar o app,
conectar conta de anúncios, nem postar nada no Instagram. Se uma tela divergir, pare e
descreva.
