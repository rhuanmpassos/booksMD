"""Extrator de texto de arquivos TXT."""

import chardet


def extract_txt(file_path: str) -> str:
    """
    Extrai texto de um arquivo TXT.
    
    Args:
        file_path: Caminho do arquivo TXT
        
    Returns:
        Texto do arquivo
    """
    try:
        # Detecta encoding
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            detected = chardet.detect(raw_data)
            encoding = detected['encoding'] or 'utf-8'
        
        # Lê com encoding detectado
        with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
            return f.read()
    
    except Exception as e:
        raise ValueError(f"Erro ao processar TXT: {str(e)}")

