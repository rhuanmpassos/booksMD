"""Gerador de arquivos PDF a partir de Markdown."""

import os
import markdown
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration


class PDFGenerator:
    """
    Converte arquivos Markdown para PDF com estilo profissional.
    """
    
    # CSS para estilização do PDF
    PDF_STYLES = """
    @import url('https://fonts.googleapis.com/css2?family=Merriweather:wght@400;700&family=Open+Sans:wght@400;600&display=swap');
    
    @page {
        size: A4;
        margin: 2.5cm 2cm;
        
        @top-center {
            content: string(book-title);
            font-size: 10pt;
            color: #666;
        }
        
        @bottom-center {
            content: counter(page);
            font-size: 10pt;
            color: #666;
        }
    }
    
    @page :first {
        @top-center { content: none; }
    }
    
    body {
        font-family: 'Merriweather', Georgia, serif;
        font-size: 11pt;
        line-height: 1.7;
        color: #1a1a1a;
        text-align: justify;
    }
    
    h1 {
        font-family: 'Open Sans', Arial, sans-serif;
        font-size: 24pt;
        font-weight: 700;
        color: #2c3e50;
        margin-top: 2em;
        margin-bottom: 0.5em;
        page-break-before: always;
        string-set: book-title content();
    }
    
    h1:first-of-type {
        page-break-before: avoid;
        font-size: 28pt;
        text-align: center;
        border-bottom: 3px solid #3498db;
        padding-bottom: 0.5em;
    }
    
    h2 {
        font-family: 'Open Sans', Arial, sans-serif;
        font-size: 16pt;
        font-weight: 600;
        color: #34495e;
        margin-top: 1.5em;
        margin-bottom: 0.5em;
        border-left: 4px solid #3498db;
        padding-left: 0.5em;
    }
    
    h3 {
        font-family: 'Open Sans', Arial, sans-serif;
        font-size: 13pt;
        font-weight: 600;
        color: #555;
        margin-top: 1em;
    }
    
    p {
        margin-bottom: 0.8em;
        orphans: 3;
        widows: 3;
    }
    
    strong {
        color: #2c3e50;
    }
    
    em {
        font-style: italic;
        color: #555;
    }
    
    ul, ol {
        margin-left: 1.5em;
        margin-bottom: 1em;
    }
    
    li {
        margin-bottom: 0.3em;
    }
    
    blockquote {
        margin: 1em 2em;
        padding: 0.5em 1em;
        border-left: 4px solid #bdc3c7;
        background: #f9f9f9;
        font-style: italic;
        color: #555;
    }
    
    code {
        font-family: 'Courier New', monospace;
        background: #f4f4f4;
        padding: 0.2em 0.4em;
        border-radius: 3px;
        font-size: 0.9em;
    }
    
    pre {
        background: #2c3e50;
        color: #ecf0f1;
        padding: 1em;
        border-radius: 5px;
        overflow-x: auto;
        font-size: 0.85em;
        line-height: 1.4;
    }
    
    pre code {
        background: none;
        padding: 0;
        color: inherit;
    }
    
    hr {
        border: none;
        border-top: 1px solid #ddd;
        margin: 2em 0;
    }
    
    a {
        color: #3498db;
        text-decoration: none;
    }
    
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 1em 0;
    }
    
    th, td {
        border: 1px solid #ddd;
        padding: 0.5em;
        text-align: left;
    }
    
    th {
        background: #f4f4f4;
        font-weight: 600;
    }
    
    /* Glossário */
    #glossário ul {
        list-style: none;
        margin-left: 0;
    }
    
    #glossário li {
        margin-bottom: 0.8em;
        padding-left: 1em;
        border-left: 2px solid #3498db;
    }
    
    /* Sumário */
    #sumário ul {
        list-style: none;
    }
    
    #sumário a {
        display: block;
        padding: 0.3em 0;
        border-bottom: 1px dotted #ddd;
    }
    
    /* Avisos */
    .warning {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1em;
        margin: 1em 0;
    }
    """
    
    def __init__(self, output_dir: str = "./outputs"):
        """
        Inicializa o gerador.
        
        Args:
            output_dir: Diretório de saída
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.font_config = FontConfiguration()
    
    def convert(self, md_filepath: str) -> str:
        """
        Converte arquivo Markdown para PDF.
        
        Args:
            md_filepath: Caminho do arquivo Markdown
            
        Returns:
            Caminho do PDF gerado
        """
        # Lê o Markdown
        with open(md_filepath, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Converte para HTML
        html_content = self._md_to_html(md_content)
        
        # Gera PDF
        pdf_filepath = md_filepath.replace('.md', '.pdf')
        
        html = HTML(string=html_content)
        css = CSS(string=self.PDF_STYLES, font_config=self.font_config)
        
        html.write_pdf(
            pdf_filepath,
            stylesheets=[css],
            font_config=self.font_config
        )
        
        return pdf_filepath
    
    def _md_to_html(self, md_content: str) -> str:
        """Converte Markdown para HTML."""
        # Extensões do Markdown
        extensions = [
            'extra',
            'codehilite',
            'toc',
            'tables',
            'fenced_code',
            'nl2br'
        ]
        
        html_body = markdown.markdown(
            md_content,
            extensions=extensions,
            output_format='html5'
        )
        
        # Monta documento HTML completo
        html_doc = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Análise de Livro - BooksMD</title>
</head>
<body>
{html_body}
</body>
</html>"""
        
        return html_doc
    
    def convert_from_string(self, md_content: str, output_filename: str) -> str:
        """
        Converte string Markdown diretamente para PDF.
        
        Args:
            md_content: Conteúdo Markdown
            output_filename: Nome do arquivo de saída
            
        Returns:
            Caminho do PDF gerado
        """
        # Converte para HTML
        html_content = self._md_to_html(md_content)
        
        # Caminho do PDF
        if not output_filename.endswith('.pdf'):
            output_filename += '.pdf'
        
        pdf_filepath = os.path.join(self.output_dir, output_filename)
        
        # Gera PDF
        html = HTML(string=html_content)
        css = CSS(string=self.PDF_STYLES, font_config=self.font_config)
        
        html.write_pdf(
            pdf_filepath,
            stylesheets=[css],
            font_config=self.font_config
        )
        
        return pdf_filepath

