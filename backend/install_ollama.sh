#!/bin/bash
# Script para instalar e configurar Ollama no Lightning

echo "🦙 Instalando Ollama..."
echo ""

# Instala Ollama
echo "📥 Baixando e instalando Ollama..."
curl -fsSL https://ollama.ai/install.sh | sh

if [ $? -eq 0 ]; then
    echo "✅ Ollama instalado com sucesso!"
else
    echo "❌ Erro ao instalar Ollama"
    exit 1
fi

echo ""
echo "🚀 Iniciando servidor Ollama em background..."
ollama serve &
OLLAMA_PID=$!

# Aguarda o servidor iniciar
sleep 3

# Verifica se está rodando
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Servidor Ollama iniciado (PID: $OLLAMA_PID)"
else
    echo "⚠️  Servidor pode não estar respondendo ainda. Aguarde alguns segundos."
fi

echo ""
echo "📥 Baixando modelo ollama pull llama3 (47 GB)..."
echo "   Melhor modelo para análise de livros na A100 80GB"
echo "   Isso pode demorar alguns minutos..."
ollama pull llama4:128x17b

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Modelo base baixado!"
    echo ""
    echo "🔧 Criando versão otimizada com contexto 32K..."
    
    # Cria Modelfile otimizado para A100 80GB
    cat > /tmp/Modelfile.qwen-optimized << 'MODELFILE'
# Qwen 2.5 72B otimizado para A100 80GB
FROM qwen2.5:72b

# Contexto grande (aproveita a VRAM disponível)
PARAMETER num_ctx 32768

# Parâmetros otimizados para análise de livros
PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1

# Usar todas as GPUs disponíveis
PARAMETER num_gpu 99
MODELFILE

    ollama create qwen2.5:72b-optimized -f /tmp/Modelfile.qwen-optimized
    
    if [ $? -eq 0 ]; then
        echo "✅ Modelo otimizado criado: qwen2.5:72b-optimized"
    fi
    
    echo ""
    echo "🎉 Ollama configurado e pronto!"
    echo ""
    echo "📊 Modelos instalados:"
    ollama list
    echo ""
    echo "📝 Para iniciar o Ollama manualmente:"
    echo "   ollama serve"
    echo ""
    echo "⚙️  Configure no .env:"
    echo "   OLLAMA_MODEL=qwen2.5:72b-optimized"
else
    echo ""
    echo "⚠️  Erro ao baixar modelo. Você pode baixar manualmente depois:"
    echo "   ollama pull qwen2.5:72b"
fi






