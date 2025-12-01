"""Analisador de livros usando Gradio Spaces do Hugging Face (gratuito)."""

from dotenv import load_dotenv
load_dotenv()

import logging
import asyncio
from typing import Optional
from gradio_client import Client
from ..config import get_settings

logger = logging.getLogger("booksMD.analyzer.gradio")


class GradioAnalyzer:
    """
    Analisa capítulos de livros usando Gradio Spaces do Hugging Face.
    
    Usa o Space burak/Llama-4-Maverick-17B-Websearch que é gratuito.
    """
    
    SYSTEM_PROMPT = """Você é um PROFESSOR UNIVERSITÁRIO DE ELITE e ANALISTA DE NEGÓCIOS com 30 anos de experiência, especialista em transformar livros complexos em conhecimento profundo e aplicável.

🎯 SUA MISSÃO: Criar uma AULA COMPLETA e EXAUSTIVA sobre este capítulo - NÃO um resumo, mas uma EXPLICAÇÃO DETALHADA que EXPANDE cada conceito.

⚠️ REGRA CRÍTICA DE TAMANHO: Sua análise DEVE ter pelo menos 5-8x o tamanho do capítulo original. Se o capítulo tem 300 palavras, sua análise deve ter MÍNIMO 1500-2400 palavras. EXPANDA MUITO, NÃO RESUMIR!

═══════════════════════════════════════════════════════════════════
📌 PRINCÍPIOS FUNDAMENTAIS (NUNCA VIOLE)
═══════════════════════════════════════════════════════════════════

1. ❌ PROIBIDO RESUMIR: Você NÃO está resumindo. Está ENSINANDO e EXPANDINDO. 
   - Cada parágrafo do capítulo deve gerar MÚLTIPLOS parágrafos de explicação
   - Cada conceito deve ser EXPLICADO, EXEMPLIFICADO e APLICADO
   - Se o capítulo menciona algo, você DEVE explicar em detalhes

2. 📖 COBERTURA TOTAL: Analise CADA parágrafo, CADA ideia, CADA exemplo, CADA dado do capítulo.
   - Nada pode ser ignorado ou pulado
   - Cada menção deve ser expandida com contexto e explicação

3. 🎓 PROFUNDIDADE MÁXIMA: Explique como se o leitor fosse um novato inteligente que quer DOMINAR o assunto.
   - Para cada conceito: O QUE é, POR QUE existe, COMO funciona, QUANDO usar, ONDE aplicar
   - Adicione exemplos práticos, analogias, comparações
   - Explique o contexto histórico ou teórico quando relevante

4. 🌐 TRADUÇÃO INTELIGENTE: Traduza para português brasileiro fluente, mas MANTENHA termos técnicos em inglês entre parênteses quando relevante.

5. 🔗 CONEXÕES OBRIGATÓRIAS: Se houver contexto de capítulos anteriores, INTEGRE as ideias mostrando evolução e conexões.

6. 💼 APLICAÇÃO REAL: Para CADA conceito importante:
   - Explique COMO usar no mundo real
   - Dê exemplos concretos e práticos
   - Liste passos específicos de implementação
   - Mencione armadilhas comuns e como evitá-las

7. 📏 EXPANSÃO OBRIGATÓRIA (CRÍTICO!): 
   - Cada ideia do capítulo = Mínimo 5-8 parágrafos de explicação detalhada
   - Cada exemplo do livro = Análise completa (3-5 parágrafos) + 2-3 exemplos adicionais do mundo real
   - Cada dado/estatística = Contexto completo + interpretação profunda + implicações práticas + comparações
   - Cada parágrafo do capítulo original = Mínimo 2-3 parágrafos de análise na sua resposta
   - NUNCA pule ou resuma - sempre EXPANDA e EXPLIQUE em profundidade

═══════════════════════════════════════════════════════════════════
📋 ESTRUTURA OBRIGATÓRIA DA ANÁLISE (SEJA EXTENSIVO EM CADA SEÇÃO)
═══════════════════════════════════════════════════════════════════

## 📖 Contexto e Propósito do Capítulo
- Por que este capítulo existe na obra? (2-3 parágrafos)
- Qual problema ele resolve? (explique o problema em detalhes)
- Como se conecta com o que veio antes? (mostre conexões específicas)
- Qual a importância deste capítulo no contexto geral? (1-2 parágrafos)

## 🧠 Análise Profunda das Ideias Centrais
Para CADA ideia principal mencionada no capítulo:
- O que é a ideia? (definição detalhada)
- Por que é importante? (justificativa e contexto)
- Como funciona na prática? (mecanismo de funcionamento)
- Exemplos concretos do livro (análise detalhada de cada exemplo)
- Exemplos adicionais do mundo real (2-3 exemplos por ideia)
- Implicações e consequências (o que isso significa na prática)

## 🛠️ Frameworks e Metodologias
Se houver frameworks ou metodologias:
- Explicação completa do framework (cada componente)
- Passo a passo detalhado de como aplicar
- Exemplos práticos de cada etapa
- Quando usar vs quando não usar
- Variações e adaptações possíveis

## 📊 Dados e Evidências
Para cada dado, estatística ou evidência mencionada:
- O que o dado mostra? (interpretação)
- Contexto e fonte (quando disponível)
- O que isso significa na prática? (implicações)
- Comparações relevantes (se aplicável)
- Limitações ou ressalvas (se houver)

## 🏢 Casos de Estudo
Para cada caso ou exemplo do livro:
- Resumo do caso (contexto completo)
- O que foi feito? (detalhamento das ações)
- Por que funcionou (ou não)? (análise dos fatores)
- Lições aprendidas (extração de insights)
- Como aplicar essas lições? (aplicação prática)

## 🎯 Aplicações Práticas
Liste ações específicas e detalhadas:
- Para cada ação: O QUE fazer, COMO fazer, QUANDO fazer, ONDE aplicar
- Passos concretos e mensuráveis
- Recursos necessários
- Indicadores de sucesso
- Armadilhas comuns e como evitá-las

## 📝 Glossário Técnico
Para cada termo técnico:
- Definição completa e clara
- Contexto de uso
- Exemplos práticos
- Relação com outros conceitos

## 📌 Síntese para Continuidade
- 5-7 frases essenciais que conectam este capítulo com os próximos
- Pontos-chave que serão relevantes adiante
- Questões que serão exploradas nos próximos capítulos

═══════════════════════════════════════════════════════════════════
⚠️ LEMBRE-SE: SUA ANÁLISE DEVE SER MUITO MAIS LONGA QUE O CAPÍTULO ORIGINAL!
═══════════════════════════════════════════════════════════════════

Responda SEMPRE em português brasileiro. Seja EXTREMAMENTE detalhado, educativo e expansivo. NÃO resuma - EXPANDA cada conceito em múltiplos parágrafos."""

    def __init__(
        self,
        space_id: str = "burak/Llama-4-Maverick-17B-Websearch",
        use_web_search: bool = False
    ):
        """
        Inicializa o analisador.
        
        Args:
            space_id: ID do Space no Hugging Face
            use_web_search: Se deve usar busca na web (disponível no Space)
        """
        self.space_id = space_id
        self.use_web_search = use_web_search
        self._client = None
        
        logger.info(f"Inicializando GradioAnalyzer")
        logger.info(f"  Space: {space_id}")
        logger.info(f"  Web Search: {use_web_search}")
    
    def _get_client(self) -> Client:
        """Retorna o cliente Gradio, criando se necessário."""
        if self._client is None:
            logger.info(f"  Conectando ao Space {self.space_id}...")
            self._client = Client(self.space_id)
            logger.info(f"  ✓ Conectado!")
        return self._client
    
    async def _query(self, message: str, history: list = None) -> str:
        """
        Faz query ao modelo via Gradio API.
        
        Args:
            message: Mensagem para enviar
            history: Histórico de conversa (opcional)
            
        Returns:
            Resposta do modelo
        """
        if history is None:
            history = []
        
        try:
            # Executa em thread separada para não bloquear
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._get_client().predict(
                    message=message,
                    history=history,
                    use_Web_Search=self.use_web_search,
                    api_name="/query_maverick_streaming"
                )
            )
            
            # O resultado é uma tupla (history, markdown)
            return self._extract_text(result)
            
        except Exception as e:
            logger.error(f"  ❌ Erro na query: {e}")
            raise
    
    def _extract_text(self, result) -> str:
        """Extrai texto do resultado do Gradio."""
        if isinstance(result, str):
            return result
        
        if isinstance(result, tuple):
            # Formato (history, markdown)
            if len(result) >= 2 and result[1]:
                return str(result[1])
            if len(result) >= 1 and result[0]:
                if isinstance(result[0], list) and len(result[0]) > 0:
                    last = result[0][-1]
                    if isinstance(last, dict):
                        return last.get("content", str(last))
                    return str(last)
                return str(result[0])
        
        if isinstance(result, list):
            if len(result) >= 2 and result[1]:
                return str(result[1])
            if len(result) >= 1 and result[0]:
                return str(result[0])
        
        if isinstance(result, dict):
            if "content" in result:
                return str(result["content"])
            if "data" in result:
                return self._extract_text(result["data"])
        
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
        
        Args:
            chapter_content: Conteúdo do capítulo
            chapter_title: Título do capítulo
            chapter_number: Número do capítulo
            previous_context: Resumo dos capítulos anteriores (opcional)
            language_hint: Idioma detectado
            
        Returns:
            Dicionário com a análise
        """
        # Limita tamanho do conteúdo (Spaces gratuitos têm limite)
        max_chars = 15000
        if len(chapter_content) > max_chars:
            chapter_content = chapter_content[:max_chars] + "\n\n[... conteúdo truncado para caber no limite ...]"
        
        # Calcula tamanho esperado da análise (5-8x o tamanho do capítulo)
        chapter_words = len(chapter_content.split())
        min_analysis_words = chapter_words * 5
        max_analysis_words = chapter_words * 8
        
        # Monta o prompt
        user_prompt = f"""{self.SYSTEM_PROMPT}

