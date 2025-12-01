#!/bin/bash
# ==========================================================
# Script para conectar ao BooksMD com port-forwarding
# RODE ESTE SCRIPT NO SEU PC LOCAL (não no servidor)
# ==========================================================

# Configurações - EDITE ESTAS VARIÁVEIS
SSH_USER="seu_usuario"          # Seu usuário SSH
SSH_HOST="seu_servidor.com"     # Endereço do servidor
SSH_KEY=""                       # Caminho da chave SSH (opcional)
LOCAL_PORT=8000                  # Porta local
REMOTE_PORT=8000                 # Porta remota

echo "========================================"
echo "🔗 Conectando ao BooksMD..."
echo "========================================"
echo ""
echo "Após conectar, acesse:"
echo "   http://localhost:$LOCAL_PORT"
echo ""
echo "Pressione CTRL+C para desconectar"
echo "========================================"
echo ""

# Monta comando SSH
if [ -n "$SSH_KEY" ]; then
    ssh -L $LOCAL_PORT:localhost:$REMOTE_PORT -i "$SSH_KEY" $SSH_USER@$SSH_HOST
else
    ssh -L $LOCAL_PORT:localhost:$REMOTE_PORT $SSH_USER@$SSH_HOST
fi

