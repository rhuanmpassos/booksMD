#!/bin/bash
# Script de inicialização para EC2 (Amazon Linux 2023)

set -e

echo "🚀 Iniciando configuração do BooksMD Backend..."

# Atualiza sistema
yum update -y

# Instala Python 3.11 e ferramentas
yum install -y python3.11 python3.11-pip git

# Instala dependências do sistema para WeasyPrint
yum install -y \
    cairo-devel \
    pango-devel \
    libffi-devel \
    shared-mime-info \
    gcc \
    g++

# Cria diretório da aplicação
mkdir -p /opt/booksmd
cd /opt/booksmd

# Clona repositório (ajuste a URL)
# Se usar CodeDeploy, pule esta etapa
git clone https://github.com/seu-usuario/booksmd.git . || echo "Repositório já existe"

cd backend

# Cria ambiente virtual
python3.11 -m venv venv
source venv/bin/activate

# Instala dependências
pip install --upgrade pip
pip install -r requirements.txt

# Cria diretórios
mkdir -p uploads outputs data

# Cria arquivo .env (ajuste as variáveis)
cat > .env << 'EOF'
LLM_PROVIDER=gradio
GRADIO_SPACE_ID=burak/Llama-4-Maverick-17B-Websearch
GRADIO_USE_WEB_SEARCH=False
HOST=0.0.0.0
PORT=8000
DEBUG=False
UPLOAD_DIR=/opt/booksmd/backend/uploads
OUTPUT_DIR=/opt/booksmd/backend/outputs
CORS_ORIGINS=*
EOF

# Cria service systemd
cat > /etc/systemd/system/booksmd.service << 'EOF'
[Unit]
Description=BooksMD Backend API
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/opt/booksmd/backend
Environment="PATH=/opt/booksmd/backend/venv/bin"
ExecStart=/opt/booksmd/backend/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Habilita e inicia serviço
systemctl daemon-reload
systemctl enable booksmd
systemctl start booksmd

echo "✅ BooksMD Backend configurado e iniciado!"
echo "📝 Verifique logs com: journalctl -u booksmd -f"