═══════════════════════════════════════════════════════════════════
📚 CAPÍTULO {chapter_number}: {chapter_title}
═══════════════════════════════════════════════════════════════════

TAMANHO DO CAPÍTULO ORIGINAL: {chapter_words:,} palavras
TAMANHO MÍNIMO ESPERADO DA SUA ANÁLISE: {min_analysis_words:,} a {max_analysis_words:,} palavras
⚠️ SUA ANÁLISE DEVE SER MUITO MAIS LONGA QUE O CAPÍTULO ORIGINAL!

═══════════════════════════════════════════════════════════════════
📖 CONTEÚDO DO CAPÍTULO:
═══════════════════════════════════════════════════════════════════

{chapter_content}

═══════════════════════════════════════════════════════════════════
🎯 INSTRUÇÕES FINAIS (LEIA COM ATENÇÃO - CRÍTICO!)
═══════════════════════════════════════════════════════════════════

⚠️ TAMANHO MÍNIMO OBRIGATÓRIO: {min_analysis_words:,} palavras (ideal: {max_analysis_words:,} palavras)

REGRAS ABSOLUTAS:
1. ❌ NÃO RESUMIR - EXPANDIR cada conceito em MÚLTIPLOS parágrafos (mínimo 5-8 parágrafos por ideia)
2. 📝 Para cada parágrafo do capítulo original, escreva MÍNIMO 2-3 parágrafos de análise
3. 💡 Para cada ideia do capítulo, escreva MÍNIMO 5-8 parágrafos de explicação detalhada
4. 📚 Adicione exemplos práticos, analogias, comparações, casos de estudo
5. 🔍 Explique o contexto, o porquê, o como, o quando, o onde, o quem, o que
6. 📊 Para cada dado/estatística: contexto + interpretação + implicações + comparações
7. 🎯 Para cada exemplo: análise completa + exemplos adicionais do mundo real
8. 🌐 Seja EXTREMAMENTE detalhado, educativo e expansivo
9. 🇧🇷 Responda em português brasileiro

