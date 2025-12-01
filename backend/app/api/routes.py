"""Rotas da API do BooksMD."""

from dotenv import load_dotenv
load_dotenv()  # Carrega variáveis de ambiente do arquivo .env

import os
import uuid
import asyncio
import aiofiles
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import Optional

from ..models import (
    BookJob, BookType, BookStatus,
    UploadResponse, JobStatusResponse, DownloadInfo
)
from ..storage.job_storage import get_storage
from ..processor import get_processor
from ..config import get_settings

logger = logging.getLogger("booksMD.api")

router = APIRouter(prefix="/api", tags=["books"])

# Armazena tasks em andamento
_running_tasks: dict = {}


def get_file_type(filename: str) -> BookType:
    """Determina o tipo do arquivo."""
    ext = filename.lower().rsplit('.', 1)[-1]
    type_map = {
        'pdf': BookType.PDF,
        'epub': BookType.EPUB,
        'txt': BookType.TXT
    }
    if ext not in type_map:
        raise ValueError(f"Formato não suportado: {ext}")
    return type_map[ext]


@router.post("/upload", response_model=UploadResponse)
async def upload_book(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload de livro para análise.
    
    Aceita arquivos PDF, EPUB e TXT.
    """
    logger.info("=" * 50)
    logger.info(f"📤 UPLOAD RECEBIDO: {file.filename}")
    
    settings = get_settings()
    storage = get_storage()
    
    # Valida tipo de arquivo
    try:
        file_type = get_file_type(file.filename)
        logger.info(f"   Tipo detectado: {file_type.value}")
    except ValueError as e:
        logger.error(f"   ❌ Tipo não suportado: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    # Valida tamanho
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    logger.info(f"   Tamanho: {size_mb:.2f} MB")
    
    if size_mb > settings.max_file_size_mb:
        logger.error(f"   ❌ Arquivo muito grande (máx: {settings.max_file_size_mb}MB)")
        raise HTTPException(
            status_code=413,
            detail=f"Arquivo muito grande. Máximo: {settings.max_file_size_mb}MB"
        )
    
    # Cria job
    job_id = str(uuid.uuid4())
    logger.info(f"   Job ID: {job_id}")
    
    job = BookJob(
        id=job_id,
        filename=file.filename,
        file_type=file_type
    )
    storage.create(job)
    
    # Salva arquivo
    os.makedirs(settings.upload_dir, exist_ok=True)
    file_path = os.path.join(settings.upload_dir, f"{job_id}_{file.filename}")
    
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    logger.info(f"   Arquivo salvo em: {file_path}")
    
    # Inicia processamento em background
    async def process_book():
        logger.info(f"🔄 INICIANDO PROCESSAMENTO [Job: {job_id[:8]}...]")
        try:
            processor = get_processor()
            await processor.process(job_id, file_path)
        except Exception as e:
            logger.exception(f"❌ ERRO NO PROCESSAMENTO [Job: {job_id[:8]}...]: {e}")
            storage.set_error(job_id, str(e))
        finally:
            _running_tasks.pop(job_id, None)
    
    # Cria task assíncrona
    task = asyncio.create_task(process_book())
    _running_tasks[job_id] = task
    
    logger.info(f"✅ Upload processado, task iniciada")
    logger.info("=" * 50)
    
    return UploadResponse(
        job_id=job_id,
        message="Arquivo recebido. Processamento iniciado.",
        filename=file.filename
    )


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Obtém o status do processamento.
    """
    storage = get_storage()
    job = storage.get(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    # Garante que a comparação funcione mesmo se status vier como string
    status_value = job.status.value if isinstance(job.status, BookStatus) else str(job.status)
    is_completed = status_value == BookStatus.COMPLETED.value or status_value == "completed"
    
    # Verifica se arquivos existem mesmo com status diferente de completed
    md_exists = bool(job.output_md_path and os.path.exists(job.output_md_path))
    pdf_exists = bool(job.output_pdf_path and os.path.exists(job.output_pdf_path))
    
    # output_ready = True se status completed OU se arquivos existem
    output_ready = bool(is_completed or md_exists or pdf_exists)
    
    logger.debug(f"📊 Status check [{job_id[:8]}]: status={status_value}, completed={is_completed}, md_exists={md_exists}, pdf_exists={pdf_exists}, output_ready={output_ready}")
    
    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        progress=job.progress,
        current_step=job.current_step,
        error_message=job.error_message,
        metadata=job.metadata,
        output_ready=output_ready
    )


@router.get("/download/{job_id}/info", response_model=DownloadInfo)
async def get_download_info(job_id: str):
    """
    Obtém informações de download.
    Permite acesso se arquivos existem, mesmo com status diferente de 'completed'.
    """
    storage = get_storage()
    job = storage.get(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    # Verifica se arquivos existem (independente do status)
    md_available = job.output_md_path and os.path.exists(job.output_md_path)
    pdf_available = job.output_pdf_path and os.path.exists(job.output_pdf_path)
    
    # Se nenhum arquivo existe, verifica se está em processamento ou falhou
    if not md_available and not pdf_available:
        status_value = job.status.value if isinstance(job.status, BookStatus) else str(job.status)
        if status_value == BookStatus.FAILED.value or status_value == "failed":
            raise HTTPException(status_code=400, detail=f"Processamento falhou: {job.error_message}")
        elif status_value != BookStatus.COMPLETED.value and status_value != "completed":
            raise HTTPException(status_code=400, detail="Arquivos ainda não disponíveis. Processamento em andamento.")
        else:
            raise HTTPException(status_code=404, detail="Arquivos não encontrados")
    
    logger.info(f"📥 Download info [{job_id[:8]}]: md={md_available}, pdf={pdf_available}")
    
    return DownloadInfo(
        md_available=md_available,
        pdf_available=pdf_available,
        md_filename=os.path.basename(job.output_md_path) if md_available else None,
        pdf_filename=os.path.basename(job.output_pdf_path) if pdf_available else None
    )


@router.head("/download/{job_id}/md")
@router.get("/download/{job_id}/md")
async def download_markdown(job_id: str):
    """
    Download do arquivo Markdown.
    Suporta HEAD para verificar disponibilidade.
    """
    storage = get_storage()
    job = storage.get(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    if not job.output_md_path or not os.path.exists(job.output_md_path):
        raise HTTPException(status_code=404, detail="Arquivo MD não disponível")
    
    filename = os.path.basename(job.output_md_path)
    
    return FileResponse(
        path=job.output_md_path,
        filename=filename,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.head("/download/{job_id}/pdf")
@router.get("/download/{job_id}/pdf")
async def download_pdf(job_id: str):
    """
    Download do arquivo PDF.
    Suporta HEAD para verificar disponibilidade.
    """
    storage = get_storage()
    job = storage.get(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    if not job.output_pdf_path or not os.path.exists(job.output_pdf_path):
        raise HTTPException(status_code=404, detail="Arquivo PDF não disponível")
    
    filename = os.path.basename(job.output_pdf_path)
    
    return FileResponse(
        path=job.output_pdf_path,
        filename=filename,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get("/jobs")
async def list_jobs():
    """
    Lista todos os jobs.
    """
    storage = get_storage()
    jobs = storage.list_all()
    
    return {
        "total": len(jobs),
        "jobs": [
            {
                "id": j.get("id"),
                "filename": j.get("filename"),
                "status": j.get("status"),
                "progress": j.get("progress"),
                "created_at": j.get("created_at")
            }
            for j in jobs
        ]
    }


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """
    Remove um job.
    """
    storage = get_storage()
    job = storage.get(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    # Remove arquivos
    settings = get_settings()
    
    if job.output_md_path and os.path.exists(job.output_md_path):
        os.remove(job.output_md_path)
    
    if job.output_pdf_path and os.path.exists(job.output_pdf_path):
        os.remove(job.output_pdf_path)
    
    # Remove arquivo de upload
    upload_pattern = os.path.join(settings.upload_dir, f"{job_id}_*")
    import glob
    for f in glob.glob(upload_pattern):
        os.remove(f)
    
    # Remove job
    storage.delete(job_id)
    
    return {"message": "Job removido com sucesso"}

