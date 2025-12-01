"""Tarefas de processamento de livros."""

from dotenv import load_dotenv
load_dotenv()  # Carrega variáveis de ambiente do arquivo .env

import asyncio
from .celery_app import celery_app
from ..storage.job_storage import get_storage
from ..extractors import extract_text, detect_language
from ..splitter import ChapterSplitter
from ..analyzer import BookAnalyzer
from ..generator import MarkdownGenerator, PDFGenerator
from ..models import BookStatus, BookMetadata
from ..config import get_settings


def run_async(coro):
    """Executa coroutine de forma síncrona."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@celery_app.task(bind=True, max_retries=3)
def process_book_task(self, job_id: str, file_path: str):
    """
    Tarefa principal de processamento de livro.
    
    Args:
        job_id: ID do job
        file_path: Caminho do arquivo
    """
    storage = get_storage()
    settings = get_settings()
    
    try:
        # PASSO 1: Extração de texto
        storage.update_status(
            job_id,
            BookStatus.EXTRACTING,
            progress=5,
            current_step="Extraindo texto do arquivo..."
        )
        
        text, file_type = extract_text(file_path)
        language = detect_language(text)
        
        if not text or len(text) < 100:
            raise ValueError("Arquivo vazio ou com pouco conteúdo")
        
        # PASSO 2: Divisão em capítulos
        storage.update_status(
            job_id,
            BookStatus.SPLITTING,
            progress=15,
            current_step="Identificando capítulos..."
        )
        
        splitter = ChapterSplitter(max_tokens=settings.max_tokens_per_chunk)
        chapters = splitter.split_by_chapters(text)
        stats = splitter.get_book_stats(chapters)
        
        # Atualiza metadados
        job = storage.get(job_id)
        metadata = BookMetadata(
            title=job.filename.rsplit('.', 1)[0] if job else "Livro",
            author="A identificar",
            language=language,
            total_chapters=len(chapters),
            total_words=stats['total_words']
        )
        storage.update(job_id, metadata=metadata.model_dump())
        
        # PASSO 3: Análise com IA
        storage.update_status(
            job_id,
            BookStatus.ANALYZING,
            progress=20,
            current_step="Iniciando análise com IA..."
        )
        
        analyzer = BookAnalyzer()
        all_analyses = []
        
        for i, chapter in enumerate(chapters):
            progress = 20 + (60 * (i + 1) / len(chapters))
            storage.update_status(
                job_id,
                BookStatus.ANALYZING,
                progress=progress,
                current_step=f"Analisando capítulo {i+1} de {len(chapters)}..."
            )
            
            # Analisa o capítulo
            result = run_async(analyzer.analyze_chapter(
                chapter_content=chapter.content,
                chapter_title=chapter.title,
                chapter_number=chapter.number
            ))
            
            all_analyses.append(result)
            storage.add_chapter_analysis(job_id, result)
        
        # PASSO 4: Gera glossário e conclusões
        storage.update_status(
            job_id,
            BookStatus.GENERATING,
            progress=85,
            current_step="Gerando glossário e conclusões..."
        )
        
        glossary = run_async(analyzer.extract_glossary(all_analyses))
        conclusions = run_async(analyzer.generate_book_summary(
            all_analyses,
            metadata.title,
            metadata.author
        ))
        
        # PASSO 5: Gera Markdown
        storage.update_status(
            job_id,
            BookStatus.GENERATING,
            progress=90,
            current_step="Gerando arquivo Markdown..."
        )
        
        md_generator = MarkdownGenerator(settings.output_dir)
        md_path = md_generator.generate(
            book_title=metadata.title,
            book_author=metadata.author,
            language=language,
            chapters_analysis=all_analyses,
            glossary=glossary,
            conclusions=conclusions,
            job_id=job_id
        )
        
        # PASSO 6: Gera PDF
        storage.update_status(
            job_id,
            BookStatus.GENERATING,
            progress=95,
            current_step="Convertendo para PDF..."
        )
        
        pdf_generator = PDFGenerator(settings.output_dir)
        pdf_path = pdf_generator.convert(md_path)
        
        # PASSO 7: Finaliza
        storage.set_complete(job_id, md_path, pdf_path)
        
        return {
            "success": True,
            "job_id": job_id,
            "md_path": md_path,
            "pdf_path": pdf_path
        }
        
    except Exception as e:
        storage.set_error(job_id, str(e))
        raise self.retry(exc=e, countdown=60) if self.request.retries < 3 else None


@celery_app.task
def cleanup_old_jobs(days: int = 7):
    """Remove jobs antigos."""
    from datetime import datetime, timedelta
    
    storage = get_storage()
    cutoff = datetime.now() - timedelta(days=days)
    
    for job_data in storage.list_all():
        created = datetime.fromisoformat(job_data.get('created_at', ''))
        if created < cutoff:
            storage.delete(job_data['id'])

