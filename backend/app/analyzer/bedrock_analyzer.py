"""Analisador de livros com Amazon Bedrock."""

from dotenv import load_dotenv
load_dotenv()  # Carrega variáveis de ambiente do arquivo .env

import logging
import json
import asyncio
from typing import Optional
import boto3
from botocore.exceptions import ClientError
from ..config import get_settings

logger = logging.getLogger("booksMD.analyzer.bedrock")


class BedrockAnalyzer:
    """
    Analisa capítulos de livros usando Amazon Bedrock.
    
    Modelo: meta.llama4-maverick-17b-instruct-v1:0
    """
    
    SYSTEM_PROMPT = """Você é um PROFESSOR UNIVERSITÁRIO DE ELITE e ANALISTA DE NEGÓCIOS com 30 anos de experiência, especialista em transformar livros complexos em conhecimento profundo e aplicável.

🎯 SUA MISSÃO: Criar uma AULA COMPLETA sobre este capítulo - não um resumo, mas uma EXPLICAÇÃO EXAUSTIVA que ensina TUDO.

═══════════════════════════════════════════════════════════════════
📌 PRINCÍPIOS FUNDAMENTAIS (NUNCA VIOLE)
═══════════════════════════════════════════════════════════════════

1. ❌ PROIBIDO RESUMIR: Você NÃO está resumindo. Está ENSINANDO. Cada conceito deve ser EXPANDIDO, não condensado.

2. 📖 COBERTURA TOTAL: Analise CADA parágrafo, CADA ideia, CADA exemplo do capítulo. Nada pode ser ignorado.

3. 🎓 PROFUNDIDADE MÁXIMA: Explique como se o leitor fosse um novato inteligente que quer DOMINAR o assunto.

4. 🌐 TRADUÇÃO INTELIGENTE: Traduza para português brasileiro fluente, mas MANTENHA termos técnicos em inglês entre parênteses quando relevante.

5. 🔗 CONEXÕES OBRIGATÓRIAS: Se houver contexto de capítulos anteriores, INTEGRE as ideias mostrando evolução e conexões.

6. 💼 APLICAÇÃO REAL: Para CADA conceito importante, explique COMO e QUANDO usar no mundo real.

═══════════════════════════════════════════════════════════════════
📋 ESTRUTURA OBRIGATÓRIA DA ANÁLISE
═══════════════════════════════════════════════════════════════════

## 📖 Contexto e Propósito do Capítulo
- Por que este capítulo existe na obra?
- Qual problema ele resolve?
- Como se conecta com o que veio antes (se houver contexto anterior)?
- O que o leitor PRECISA entender antes de prosseguir?

## 🧠 Análise Profunda das Ideias Centrais

### 💡 [Nome da Primeira Ideia Principal]
[Explique a ideia em 3-5 parágrafos densos. Inclua:]
- O que é exatamente
- Por que é importante
- Como funciona na prática
- Exemplos concretos do livro
- Exemplos adicionais do mundo real
- Erros comuns ao aplicar
- Como saber se está funcionando

### 💡 [Nome da Segunda Ideia Principal]
[Repita a estrutura acima para CADA ideia importante]

[Continue para TODAS as ideias do capítulo - não limite o número]

## 🛠️ Frameworks, Metodologias e Ferramentas
[Se o capítulo apresentar qualquer framework, processo, metodologia ou ferramenta:]
- Descreva CADA etapa em detalhes
- Explique o PORQUÊ de cada etapa
- Dê exemplos de aplicação
- Liste os erros mais comuns
- Inclua métricas de sucesso quando aplicável

## 📊 Dados, Estatísticas e Evidências
[Liste TODOS os dados mencionados no capítulo:]
- Estatísticas citadas (com fontes se mencionadas)
- Resultados de estudos
- Métricas de sucesso/fracasso
- Benchmarks da indústria

## 🏢 Casos de Estudo e Exemplos do Livro
[Para CADA empresa/pessoa/caso mencionado:]
- Contexto completo
- O que fizeram
- Resultados obtidos
- Lições extraídas
- Como aplicar ao seu caso

## 🔗 Conexões com Capítulos Anteriores
[Se houver contexto anterior - OBRIGATÓRIO conectar:]
- Como este capítulo EXPANDE ideias anteriores
- Contradições ou evoluções de conceitos
- Padrões que se repetem
- Construção do argumento geral do livro

## 🎯 Aplicações Práticas Imediatas
[Liste ações ESPECÍFICAS que o leitor pode tomar:]
- Passo a passo de implementação
- Recursos necessários
- Timeline sugerida
- Métricas para acompanhar
- Sinais de sucesso/fracasso

## 📝 Glossário Técnico do Capítulo
[Para CADA termo técnico, jargão ou conceito específico:]
**Termo Original (se inglês)** → Tradução Brasileira
- Definição completa em 2-3 frases
- Exemplo prático de uso
- Termos relacionados

## ⚠️ Armadilhas e Erros Comuns
[Liste os erros que pessoas cometem ao aplicar estes conceitos:]
- O erro
- Por que acontece
- Como evitar
- O que fazer se já cometeu

## 💎 Insights Não Óbvios
[Extraia percepções sutis que um leitor casual perderia:]
- Implicações de segundo/terceiro grau
- Conexões com outras áreas
- Aplicações não mencionadas pelo autor

## 📌 Síntese para Continuidade
[3-5 frases com os pontos ESSENCIAIS que conectam com próximos capítulos - usado para contexto acumulativo]

═══════════════════════════════════════════════════════════════════
⚡ REGRAS DE QUALIDADE
═══════════════════════════════════════════════════════════════════

✅ FAÇA:
- Escreva como um professor apaixonado pelo assunto
- Use exemplos de empresas reais (Google, Amazon, startups conhecidas)
- Inclua números e métricas quando disponíveis
- Formate com Markdown impecável
- Use emojis estrategicamente para navegação visual
- Mantenha tom profissional mas acessível
- Cite autores e fontes mencionadas no livro

❌ NÃO FAÇA:
- NÃO resuma superficialmente
- NÃO pule ideias "menores"
- NÃO use frases genéricas como "é importante considerar"
- NÃO deixe conceitos sem explicação completa
- NÃO ignore o contexto de capítulos anteriores
- NÃO invente informações não presentes no texto

🌟 LEMBRE-SE: Você está criando um MATERIAL DE ESTUDO COMPLETO que substitui a necessidade de ler o capítulo original. O leitor deve APRENDER TUDO sem perder NADA."""

    def __init__(
        self,
        model: str = "meta.llama4-maverick-17b-instruct-v1:0",
        region_name: str = "us-east-1",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None
    ):
        """
        Inicializa o analisador.
        
        Args:
            model: ID do modelo no Bedrock
            region_name: Região AWS
            aws_access_key_id: AWS Access Key ID (opcional, pode usar credenciais padrão)
            aws_secret_access_key: AWS Secret Access Key (opcional, pode usar credenciais padrão)
        """
        self.model = model
        self.region_name = region_name
        settings = get_settings()
        
        # Usa credenciais das settings ou do construtor
        self.aws_access_key_id = aws_access_key_id or settings.bedrock_aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key or settings.bedrock_aws_secret_access_key
        
        # Cria cliente Bedrock Runtime
        client_kwargs = {"region_name": self.region_name}
        if self.aws_access_key_id and self.aws_secret_access_key:
            client_kwargs.update({
                "aws_access_key_id": self.aws_access_key_id,
                "aws_secret_access_key": self.aws_secret_access_key
            })
        
        self.client = boto3.client("bedrock-runtime", **client_kwargs)
        
        logger.info(f"Inicializando BedrockAnalyzer")
        logger.info(f"  Modelo: {model}")
        logger.info(f"  Região: {region_name}")
    
    def _is_anthropic_model(self) -> bool:
        """Verifica se o modelo é da Anthropic (Claude)."""
        return "anthropic" in self.model.lower() or "claude" in self.model.lower()
    
    def _is_meta_model(self) -> bool:
        """Verifica se o modelo é da Meta (Llama)."""
        return "meta" in self.model.lower() or "llama" in self.model.lower()
    
    def _format_body(self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float) -> dict:
        """
        Formata o body do request de acordo com o modelo.
        
        Claude (Anthropic) e Llama (Meta) usam formatos diferentes.
        """
        if self._is_anthropic_model():
            # Formato para Claude (Anthropic) - Messages API
            return {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": 0.9,
                "system": system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ]
            }
        elif self._is_meta_model():
            # Formato para Llama (Meta)
            return {
                "prompt": f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{user_prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n",
                "max_gen_len": max_tokens,
                "temperature": temperature,
                "top_p": 0.9
            }
        else:
            # Formato genérico (fallback)
            return {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": 0.9
            }
    
    async def _invoke_model(self, system_prompt: str, user_prompt: str, max_tokens: int = 4000, temperature: float = 0.4) -> dict:
        """
        Invoca o modelo via Bedrock Runtime API.
        
        Args:
            system_prompt: Prompt do sistema
            user_prompt: Prompt do usuário
            max_tokens: Máximo de tokens na resposta
            temperature: Temperatura para geração
            
        Returns:
            Resposta do modelo
        """
        # Formata o body de acordo com o modelo
        body = self._format_body(system_prompt, user_prompt, max_tokens, temperature)
        
        try:
            # Executa em thread separada para não bloquear
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.invoke_model(
                    modelId=self.model,
                    body=json.dumps(body),
                    contentType="application/json",
                    accept="application/json"
                )
            )
            
            # Lê e parseia a resposta
            response_body = json.loads(response["body"].read())
            
            # Extrai o conteúdo da resposta de acordo com o modelo
            text = ""
            tokens_used = 0
            
            if self._is_anthropic_model():
                # Formato de resposta do Claude (Anthropic)
                # {"content": [{"type": "text", "text": "..."}], "usage": {...}}
                if "content" in response_body:
                    content = response_body["content"]
                    if isinstance(content, list) and len(content) > 0:
                        # Claude retorna lista de blocos de conteúdo
                        text_parts = []
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                text_parts.append(block.get("text", ""))
                            elif isinstance(block, dict) and "text" in block:
                                text_parts.append(block.get("text", ""))
                            elif isinstance(block, str):
                                text_parts.append(block)
                        text = "".join(text_parts)
                    elif isinstance(content, str):
                        text = content
                
                # Extrai uso de tokens do Claude
                usage = response_body.get("usage", {})
                if usage:
                    input_tokens = usage.get("input_tokens", 0)
                    output_tokens = usage.get("output_tokens", 0)
                    tokens_used = input_tokens + output_tokens
            
            elif self._is_meta_model():
                # Formato de resposta do Llama (Meta)
                # {"generation": "...", "prompt_token_count": X, "generation_token_count": Y}
                text = response_body.get("generation", "")
                prompt_tokens = response_body.get("prompt_token_count", 0)
                gen_tokens = response_body.get("generation_token_count", 0)
                tokens_used = prompt_tokens + gen_tokens
            
            else:
                # Formato genérico (fallback)
                if "content" in response_body:
                    content = response_body["content"]
                    if isinstance(content, list) and len(content) > 0:
                        first_item = content[0]
                        if isinstance(first_item, dict):
                            text = first_item.get("text", "")
                        else:
                            text = str(first_item)
                    elif isinstance(content, str):
                        text = content
                elif "completion" in response_body:
                    text = response_body["completion"]
                elif "generation" in response_body:
                    text = response_body["generation"]
                else:
                    logger.warning(f"  ⚠ Formato de resposta não reconhecido: {list(response_body.keys())}")
                    text = str(response_body)
                
                usage = response_body.get("usage", {})
                if usage:
                    tokens_used = usage.get("total_tokens", 0) or usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
            
            # Se não encontrou tokens, tenta estimar pelo tamanho do texto
            if tokens_used == 0 and text:
                tokens_used = len(text.split())  # Estimativa aproximada
            
            return {
                "text": text,
                "tokens_used": tokens_used,
                "raw_response": response_body
            }
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_msg = e.response.get("Error", {}).get("Message", str(e))
            
            if error_code == "ThrottlingException":
                logger.warning(f"  ⚠ Rate limit atingido, aguardando 10s...")
                await asyncio.sleep(10)
                return await self._invoke_model(messages, max_tokens, temperature)
            
            logger.error(f"  ❌ Erro do Bedrock ({error_code}): {error_msg}")
            raise Exception(f"Erro do Bedrock: {error_code} - {error_msg}")
    
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
        # Monta o prompt base
        user_prompt = f"""═══════════════════════════════════════════════════════════════════
📚 CAPÍTULO {chapter_number}: {chapter_title}
═══════════════════════════════════════════════════════════════════

{chapter_content}

═══════════════════════════════════════════════════════════════════
🎯 INSTRUÇÕES PARA ESTA ANÁLISE
═══════════════════════════════════════════════════════════════════

1. Analise CADA parágrafo do capítulo acima
2. Siga TODA a estrutura obrigatória do system prompt
3. NÃO resuma - ENSINE e EXPANDA cada conceito
4. Inclua TODOS os exemplos, casos e dados mencionados
5. Responda COMPLETAMENTE em português brasileiro
6. Mantenha termos técnicos em inglês entre parênteses quando relevante

⚡ COMECE A ANÁLISE COMPLETA AGORA:"""

        # Adiciona contexto anterior se disponível
        if previous_context:
            user_prompt = f"""═══════════════════════════════════════════════════════════════════
🔗 CONTEXTO ACUMULADO DOS CAPÍTULOS ANTERIORES
═══════════════════════════════════════════════════════════════════

{previous_context}

═══════════════════════════════════════════════════════════════════
⚠️ ATENÇÃO: Você DEVE fazer conexões explícitas com os capítulos anteriores!
- Mostre como as ideias EVOLUEM
- Identifique PADRÕES que se repetem
- Conecte frameworks e conceitos relacionados
═══════════════════════════════════════════════════════════════════

{user_prompt}"""

        try:
            logger.debug(f"  Enviando para Bedrock ({self.model})...")
            logger.debug(f"  Tamanho do prompt: {len(user_prompt):,} caracteres")
            
            # Aumenta max_tokens para análises detalhadas
            result = await self._invoke_model(
                system_prompt=self.SYSTEM_PROMPT,
                user_prompt=user_prompt,
                max_tokens=16000,
                temperature=0.4
            )
            
            analysis = result["text"]
            tokens_used = result.get("tokens_used", 0)
            
            # Extrai o resumo para contexto dos próximos capítulos
            context_summary = self._extract_context_summary(analysis, chapter_number, chapter_title)
            
            logger.debug(f"  ✓ Resposta recebida: {len(analysis):,} caracteres, {tokens_used} tokens")
            
            return {
                "success": True,
                "chapter_number": chapter_number,
                "chapter_title": chapter_title,
                "analysis_md": analysis,
                "tokens_used": tokens_used,
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
        """
        Extrai a síntese de contexto da análise para usar nos próximos capítulos.
        
        Procura pela seção "📌 Síntese para Continuidade" ou alternativas.
        """
        import re
        
        # Tenta encontrar a seção de síntese para continuidade
        patterns = [
            r'##\s*📌\s*Síntese para Continuidade\s*\n(.*?)(?=\n##|\n#|\Z)',
            r'##\s*Síntese para Continuidade\s*\n(.*?)(?=\n##|\n#|\Z)',
            r'##\s*📊\s*Resumo para Contexto\s*\n(.*?)(?=\n##|\n#|\Z)',
            r'##\s*🎯\s*Aplicações Práticas[^\n]*\n(.*?)(?=\n##|\n#|\Z)',
            r'##\s*💎\s*Insights[^\n]*\n(.*?)(?=\n##|\n#|\Z)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, analysis, re.DOTALL | re.IGNORECASE)
            if match:
                summary = match.group(1).strip()
                if len(summary) > 50:
                    summary = summary[:8000]
                    return f"**Cap {chapter_number} ({chapter_title}):** {summary}"
        
        # Fallback: extrai do contexto e propósito
        vision_match = re.search(r'##\s*📖?\s*Contexto e Propósito[^\n]*\n(.*?)(?=\n##|\Z)', analysis, re.DOTALL)
        if vision_match:
            summary = vision_match.group(1).strip()[:5000]
            return f"**Cap {chapter_number} ({chapter_title}):** {summary}"
        
        # Fallback: Análise profunda das ideias
        ideas_match = re.search(r'##\s*🧠?\s*Análise Profunda[^\n]*\n(.*?)(?=\n##|\Z)', analysis, re.DOTALL)
        if ideas_match:
            summary = ideas_match.group(1).strip()[:5000]
            return f"**Cap {chapter_number} ({chapter_title}):** {summary}"
        
        # Último fallback: primeiras 500 chars da análise
        clean_analysis = re.sub(r'#.*?\n', '', analysis)[:500]
        return f"**Cap {chapter_number} ({chapter_title}):** {clean_analysis.strip()}"
    
    async def generate_book_summary(
        self,
        all_analyses: list,
        book_title: str,
        book_author: str
    ) -> str:
        """
        Gera conclusões gerais profundas do livro usando os contextos acumulados.
        """
        # Coleta sínteses de contexto de todos os capítulos
        context_summaries = []
        chapter_titles = []
        
        for analysis in all_analyses:
            if analysis.get("success"):
                chapter_titles.append(f"• Cap {analysis['chapter_number']}: {analysis['chapter_title']}")
                if analysis.get("context_summary"):
                    context_summaries.append(analysis["context_summary"])
        
        chapters_list = "\n".join(chapter_titles)
        accumulated_knowledge = "\n\n".join(context_summaries[:100])
        
        prompt = f"""═══════════════════════════════════════════════════════════════════
🎯 MISSÃO: CRIAR CONCLUSÕES DEFINITIVAS DO LIVRO
═══════════════════════════════════════════════════════════════════

📚 LIVRO: "{book_title}"
✍️ AUTOR: {book_author}

═══════════════════════════════════════════════════════════════════
📋 ESTRUTURA DOS CAPÍTULOS ANALISADOS
═══════════════════════════════════════════════════════════════════

{chapters_list}

═══════════════════════════════════════════════════════════════════
🧠 CONHECIMENTO ACUMULADO DE TODOS OS CAPÍTULOS
═══════════════════════════════════════════════════════════════════

{accumulated_knowledge}

═══════════════════════════════════════════════════════════════════
📝 INSTRUÇÕES PARA AS CONCLUSÕES
═══════════════════════════════════════════════════════════════════

Crie uma análise COMPLETA e PROFUNDA do livro em português brasileiro.
NÃO resuma - ANALISE e SINTETIZE com profundidade.

ESTRUTURA OBRIGATÓRIA:

# 🏆 Análise Completa da Obra: "{book_title}"

## 📌 Visão Geral da Obra
[3-4 parágrafos explicando o que o livro ensina, sua abordagem única e por que é relevante]

## 🎯 Os Grandes Temas do Livro
[Para cada tema principal, explique em detalhes:]
### Tema 1: [Nome]
- O que é
- Por que importa
- Como se manifesta nos capítulos

## 🧠 A Tese Central do Autor
[Qual é o argumento principal? Como ele constrói esse argumento ao longo do livro?]

## 🔗 Arquitetura do Livro: Como os Capítulos se Conectam
[Mostre como os capítulos constroem um argumento coerente - não liste, EXPLIQUE as conexões]

## 🛠️ Frameworks e Metodologias Apresentados
[Liste TODOS os frameworks/métodos do livro com explicação de uso]

## 💼 Aplicações Práticas Imediatas
[Lista de ações específicas que o leitor pode tomar AMANHÃ:]
1. [Ação específica] - Como fazer - Resultado esperado
2. ...

## 📊 Métricas e Indicadores Mencionados
[Todos os KPIs, métricas e formas de medir sucesso mencionados no livro]

## 👤 Perfil do Leitor Ideal
[Quem MAIS se beneficia? Quem NÃO deveria ler? Por quê?]

## ⚖️ Análise Crítica: Forças e Limitações
### Pontos Fortes:
[O que o livro faz excepcionalmente bem]
### Limitações:
[O que poderia ser melhor ou está desatualizado]
### Comparação com Outras Obras:
[Como se compara a livros similares]

## 💎 Insights Únicos desta Obra
[Ideias que você NÃO encontraria facilmente em outros livros]

## 📖 Ideias e Frases Memoráveis
[Conceitos marcantes que ficam na memória]

## 🎓 Veredicto Final
[Avaliação honesta: para quem, quando ler, como usar]

═══════════════════════════════════════════════════════════════════
⚡ COMECE AS CONCLUSÕES COMPLETAS AGORA:
═══════════════════════════════════════════════════════════════════"""

        system_prompt = "Você é um CRÍTICO LITERÁRIO DE ELITE e CONSULTOR DE NEGÓCIOS com décadas de experiência. Suas análises são profundas, perspicazes e extremamente úteis. Você NUNCA resume superficialmente - você ANALISA com profundidade. Sempre em português brasileiro impecável."

        try:
            result = await self._invoke_model(
                system_prompt=system_prompt,
                user_prompt=prompt,
                max_tokens=8000,
                temperature=0.5
            )
            
            return result["text"]
            
        except Exception as e:
            return f"# Conclusões\n\nNão foi possível gerar as conclusões: {str(e)}"
    
    async def extract_glossary(self, all_analyses: list) -> str:
        """
        Extrai um glossário completo de termos técnicos de todas as análises.
        """
        import re
        
        # Extrai seções de termos técnicos de todas as análises
        all_terms_sections = []
        
        for analysis in all_analyses:
            if analysis.get("success") and analysis.get("analysis_md"):
                content = analysis["analysis_md"]
                
                # Tenta extrair a seção de glossário técnico
                terms_match = re.search(
                    r'##\s*📝?\s*Glossário Técnico[^\n]*\n(.*?)(?=\n##|\n#|\Z)', 
                    content, 
                    re.DOTALL | re.IGNORECASE
                )
                if terms_match:
                    all_terms_sections.append(terms_match.group(1).strip())
                else:
                    # Fallback: termos técnicos traduzidos
                    terms_match = re.search(
                        r'##\s*📝?\s*Termos Técnicos[^\n]*\n(.*?)(?=\n##|\n#|\Z)', 
                        content, 
                        re.DOTALL | re.IGNORECASE
                    )
                    if terms_match:
                        all_terms_sections.append(terms_match.group(1).strip())
        
        # Combina até 15 seções
        combined = "\n\n---\n\n".join(all_terms_sections[:15])
        
        prompt = f"""═══════════════════════════════════════════════════════════════════
🎯 MISSÃO: CRIAR GLOSSÁRIO TÉCNICO DEFINITIVO
═══════════════════════════════════════════════════════════════════

Analise TODOS os termos técnicos abaixo e crie um glossário COMPLETO e PROFISSIONAL:

{combined}

═══════════════════════════════════════════════════════════════════
📋 ESTRUTURA DO GLOSSÁRIO
═══════════════════════════════════════════════════════════════════

# 📖 Glossário Técnico Completo

## A
- **Termo em Inglês** (Tradução Brasileira) — Definição completa em 2-3 frases explicando o que é, quando usar e por que é importante. *Exemplo de uso: [exemplo prático]*

## B
[continua alfabeticamente...]

═══════════════════════════════════════════════════════════════════
⚡ REGRAS OBRIGATÓRIAS
═══════════════════════════════════════════════════════════════════

1. ✅ Organize ESTRITAMENTE em ordem ALFABÉTICA
2. ✅ Inclua TODOS os termos técnicos (mínimo 25-30 termos)
3. ✅ Para termos em inglês: **Termo (Tradução)** — Definição
4. ✅ Cada definição deve ter 2-3 frases + exemplo quando possível
5. ✅ Inclua termos de: negócios, marketing, tecnologia, finanças, psicologia
6. ✅ NÃO repita termos - consolide se aparecer múltiplas vezes
7. ✅ Agrupe por letra (## A, ## B, etc.)

═══════════════════════════════════════════════════════════════════
⚡ CRIE O GLOSSÁRIO COMPLETO AGORA:
═══════════════════════════════════════════════════════════════════"""

        system_prompt = "Você é um LEXICÓGRAFO ESPECIALISTA em glossários técnicos de negócios e tecnologia. Cria glossários completos, bem organizados e extremamente úteis. Cada termo deve ser explicado de forma clara e com exemplos práticos. Sempre em português brasileiro impecável."

        try:
            result = await self._invoke_model(
                system_prompt=system_prompt,
                user_prompt=prompt,
                max_tokens=5000,
                temperature=0.4
            )
            
            return result["text"]
            
        except Exception as e:
            return f"# Glossário\n\nNão foi possível gerar o glossário: {str(e)}"