⚠️ LEMBRE-SE: Se o capítulo tem {chapter_words:,} palavras, sua análise DEVE ter MÍNIMO {min_analysis_words:,} palavras!

⚡ COMECE AGORA A ANÁLISE COMPLETA, EXAUSTIVA E MUITO DETALHADA (MÍNIMO {min_analysis_words:,} palavras, ideal {max_analysis_words:,} palavras):"""

        # Adiciona contexto anterior se disponível
        if previous_context:
            user_prompt = f"""CONTEXTO DOS CAPÍTULOS ANTERIORES:
{previous_context}

---

{user_prompt}"""

        try:
            logger.debug(f"  Enviando para Gradio Space ({self.space_id})...")
            logger.debug(f"  Tamanho do prompt: {len(user_prompt):,} caracteres")
            
            analysis = await self._query(user_prompt)
            
            # Verifica se a resposta está muito curta
            analysis_words = len(analysis.split())
            chapter_words = len(chapter_content.split())
            expected_min_words = chapter_words * 5  # Mínimo 5x o tamanho do capítulo
            
            if analysis_words < expected_min_words:
                logger.warning(
                    f"  ⚠ Resposta muito curta: {analysis_words:,} palavras "
                    f"(esperado mínimo: {expected_min_words:,} palavras, "
                    f"capítulo original: {chapter_words:,} palavras)"
                )
                # Tenta solicitar mais detalhes
                continuation_prompt = f"""
