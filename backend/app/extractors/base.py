"""Funções base de extração de texto."""

import os
import re
import logging
from typing import Tuple

logger = logging.getLogger("booksMD.extractor")


def detect_language(text: str) -> str:
    """
    Detecta o idioma do texto de forma simples.
    
    Args:
        text: Texto para análise
        
    Returns:
        Código do idioma (pt, en, es, etc)
    """
    # Palavras comuns em cada idioma
    pt_words = ["de", "que", "não", "para", "uma", "com", "são", "está", "isso", "como", "mais", "você"]
    en_words = ["the", "and", "that", "have", "for", "not", "with", "you", "this", "but", "from", "they"]
    es_words = ["que", "los", "del", "las", "una", "con", "para", "está", "pero", "más", "como", "hay"]
    
    text_lower = text.lower()
    words = re.findall(r'\b\w+\b', text_lower)
    
    if not words:
        return "pt"
    
    # Conta ocorrências
    pt_count = sum(1 for w in words if w in pt_words)
    en_count = sum(1 for w in words if w in en_words)
    es_count = sum(1 for w in words if w in es_words)
    
    total = len(words)
    
    scores = {
        "pt": pt_count / total if total > 0 else 0,
        "en": en_count / total if total > 0 else 0,
        "es": es_count / total if total > 0 else 0
    }
    
    return max(scores, key=scores.get)


def clean_text(text: str) -> str:
    """
    Limpa o texto extraído.
    
    Args:
        text: Texto bruto
        
    Returns:
        Texto limpo
    """
    # Remove múltiplas quebras de linha
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove espaços extras
    text = re.sub(r' {2,}', ' ', text)
    
    # Remove números de página isolados
    text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
    
    # Remove cabeçalhos/rodapés comuns
    text = re.sub(r'\n.*?página \d+.*?\n', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'\n.*?page \d+.*?\n', '\n', text, flags=re.IGNORECASE)
    
    # Remove hífens de quebra de palavra
    text = re.sub(r'-\n', '', text)
    
    return text.strip()


def extract_text(file_path: str) -> Tuple[str, str]:
    """
    Extrai texto de qualquer formato suportado.
    
    Args:
        file_path: Caminho do arquivo
        
    Returns:
        Tupla (texto_extraido, tipo_arquivo)
    """
    from .pdf_extractor import extract_pdf
    from .epub_extractor import extract_epub
    from .txt_extractor import extract_txt
    
    ext = os.path.splitext(file_path)[1].lower()
    logger.debug(f"Extraindo texto de: {os.path.basename(file_path)}")
    logger.debug(f"  Extensão detectada: {ext}")
    
    extractors = {
        '.pdf': extract_pdf,
        '.epub': extract_epub,
        '.txt': extract_txt
    }
    
    if ext not in extractors:
        logger.error(f"  Formato não suportado: {ext}")
        raise ValueError(f"Formato não suportado: {ext}")
    
    logger.debug(f"  Usando extrator: {extractors[ext].__name__}")
    text = extractors[ext](file_path)
    
    logger.debug(f"  Texto bruto: {len(text):,} caracteres")
    text = clean_text(text)
    logger.debug(f"  Texto limpo: {len(text):,} caracteres")
    
    return text, ext[1:]  # Remove o ponto da extensão

