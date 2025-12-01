"""Módulo de extração de texto de arquivos."""

from .pdf_extractor import extract_pdf
from .epub_extractor import extract_epub
from .txt_extractor import extract_txt
from .base import extract_text, detect_language

__all__ = [
    "extract_pdf",
    "extract_epub", 
    "extract_txt",
    "extract_text",
    "detect_language"
]

