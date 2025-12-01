# 🚀 Guia de Deploy - BooksMD

## 📋 Índice
1. [Deploy do Frontend na Vercel](#deploy-do-frontend-na-vercel)
2. [Deploy do Backend no EC2 (via CLI)](#deploy-do-backend-no-ec2-via-cli)
3. [Configurar Integração](#configurar-integração)
4. [Checklist](#checklist)

---

## 🎨 Deploy do Frontend na Vercel

### 1. Arquivo `vercel.json` na Raiz

O arquivo `vercel.json` já está criado na raiz do projeto:

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

### 2. Deploy na Vercel

1. Acesse [vercel.com](https://vercel.com)
2. Faça login com GitHub
3. Clique em "Add New Project"
4. Importe o repositório `booksmd`
5. Configure:
   - **Framework Preset**: Angular
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist/booksmd`
6. Clique em "Deploy"

### 3. Anotar URL do Frontend

Após o deploy, anote a URL gerada (ex: `https://booksmd.vercel.app`)

---

## 🖥️ Deploy do Backend no EC2 (via CLI)

### Pré-requisitos

- AWS CLI configurado (`aws configure`)
- Key pair criado na AWS
- VPC e Subnet configurados

### 1. Obter AMI ID e Configurações

```bash
# Listar AMIs mais recentes do Amazon Linux 2023
aws ec2 describe-images \
  --owners amazon \
  --filters "Name=name,Values=al2023-ami-2023*" "Name=architecture,Values=x86_64" \
  --query 'Images | sort_by(@, &CreationDate) | [-1].[ImageId,Name]' \
  --output table

# Obter VPC ID
aws ec2 describe-vpcs --query 'Vpcs[0].VpcId' --output text

# Obter Subnet ID
aws ec2 describe-subnets --query 'Subnets[0].SubnetId' --output text

# Criar Security Group (se não existir)
aws ec2 create-security-group \
  --group-name booksmd-backend-sg \
  --description "Security group para BooksMD Backend" \
  --vpc-id vpc-xxxxx

# Anotar o Security Group ID retornado (sg-xxxxx)
```

### 2. Configurar Security Group

```bash
# Permitir SSH (porta 22)
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0

# Permitir HTTP (porta 8000)
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp \
  --port 8000 \
  --cidr 0.0.0.0/0
```

### 3. Criar Instância EC2

```bash
# Criar instância EC2 (ajuste os valores)
aws ec2 run-instances \
  --image-id ami-xxxxx \
  --instance-type t3.medium \
  --key-name sua-chave \
  --security-group-ids sg-xxxxx \
  --subnet-id subnet-xxxxx \
  --user-data file://aws/user-data.sh \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=booksmd-backend}]' \
  --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":30,"VolumeType":"gp3"}}]'

# Anotar Instance ID retornado (i-xxxxx)
```

### 4. Obter IP Público

```bash
# Obter IP público da instância
aws ec2 describe-instances \
  --instance-ids i-xxxxx \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text

# Ou obter DNS público
aws ec2 describe-instances \
  --instance-ids i-xxxxx \
  --query 'Reservations[0].Instances[0].PublicDnsName' \
  --output text
```

### 5. Conectar via SSH e Configurar Manualmente (se user-data não funcionar)

```bash
# Conectar via SSH
ssh -i sua-chave.pem ec2-user@IP_PUBLICO

# Na instância, executar:
cd /home/ec2-user
git clone https://github.com/seu-usuario/booksmd.git
cd booksmd/backend

# Ou usar o script de setup
chmod +x aws/ec2-setup.sh
./aws/ec2-setup.sh
```

### 6. Configurar Variáveis de Ambiente

Na instância EC2, edite o arquivo `.env`:

```bash
cd /opt/booksmd/backend  # ou /home/ec2-user/booksmd/backend
nano .env
```

Configure:

```env
LLM_PROVIDER=gradio
GRADIO_SPACE_ID=burak/Llama-4-Maverick-17B-Websearch
GRADIO_USE_WEB_SEARCH=False

# Ou se usar OpenAI:
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-4o

HOST=0.0.0.0
PORT=8000
DEBUG=False

# IMPORTANTE: Configure com a URL do frontend na Vercel
CORS_ORIGINS=https://seu-frontend.vercel.app,https://seu-frontend.vercel.app/*

UPLOAD_DIR=/opt/booksmd/backend/uploads
OUTPUT_DIR=/opt/booksmd/backend/outputs
```

### 7. Iniciar Serviço

```bash
# Se o serviço systemd foi criado pelo user-data
sudo systemctl start booksmd
sudo systemctl enable booksmd

# Verificar status
sudo systemctl status booksmd

# Ver logs
sudo journalctl -u booksmd -f
```

### 8. Criar EBS Volume para Storage Persistente (Opcional)

```bash
# Criar volume EBS (100GB)
aws ec2 create-volume \
  --size 100 \
  --volume-type gp3 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=volume,Tags=[{Key=Name,Value=booksmd-storage}]'

# Anotar Volume ID (vol-xxxxx)

# Obter Availability Zone da instância
aws ec2 describe-instances \
  --instance-ids i-xxxxx \
  --query 'Reservations[0].Instances[0].Placement.AvailabilityZone' \
  --output text

# Anexar volume à instância
aws ec2 attach-volume \
  --volume-id vol-xxxxx \
  --instance-id i-xxxxx \
  --device /dev/sdf

# Na instância, formatar e montar:
ssh -i sua-chave.pem ec2-user@IP_PUBLICO

sudo mkfs -t ext4 /dev/xvdf
sudo mkdir /data
sudo mount /dev/xvdf /data
echo '/dev/xvdf /data ext4 defaults,nofail 0 2' | sudo tee -a /etc/fstab

# Atualizar .env para usar /data
UPLOAD_DIR=/data/uploads
OUTPUT_DIR=/data/outputs
```

### 9. Configurar Application Load Balancer (Opcional - para HTTPS)

```bash
# Criar Target Group
aws elbv2 create-target-group \
  --name booksmd-targets \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-xxxxx \
  --health-check-path /health

# Anotar Target Group ARN

# Registrar instância no Target Group
aws elbv2 register-targets \
  --target-group-arn arn:aws:elasticloadbalancing:REGION:ACCOUNT:targetgroup/booksmd-targets/ID \
  --targets Id=i-xxxxx

# Criar Application Load Balancer
aws elbv2 create-load-balancer \
  --name booksmd-alb \
  --subnets subnet-xxxxx subnet-yyyyy \
  --security-groups sg-xxxxx

# Anotar Load Balancer ARN

# Criar listener HTTP (redireciona para HTTPS depois)
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:REGION:ACCOUNT:loadbalancer/app/booksmd-alb/ID \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:REGION:ACCOUNT:targetgroup/booksmd-targets/ID

# Para HTTPS, primeiro crie certificado no ACM, depois:
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:REGION:ACCOUNT:loadbalancer/app/booksmd-alb/ID \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=arn:aws:acm:REGION:ACCOUNT:certificate/CERT_ID \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:REGION:ACCOUNT:targetgroup/booksmd-targets/ID
```

---

## 🔗 Configurar Integração

### 1. Atualizar Frontend com URL do Backend

Após o backend estar rodando, atualize o `environment.prod.ts`:

```bash
cd frontend
npm run set-api-url http://IP_PUBLICO_EC2:8000
```

Ou edite manualmente `frontend/src/environments/environment.prod.ts`:

```typescript
export const environment = {
  production: true,
  apiUrl: 'http://IP_PUBLICO_EC2:8000' // Ou URL do ALB se configurou
};
```

### 2. Commit e Push

```bash
git add frontend/src/environments/environment.prod.ts
git commit -m "Configurar URL do backend para produção"
git push origin main
```

O Vercel fará redeploy automaticamente.

### 3. Testar Integração

1. Acesse o frontend: `https://seu-frontend.vercel.app`
2. Tente fazer upload de um livro
3. Verifique se o backend responde
4. Verifique logs no EC2: `sudo journalctl -u booksmd -f`

---

## 📋 Checklist

### Frontend (Vercel)
- [ ] `vercel.json` configurado na raiz
- [ ] Repositório conectado na Vercel
- [ ] Build configurado corretamente
- [ ] Deploy realizado com sucesso
- [ ] URL do frontend anotada

### Backend (EC2)
- [ ] Security Group criado e configurado
- [ ] Instância EC2 criada
- [ ] IP público anotado
- [ ] Conectado via SSH
- [ ] Código clonado/configurado
- [ ] Dependências instaladas
- [ ] Arquivo `.env` configurado
- [ ] CORS configurado com URL do frontend
- [ ] Serviço systemd iniciado
- [ ] Backend respondendo em `/health`
- [ ] EBS volume anexado (opcional)
- [ ] ALB configurado (opcional)

### Integração
- [ ] `environment.prod.ts` atualizado com URL do backend
- [ ] Frontend fazendo deploy na Vercel
- [ ] CORS funcionando (sem erros no console)
- [ ] Upload de arquivo funciona
- [ ] Status de job é atualizado
- [ ] Download de MD/PDF funciona

---

## 🐛 Troubleshooting

### Erro: CORS bloqueado

**Solução:**
- Verifique `CORS_ORIGINS` no `.env` do backend
- Inclua a URL exata do frontend (com `https://`)
- Reinicie o serviço: `sudo systemctl restart booksmd`

### Erro: Backend não responde

**Solução:**
- Verifique se o serviço está rodando: `sudo systemctl status booksmd`
- Verifique logs: `sudo journalctl -u booksmd -n 50`
- Verifique se a porta 8000 está aberta no Security Group
- Teste localmente na instância: `curl http://localhost:8000/health`

### Erro: Build do frontend falha

**Solução:**
- Verifique Node.js version (18+)
- Limpe cache: `rm -rf node_modules package-lock.json`
- Reinstale: `npm install`
- Verifique `angular.json` e `package.json`

### Erro: Arquivos não persistem

**Solução:**
- Verifique se o EBS volume está montado: `df -h`
- Verifique permissões: `ls -la /data` (ou diretório configurado)
- Configure `UPLOAD_DIR` e `OUTPUT_DIR` no `.env`

---

## 📚 Comandos Úteis

### EC2

```bash
# Ver status da instância
aws ec2 describe-instance-status --instance-ids i-xxxxx

# Reiniciar instância
aws ec2 reboot-instances --instance-ids i-xxxxx

# Parar instância
aws ec2 stop-instances --instance-ids i-xxxxx

# Iniciar instância
aws ec2 start-instances --instance-ids i-xxxxx

# Ver logs do CloudWatch (se configurado)
aws logs tail /aws/ec2/booksmd-backend --follow
```

### No Servidor

```bash
# Ver status do serviço
sudo systemctl status booksmd

# Reiniciar serviço
sudo systemctl restart booksmd

# Ver logs em tempo real
sudo journalctl -u booksmd -f

# Ver últimas 100 linhas de log
sudo journalctl -u booksmd -n 100

# Testar endpoint
curl http://localhost:8000/health
```

---

**Última atualização**: 2024
**Versão do projeto**: 1.0.0
