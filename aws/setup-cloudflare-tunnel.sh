#!/bin/bash
# Script para configurar Cloudflare Tunnel no EC2
# Isso fornece HTTPS gratuito para o backend

echo "=========================================="
echo "Configurando Cloudflare Tunnel"
echo "=========================================="

# 1. Instalar cloudflared
echo ""
echo "[1/4] Instalando cloudflared..."
curl -L --output cloudflared.rpm https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-x86_64.rpm
sudo yum localinstall -y cloudflared.rpm
rm cloudflared.rpm

# 2. Verificar instalação
echo ""
echo "[2/4] Verificando instalação..."
cloudflared --version

# 3. Criar túnel (modo quick - sem autenticação Cloudflare)
echo ""
echo "[3/4] Criando túnel..."
echo "O túnel será criado apontando para localhost:8000"
echo ""

# Criar serviço systemd para o túnel
sudo tee /etc/systemd/system/cloudflared.service > /dev/null <<EOF
[Unit]
Description=Cloudflare Tunnel
After=network.target

[Service]
Type=simple
User=ec2-user
ExecStart=/usr/local/bin/cloudflared tunnel --url http://localhost:8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 4. Iniciar serviço
echo ""
echo "[4/4] Iniciando serviço..."
sudo systemctl daemon-reload
sudo systemctl enable cloudflared
sudo systemctl start cloudflared

# Aguardar inicialização
sleep 5

# Mostrar URL do túnel
echo ""
echo "=========================================="
echo "CLOUDFLARE TUNNEL CONFIGURADO!"
echo "=========================================="
echo ""
echo "Para ver a URL HTTPS do seu backend, execute:"
echo "  sudo journalctl -u cloudflared -n 50 | grep 'https://'"
echo ""
echo "A URL será algo como: https://xxx-xxx-xxx.trycloudflare.com"
echo ""
echo "Atualize o frontend com essa URL!"
echo ""

