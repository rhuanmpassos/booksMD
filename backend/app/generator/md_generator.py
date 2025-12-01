"""Gerador de arquivos Markdown."""

from typing import List, Optional
from datetime import datetime
import os
import re


class MarkdownGenerator:
    """
    Gera arquivo Markdown final com todas as análises.
    """
    
    def __init__(self, output_dir: str = "./outputs"):
        """
        Inicializa o gerador.
        
        Args:
            output_dir: Diretório de saída
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate(
        self,
        book_title: str,
        book_author: str,
        language: str,
        chapters_analysis: List[dict],
        glossary: str = "",
        conclusions: str = "",
        job_id: str = ""
    ) -> str:
        """
        Gera o arquivo Markdown completo.
        
        Args:
            book_title: Título do livro
            book_author: Autor do livro
            language: Idioma original
            chapters_analysis: Lista de análises por capítulo
            glossary: Glossário de termos
            conclusions: Conclusões gerais
            job_id: ID do job para nome do arquivo
            
        Returns:
            Caminho do arquivo gerado
        """
        # Gera sumário
        toc = self._generate_toc(chapters_analysis)
        
        # Header do documento
        header = f"""# Análise Completa do Livro: {book_title}

**Autor:** {book_author}  
**Idioma Original:** {language}  
**Data da Análise:** {datetime.now().strftime("%d/%m/%Y")}  
**Gerado por:** BooksMD - Sistema de Análise Inteligente de Livros

---

{toc}

---

"""
        
        # Corpo com análises
        body = self._generate_body(chapters_analysis)
        
        # Footer com glossário e conclusões
        footer = f"""

---

{glossary if glossary else self._empty_glossary()}

---

{conclusions if conclusions else self._empty_conclusions()}

---

*Documento gerado automaticamente pelo BooksMD*
"""
        
        # Monta documento completo
        full_document = header + body + footer
        
        # Salva arquivo
        filename = self._sanitize_filename(book_title, job_id)
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_document)
        
        return filepath
    
    def _generate_toc(self, chapters: List[dict]) -> str:
        """Gera o sumário do documento."""
        toc_lines = ["# Sumário\n"]
        
        for chapter in chapters:
            if chapter.get("success"):
                num = chapter.get("chapter_number", "?")
                title = chapter.get("chapter_title", f"Capítulo {num}")
                anchor = self._generate_anchor(f"capítulo-{num}-{title}")
                toc_lines.append(f"- [Capítulo {num} — {title}](#{anchor})")
        
        toc_lines.append("- [Glossário](#glossário)")
        toc_lines.append("- [Conclusões Gerais](#conclusões-gerais-da-obra)")
        
        return "\n".join(toc_lines)
    
    def _generate_body(self, chapters: List[dict]) -> str:
        """Gera o corpo do documento com todas as análises."""
        body_parts = []
        
        for chapter in chapters:
            if chapter.get("success"):
                num = chapter.get("chapter_number", "?")
                title = chapter.get("chapter_title", f"Capítulo {num}")
                analysis = chapter.get("analysis_md", "Análise não disponível")
                
                chapter_section = f"""
# Capítulo {num} — {title}

{analysis}

---
"""
                body_parts.append(chapter_section)
            else:
                # Capítulo com erro
                num = chapter.get("chapter_number", "?")
                error = chapter.get("error", "Erro desconhecido")
                
                chapter_section = f"""
# Capítulo {num}

> ⚠️ **Erro na análise:** {error}

---
"""
                body_parts.append(chapter_section)
        
        return "\n".join(body_parts)
    
    def _generate_anchor(self, text: str) -> str:
        """Gera anchor para links internos."""
        # Remove acentos e caracteres especiais
        anchor = text.lower()
        anchor = re.sub(r'[áàâã]', 'a', anchor)
        anchor = re.sub(r'[éèê]', 'e', anchor)
        anchor = re.sub(r'[íìî]', 'i', anchor)
        anchor = re.sub(r'[óòôõ]', 'o', anchor)
        anchor = re.sub(r'[úùû]', 'u', anchor)
        anchor = re.sub(r'[ç]', 'c', anchor)
        anchor = re.sub(r'[^a-z0-9\s-]', '', anchor)
        anchor = re.sub(r'\s+', '-', anchor)
        return anchor
    
    def _sanitize_filename(self, title: str, job_id: str) -> str:
        """Gera nome de arquivo seguro."""
        # Remove caracteres não permitidos
        safe_title = re.sub(r'[<>:"/\\|?*]', '', title)
        safe_title = safe_title[:50]  # Limita tamanho
        safe_title = safe_title.strip()
        
        if not safe_title:
            safe_title = "analise"
        
        return f"{safe_title}_{job_id[:8]}.md"
    
    def _empty_glossary(self) -> str:
        """Retorna glossário vazio formatado."""
        return """# Glossário

*Glossário não disponível para este livro.*
"""
    
    def _empty_conclusions(self) -> str:
        """Retorna conclusões vazias formatadas."""
        return """# Conclusões Gerais da Obra

*Conclusões não disponíveis para este livro.*
"""

