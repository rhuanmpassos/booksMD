"""Modelos de dados do BooksMD."""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime
import uuid


class BookStatus(str, Enum):
    """Status do processamento do livro."""
    PENDING = "pending"
    EXTRACTING = "extracting"
    SPLITTING = "splitting"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class BookType(str, Enum):
    """Tipos de arquivo suportados."""
    PDF = "pdf"
    EPUB = "epub"
    TXT = "txt"


class ChapterAnalysis(BaseModel):
    """Análise de um capítulo."""
    chapter_number: int
    chapter_title: str
    original_text: Optional[str] = ""
    analysis_md: Optional[str] = ""
    tokens_used: int = 0
    processed_at: Optional[datetime] = None
    success: bool = True
    error: Optional[str] = None


class BookMetadata(BaseModel):
    """Metadados do livro."""
    title: str = "Livro Sem Título"
    author: str = "Autor Desconhecido"
    language: str = "pt"
    total_chapters: int = 0
    total_words: int = 0


class BookJob(BaseModel):
    """Job de processamento de livro."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    file_type: BookType
    status: BookStatus = BookStatus.PENDING
    progress: float = 0.0
    current_step: str = "Aguardando processamento"
    metadata: Optional[BookMetadata] = None
    chapters: List[ChapterAnalysis] = []
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    output_md_path: Optional[str] = None
    output_pdf_path: Optional[str] = None


class UploadResponse(BaseModel):
    """Resposta do upload."""
    job_id: str
    message: str
    filename: str


class JobStatusResponse(BaseModel):
    """Status do job."""
    job_id: str
    status: BookStatus
    progress: float
    current_step: str
    error_message: Optional[str] = None
    metadata: Optional[BookMetadata] = None
    output_ready: bool = False


class DownloadInfo(BaseModel):
    """Informações para download."""
    md_available: bool
    pdf_available: bool
    md_filename: Optional[str] = None
    pdf_filename: Optional[str] = None

