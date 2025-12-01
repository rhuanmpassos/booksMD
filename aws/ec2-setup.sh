#!/bin/bash
# Script auxiliar para configurar EC2 manualmente (se user-data não funcionar)

set -e

echo "🔧 Configurando BooksMD Backend no EC2..."

# Instala dependências
sudo yum update -y
sudo yum install -y python3.11 python3.11-pip git

# Instala dependências do sistema
sudo yum install -y \
    cairo-devel \
    pango-devel \
    libffi-devel \
    shared-mime-info \
    gcc \
    g++

# Navega para diretório
cd /home/ec2-user
git clone https://github.com/seu-usuario/booksmd.git || echo "Repositório já existe"
cd booksmd/backend

# Cria venv
python3.11 -m venv venv
source venv/bin/activate

# Instala dependências
pip install --upgrade pip
pip install -r requirements.txt

# Cria diretórios
mkdir -p uploads outputs data

# Cria .env
cat > .env << 'EOF'
LLM_PROVIDER=gradio
GRADIO_SPACE_ID=burak/Llama-4-Maverick-17B-Websearch
HOST=0.0.0.0
PORT=8000
DEBUG=False
CORS_ORIGINS=*
EOF

echo "✅ Configuração concluída!"
echo "🚀 Para iniciar: cd /home/ec2-user/booksmd/backend && source venv/bin/activate && python main.py"

