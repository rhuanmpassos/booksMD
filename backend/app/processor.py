"""Processador síncrono para uso sem Celery/Redis."""

from dotenv import load_dotenv
load_dotenv()  # Carrega variáveis de ambiente do arquivo .env

import asyncio
import logging
from typing import Optional
from .storage.job_storage import get_storage
from .extractors import extract_text, detect_language
from .splitter import ChapterSplitter
from .analyzer import get_analyzer
from .generator import MarkdownGenerator, PDFGenerator
from .models import BookStatus, BookMetadata
from .config import get_settings

logger = logging.getLogger("booksMD.processor")


class BookProcessor:
    """
    Processador de livros para execução síncrona.
    
    Suporta múltiplos providers de LLM: Ollama, OpenAI, Hugging Face, Amazon Bedrock.
    """
    
    def __init__(self):
        self.storage = get_storage()
        self.settings = get_settings()
        logger.debug(f"📦 Processor inicializado - Storage ID: {id(self.storage)}")
    
    def _get_analyzer(self):
        """Retorna o analisador configurado."""
        provider = self.settings.llm_provider
        
        if provider == "ollama":
            return get_analyzer(
                provider="ollama",
                model=self.settings.ollama_model,
                host=self.settings.ollama_host
            )
        elif provider == "openai":
            return get_analyzer(
                provider="openai",
                api_key=self.settings.openai_api_key,
                model=self.settings.openai_model
            )
        elif provider == "huggingface":
            return get_analyzer(
                provider="huggingface",
                model=self.settings.huggingface_model,
                api_key=self.settings.huggingface_token
            )
        elif provider == "bedrock":
            return get_analyzer(
                provider="bedrock",
                model=self.settings.bedrock_model,
                region_name=self.settings.bedrock_region_name,
                aws_access_key_id=self.settings.bedrock_aws_access_key_id or None,
                aws_secret_access_key=self.settings.bedrock_aws_secret_access_key or None
            )
        elif provider == "gradio":
            return get_analyzer(
                provider="gradio",
                space_id=self.settings.gradio_space_id,
                use_web_search=self.settings.gradio_use_web_search
            )
        else:
            # Default: Ollama
            return get_analyzer(provider="ollama")
    
    async def process(self, job_id: str, file_path: str) -> dict:
        """
        Processa um livro de forma assíncrona.
        
        Args:
            job_id: ID do job
            file_path: Caminho do arquivo
            
        Returns:
            Resultado do processamento
        """
        short_id = job_id[:8]
        logger.info(f"[{short_id}] ▶ Iniciando processamento")
        logger.info(f"[{short_id}]   Arquivo: {file_path}")
        
        try:
            # PASSO 1: Extração de texto
            logger.info(f"[{short_id}] 📄 PASSO 1/6: Extraindo texto...")
            self._update(job_id, BookStatus.EXTRACTING, 5, "Extraindo texto...")
            
            text, file_type = extract_text(file_path)
            language = detect_language(text)
            
            logger.info(f"[{short_id}]   ✓ Texto extraído: {len(text):,} caracteres")
            logger.info(f"[{short_id}]   ✓ Tipo: {file_type}")
            logger.info(f"[{short_id}]   ✓ Idioma detectado: {language}")
            
            if not text or len(text) < 100:
                raise ValueError("Arquivo vazio ou com pouco conteúdo")
            
            # PASSO 2: Divisão em capítulos
            logger.info(f"[{short_id}] 📚 PASSO 2/6: Dividindo em capítulos...")
            self._update(job_id, BookStatus.SPLITTING, 15, "Identificando capítulos...")
            
            splitter = ChapterSplitter(max_tokens=self.settings.max_tokens_per_chunk)
            chapters = splitter.split_by_chapters(text)
            stats = splitter.get_book_stats(chapters)
            
            logger.info(f"[{short_id}]   ✓ Capítulos encontrados: {len(chapters)}")
            logger.info(f"[{short_id}]   ✓ Total de tokens: {stats['total_tokens']:,}")
            logger.info(f"[{short_id}]   ✓ Total de palavras: {stats['total_words']:,}")
            for ch in chapters[:5]:  # Mostra primeiros 5
                logger.debug(f"[{short_id}]     - Cap {ch.number}: {ch.title[:50]}... ({ch.token_count} tokens)")
            if len(chapters) > 5:
                logger.debug(f"[{short_id}]     ... e mais {len(chapters) - 5} capítulos")
            
            # Atualiza metadados
            job = self.storage.get(job_id)
            metadata = BookMetadata(
                title=job.filename.rsplit('.', 1)[0] if job else "Livro",
                author="A identificar",
                language=language,
                total_chapters=len(chapters),
                total_words=stats['total_words']
            )
            self.storage.update(job_id, metadata=metadata.model_dump())
            
            # PASSO 3: Análise com IA (com contexto acumulativo)
            provider = self.settings.llm_provider
            logger.info(f"[{short_id}] 🤖 PASSO 3/6: Analisando com IA ({provider})...")
            logger.info(f"[{short_id}]   📚 Sistema de contexto acumulativo ATIVADO")
            self._update(job_id, BookStatus.ANALYZING, 20, f"Iniciando análise com {provider}...")
            
            analyzer = self._get_analyzer()
            all_analyses = []
            
            # Contexto acumulativo para conexões entre capítulos
            accumulated_context = []
            MAX_CONTEXT_ITEMS = 50  # Aumentado para A100 80GB - mantém últimos 50 resumos
            
            for i, chapter in enumerate(chapters):
                progress = 20 + (60 * (i + 1) / len(chapters))
                logger.info(f"[{short_id}]   📖 Analisando capítulo {i+1}/{len(chapters)}: {chapter.title[:40]}...")
                self._update(
                    job_id, BookStatus.ANALYZING, progress,
                    f"Analisando capítulo {i+1} de {len(chapters)}..."
                )
                
                # Monta contexto dos capítulos anteriores
                previous_context = None
                if accumulated_context:
                    previous_context = "\n\n".join(accumulated_context[-MAX_CONTEXT_ITEMS:])
                    logger.debug(f"[{short_id}]     📎 Usando contexto de {len(accumulated_context)} capítulos anteriores")
                
                result = await analyzer.analyze_chapter(
                    chapter_content=chapter.content,
                    chapter_title=chapter.title,
                    chapter_number=chapter.number,
                    previous_context=previous_context  # Passa contexto acumulado
                )
                
                if result.get("success"):
                    logger.info(f"[{short_id}]     ✓ Capítulo {i+1} analisado ({result.get('tokens_used', 0)} tokens)")
                    
                    # Acumula o resumo do capítulo para os próximos
                    context_summary = result.get("context_summary", "")
                    if context_summary:
                        accumulated_context.append(context_summary)
                        logger.debug(f"[{short_id}]     📝 Contexto acumulado: {len(context_summary)} chars")
                else:
                    logger.warning(f"[{short_id}]     ⚠ Capítulo {i+1} falhou: {result.get('error', 'Erro desconhecido')}")
                
                all_analyses.append(result)
                self.storage.add_chapter_analysis(job_id, result)
            
            # PASSO 4: Glossário e conclusões
            logger.info(f"[{short_id}] 📝 PASSO 4/6: Gerando glossário e conclusões...")
            self._update(job_id, BookStatus.GENERATING, 85, "Gerando conclusões...")
            
            glossary = await analyzer.extract_glossary(all_analyses)
            logger.info(f"[{short_id}]   ✓ Glossário gerado")
            
            conclusions = await analyzer.generate_book_summary(
                all_analyses, metadata.title, metadata.author
            )
            logger.info(f"[{short_id}]   ✓ Conclusões geradas")
            
            # PASSO 5: Gera Markdown
            logger.info(f"[{short_id}] 📄 PASSO 5/6: Gerando Markdown...")
            self._update(job_id, BookStatus.GENERATING, 90, "Gerando Markdown...")
            
            md_generator = MarkdownGenerator(self.settings.output_dir)
            md_path = md_generator.generate(
                book_title=metadata.title,
                book_author=metadata.author,
                language=language,
                chapters_analysis=all_analyses,
                glossary=glossary,
                conclusions=conclusions,
                job_id=job_id
            )
            logger.info(f"[{short_id}]   ✓ Markdown salvo: {md_path}")
            
            # PASSO 6: Gera PDF
            logger.info(f"[{short_id}] 📑 PASSO 6/6: Convertendo para PDF...")
            self._update(job_id, BookStatus.GENERATING, 95, "Convertendo para PDF...")
            
            pdf_generator = PDFGenerator(self.settings.output_dir)
            pdf_path = pdf_generator.convert(md_path)
            logger.info(f"[{short_id}]   ✓ PDF gerado: {pdf_path}")
            
            # Finaliza
            self.storage.set_complete(job_id, md_path, pdf_path)
            
            logger.info(f"[{short_id}] ✅ PROCESSAMENTO CONCLUÍDO COM SUCESSO!")
            logger.info(f"[{short_id}]   MD: {md_path}")
            logger.info(f"[{short_id}]   PDF: {pdf_path}")
            
            # LIMPEZA: Remove arquivo original da pasta uploads
            try:
                import os
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"[{short_id}] 🗑️ Arquivo original removido: {file_path}")
            except Exception as cleanup_error:
                logger.warning(f"[{short_id}] ⚠️ Não foi possível remover arquivo original: {cleanup_error}")
            
            return {
                "success": True,
                "job_id": job_id,
                "md_path": md_path,
                "pdf_path": pdf_path
            }
            
        except Exception as e:
            logger.exception(f"[{short_id}] ❌ ERRO NO PROCESSAMENTO: {e}")
            self.storage.set_error(job_id, str(e))
            return {
                "success": False,
                "job_id": job_id,
                "error": str(e)
            }
    
    def _update(self, job_id: str, status: BookStatus, progress: float, step: str):
        """Atualiza status do job."""
        self.storage.update_status(job_id, status, progress, step)


# Instância global
_processor: Optional[BookProcessor] = None


def get_processor() -> BookProcessor:
    """Retorna instância do processador."""
    global _processor
    if _processor is None:
        _processor = BookProcessor()
    return _processor

