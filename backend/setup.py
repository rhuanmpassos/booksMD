"""Script de setup do BooksMD."""

from dotenv import load_dotenv
import os
import shutil

def setup():
    """Configura o ambiente do BooksMD."""
    print("🚀 Configurando BooksMD...\n")
    
    # Cria diretórios
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("outputs", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    print("✅ Diretórios criados")
    
    # Cria .env se não existir
    if not os.path.exists(".env"):
        env_content = """# BooksMD - Configuração
# Provider: ollama (local), huggingface (gratuito), openai (pago)

LLM_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# Para usar Hugging Face (gratuito), descomente:
# LLM_PROVIDER=huggingface
# HUGGINGFACE_MODEL=mistralai/Mistral-7B-Instruct-v0.3
# HUGGINGFACE_TOKEN=hf_seu_token

# Servidor
HOST=0.0.0.0
PORT=8000
DEBUG=True

# CORS - Use "*" para aceitar todas as origens (acesso remoto)
# Ou liste origens específicas separadas por vírgula
CORS_ORIGINS=*
"""
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ Arquivo .env criado")
    else:
        print("ℹ️  Arquivo .env já existe")
    
    # Carrega e exibe as variáveis do .env
    load_dotenv()  # Carrega variáveis de ambiente do arquivo .env
    
    print("\n📄 Variáveis carregadas do .env:")
    print("-" * 50)
    
    # Variáveis principais para exibir
    env_vars = {
        "LLM_PROVIDER": os.getenv("LLM_PROVIDER", "não definido"),
        "OLLAMA_HOST": os.getenv("OLLAMA_HOST", "não definido"),
        "OLLAMA_MODEL": os.getenv("OLLAMA_MODEL", "não definido"),
        "HUGGINGFACE_MODEL": os.getenv("HUGGINGFACE_MODEL", "não definido"),
        "OPENAI_MODEL": os.getenv("OPENAI_MODEL", "não definido"),
        "HOST": os.getenv("HOST", "0.0.0.0"),
        "PORT": os.getenv("PORT", "8000"),
        "CORS_ORIGINS": os.getenv("CORS_ORIGINS", "*"),
        "DEBUG": os.getenv("DEBUG", "não definido"),
    }
    
    for key, value in env_vars.items():
        # Oculta tokens/chaves sensíveis
        if "TOKEN" in key or "KEY" in key:
            display_value = "***" if value != "não definido" else value
        else:
            display_value = value
        print(f"  {key}: {display_value}")
    
    print("-" * 50)
    
    print("\n📋 Próximos passos:")
    print("1. Instale Ollama: https://ollama.ai")
    print("2. Baixe um modelo: ollama pull llama3.1:8b")
    print("3. Inicie o servidor: python main.py")
    print("\n🎉 Setup concluído!")

if __name__ == "__main__":
    setup()

