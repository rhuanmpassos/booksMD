#!/bin/bash
# Script para configurar HTTPS gratuito usando Cloudflare Tunnel
# Execute no servidor EC2

set -e

echo "🔒 Configurando HTTPS gratuito com Cloudflare Tunnel..."

# Instala cloudflared
echo "📦 Instalando cloudflared..."
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared

# Cria diretório de configuração
mkdir -p /etc/cloudflared

# Cria arquivo de configuração
cat > /etc/cloudflared/config.yml << 'EOF'
tunnel: booksmd-backend
credentials-file: /etc/cloudflared/credentials.json

ingress:
  - hostname: api-booksmd.your-domain.com
    service: http://localhost:8000
  - service: http_status:404
EOF

echo ""
echo "⚠️  IMPORTANTE: Você precisa:"
echo "1. Criar um tunnel no Cloudflare Dashboard"
echo "2. Baixar o arquivo credentials.json"
echo "3. Copiar para /etc/cloudflared/credentials.json"
echo "4. Configurar o hostname no Cloudflare DNS"
echo ""
echo "Ou execute: cloudflared tunnel login"
echo "Depois: cloudflared tunnel create booksmd-backend"

# Cria serviço systemd
cat > /etc/systemd/system/cloudflared.service << 'EOF'
[Unit]
Description=Cloudflare Tunnel
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/cloudflared tunnel --config /etc/cloudflared/config.yml run
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Cloudflared configurado!"
echo "📝 Para iniciar: sudo systemctl enable cloudflared && sudo systemctl start cloudflared"

