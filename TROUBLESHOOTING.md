# 🔧 Troubleshooting - Erro ao Enviar Arquivo

## Problema
Erro "Erro ao enviar arquivo. Tente novamente." no frontend.

## Possíveis Causas

### 1. Backend não está rodando
**Verificar:**
```bash
# No servidor EC2
ssh -i booksmd-backend-key.pem ec2-user@52.87.194.234
sudo systemctl status booksmd
```

**Solução:**
```bash
# Se não estiver rodando
sudo systemctl start booksmd
sudo systemctl enable booksmd
```

### 2. CORS bloqueado
**Verificar:**
- Abra o Console do navegador (F12)
- Veja se há erros de CORS

**Solução:**
No servidor EC2, edite `/opt/booksmd/backend/.env`:
```env
CORS_ORIGINS=https://booksmd.vercel.app,https://booksmd.vercel.app/*
```

Depois reinicie:
```bash
sudo systemctl restart booksmd
```

### 3. Mixed Content (HTTPS → HTTP)
**Sintoma:**
- Erro no console: "Mixed Content: The page was loaded over HTTPS, but requested an insecure resource"

**Solução Temporária:**
- O frontend já está configurado para usar a URL direta
- Browsers modernos podem bloquear - precisa de HTTPS no backend

**Solução Definitiva:**
- Configure HTTPS no backend (ver `aws/setup-https-alb.ps1`)

### 4. Backend não configurado corretamente
**Verificar logs:**
```bash
ssh -i booksmd-backend-key.pem ec2-user@52.87.194.234
sudo journalctl -u booksmd -n 100 -f
```

**Verificar se o código foi clonado:**
```bash
ls -la /opt/booksmd/backend/
```

Se não existir:
```bash
cd /opt
git clone https://github.com/rhuanmpassos/booksMD.git
cd booksMD/backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Porta 8000 não acessível
**Verificar Security Group:**
```bash
# Via AWS CLI
aws ec2 describe-security-groups --group-ids sg-0e3e80528a9e9f2ba --region us-east-1
```

**Verificar se porta está aberta:**
```bash
# No servidor
sudo netstat -tlnp | grep 8000
```

## Testes Rápidos

### 1. Testar Health Check
```bash
curl http://52.87.194.234:8000/health
```

### 2. Testar Upload (via curl)
```bash
curl -X POST http://52.87.194.234:8000/api/upload \
  -F "file=@teste.pdf" \
  -H "Origin: https://booksmd.vercel.app"
```

### 3. Verificar CORS
No console do navegador, execute:
```javascript
fetch('http://52.87.194.234:8000/health', {
  headers: { 'Origin': 'https://booksmd.vercel.app' }
}).then(r => r.json()).then(console.log).catch(console.error)
```

## Solução Rápida

1. **Conecte no servidor:**
```bash
ssh -i booksmd-backend-key.pem ec2-user@52.87.194.234
```

2. **Verifique o serviço:**
```bash
sudo systemctl status booksmd
```

3. **Se não estiver rodando, inicie:**
```bash
cd /opt/booksmd/backend
source venv/bin/activate
python main.py
```

4. **Ou reinicie o serviço:**
```bash
sudo systemctl restart booksmd
sudo journalctl -u booksmd -f
```

## Próximos Passos

Após verificar o backend, atualize o frontend:
```bash
git add frontend/src/environments/environment.prod.ts
git commit -m "Atualizar URL do backend"
git push origin main
```

O Vercel fará redeploy automaticamente.

