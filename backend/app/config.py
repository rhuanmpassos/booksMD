"""Configurações do sistema BooksMD."""

from dotenv import load_dotenv
load_dotenv()  # Carrega variáveis de ambiente do arquivo .env

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Literal
import os


class Settings(BaseSettings):
    """Configurações da aplicação."""
    
    # LLM Provider: "ollama", "openai", "huggingface", "bedrock" ou "gradio"
    llm_provider: Literal["ollama", "openai", "huggingface", "bedrock", "gradio"] = "ollama"
    
    # Ollama (padrão - modelos locais)
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"  # ou mistral, qwen2.5, etc
    
    # OpenAI (opcional)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    
    # Hugging Face (gratuito)
    huggingface_token: str = ""
    huggingface_model: str = "mistralai/Mistral-7B-Instruct-v0.3"
    
    # Amazon Bedrock
    bedrock_model: str = "meta.llama4-maverick-17b-instruct-v1:0"
    bedrock_region_name: str = "us-east-1"
    bedrock_aws_access_key_id: str = ""
    bedrock_aws_secret_access_key: str = ""
    
    # Gradio Spaces (gratuito - Llama 4 Maverick)
    gradio_space_id: str = "burak/Llama-4-Maverick-17B-Websearch"
    gradio_use_web_search: bool = False
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Servidor
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # Diretórios
    upload_dir: str = "./uploads"
    output_dir: str = "./outputs"
    
    # Limites (removidos para A100 80GB)
    max_file_size_mb: int = 10000  # 10GB - praticamente sem limite
    max_tokens_per_chunk: int = 1000000  # 1M tokens - praticamente sem limite
    
    # CORS - Aceita todas as origens por padrão para desenvolvimento remoto
    # Para produção, configure CORS_ORIGINS no .env com origens específicas
    cors_origins: str = "*"  # "*" aceita todas as origens, ou lista separada por vírgula
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
    def get_cors_origins(self) -> list[str]:
        """Retorna lista de origens CORS permitidas."""
        if self.cors_origins == "*":
            return ["*"]  # Aceita todas as origens
        # Se for uma string com múltiplas origens separadas por vírgula
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """Retorna as configurações cacheadas."""
    return Settings()


# Cria diretórios necessários
def init_directories():
    """Inicializa diretórios do sistema."""
    settings = get_settings()
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.output_dir, exist_ok=True)

