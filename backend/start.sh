#!/bin/bash
# Script para iniciar o backend BooksMD

echo "🚀 Iniciando BooksMD Backend..."
echo ""

# Verifica se está no diretório correto
if [ ! -f "main.py" ]; then
    echo "❌ Erro: main.py não encontrado!"
    echo "   Certifique-se de estar no diretório do backend: cd ~/booksMD"
    exit 1
fi

# Verifica se o .env existe
if [ ! -f ".env" ]; then
    echo "⚠️  Arquivo .env não encontrado. Executando setup..."
    python setup.py
    echo ""
fi

# Verifica se há um processo uvicorn já rodando
if pgrep -f "uvicorn.*main:app" > /dev/null; then
    echo "⚠️  Já existe um processo uvicorn rodando!"
    echo "   Para parar: pkill -f 'uvicorn.*main:app'"
    echo ""
    read -p "Deseja continuar mesmo assim? (s/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        exit 1
    fi
fi

echo "✅ Iniciando servidor..."
echo "   URL: http://localhost:8000"
echo "   Pressione CTRL+C para parar"
echo "   ⚠️  IMPORTANTE: Deixe este terminal aberto!"
echo ""

# Inicia o servidor
python main.py






