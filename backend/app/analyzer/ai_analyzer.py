"""Analisador de livros com OpenAI."""

from dotenv import load_dotenv
load_dotenv()  # Carrega variáveis de ambiente do arquivo .env

import openai
from typing import Optional, AsyncGenerator
import asyncio
from ..config import get_settings


class BookAnalyzer:
    """
    Analisa capítulos de livros usando OpenAI GPT.
    
    Gera análises detalhadas, traduz conteúdo e explica termos técnicos.
    """
    
    SYSTEM_PROMPT = """Você é um Analisador Profissional de Livros.

Receberá um capítulo ou trecho de um livro. Sua função é:

1. Ler e entender profundamente o conteúdo.
2. Explicar cada ideia com clareza e profundidade.
3. Traduzir tudo para português se estiver em inglês ou outro idioma.
4. Explicar termos técnicos de negócios, finanças, marketing, tecnologia, psicologia etc.
5. Dar exemplos práticos quando necessário para facilitar o entendimento.
6. NÃO resuma superficialmente. A explicação deve ser detalhada e didática.
7. Gerar a saída em Markdown formatado e organizado.

A estrutura OBRIGATÓRIA da sua resposta:

## Visão Geral do Capítulo
[Contexto e propósito do capítulo]

## Ideias Centrais Explicadas
[Análise detalhada de cada ideia principal]

## Conceitos Importantes e Definições
[Definições claras de cada conceito mencionado]

## Exemplos Práticos
[Exemplos do mundo real para ilustrar os conceitos]

## Termos Técnicos Traduzidos e Explicados
[Lista de termos com explicações]

## Análise do Impacto na Obra
[Como este capítulo contribui para a obra como um todo]

IMPORTANTE:
- Seja detalhado e educativo
- Use linguagem clara e acessível
- Mantenha a profundidade analítica
- Formate adequadamente em Markdown"""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        """
        Inicializa o analisador.
        
        Args:
            api_key: Chave da API OpenAI
            model: Modelo a usar
        """
        settings = get_settings()
        self.api_key = api_key or settings.openai_api_key
        self.model = model
        self.client = openai.AsyncOpenAI(api_key=self.api_key)
    
    async def analyze_chapter(
        self,
        chapter_content: str,
        chapter_title: str,
        chapter_number: int,
        previous_context: Optional[str] = None,
        language_hint: str = "auto"
    ) -> dict:
        """
        Analisa um capítulo do livro.
        
        Args:
            chapter_content: Conteúdo do capítulo
            chapter_title: Título do capítulo
            chapter_number: Número do capítulo
            previous_context: Resumo dos capítulos anteriores (opcional)
            language_hint: Idioma detectado
            
        Returns:
            Dicionário com a análise
        """
        # Monta o prompt
        user_prompt = f"""# Capítulo {chapter_number}: {chapter_title}

{chapter_content}

---

Analise este capítulo seguindo a estrutura obrigatória."""

        # Adiciona contexto anterior se disponível
        if previous_context:
            user_prompt = f"""CONTEXTO DOS CAPÍTULOS ANTERIORES:
{previous_context}

---

{user_prompt}

Considere o contexto anterior ao fazer conexões."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            analysis = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            return {
                "success": True,
                "chapter_number": chapter_number,
                "chapter_title": chapter_title,
                "analysis_md": analysis,
                "tokens_used": tokens_used
            }
            
        except openai.RateLimitError:
            # Espera e tenta novamente
            await asyncio.sleep(60)
            return await self.analyze_chapter(
                chapter_content, chapter_title, chapter_number,
                previous_context, language_hint
            )
            
        except Exception as e:
            return {
                "success": False,
                "chapter_number": chapter_number,
                "chapter_title": chapter_title,
                "error": str(e),
                "tokens_used": 0
            }
    
    async def generate_book_summary(
        self,
        all_analyses: list,
        book_title: str,
        book_author: str
    ) -> str:
        """
        Gera um sumário e conclusões gerais do livro.
        
        Args:
            all_analyses: Lista de análises de cada capítulo
            book_title: Título do livro
            book_author: Autor do livro
            
        Returns:
            Conclusões em Markdown
        """
        # Extrai pontos principais de cada análise
        summaries = []
        for analysis in all_analyses:
            if analysis.get("success"):
                summaries.append(f"Capítulo {analysis['chapter_number']}: {analysis['chapter_title']}")
        
        chapters_overview = "\n".join(summaries)
        
        prompt = f"""Com base na análise completa do livro "{book_title}" de {book_author}, 
gere as conclusões gerais da obra.

Capítulos analisados:
{chapters_overview}

Gere:

# Conclusões Gerais da Obra

## Temas Principais
[Os grandes temas do livro]

## Mensagem Central
[A mensagem principal que o autor quer transmitir]

## Aplicações Práticas
[Como aplicar os ensinamentos do livro]

## Para Quem é Recomendado
[Perfil do leitor ideal]

## Nota Final
[Avaliação geral da obra]"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um crítico literário experiente."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"# Conclusões\n\nNão foi possível gerar as conclusões: {str(e)}"
    
    async def extract_glossary(self, all_analyses: list) -> str:
        """
        Extrai um glossário de termos técnicos de todas as análises.
        
        Args:
            all_analyses: Lista de análises
            
        Returns:
            Glossário em Markdown
        """
        # Combina todas as seções de termos técnicos
        terms_sections = []
        for analysis in all_analyses:
            if analysis.get("success") and analysis.get("analysis_md"):
                terms_sections.append(analysis["analysis_md"])
        
        combined = "\n\n".join(terms_sections)
        
        prompt = f"""Analise o texto abaixo e extraia todos os termos técnicos mencionados.

{combined[:8000]}  # Limita tamanho

Gere um glossário organizado em Markdown:

# Glossário

- **Termo 1** — Definição clara e concisa
- **Termo 2** — Definição clara e concisa
...

Ordene alfabeticamente. Inclua apenas termos relevantes e técnicos."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um especialista em criar glossários técnicos."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"# Glossário\n\nNão foi possível gerar o glossário: {str(e)}"

