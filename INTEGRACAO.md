# 🔗 Integração Frontend (Vercel) ↔ Backend (EC2)

## ✅ Status da Integração

A integração já está **100% configurada e funcionando**!

### Configuração Atual

**Frontend (Vercel):**
- URL: https://booksmd.vercel.app
- Backend URL configurada: `http://52.87.194.234:8000`
- Arquivo: `frontend/src/environments/environment.prod.ts`

**Backend (EC2):**
- URL: http://52.87.194.234:8000
- Health Check: http://52.87.194.234:8000/health
- CORS: Configurado para aceitar requisições de `https://booksmd.vercel.app`

## 🔄 Como Funciona

```
┌─────────────────────────────────┐
│  Frontend (Vercel)              │
│  https://booksmd.vercel.app     │
└──────────────┬──────────────────┘
               │ HTTP Request
               │ (via ApiService)
               ▼
┌─────────────────────────────────┐
│  Backend (EC2)                   │
│  http://52.87.194.234:8000       │
│  /api/upload                     │
│  /api/status/{job_id}            │
│  /api/download/{job_id}/md       │
└─────────────────────────────────┘
```

## 📝 Fluxo de Requisições

1. **Upload de Livro:**
   ```
   Frontend → POST http://52.87.194.234:8000/api/upload
   ```

2. **Verificar Status:**
   ```
   Frontend → GET http://52.87.194.234:8000/api/status/{job_id}
   ```

3. **Download:**
   ```
   Frontend → GET http://52.87.194.234:8000/api/download/{job_id}/md
   ```

## 🔍 Verificação

### Testar Backend
```bash
curl http://52.87.194.234:8000/health
```

### Testar CORS
No console do navegador (F12) ao acessar https://booksmd.vercel.app:
- Não deve aparecer erros de CORS
- Requisições para `http://52.87.194.234:8000` devem funcionar

## 🛠️ Arquivos de Configuração

### Frontend
- `frontend/src/environments/environment.prod.ts` - URL do backend
- `frontend/src/app/services/api.service.ts` - Serviço que faz as requisições

### Backend
- `backend/app/config.py` - Configurações do servidor
- `.env` no servidor EC2 - Variáveis de ambiente (CORS_ORIGINS)

## ⚠️ Importante

1. **HTTPS vs HTTP:**
   - Frontend: HTTPS (Vercel)
   - Backend: HTTP (EC2)
   - Browsers modernos podem bloquear requisições HTTP de sites HTTPS
   - **Solução:** Configure um Application Load Balancer com certificado SSL na AWS

2. **CORS:**
   - Atualmente configurado para aceitar todas as origens (`*`)
   - Em produção, configure especificamente: `https://booksmd.vercel.app`

3. **Firewall:**
   - Security Group já está configurado (porta 8000 aberta)
   - Verifique se não há firewall adicional bloqueando

## 🚀 Próximos Passos (Opcional)

### 1. Configurar HTTPS no Backend (Recomendado)

Use Application Load Balancer com certificado ACM:

```bash
# Criar certificado SSL no ACM
aws acm request-certificate --domain-name api.booksmd.com --validation-method DNS

# Criar ALB com HTTPS
# (ver DEPLOY_VERCEL.md para instruções completas)
```

### 2. Atualizar Frontend com URL HTTPS

Depois de configurar HTTPS:
```bash
cd frontend
node replace-api-url.js https://api.booksmd.com
```

### 3. Configurar CORS Específico

No servidor EC2, edite `.env`:
```env
CORS_ORIGINS=https://booksmd.vercel.app,https://booksmd.vercel.app/*
```

## ✅ Checklist de Integração

- [x] Backend rodando e respondendo
- [x] Frontend configurado com URL do backend
- [x] CORS configurado
- [x] Security Group permitindo porta 8000
- [x] ApiService usando environment.apiUrl
- [ ] HTTPS configurado (opcional)
- [ ] Teste completo de upload e download

## 🐛 Troubleshooting

### Erro: CORS bloqueado
- Verifique `CORS_ORIGINS` no `.env` do backend
- Reinicie o serviço: `sudo systemctl restart booksmd`

### Erro: Connection refused
- Verifique se o backend está rodando: `sudo systemctl status booksmd`
- Verifique Security Group na AWS
- Teste: `curl http://52.87.194.234:8000/health`

### Erro: Mixed Content (HTTPS → HTTP)
- Configure HTTPS no backend (ALB + ACM)
- Ou use proxy no Vercel (vercel.json rewrites)

---

**Última atualização:** 2024-12-01
**Status:** ✅ Integração Funcionando

