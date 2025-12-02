"""Aplicação principal do BooksMD."""

from dotenv import load_dotenv
load_dotenv()  # Carrega variáveis de ambiente do arquivo .env

import logging
import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings, init_directories
from app.api import router

# Configuração de logging detalhado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Reduz logs verbosos de bibliotecas externas
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("watchfiles").setLevel(logging.WARNING)  # Silencia detecção de arquivos

logger = logging.getLogger("booksMD")


def get_gpu_info():
    """Obtém informações sobre a GPU disponível."""
    import subprocess
    import shutil
    
    gpu_info = {
        "name": "N/A",
        "memory_total": "N/A",
        "memory_used": "N/A",
        "memory_free": "N/A",
        "utilization": "N/A"
    }
    
    # Verifica se nvidia-smi está disponível
    if not shutil.which("nvidia-smi"):
        return gpu_info
    
    try:
        # Obtém informações básicas da GPU
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu", 
             "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            # Pega a primeira GPU
            parts = result.stdout.strip().split('\n')[0].split(', ')
            if len(parts) >= 5:
                gpu_info["name"] = parts[0].strip()
                gpu_info["memory_total"] = f"{parts[1].strip()} MB"
                gpu_info["memory_used"] = f"{parts[2].strip()} MB"
                gpu_info["memory_free"] = f"{parts[3].strip()} MB"
                gpu_info["utilization"] = f"{parts[4].strip()}%"
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, Exception) as e:
        logger.debug(f"Erro ao obter informações da GPU: {e}")
    
    return gpu_info


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação."""
    # Startup
    init_directories()
    settings = get_settings()
    
    # Obtém IP da máquina para acesso externo
    import socket
    try:
        # Conecta a um servidor externo para descobrir o IP local
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = "localhost"
    
    # Obtém informações da GPU
    gpu_info = get_gpu_info()
    
    logger.info("=" * 60)
    logger.info("🚀 BooksMD Backend iniciado!")
    logger.info(f"   Provider LLM: {settings.llm_provider}")
    logger.info(f"   Modelo: {getattr(settings, f'{settings.llm_provider}_model', 'N/A')}")
    logger.info(f"   Debug: {settings.debug}")
    logger.info(f"   Host: {settings.host}:{settings.port}")
    logger.info(f"   Acesse localmente: http://localhost:{settings.port}")
    logger.info(f"   Acesse remotamente: http://{local_ip}:{settings.port}")
    logger.info(f"   CORS: {settings.cors_origins}")
    logger.info(f"   Docs: http://{local_ip}:{settings.port}/docs")
    logger.info("")
    logger.info("🖥️  Informações da GPU:")
    logger.info(f"   Nome: {gpu_info['name']}")
    logger.info(f"   Memória Total: {gpu_info['memory_total']}")
    logger.info(f"   Memória Usada: {gpu_info['memory_used']}")
    logger.info(f"   Memória Livre: {gpu_info['memory_free']}")
    logger.info(f"   Utilização: {gpu_info['utilization']}")
    logger.info("=" * 60)
    yield
    # Shutdown - Limpeza automática
    logger.info("🧹 Limpando dados temporários...")
    
    # Limpa jobs.json
    try:
        import json
        jobs_file = "./data/jobs.json"
        with open(jobs_file, 'w', encoding='utf-8') as f:
            json.dump({}, f)
        logger.info("   ✓ Jobs limpos")
    except Exception as e:
        logger.warning(f"   ⚠ Erro ao limpar jobs: {e}")
    
    # Limpa pasta uploads
    try:
        import glob
        upload_files = glob.glob("./uploads/*")
        for f in upload_files:
            try:
                os.remove(f)
            except:
                pass
        if upload_files:
            logger.info(f"   ✓ {len(upload_files)} arquivo(s) de upload removido(s)")
    except Exception as e:
        logger.warning(f"   ⚠ Erro ao limpar uploads: {e}")
    
    logger.info("👋 BooksMD Backend encerrado.")


# Cria aplicação
app = FastAPI(
    title="BooksMD API",
    description="Sistema de Análise Inteligente de Livros",
    version="1.0.0",
    lifespan=lifespan
)

# Configurações de CORS
settings = get_settings()
cors_origins = settings.get_cors_origins()
# Se aceitar todas as origens, não pode usar allow_credentials
allow_creds = cors_origins != ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_creds,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra rotas
app.include_router(router)


@app.get("/")
async def root():
    """Rota raiz."""
    return {
        "name": "BooksMD API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/ping")
async def ping():
    """Endpoint leve para keep-alive."""
    return {"status": "ok"}


@app.get("/health")
async def health():
    """Health check completo."""
    settings = get_settings()
    gpu_info = get_gpu_info()
    return {
        "status": "healthy",
        "llm_provider": settings.llm_provider,
        "model": {
            "ollama": settings.ollama_model,
            "openai": settings.openai_model,
            "huggingface": settings.huggingface_model
        }.get(settings.llm_provider, "unknown"),
        "gpu": gpu_info
    }


if __name__ == "__main__":
    import uvicorn
    import os
    
    port = settings.port
    
    # Detecta Lightning AI Cloudspace
    cloudspace_host = os.environ.get("LIGHTNING_CLOUDSPACE_HOST", "")
    
    # Banner de conexão
    print("\n" + "=" * 70)
    print("🚀 BooksMD Backend")
    print("=" * 70)
    
    if cloudspace_host:
        # Lightning AI - mostra URL pública
        public_url = f"https://{cloudspace_host.split('.')[0]}-{port}.cloudspaces.litng.ai"
        print(f"\n🌐 URL PÚBLICA (acesse de qualquer lugar):")
        print(f"\n   👉 {public_url}")
        print(f"\n📖 Documentação: {public_url}/docs")
        print(f"\n💡 Esta URL funciona mesmo com o Cursor fechado!")
    else:
        # Servidor genérico
        print(f"\n📍 URLs de acesso:")
        print(f"   • Local: http://localhost:{port}")
        print(f"\n📖 Documentação: http://localhost:{port}/docs")
        print(f"\n🔗 Para acesso remoto via SSH:")
        print(f"   ssh -L {port}:localhost:{port} <usuario>@<servidor>")
    
    print("\n" + "=" * 70 + "\n")
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        reload_includes=["*.py"] if settings.debug else None,
        reload_excludes=["uploads", "outputs", "data", "venv"] if settings.debug else None
    )