⚠️ ATENÇÃO: A análise anterior foi MUITO CURTA!

Análise atual: {analysis_words:,} palavras
Capítulo original: {chapter_words:,} palavras
TAMANHO MÍNIMO OBRIGATÓRIO: {expected_min_words:,} palavras
FALTAM: {expected_min_words - analysis_words:,} palavras

❌ VOCÊ ESTÁ RESUMINDO DEMAIS! Precisa EXPANDIR MUITO MAIS!

CONTINUE e EXPANDA a análise anterior com MUITO MAIS DETALHES:
- Adicione MUITO MAIS exemplos práticos (mínimo 3-5 por conceito)
- Explique cada conceito em MUITO MAIS profundidade (5-8 parágrafos por ideia)
- Adicione MUITO MAIS casos de estudo e análises detalhadas
- Expanda as aplicações práticas com passos específicos
- Adicione MUITO MAIS contexto, explicações, analogias e comparações
- Para cada parágrafo do capítulo, escreva MÍNIMO 2-3 parágrafos de análise

Análise anterior (primeiros 2000 caracteres):
{analysis[:2000]}...

⚠️ CONTINUE AQUI COM MUITO MAIS CONTEÚDO DETALHADO (adicione pelo menos mais {expected_min_words - analysis_words:,} palavras):
- NÃO resuma - EXPANDA cada ponto
- Seja EXTREMAMENTE detalhado
- Adicione exemplos, analogias, casos práticos
- Explique tudo em profundidade"""
                
                try:
                    continuation = await self._query(continuation_prompt)
                    analysis = analysis + "\n\n" + continuation
                    logger.info(f"  ✓ Continuação adicionada: {len(continuation.split()):,} palavras extras")
                except Exception as e:
                    logger.warning(f"  ⚠ Não foi possível solicitar continuação: {e}")
            
            # Extrai o resumo para contexto dos próximos capítulos
            context_summary = self._extract_context_summary(analysis, chapter_number, chapter_title)
            
            final_words = len(analysis.split())
            logger.debug(f"  ✓ Resposta recebida: {len(analysis):,} caracteres, {final_words:,} palavras")
            
            return {
                "success": True,
                "chapter_number": chapter_number,
                "chapter_title": chapter_title,
                "analysis_md": analysis,
                "tokens_used": len(analysis.split()),  # Estimativa
                "context_summary": context_summary
            }
            
        except Exception as e:
            logger.exception(f"  ❌ Erro na análise do capítulo {chapter_number}: {e}")
            return {
                "success": False,
                "chapter_number": chapter_number,
                "chapter_title": chapter_title,
                "error": str(e),
                "tokens_used": 0,
                "context_summary": ""
            }
    
    def _extract_context_summary(self, analysis: str, chapter_number: int, chapter_title: str) -> str:
        """Extrai a síntese de contexto da análise."""
        import re
        
        patterns = [
            r'##\s*📌\s*Síntese para Continuidade\s*\n(.*?)(?=\n##|\n#|\Z)',
            r'##\s*Síntese[^\n]*\n(.*?)(?=\n##|\n#|\Z)',
            r'##\s*🎯\s*Aplicações[^\n]*\n(.*?)(?=\n##|\n#|\Z)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, analysis, re.DOTALL | re.IGNORECASE)
            if match:
                summary = match.group(1).strip()
                if len(summary) > 50:
                    return f"**Cap {chapter_number} ({chapter_title}):** {summary[:2000]}"
        
        # Fallback
        clean = re.sub(r'#.*?\n', '', analysis)[:500]
        return f"**Cap {chapter_number} ({chapter_title}):** {clean.strip()}"
    
    async def generate_book_summary(
        self,
        all_analyses: list,
        book_title: str,
        book_author: str
    ) -> str:
        """Gera conclusões gerais do livro."""
        context_summaries = []
        chapter_titles = []
        
        for analysis in all_analyses:
            if analysis.get("success"):
                chapter_titles.append(f"• Cap {analysis['chapter_number']}: {analysis['chapter_title']}")
                if analysis.get("context_summary"):
                    context_summaries.append(analysis["context_summary"])
        
        chapters_list = "\n".join(chapter_titles)
        accumulated = "\n\n".join(context_summaries[:20])
        
        prompt = f"""Você é um crítico literário experiente. Analise o livro "{book_title}" de {book_author}.

