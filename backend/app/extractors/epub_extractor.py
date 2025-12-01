"""Extrator de texto de arquivos EPUB."""

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import html


def extract_epub(file_path: str) -> str:
    """
    Extrai texto de um arquivo EPUB.
    
    Args:
        file_path: Caminho do arquivo EPUB
        
    Returns:
        Texto extraído do EPUB
    """
    text_parts = []
    
    try:
        book = epub.read_epub(file_path)
        
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                content = item.get_content().decode('utf-8', errors='ignore')
                
                # Parse HTML
                soup = BeautifulSoup(content, 'html.parser')
                
                # Remove scripts e styles
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Extrai texto
                text = soup.get_text(separator='\n')
                text = html.unescape(text)
                
                if text.strip():
                    text_parts.append(text)
    
    except Exception as e:
        raise ValueError(f"Erro ao processar EPUB: {str(e)}")
    
    return "\n\n".join(text_parts)

