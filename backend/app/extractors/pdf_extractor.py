"""Extrator de texto de arquivos PDF."""

import logging
import fitz  # PyMuPDF

logger = logging.getLogger("booksMD.extractor.pdf")


def extract_pdf(file_path: str) -> str:
    """
    Extrai texto de um arquivo PDF.
    
    Args:
        file_path: Caminho do arquivo PDF
        
    Returns:
        Texto extraído do PDF
    """
    text_parts = []
    
    try:
        logger.debug(f"Abrindo PDF: {file_path}")
        doc = fitz.open(file_path)
        total_pages = len(doc)
        logger.info(f"  PDF aberto: {total_pages} páginas")
        
        for page_num in range(total_pages):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            
            if text.strip():
                text_parts.append(text)
            
            # Log a cada 10 páginas ou na última
            if (page_num + 1) % 10 == 0 or page_num == total_pages - 1:
                logger.debug(f"  Extraídas {page_num + 1}/{total_pages} páginas...")
        
        doc.close()
        logger.info(f"  Extração concluída: {len(text_parts)} páginas com texto")
        
    except Exception as e:
        logger.exception(f"Erro ao processar PDF: {e}")
        raise ValueError(f"Erro ao processar PDF: {str(e)}")
    
    return "\n\n".join(text_parts)

