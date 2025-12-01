"""Armazenamento de jobs em memória/arquivo."""

import json
import os
import logging
from typing import Optional, Dict
from datetime import datetime
from threading import Lock
from ..models import BookJob, BookStatus

logger = logging.getLogger("booksMD.storage")


class JobStorage:
    """
    Armazena e gerencia jobs de processamento.
    
    Usa arquivo JSON para persistência simples.
    Em produção, use Redis ou banco de dados.
    """
    
    def __init__(self, storage_dir: str = "./data"):
        """
        Inicializa o storage.
        
        Args:
            storage_dir: Diretório para armazenamento
        """
        self.storage_dir = storage_dir
        self.storage_file = os.path.join(storage_dir, "jobs.json")
        self._lock = Lock()
        self._jobs: Dict[str, dict] = {}
        
        os.makedirs(storage_dir, exist_ok=True)
        self._load()
    
    def _load(self):
        """Carrega jobs do arquivo."""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Garante que é um dicionário (não lista)
                if isinstance(data, dict):
                    self._jobs = data
                else:
                    logger.warning(f"⚠️ Arquivo jobs.json contém {type(data).__name__}, esperado dict. Resetando...")
                    self._jobs = {}
                    self._save()  # Salva como dict vazio
                
                logger.info(f"📂 Carregados {len(self._jobs)} jobs do arquivo")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao carregar jobs: {e}")
                self._jobs = {}
        else:
            logger.info("📂 Arquivo de jobs não existe, iniciando vazio")
            self._jobs = {}
    
    def _save(self):
        """Salva jobs no arquivo."""
        try:
            logger.debug(f"💾 Salvando {len(self._jobs)} jobs no arquivo {self.storage_file}")
            
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self._jobs, f, indent=2, default=str)
                f.flush()  # Força escrita do buffer
                os.fsync(f.fileno())  # Garante escrita no disco
            
            logger.debug(f"✅ Jobs salvos com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro ao salvar jobs: {e}")
    
    def create(self, job: BookJob) -> str:
        """
        Cria um novo job.
        
        Args:
            job: Objeto BookJob
            
        Returns:
            ID do job
        """
        with self._lock:
            self._jobs[job.id] = job.model_dump(mode='json')
            self._save()
        return job.id
    
    def get(self, job_id: str) -> Optional[BookJob]:
        """
        Obtém um job pelo ID.
        
        Args:
            job_id: ID do job
            
        Returns:
            BookJob ou None
        """
        with self._lock:
            data = self._jobs.get(job_id)
            if data:
                return BookJob(**data)
        return None
    
    def update(self, job_id: str, **updates) -> bool:
        """
        Atualiza campos de um job.
        
        Args:
            job_id: ID do job
            **updates: Campos para atualizar
            
        Returns:
            True se atualizado
        """
        # Campos válidos do BookJob
        valid_fields = {
            'id', 'filename', 'file_type', 'status', 'progress', 
            'current_step', 'metadata', 'chapters', 'error_message',
            'created_at', 'updated_at', 'output_md_path', 'output_pdf_path'
        }
        
        with self._lock:
            if job_id not in self._jobs:
                logger.warning(f"⚠️ update() - Job {job_id[:8]} não encontrado!")
                return False
            
            updated_keys = []
            for key, value in updates.items():
                if key in valid_fields:
                    self._jobs[job_id][key] = value
                    updated_keys.append(f"{key}={value if key != 'metadata' else '...'}")
                else:
                    logger.warning(f"⚠️ update() - Campo '{key}' ignorado (não é válido)")
            
            self._jobs[job_id]['updated_at'] = datetime.now().isoformat()
            
            logger.debug(f"📝 update() [{job_id[:8]}]: {', '.join(updated_keys)}")
            self._save()
            return True
    
    def update_status(
        self,
        job_id: str,
        status: BookStatus,
        progress: float = None,
        current_step: str = None
    ) -> bool:
        """
        Atualiza o status de um job.
        
        Args:
            job_id: ID do job
            status: Novo status
            progress: Progresso (0-100)
            current_step: Descrição do passo atual
            
        Returns:
            True se atualizado
        """
        updates = {'status': status.value}
        
        if progress is not None:
            updates['progress'] = progress
        
        if current_step is not None:
            updates['current_step'] = current_step
        
        logger.info(f"🔄 Atualizando status do job {job_id[:8]}: {status.value}, progress={progress}, step={current_step}")
        
        result = self.update(job_id, **updates)
        
        logger.debug(f"   Resultado da atualização: {result}")
        
        return result
    
    def add_chapter_analysis(self, job_id: str, analysis: dict) -> bool:
        """
        Adiciona análise de capítulo ao job.
        
        Args:
            job_id: ID do job
            analysis: Dados da análise
            
        Returns:
            True se adicionado
        """
        with self._lock:
            if job_id not in self._jobs:
                return False
            
            if 'chapters' not in self._jobs[job_id]:
                self._jobs[job_id]['chapters'] = []
            
            self._jobs[job_id]['chapters'].append(analysis)
            self._save()
            return True
    
    def set_error(self, job_id: str, error_message: str) -> bool:
        """
        Define erro no job.
        
        Args:
            job_id: ID do job
            error_message: Mensagem de erro
            
        Returns:
            True se atualizado
        """
        logger.error(f"❌ Marcando job {job_id[:8]} como FAILED: {error_message}")
        result = self.update(
            job_id,
            status=BookStatus.FAILED.value,
            error_message=error_message
        )
        logger.debug(f"   set_error resultado: {result}")
        return result
    
    def set_complete(
        self,
        job_id: str,
        md_path: str,
        pdf_path: str = None
    ) -> bool:
        """
        Marca job como completo.
        
        Args:
            job_id: ID do job
            md_path: Caminho do arquivo MD
            pdf_path: Caminho do arquivo PDF
            
        Returns:
            True se atualizado
        """
        # Converte para caminhos absolutos para garantir consistência
        abs_md_path = os.path.abspath(md_path) if md_path else None
        abs_pdf_path = os.path.abspath(pdf_path) if pdf_path else None
        
        logger.info(f"✅ Marcando job {job_id[:8]} como COMPLETED")
        logger.info(f"   MD: {abs_md_path}")
        logger.info(f"   PDF: {abs_pdf_path}")
        
        updates = {
            'status': BookStatus.COMPLETED.value,
            'progress': 100.0,
            'current_step': 'Processamento concluído',
            'output_md_path': abs_md_path
        }
        
        if abs_pdf_path:
            updates['output_pdf_path'] = abs_pdf_path
        
        result = self.update(job_id, **updates)
        
        # Verificação extra: confirma que foi salvo
        if result:
            job_data = self._jobs.get(job_id, {})
            logger.info(f"   ✓ Verificação: status={job_data.get('status')}, md={job_data.get('output_md_path')}")
        else:
            logger.error(f"   ✗ FALHA ao marcar como completo!")
        
        return result
    
    def delete(self, job_id: str) -> bool:
        """
        Remove um job.
        
        Args:
            job_id: ID do job
            
        Returns:
            True se removido
        """
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                self._save()
                return True
        return False
    
    def list_all(self) -> list:
        """Lista todos os jobs."""
        with self._lock:
            return list(self._jobs.values())


# Instância global
_storage: Optional[JobStorage] = None


def get_storage() -> JobStorage:
    """Retorna instância do storage (singleton)."""
    global _storage
    if _storage is None:
        logger.info("📁 Criando nova instância de JobStorage")
        _storage = JobStorage()
        logger.info(f"📁 JobStorage criado - ID: {id(_storage)}, arquivo: {_storage.storage_file}")
    return _storage

