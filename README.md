# meu-portfolio-aws-tdc

Portfolio pessoal hospedado na AWS com deploy contínuo via GitHub + Amplify.

## Arquitetura

```
GitHub (push na branch main)
        │
        ▼
AWS Amplify Hosting         ← build e deploy automático
(S3 + CloudFront gerenciados)
        │
        ▼
Página estática (HTML/CSS/JS)
        │
   (formulário de contato)
        │
        ▼
API Gateway HTTP API        ← https://n17vr7t1jj.execute-api.us-east-2.amazonaws.com/contact
        │
        ▼
AWS Lambda (Python 3.12)    ← portfolio-contact-handler
        │
        ▼
Amazon SES (us-east-2)      ← envia e-mail para aristideslemos7245@gmail.com
```

## Estrutura do projeto

```
meu-portfolio-aws-tdc/
├── amplify.yml              # Configuração do pipeline de build do Amplify
├── README.md
├── frontend/
│   ├── index.html           # Página principal do portfolio
│   ├── style.css            # Estilos
│   └── main.js              # Lógica do formulário de contato
└── backend/
    ├── contact_handler.py   # Função Lambda (formulário de contato)
    └── requirements.txt     # Dependências Python (referência)
```

## Recursos AWS provisionados

| Recurso | Nome / ARN | Região |
|---|---|---|
| Lambda | `portfolio-contact-handler` | us-east-2 |
| IAM Role | `portfolio-contact-lambda-role` | global |
| API Gateway | `n17vr7t1jj` / `portfolio-contact-api` | us-east-2 |
| SES Identity | `aristideslemos7245@gmail.com` | us-east-2 |

## Pré-requisitos

Antes de conectar ao Amplify, verifique:

- [ ] O e-mail `aristideslemos7245@gmail.com` foi verificado no SES  
  (clique no link recebido pelo Gmail após a criação da identidade)
- [ ] O repositório foi criado no GitHub e o código foi enviado com `git push`

## Como conectar o GitHub ao Amplify (passo a passo)

### 1. Criar o repositório no GitHub

```bash
# Na pasta raiz do projeto
git init
git add .
git commit -m "feat: portfolio inicial com backend AWS"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/meu-portfolio-aws-tdc.git
git push -u origin main
```

### 2. Criar o app no AWS Amplify

1. Acesse o [console do AWS Amplify](https://us-east-2.console.aws.amazon.com/amplify/home?region=us-east-2)
2. Clique em **"Create new app"**
3. Selecione **"GitHub"** como fonte e clique em **"Next"**
4. Autorize o Amplify a acessar sua conta GitHub (se ainda não tiver feito)
5. Selecione o repositório **`meu-portfolio-aws-tdc`** e a branch **`main`**
6. Clique em **"Next"**

### 3. Configurar o build

O Amplify vai detectar automaticamente o arquivo `amplify.yml` na raiz do projeto.

Confirme que as configurações estão assim:
- **App name:** `meu-portfolio-aws-tdc`
- **Build spec:** detectado automaticamente do `amplify.yml`
- **Base directory:** `frontend`

Clique em **"Next"** e depois **"Save and deploy"**.

### 4. Aguardar o deploy

O Amplify vai:
1. Clonar o repositório
2. Executar o build (sem compilação para HTML puro)
3. Publicar o conteúdo da pasta `frontend/`
4. Fornecer uma URL no formato: `https://main.XXXXX.amplifyapp.com`

### 5. Atualizar o CORS da Lambda (recomendado)

Após o deploy, substitua o `ALLOWED_ORIGIN` na Lambda pela URL real do Amplify:

```bash
aws lambda update-function-configuration \
  --function-name portfolio-contact-handler \
  --environment "Variables={RECIPIENT_EMAIL=aristideslemos7245@gmail.com,SENDER_EMAIL=aristideslemos7245@gmail.com,AWS_SES_REGION=us-east-2,ALLOWED_ORIGIN=https://main.XXXXX.amplifyapp.com}" \
  --region us-east-2
```

Ou pelo console: Lambda → portfolio-contact-handler → Configuration → Environment variables.

## Deploy do backend (atualização da Lambda)

Se precisar atualizar o código da função Lambda:

```bash
cd backend

# Criar o ZIP
Compress-Archive -Path contact_handler.py -DestinationPath contact_handler.zip -Force

# Fazer o upload e atualizar a função
aws lambda update-function-code \
  --function-name portfolio-contact-handler \
  --zip-file fileb://contact_handler.zip \
  --region us-east-2
```

## Variáveis de ambiente da Lambda

| Variável | Valor | Descrição |
|---|---|---|
| `RECIPIENT_EMAIL` | `aristideslemos7245@gmail.com` | E-mail que recebe os contatos |
| `SENDER_EMAIL` | `aristideslemos7245@gmail.com` | E-mail remetente (deve estar verificado no SES) |
| `AWS_SES_REGION` | `us-east-2` | Região do SES |
| `ALLOWED_ORIGIN` | `*` | Atualizar com a URL do Amplify após o deploy |

## Observações

- **SES Sandbox:** O SES inicia em modo sandbox. Neste modo, só é possível enviar e-mails para endereços verificados. Para receber mensagens de qualquer visitante, solicite a saída do sandbox em: SES Console → Account dashboard → Request production access.
- **Domínio customizado:** O Amplify suporta domínios customizados com SSL gerenciado. Configure em: Amplify Console → App → Domain management.
- **Free tier:** Todos os serviços usados estão cobertos pelo free tier da AWS para o volume esperado de um portfolio pessoal.
