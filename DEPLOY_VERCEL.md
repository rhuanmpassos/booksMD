# 🚀 Guia de Deploy na Vercel - BooksMD

## 📋 Índice
1. [Análise do Projeto](#análise-do-projeto)
2. [Limitações e Desafios](#limitações-e-desafios)
3. [Estratégias de Deploy](#estratégias-de-deploy)
4. [Configuração do Frontend](#configuração-do-frontend)
5. [Configuração do Backend](#configuração-do-backend)
   - [Opção AWS (Recomendado se você tem AWS)](#-opção-aws-backend-na-aws-recomendado-se-você-tem-aws)
   - [Estratégia 1: AWS App Runner](#estratégia-1-aws-app-runner-mais-simples---comece-aqui)
   - [Estratégia 2: EC2](#estratégia-2-ec2-recomendado-para-produção)
   - [Estratégia 3: ECS Fargate](#estratégia-3-ecs-fargate-para-escalar)
   - [Outras Opções](#opção-a-backend-em-railway-alternativa-se-não-usar-aws)
6. [Deploy Passo a Passo](#deploy-passo-a-passo)
7. [Alternativas Recomendadas](#alternativas-recomendadas)

---

## 📊 Análise do Projeto

### Estrutura Atual

```
booksmd/
├── backend/          # FastAPI (Python)
│   ├── app/
│   │   ├── api/      # Rotas REST
│   │   ├── analyzer/ # Análise com LLM
│   │   ├── extractors/ # Extração de PDF/EPUB/TXT
│   │   ├── generator/ # Geração MD/PDF
│   │   └── storage/  # Armazenamento local (JSON)
│   ├── main.py       # Servidor FastAPI
│   └── requirements.txt
│
└── frontend/         # Angular 18
    ├── src/
    │   ├── app/
    │   │   ├── pages/
    │   │   └── services/ # ApiService
    │   └── environments/
    └── package.json
```

### Características do Backend

- **Framework**: FastAPI (Python)
- **Processamento**: Análise longa de livros (pode levar minutos)
- **Armazenamento**: Sistema de arquivos local (`uploads/`, `outputs/`, `data/jobs.json`)
- **Dependências Pesadas**: 
  - PyMuPDF (PDF)
  - WeasyPrint (PDF generation)
  - Múltiplos providers de LLM (OpenAI, Ollama, Hugging Face, Bedrock, Gradio)
- **Uploads**: Até 10GB de arquivos
- **CORS**: Configurável via variáveis de ambiente

### Características do Frontend

- **Framework**: Angular 18 (Standalone Components)
- **Build**: `ng build` → `dist/booksmd/`
- **API URL**: Configurada via `environment.ts`
  - Desenvolvimento: `http://localhost:8000`
  - Produção: `''` (same origin)

---

## ⚠️ Limitações e Desafios

### Limitações da Vercel para Backend Python

1. **Timeout de Funções Serverless**
   - **Hobby (Free)**: 10 segundos máximo
   - **Pro**: 60 segundos máximo
   - **Problema**: Análise de livros pode levar vários minutos

2. **Limite de Upload**
   - **Hobby**: 50MB por requisição
   - **Pro**: 4.5GB por requisição
   - **Problema**: Livros podem ser grandes

3. **Armazenamento Persistente**
   - Vercel não oferece armazenamento de arquivos persistente
   - Arquivos são perdidos entre execuções
   - **Problema**: Precisa de `uploads/`, `outputs/`, `data/jobs.json`

4. **Dependências Pesadas**
   - WeasyPrint requer bibliotecas do sistema (GTK, Cairo, etc.)
   - PyMuPDF pode ter problemas em ambiente serverless
   - **Problema**: Build pode falhar ou ser muito lento

5. **Processamento Longo**
   - Serverless não é adequado para tarefas longas
   - **Problema**: Análise de livros é uma tarefa longa

### O que Funciona Bem na Vercel

✅ **Frontend Angular** - Perfeito para Vercel
- Build estático otimizado
- CDN global
- Deploy rápido

---

## 🎯 Estratégias de Deploy

### Opção 1: Frontend na Vercel + Backend Separado (RECOMENDADO)

**Arquitetura:**
```
Frontend (Vercel) → Backend (Railway/Render/Fly.io/AWS)
```

**Vantagens:**
- ✅ Frontend otimizado na Vercel
- ✅ Backend com processamento longo
- ✅ Armazenamento persistente
- ✅ Sem limitações de timeout

**Desvantagens:**
- ⚠️ Precisa configurar CORS no backend
- ⚠️ Dois serviços para gerenciar

### Opção 2: Tudo na Vercel (NÃO RECOMENDADO)

**Arquitetura:**
```
Frontend (Vercel) → API Routes (Vercel Serverless)
```

**Problemas:**
- ❌ Timeout de 10-60s insuficiente
- ❌ Sem armazenamento persistente
- ❌ Dependências pesadas problemáticas
- ❌ Uploads grandes limitados

### Opção 3: Backend como Serverless Functions (PARCIAL)

**Arquitetura:**
```
Frontend (Vercel) → API Routes (Vercel) → External Storage (S3/Cloudflare R2)
```

**Funciona para:**
- ✅ Endpoints simples (status, download)
- ✅ Proxy para backend externo

**Não funciona para:**
- ❌ Processamento longo (análise)
- ❌ Upload direto de arquivos grandes

---

## ⚙️ Configuração do Frontend

### 1. Arquivo `vercel.json` na Raiz

Crie um arquivo `vercel.json` na raiz do projeto:

```json
{
  "buildCommand": "cd frontend && npm install && npm run build",
  "outputDirectory": "frontend/dist/booksmd",
  "framework": "angular",
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ],
  "headers": [
    {
      "source": "/assets/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    }
  ]
}
```

### 2. Atualizar `environment.prod.ts`

O arquivo já está configurado para usar same origin:

```typescript
export const environment = {
  production: true,
  apiUrl: '' // Same origin in production
};
```

**IMPORTANTE**: Se o backend estiver em outro domínio, você precisa atualizar a URL.

#### Opção A: Usar o script automatizado (Recomendado)

```bash
cd frontend
npm run set-api-url https://seu-backend.railway.app
```

Ou diretamente:

```bash
cd frontend
node replace-api-url.js https://seu-backend.railway.app
```

#### Opção B: Editar manualmente

Edite `frontend/src/environments/environment.prod.ts`:

```typescript
export const environment = {
  production: true,
  apiUrl: 'https://seu-backend.railway.app' // URL do backend
};
```

### 3. Configurar Variáveis de Ambiente na Vercel

No painel da Vercel, adicione:

```
NODE_ENV=production
```

Se usar backend externo:
```
VITE_API_URL=https://seu-backend.railway.app
```

---

## ⚙️ Configuração do Backend

### 🏆 Opção AWS: Backend na AWS (RECOMENDADO se você tem AWS)

Como você já tem AWS e AWS CLI, esta é a melhor opção! Vou detalhar as 3 melhores estratégias:

#### Estratégia 1: AWS App Runner (MAIS SIMPLES - Comece aqui!)

**Por que escolher:**
- ✅ Mais fácil de configurar
- ✅ Deploy automático via GitHub
- ✅ Escala automaticamente
- ✅ HTTPS automático
- ✅ Custo baixo (~$5-20/mês)

**Passo a Passo:**

1. **Criar Dockerfile no `backend/`:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema para WeasyPrint
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código
COPY . .

# Expõe porta (App Runner usa PORT automático)
EXPOSE 8000

# Comando de start
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. **Criar `apprunner.yaml` na raiz do projeto (opcional):**

```yaml
version: 1.0
runtime: docker
build:
  commands:
    build:
      - echo "Building BooksMD Backend"
run:
  runtime-version: latest
  command: uvicorn main:app --host 0.0.0.0 --port 8000
  network:
    port: 8000
    env: PORT
  env:
    - name: LLM_PROVIDER
      value: "gradio"
    - name: CORS_ORIGINS
      value: "https://seu-frontend.vercel.app"
```

3. **Deploy via Console AWS:**

   a. Acesse [AWS App Runner Console](https://console.aws.amazon.com/apprunner)
   
   b. Clique em "Create service"
   
   c. Escolha "Source code repository" → Conecte GitHub
   
   d. Selecione seu repositório e branch
   
   e. Configure:
      - **Build settings**: 
        - Build command: `cd backend && docker build -t booksmd-backend .`
        - Start command: (deixar vazio, usa Dockerfile)
      - **Service settings**:
        - Service name: `booksmd-backend`
        - Port: `8000`
        - Environment variables:
          ```
          LLM_PROVIDER=gradio
          GRADIO_SPACE_ID=burak/Llama-4-Maverick-17B-Websearch
          CORS_ORIGINS=https://seu-frontend.vercel.app
          HOST=0.0.0.0
          PORT=8000
          DEBUG=False
          ```
   
   f. Clique em "Create & deploy"
   
   g. Aguarde ~5-10 minutos para build e deploy
   
   h. Anote a URL gerada (ex: `https://xxxxx.us-east-1.awsapprunner.com`)

4. **Configurar S3 para Storage (IMPORTANTE):**

Como App Runner não tem storage persistente, você precisa usar S3:

```bash
# Criar bucket S3
aws s3 mb s3://booksmd-uploads --region us-east-1
aws s3 mb s3://booksmd-outputs --region us-east-1

# Configurar CORS no bucket
aws s3api put-bucket-cors --bucket booksmd-uploads --cors-configuration file://cors.json
```

Crie `cors.json`:
```json
{
  "CORSRules": [
    {
      "AllowedOrigins": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
      "AllowedHeaders": ["*"],
      "MaxAgeSeconds": 3000
    }
  ]
}
```

5. **Atualizar código para usar S3 (opcional, mas recomendado):**

Você precisaria modificar o código para salvar arquivos no S3 ao invés do sistema de arquivos local. Isso é mais complexo, então para começar, você pode usar a Estratégia 2 (EC2) que tem storage persistente.

**Custo:** ~$5-20/mês

---

#### Estratégia 2: EC2 (RECOMENDADO para produção)

**Por que escolher:**
- ✅ Storage persistente (EBS)
- ✅ Sem limite de tempo
- ✅ Controle total
- ✅ Pode usar Spot Instances (mais barato)
- ✅ Melhor para processamento longo

**Passo a Passo:**

1. **Criar instância EC2:**

```bash
# Via AWS CLI
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.medium \
  --key-name sua-chave \
  --security-group-ids sg-xxxxx \
  --subnet-id subnet-xxxxx \
  --user-data file://user-data.sh \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=booksmd-backend}]'
```

2. **Criar `user-data.sh` (script de inicialização):**

```bash
#!/bin/bash
yum update -y
yum install -y python3.11 python3-pip git

# Instala dependências do sistema para WeasyPrint
yum install -y \
  cairo-devel \
  pango-devel \
  libffi-devel \
  shared-mime-info

# Clona repositório (ou usa CodeDeploy)
cd /opt
git clone https://github.com/seu-usuario/booksmd.git
cd booksmd/backend

# Cria ambiente virtual
python3.11 -m venv venv
source venv/bin/activate

# Instala dependências
pip install -r requirements.txt

# Cria diretórios
mkdir -p uploads outputs data

# Cria arquivo .env
cat > .env << EOF
LLM_PROVIDER=gradio
GRADIO_SPACE_ID=burak/Llama-4-Maverick-17B-Websearch
CORS_ORIGINS=https://seu-frontend.vercel.app
HOST=0.0.0.0
PORT=8000
DEBUG=False
UPLOAD_DIR=/opt/booksmd/backend/uploads
OUTPUT_DIR=/opt/booksmd/backend/outputs
EOF

# Cria service systemd
cat > /etc/systemd/system/booksmd.service << EOF
[Unit]
Description=BooksMD Backend
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/opt/booksmd/backend
Environment="PATH=/opt/booksmd/backend/venv/bin"
ExecStart=/opt/booksmd/backend/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Inicia serviço
systemctl daemon-reload
systemctl enable booksmd
systemctl start booksmd
```

3. **Configurar Security Group:**

```bash
# Permite HTTP/HTTPS
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp \
  --port 8000 \
  --cidr 0.0.0.0/0
```

4. **Configurar Application Load Balancer (para HTTPS):**

```bash
# Criar ALB
aws elbv2 create-load-balancer \
  --name booksmd-alb \
  --subnets subnet-xxxxx subnet-yyyyy \
  --security-groups sg-xxxxx

# Criar target group
aws elbv2 create-target-group \
  --name booksmd-targets \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-xxxxx

# Registrar instância
aws elbv2 register-targets \
  --target-group-arn arn:aws:elasticloadbalancing:... \
  --targets Id=i-xxxxx

# Criar listener HTTPS (com certificado ACM)
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:... \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=arn:aws:acm:... \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:...
```

5. **Anexar EBS Volume para Storage Persistente:**

```bash
# Criar volume EBS (100GB)
aws ec2 create-volume \
  --size 100 \
  --volume-type gp3 \
  --availability-zone us-east-1a

# Anexar à instância
aws ec2 attach-volume \
  --volume-id vol-xxxxx \
  --instance-id i-xxxxx \
  --device /dev/sdf

# Na instância, formatar e montar:
# sudo mkfs -t ext4 /dev/xvdf
# sudo mkdir /data
# sudo mount /dev/xvdf /data
# echo '/dev/xvdf /data ext4 defaults,nofail 0 2' | sudo tee -a /etc/fstab
```

**Custo:** ~$30-100/mês (dependendo da instância)

---

#### Estratégia 3: ECS Fargate (Para escalar)

**Por que escolher:**
- ✅ Escala automaticamente
- ✅ Containers isolados
- ✅ Integração com outros serviços AWS

**Passo a Passo:**

1. **Criar Dockerfile** (mesmo da Estratégia 1)

2. **Criar `Dockerfile` e fazer push para ECR:**

```bash
# Login no ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Criar repositório
aws ecr create-repository --repository-name booksmd-backend

# Build e push
cd backend
docker build -t booksmd-backend .
docker tag booksmd-backend:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/booksmd-backend:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/booksmd-backend:latest
```

3. **Criar task definition:**

```json
{
  "family": "booksmd-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "booksmd-backend",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/booksmd-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "LLM_PROVIDER", "value": "gradio"},
        {"name": "CORS_ORIGINS", "value": "https://seu-frontend.vercel.app"},
        {"name": "HOST", "value": "0.0.0.0"},
        {"name": "PORT", "value": "8000"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/booksmd-backend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

4. **Criar cluster e serviço via Console AWS ou CLI**

**Custo:** ~$50-200/mês

---

### 🎯 Recomendação Final para AWS

**Para começar rápido:** Use **App Runner** (Estratégia 1)
- Mais simples
- Deploy em ~10 minutos
- Custo baixo

**Para produção:** Use **EC2** (Estratégia 2)
- Storage persistente
- Controle total
- Melhor custo-benefício

**Para escalar:** Use **ECS Fargate** (Estratégia 3)
- Escala automática
- Melhor para alto volume

---

### Opção A: Backend em Railway (Alternativa se não usar AWS)

#### 1. Criar `railway.json` (opcional)

```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "cd backend && python main.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

#### 2. Criar `Procfile` no diretório `backend/`

```
web: cd backend && python main.py
```

Ou:

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

#### 3. Variáveis de Ambiente no Railway

Configure no painel do Railway:

```env
LLM_PROVIDER=gradio
GRADIO_SPACE_ID=burak/Llama-4-Maverick-17B-Websearch
GRADIO_USE_WEB_SEARCH=False

# Ou se usar OpenAI:
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-4o

HOST=0.0.0.0
PORT=$PORT
DEBUG=False

CORS_ORIGINS=https://seu-frontend.vercel.app,https://seu-frontend.vercel.app/*
```

#### 4. Armazenamento Persistente

Railway oferece volume persistente. Configure:

```env
UPLOAD_DIR=/data/uploads
OUTPUT_DIR=/data/outputs
```

E monte um volume em `/data` no Railway.

### Opção B: Backend em Render

#### 1. Criar `render.yaml` na raiz

```yaml
services:
  - type: web
    name: booksmd-backend
    env: python
    buildCommand: cd backend && pip install -r requirements.txt
    startCommand: cd backend && python main.py
    envVars:
      - key: LLM_PROVIDER
        value: gradio
      - key: CORS_ORIGINS
        value: https://seu-frontend.vercel.app
      - key: HOST
        value: 0.0.0.0
      - key: PORT
        value: 10000
```

### Opção C: Backend em Fly.io

#### 1. Criar `fly.toml` no diretório `backend/`

```toml
app = "booksmd-backend"
primary_region = "gru"

[build]

[env]
  LLM_PROVIDER = "gradio"
  HOST = "0.0.0.0"
  PORT = "8080"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = false
  auto_start_machines = true
  min_machines_running = 1

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 2048
```

#### 2. Criar `Dockerfile` no diretório `backend/`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema para WeasyPrint
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

---

## 📝 Deploy Passo a Passo

### Passo 1: Preparar o Repositório

```bash
# Certifique-se de que tudo está commitado
git add .
git commit -m "Preparar para deploy na Vercel"
git push origin main
```

### Passo 2: Deploy do Frontend na Vercel

1. Acesse [vercel.com](https://vercel.com)
2. Faça login com GitHub
3. Clique em "Add New Project"
4. Importe o repositório `booksmd`
5. Configure:
   - **Framework Preset**: Angular
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist/booksmd`
6. Adicione variáveis de ambiente (se necessário)
7. Clique em "Deploy"

### Passo 3: Deploy do Backend (Railway - Exemplo)

1. Acesse [railway.app](https://railway.app)
2. Faça login com GitHub
3. Clique em "New Project"
4. Selecione "Deploy from GitHub repo"
5. Escolha o repositório `booksmd`
6. Configure:
   - **Root Directory**: `backend`
   - **Start Command**: `python main.py`
7. Adicione variáveis de ambiente
8. Configure volume persistente para `/data`
9. Anote a URL gerada (ex: `https://booksmd-backend.railway.app`)

### Passo 4: Atualizar Frontend com URL do Backend

1. Anote a URL do backend (ex: `https://booksmd-backend.railway.app`)
2. Atualize o `environment.prod.ts` usando o script:

```bash
cd frontend
npm run set-api-url https://seu-backend.railway.app
```

Ou edite manualmente `frontend/src/environments/environment.prod.ts`:

```typescript
export const environment = {
  production: true,
  apiUrl: 'https://seu-backend.railway.app'
};
```

3. Commit e push das alterações:

```bash
git add frontend/src/environments/environment.prod.ts
git commit -m "Configurar URL do backend para produção"
git push origin main
```

4. O Vercel fará redeploy automaticamente

### Passo 5: Configurar CORS no Backend

No Railway (ou outro serviço), adicione:

```env
CORS_ORIGINS=https://seu-frontend.vercel.app,https://seu-frontend.vercel.app/*
```

### Passo 6: Testar

1. Acesse o frontend: `https://seu-frontend.vercel.app`
2. Tente fazer upload de um livro
3. Verifique se o backend responde
4. Verifique logs no Railway/Vercel

---

## 🔄 Alternativas Recomendadas

### Se Vercel Não For Adequado

#### Opção 1: Render (Full Stack)

- ✅ Suporta Python e Node.js
- ✅ Armazenamento persistente
- ✅ Sem timeout rígido
- ✅ Free tier disponível

**Deploy:**
1. Crie `render.yaml` na raiz
2. Configure frontend e backend como serviços separados
3. Deploy automático via GitHub

#### Opção 2: Fly.io (Full Stack)

- ✅ Suporta Docker
- ✅ Máquinas persistentes
- ✅ Sem timeout
- ✅ Bom para processamento longo

**Deploy:**
1. Crie `Dockerfile` para backend
2. Crie `fly.toml` para cada serviço
3. Deploy via CLI: `fly deploy`

#### Opção 3: Railway (Full Stack)

- ✅ Simples de configurar
- ✅ Volumes persistentes
- ✅ Deploy automático
- ✅ Free tier limitado

**Deploy:**
1. Conecte repositório GitHub
2. Configure variáveis de ambiente
3. Deploy automático

#### Opção 4: AWS (RECOMENDADO se você já tem AWS)

Como você já tem AWS e AWS CLI, esta é uma excelente opção! Aqui estão as melhores estratégias:

##### 🥇 Opção A: AWS App Runner (MAIS SIMPLES - Recomendado para começar)

**Vantagens:**
- ✅ Muito simples de configurar
- ✅ Deploy automático via GitHub
- ✅ Escala automaticamente
- ✅ Timeout de até 15 minutos (suficiente para a maioria dos casos)
- ✅ Custo baixo (paga apenas pelo uso)
- ✅ HTTPS automático

**Limitações:**
- ⚠️ Storage temporário (arquivos são perdidos ao reiniciar)
- ⚠️ Solução: Usar S3 para uploads e outputs

**Deploy:**
1. Crie um `Dockerfile` no diretório `backend/`
2. Configure App Runner no console AWS
3. Conecte com GitHub
4. Configure variáveis de ambiente
5. Use S3 para armazenar arquivos

**Custo estimado:** ~$5-20/mês (dependendo do uso)

##### 🥈 Opção B: EC2 (MAIS CONTROLE - Recomendado para produção)

**Vantagens:**
- ✅ Controle total sobre a máquina
- ✅ Storage persistente (EBS volumes)
- ✅ Sem limite de tempo de processamento
- ✅ Pode usar Spot Instances para economizar
- ✅ Pode instalar dependências do sistema (WeasyPrint)

**Desvantagens:**
- ⚠️ Precisa gerenciar servidor (atualizações, segurança)
- ⚠️ Mais complexo de configurar

**Deploy:**
1. Crie instância EC2 (t3.medium ou maior)
2. Configure security groups
3. Instale Python, dependências
4. Configure systemd para auto-start
5. Use Application Load Balancer para HTTPS

**Custo estimado:** ~$30-100/mês (dependendo da instância)

##### 🥉 Opção C: ECS/Fargate (ESCALÁVEL - Para alto volume)

**Vantagens:**
- ✅ Escala automaticamente
- ✅ Containers isolados
- ✅ Integração com outros serviços AWS
- ✅ Pode usar EFS para storage compartilhado

**Desvantagens:**
- ⚠️ Mais complexo de configurar
- ⚠️ Pode ser mais caro

**Custo estimado:** ~$50-200/mês

##### 🏆 Opção D: Híbrida (RECOMENDADA para produção)

**Arquitetura:**
```
Frontend (Vercel)
    ↓
Backend API (App Runner ou EC2)
    ↓
S3 (Uploads e Outputs)
    ↓
DynamoDB ou RDS (Jobs metadata)
```

**Vantagens:**
- ✅ Melhor custo-benefício
- ✅ Escalável
- ✅ Storage persistente (S3)
- ✅ Frontend otimizado na Vercel

**Custo estimado:** ~$10-50/mês

---

## 📋 Checklist de Deploy

### Frontend (Vercel)
- [ ] Criar `vercel.json` na raiz
- [ ] Configurar `environment.prod.ts` com URL do backend
- [ ] Testar build local: `cd frontend && npm run build`
- [ ] Verificar que `dist/booksmd` contém os arquivos
- [ ] Configurar variáveis de ambiente na Vercel
- [ ] Deploy e testar acesso

### Backend (Railway/Render/Fly.io)
- [ ] Criar `Procfile` ou `Dockerfile`
- [ ] Configurar variáveis de ambiente
- [ ] Configurar CORS com URL do frontend
- [ ] Configurar volume persistente (se necessário)
- [ ] Testar endpoint `/health`
- [ ] Verificar logs de erro

### Integração
- [ ] Frontend consegue acessar backend (CORS OK)
- [ ] Upload de arquivo funciona
- [ ] Status de job é atualizado
- [ ] Download de MD/PDF funciona
- [ ] Erros são tratados corretamente

---

## 🐛 Troubleshooting

### Erro: CORS bloqueado

**Solução:**
- Verifique `CORS_ORIGINS` no backend
- Inclua a URL exata do frontend (com `https://`)
- Reinicie o backend após mudar CORS

### Erro: Timeout na Vercel

**Solução:**
- Backend não pode estar na Vercel
- Use Railway/Render/Fly.io para backend
- Frontend na Vercel, backend externo

### Erro: Arquivos não persistem

**Solução:**
- Configure volume persistente no Railway
- Ou use S3/Cloudflare R2 para storage
- Atualize código para usar storage externo

### Erro: Build do frontend falha

**Solução:**
- Verifique Node.js version (18+)
- Limpe cache: `rm -rf node_modules package-lock.json`
- Reinstale: `npm install`
- Verifique `angular.json` e `package.json`

### Erro: Backend não inicia

**Solução:**
- Verifique variáveis de ambiente
- Verifique `requirements.txt`
- Verifique logs no serviço de deploy
- Teste localmente primeiro

---

## 📚 Recursos Adicionais

- [Documentação Vercel](https://vercel.com/docs)
- [Documentação Railway](https://docs.railway.app)
- [Documentação Render](https://render.com/docs)
- [Documentação Fly.io](https://fly.io/docs)
- [Angular Deployment](https://angular.io/guide/deployment)

---

## 💡 Conclusão

**Recomendação Final:**

### 🏆 Se você tem AWS (RECOMENDADO):

1. **Frontend**: Deploy na Vercel (otimizado, rápido, CDN global)
2. **Backend**: Deploy na AWS
   - **Para começar rápido**: AWS App Runner (~$5-20/mês)
   - **Para produção**: EC2 com EBS (~$30-100/mês)
   - **Para escalar**: ECS Fargate (~$50-200/mês)
3. **Storage**: EBS volumes (EC2) ou S3 (App Runner/ECS)
4. **Configuração**: CORS adequado, variáveis de ambiente configuradas
5. **Monitoramento**: CloudWatch Logs

**Vantagens da AWS:**
- ✅ Você já tem acesso
- ✅ Controle total sobre recursos
- ✅ Escalável e confiável
- ✅ Integração com outros serviços AWS
- ✅ Custo competitivo

### Alternativa (se não usar AWS):

1. **Frontend**: Deploy na Vercel
2. **Backend**: Deploy em Railway ou Render
3. **Configuração**: CORS adequado, variáveis de ambiente configuradas

Esta arquitetura oferece o melhor dos dois mundos: frontend rápido na Vercel e backend robusto em um serviço adequado para processamento longo.

---

**Última atualização**: 2024
**Versão do projeto**: 1.0.0

