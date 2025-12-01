"""Analisador de livros com Hugging Face Inference API (gratuito)."""

from dotenv import load_dotenv
load_dotenv()  # Carrega variáveis de ambiente do arquivo .env

import httpx
from typing import Optional
import asyncio
import os
from ..config import get_settings


class HuggingFaceAnalyzer:
    """
    Analisa capítulos de livros usando a API gratuita do Hugging Face.
    
    Modelos gratuitos recomendados:
    - mistralai/Mistral-7B-Instruct-v0.3
    - microsoft/Phi-3-mini-4k-instruct
    - google/gemma-2-9b-it
    - meta-llama/Meta-Llama-3-8B-Instruct
    """
    
    API_URL = "https://api-inference.huggingface.co/models"
    
    SYSTEM_PROMPT = """Você é um Analisador Profissional de Livros.

Sua função é analisar capítulos de livros e:
1. Explicar cada ideia com clareza
2. Traduzir para português se necessário
3. Explicar termos técnicos
4. Dar exemplos práticos
5. NÃO resumir superficialmente - seja detalhado

Formato da resposta (Markdown):

## Visão Geral do Capítulo
[Contexto]

## Ideias Centrais
[Análise]

## Conceitos Importantes
[Definições]

## Exemplos Práticos
[Exemplos]

## Termos Técnicos
[Lista de termos]

Responda SEMPRE em português brasileiro."""

    def __init__(
        self, 
        model: str = "mistralai/Mistral-7B-Instruct-v0.3",
        api_key: Optional[str] = None
    ):
        """
        Inicializa o analisador.
        
        Args:
            model: Nome do modelo no Hugging Face
            api_key: Token do Hugging Face (opcional, mas recomendado)
        """
        self.model = model
        settings = get_settings()
        self.api_key = api_key or settings.huggingface_token or os.getenv("HF_TOKEN", "")
        self.api_url = f"{self.API_URL}/{model}"
        
        self.headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
    
    async def _query(self, prompt: str, max_tokens: int = 2000) -> str:
        """Faz query ao modelo."""
        
        # Formato para modelos instruct
        if "mistral" in self.model.lower():
            formatted_prompt = f"<s>[INST] {self.SYSTEM_PROMPT}\n\n{prompt} [/INST]"
        elif "llama" in self.model.lower():
            formatted_prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n{self.SYSTEM_PROMPT}<|eot_id|><|start_header_id|>user<|end_header_id|>\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"
        elif "phi" in self.model.lower():
            formatted_prompt = f"<|system|>\n{self.SYSTEM_PROMPT}<|end|>\n<|user|>\n{prompt}<|end|>\n<|assistant|>"
        else:
            formatted_prompt = f"{self.SYSTEM_PROMPT}\n\nUser: {prompt}\n\nAssistant:"
        
        payload = {
            "inputs": formatted_prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": 0.7,
                "top_p": 0.9,
                "do_sample": True,
                "return_full_text": False
            },
            "options": {
                "wait_for_model": True,
                "use_cache": False
            }
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                self.api_url,
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 503:
                # Modelo carregando, espera
                await asyncio.sleep(20)
                return await self._query(prompt, max_tokens)
            
            response.raise_for_status()
            result = response.json()
            
            if isinstance(result, list) and len(result) > 0:
                return result[0].get("generated_text", "")
            return str(result)
    
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
        """
        # Limita tamanho (modelos gratuitos têm limite menor)
        max_chars = 8000
        if len(chapter_content) > max_chars:
            chapter_content = chapter_content[:max_chars] + "\n\n[... conteúdo truncado ...]"
        
        prompt = f"""Analise este capítulo de livro:

# Capítulo {chapter_number}: {chapter_title}

{chapter_content}

---

Gere uma análise detalhada seguindo a estrutura. Responda em português brasileiro."""

        try:
            analysis = await self._query(prompt, max_tokens=2000)
            
            return {
                "success": True,
                "chapter_number": chapter_number,
                "chapter_title": chapter_title,
                "analysis_md": analysis,
                "tokens_used": len(analysis.split())
            }
            
        except httpx.HTTPStatusError as e:
            error_msg = f"Erro HTTP {e.response.status_code}"
            if e.response.status_code == 401:
                error_msg = "Token HuggingFace inválido ou ausente"
            elif e.response.status_code == 429:
                error_msg = "Limite de requisições atingido. Aguarde alguns minutos."
            
            return {
                "success": False,
                "chapter_number": chapter_number,
                "chapter_title": chapter_title,
                "error": error_msg,
                "tokens_used": 0
            }
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
        """Gera conclusões gerais do livro."""
        summaries = [
            f"Cap {a['chapter_number']}: {a['chapter_title']}"
            for a in all_analyses if a.get("success")
        ]
        
        prompt = f"""Livro: "{book_title}" de {book_author}

Capítulos: {', '.join(summaries)}

Gere as conclusões gerais em português:

# Conclusões Gerais da Obra

## Temas Principais
## Mensagem Central
## Aplicações Práticas
## Para Quem é Recomendado"""

        try:
            return await self._query(prompt, max_tokens=1500)
        except Exception as e:
            return f"# Conclusões\n\nErro: {str(e)}"
    
    async def extract_glossary(self, all_analyses: list) -> str:
        """Extrai glossário de termos."""
        terms = []
        for a in all_analyses[:3]:  # Limita para não estourar
            if a.get("success"):
                terms.append(a.get("analysis_md", "")[:1500])
        
        prompt = f"""Extraia termos técnicos deste texto e crie um glossário:

{chr(10).join(terms)}

# Glossário
- **Termo** — Definição

Ordene alfabeticamente. Português brasileiro."""

        try:
            return await self._query(prompt, max_tokens=1500)
        except Exception as e:
            return f"# Glossário\n\nErro: {str(e)}"

