# 🚀 Guia Rápido - Deploy na AWS

Este diretório contém scripts e configurações para deploy do backend na AWS.

## 📁 Arquivos

- `user-data.sh` - Script de inicialização automática para EC2
- `ec2-setup.sh` - Script para configurar EC2 manualmente
- `s3-cors.json` - Configuração CORS para buckets S3

## 🎯 Opções de Deploy

### Opção 1: AWS App Runner (Mais Simples)

1. Use o `Dockerfile` na raiz do `backend/`
2. Siga as instruções no `DEPLOY_VERCEL.md` seção "Estratégia 1: AWS App Runner"

### Opção 2: EC2 (Recomendado para Produção)

#### Via user-data (Automático)

1. Ao criar instância EC2, cole o conteúdo de `user-data.sh` no campo "User data"
2. A instância será configurada automaticamente ao iniciar

#### Via Script Manual

```bash
# Copie o script para a instância
scp aws/ec2-setup.sh ec2-user@seu-ip:/home/ec2-user/

# Conecte via SSH
ssh ec2-user@seu-ip

# Execute o script
chmod +x ec2-setup.sh
./ec2-setup.sh
```

### Opção 3: ECS Fargate

1. Use o `Dockerfile` na raiz do `backend/`
2. Siga as instruções no `DEPLOY_VERCEL.md` seção "Estratégia 3: ECS Fargate"

## 🔧 Configuração de S3 (Opcional)

Se quiser usar S3 para armazenar uploads e outputs:

```bash
# Criar buckets
aws s3 mb s3://booksmd-uploads --region us-east-1
aws s3 mb s3://booksmd-outputs --region us-east-1

# Configurar CORS
aws s3api put-bucket-cors \
  --bucket booksmd-uploads \
  --cors-configuration file://aws/s3-cors.json

aws s3api put-bucket-cors \
  --bucket booksmd-outputs \
  --cors-configuration file://aws/s3-cors.json
```

## 📝 Variáveis de Ambiente

Ajuste as variáveis no `.env` ou via AWS Systems Manager Parameter Store:

- `LLM_PROVIDER` - Provider de LLM (gradio, openai, ollama, etc.)
- `CORS_ORIGINS` - Origens permitidas (URL do frontend na Vercel)
- `HOST` - Host do servidor (0.0.0.0 para EC2)
- `PORT` - Porta do servidor (8000)

## 🔒 Security Groups

Configure o Security Group da EC2 para permitir:

- Porta 8000 (HTTP) - Para acesso direto ou ALB
- Porta 22 (SSH) - Para acesso remoto

## 📚 Mais Informações

Consulte `DEPLOY_VERCEL.md` para instruções detalhadas.