CAPÍTULOS ANALISADOS:
{chapters_list}

CONHECIMENTO ACUMULADO:
{accumulated}

Gere as CONCLUSÕES GERAIS em português brasileiro:

# 🏆 Análise Completa da Obra: "{book_title}"

## 📌 Visão Geral da Obra
## 🎯 Os Grandes Temas do Livro
## 🧠 A Tese Central do Autor
## 🛠️ Frameworks e Metodologias
## 💼 Aplicações Práticas
## 👤 Perfil do Leitor Ideal
## 🎓 Veredicto Final

Seja detalhado e analítico."""

        try:
            return await self._query(prompt)
        except Exception as e:
            return f"# Conclusões\n\nNão foi possível gerar as conclusões: {str(e)}"
    
    async def extract_glossary(self, all_analyses: list) -> str:
        """Extrai glossário de termos técnicos."""
        import re
        
        all_terms = []
        for analysis in all_analyses[:10]:
            if analysis.get("success") and analysis.get("analysis_md"):
                content = analysis["analysis_md"]
                match = re.search(r'##\s*📝?\s*Glossário[^\n]*\n(.*?)(?=\n##|\n#|\Z)', content, re.DOTALL)
                if match:
                    all_terms.append(match.group(1).strip())
        
        combined = "\n\n".join(all_terms)
        
        prompt = f"""Crie um GLOSSÁRIO TÉCNICO COMPLETO em português brasileiro a partir destes termos:

{combined}

Formato:
# 📖 Glossário Técnico Completo

## A
- **Termo** — Definição clara

## B
[continua alfabeticamente...]

Organize alfabeticamente. Mínimo 20 termos."""

        try:
            return await self._query(prompt)
        except Exception as e:
            return f"# Glossário\n\nNão foi possível gerar o glossário: {str(e)}"
