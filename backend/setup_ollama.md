# 🦙 Configurando Ollama para o BooksMD

## 1. Instalar Ollama

### Windows
```powershell
# Baixe e instale de:
# https://ollama.ai/download

# Ou via winget:
winget install Ollama.Ollama
```

### Linux
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### macOS
```bash
brew install ollama
```

## 2. Iniciar o Servidor Ollama

```bash
ollama serve
```

O servidor roda em `http://localhost:11434`

## 3. Baixar um Modelo

### Recomendados para BooksMD:

| Modelo | VRAM | Qualidade | Velocidade |
|--------|------|-----------|------------|
| `llama3.1:8b` | 8GB | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| `mistral` | 8GB | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| `qwen2.5:14b` | 16GB | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| `mixtral` | 24GB | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

### Comandos para baixar:

```bash
# Opção 1: LLaMA 3.1 8B (recomendado)
ollama pull llama3.1:8b

# Opção 2: Mistral (mais rápido)
ollama pull mistral

# Opção 3: Qwen 2.5 (melhor para português)
ollama pull qwen2.5:14b

# Opção 4: Mixtral (mais potente, precisa de mais VRAM)
ollama pull mixtral
```

## 4. Testar o Modelo

```bash
ollama run llama3.1:8b "Olá! Explique o que é machine learning em português."
```

## 5. Configurar o BooksMD

Crie o arquivo `backend/.env`:

```env
LLM_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

## 6. Executar

```bash
cd backend
python main.py
```

## Dicas

### Pouca VRAM?
Use modelos menores:
```bash
ollama pull llama3.2:3b   # 4GB VRAM
ollama pull phi3:mini      # 4GB VRAM
```

### Quer melhor qualidade em português?
```bash
ollama pull qwen2.5:14b
```

### Usando CPU (sem GPU)?
Modelos menores funcionam, mas são mais lentos:
```bash
ollama pull llama3.2:1b   # Muito leve
ollama pull tinyllama      # Muito leve
```

## Troubleshooting

### Erro: "connection refused"
- Verifique se o Ollama está rodando: `ollama serve`

### Erro: "model not found"
- Baixe o modelo: `ollama pull llama3.1:8b`

### Muito lento?
- Use um modelo menor
- Verifique se está usando GPU: `nvidia-smi`

