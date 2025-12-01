#!/bin/bash
# Script para corrigir CORS no backend EC2

echo "🔧 Corrigindo CORS no backend..."

# Conecta no servidor e atualiza .env
ssh -i ../booksmd-backend-key.pem ec2-user@52.87.194.234 << 'EOF'
cd /opt/booksmd/backend

# Atualiza CORS_ORIGINS no .env
sed -i 's|CORS_ORIGINS=.*|CORS_ORIGINS=https://booksmd.vercel.app,https://booksmd.vercel.app/*|' .env

# Verifica se foi atualizado
grep CORS_ORIGINS .env

# Reinicia o serviço
sudo systemctl restart booksmd

# Aguarda um pouco
sleep 2

# Verifica status
sudo systemctl status booksmd --no-pager -l

echo "✅ CORS atualizado e serviço reiniciado"
EOF

echo "✅ CORS corrigido!"

