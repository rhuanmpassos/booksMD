# 🔒 Solução para Mixed Content (HTTPS → HTTP)

## Problema

O erro "Status: N/A" acontece porque browsers modernos **bloqueiam requisições HTTP de sites HTTPS** por segurança (Mixed Content).

## ✅ Soluções (da mais simples para mais complexa)

### Solução 1: Cloudflare Tunnel (100% GRATUITO - RECOMENDADO)

**Vantagens:**
- ✅ Totalmente gratuito
- ✅ HTTPS automático
- ✅ Sem necessidade de domínio próprio (usa subdomínio do Cloudflare)
- ✅ Configuração simples

**Passo a Passo:**

1. **Crie conta no Cloudflare** (gratuita): https://dash.cloudflare.com/sign-up

2. **No servidor EC2, instale cloudflared:**
```bash
ssh -i booksmd-backend-key.pem ec2-user@52.87.194.234

# Instala cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared

# Login no Cloudflare
cloudflared tunnel login
```

3. **Crie o tunnel:**
```bash
cloudflared tunnel create booksmd-backend
```

4. **Configure DNS (opcional - se tiver domínio):**
```bash
cloudflared tunnel route dns booksmd-backend api.booksmd.seu-dominio.com
```

5. **Crie arquivo de configuração:**
```bash
mkdir -p ~/.cloudflared
nano ~/.cloudflared/config.yml
```

Conteúdo:
```yaml
tunnel: booksmd-backend
credentials-file: /home/ec2-user/.cloudflared/[TUNNEL-ID].json

ingress:
  - hostname: api-booksmd-[seu-id].trycloudflare.com
    service: http://localhost:8000
  - service: http_status:404
```

6. **Inicie o tunnel:**
```bash
cloudflared tunnel run booksmd-backend
```

7. **Configure como serviço systemd (para iniciar automaticamente):**
```bash
sudo cloudflared service install
sudo systemctl start cloudflared
sudo systemctl enable cloudflared
```

8. **Anote a URL gerada** (ex: `https://api-booksmd-xxxxx.trycloudflare.com`)

9. **Atualize o frontend:**
```bash
cd frontend
node replace-api-url.js https://api-booksmd-xxxxx.trycloudflare.com
```

### Solução 2: Application Load Balancer + ACM (HTTPS, mas tem custo)

**Custo:** ~$16/mês (ALB) + certificado SSL gratuito

**Vantagens:**
- ✅ HTTPS nativo
- ✅ Escalável
- ✅ Integração com AWS

**Desvantagens:**
- ⚠️ Tem custo mensal

**Execute:**
```bash
cd aws
.\setup-https-alb.ps1
```

### Solução 3: Nginx + Let's Encrypt (Gratuito, mas precisa de domínio)

**Vantagens:**
- ✅ Totalmente gratuito
- ✅ Certificado SSL automático (Let's Encrypt)

**Desvantagens:**
- ⚠️ Precisa de domínio próprio
- ⚠️ Mais complexo de configurar

## 🎯 Recomendação

**Use Cloudflare Tunnel** - É a solução mais simples e totalmente gratuita. Não precisa de domínio próprio (usa subdomínio do Cloudflare) e configuração é rápida.

## 📝 Após Configurar HTTPS

1. Atualize `frontend/src/environments/environment.prod.ts` com a URL HTTPS
2. Faça commit e push
3. O Vercel fará redeploy
4. Teste novamente o upload

---

**Status atual:** Backend em HTTP, precisa de HTTPS para funcionar com frontend HTTPS.

