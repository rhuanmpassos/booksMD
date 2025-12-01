"""Analisador de livros com Ollama (modelos locais)."""

from dotenv import load_dotenv
load_dotenv()  # Carrega variáveis de ambiente do arquivo .env

import logging
import ollama
from typing import Optional
import asyncio
from ..config import get_settings

logger = logging.getLogger("booksMD.analyzer.ollama")


class OllamaAnalyzer:
    """
    Analisa capítulos de livros usando modelos locais via Ollama.
    
    Modelos recomendados:
    - llama3.1:8b - Bom equilíbrio entre qualidade e velocidade
    - mistral - Rápido e eficiente
    - mixtral - Mais potente (requer mais VRAM)
    - qwen2.5:14b - Excelente para português
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

    def __init__(self, model: str = "llama3.1:8b", host: str = "http://localhost:11434"):
        """
        Inicializa o analisador.
        
        Args:
            model: Nome do modelo Ollama
            host: URL do servidor Ollama
        """
        self.model = model
        self.host = host
        logger.info(f"Inicializando OllamaAnalyzer")
        logger.info(f"  Modelo: {model}")
        logger.info(f"  Host: {host}")
        self.client = ollama.Client(host=host)
    
    def _check_model_available(self) -> bool:
        """Verifica se o modelo está disponível."""
        try:
            logger.debug(f"Verificando disponibilidade do modelo {self.model}...")
            models = self.client.list()
            
            # A API do Ollama pode retornar 'models' como lista de objetos ou dicionários
            models_list = models.get('models', [])
            available = []
            for m in models_list:
                # Suporta tanto objeto quanto dicionário
                if hasattr(m, 'model'):
                    available.append(m.model)
                elif isinstance(m, dict) and 'name' in m:
                    available.append(m['name'])
                elif isinstance(m, dict) and 'model' in m:
                    available.append(m['model'])
            
            logger.debug(f"  Modelos disponíveis: {available}")
            
            # Verifica se o modelo ou variante está disponível
            for m in available:
                if self.model in m or m in self.model:
                    logger.debug(f"  ✓ Modelo {self.model} encontrado")
                    return True
            logger.warning(f"  ✗ Modelo {self.model} NÃO encontrado")
            return False
        except Exception as e:
            logger.error(f"  Erro ao verificar modelos: {e}")
            return False
    
    def _pull_model_if_needed(self):
        """Baixa o modelo se não estiver disponível."""
        if not self._check_model_available():
            logger.info(f"📥 Baixando modelo {self.model}... Isso pode demorar.")
            try:
                self.client.pull(self.model)
                logger.info(f"✅ Modelo {self.model} baixado com sucesso!")
            except Exception as e:
                logger.error(f"❌ Erro ao baixar modelo: {e}")
                raise RuntimeError(f"Erro ao baixar modelo: {e}")
    
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
        # Verifica/baixa modelo
        self._pull_model_if_needed()
        
        # Limite removido para A100 80GB - processa capítulos completos
        # max_chars = 5000000  # ~1.25M tokens - praticamente sem limite
        # if len(chapter_content) > max_chars:
        #     logger.debug(f"  ⚠ Conteúdo truncado de {len(chapter_content):,} para {max_chars:,} caracteres")
        #     chapter_content = chapter_content[:max_chars] + "\n\n[... conteúdo truncado para caber no contexto ...]"
        
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

        # Adiciona contexto anterior se disponível (para conexões entre capítulos)
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
            logger.debug(f"  Enviando para Ollama ({self.model})...")
            logger.debug(f"  Tamanho do prompt: {len(user_prompt):,} caracteres")
            
            # Executa em thread separada para não bloquear
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    options={
                        "temperature": 0.4,  # Mais focado e consistente
                        "num_predict": 16000,  # Aumentado para A100 80GB - análises MUITO detalhadas
                        "top_p": 0.9,
                        "repeat_penalty": 1.1,  # Evita repetições
                    }
                )
            )
            
            analysis = response['message']['content']
            tokens_used = response.get('eval_count', 0)
            
            # Extrai o resumo para contexto dos próximos capítulos
            context_summary = self._extract_context_summary(analysis, chapter_number, chapter_title)
            
            logger.debug(f"  ✓ Resposta recebida: {len(analysis):,} caracteres, {tokens_used} tokens")
            
            return {
                "success": True,
                "chapter_number": chapter_number,
                "chapter_title": chapter_title,
                "analysis_md": analysis,
                "tokens_used": tokens_used,
                "context_summary": context_summary  # Novo: resumo para próximos capítulos
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
        
        # Tenta encontrar a seção de síntese para continuidade (nova estrutura)
        patterns = [
            r'##\s*📌\s*Síntese para Continuidade\s*\n(.*?)(?=\n##|\n#|\Z)',
            r'##\s*Síntese para Continuidade\s*\n(.*?)(?=\n##|\n#|\Z)',
            r'##\s*📊\s*Resumo para Contexto\s*\n(.*?)(?=\n##|\n#|\Z)',  # Compatibilidade
            r'##\s*🎯\s*Aplicações Práticas[^\n]*\n(.*?)(?=\n##|\n#|\Z)',
            r'##\s*💎\s*Insights[^\n]*\n(.*?)(?=\n##|\n#|\Z)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, analysis, re.DOTALL | re.IGNORECASE)
            if match:
                summary = match.group(1).strip()
                if len(summary) > 50:  # Síntese válida
                    # Limite aumentado para A100 80GB - contexto rico
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

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "Você é um CRÍTICO LITERÁRIO DE ELITE e CONSULTOR DE NEGÓCIOS com décadas de experiência. Suas análises são profundas, perspicazes e extremamente úteis. Você NUNCA resume superficialmente - você ANALISA com profundidade. Sempre em português brasileiro impecável."},
                        {"role": "user", "content": prompt}
                    ],
                    options={"temperature": 0.5, "num_predict": 8000, "repeat_penalty": 1.1}
                )
            )
            
            return response['message']['content']
            
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
                
                # Tenta extrair a seção de glossário técnico (nova estrutura)
                terms_match = re.search(
                    r'##\s*📝?\s*Glossário Técnico[^\n]*\n(.*?)(?=\n##|\n#|\Z)', 
                    content, 
                    re.DOTALL | re.IGNORECASE
                )
                if terms_match:
                    all_terms_sections.append(terms_match.group(1).strip())
                else:
                    # Fallback: termos técnicos traduzidos (estrutura antiga)
                    terms_match = re.search(
                        r'##\s*📝?\s*Termos Técnicos[^\n]*\n(.*?)(?=\n##|\n#|\Z)', 
                        content, 
                        re.DOTALL | re.IGNORECASE
                    )
                    if terms_match:
                        all_terms_sections.append(terms_match.group(1).strip())
        
        # Combina até 15 seções para A100 80GB
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

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "Você é um LEXICÓGRAFO ESPECIALISTA em glossários técnicos de negócios e tecnologia. Cria glossários completos, bem organizados e extremamente úteis. Cada termo deve ser explicado de forma clara e com exemplos práticos. Sempre em português brasileiro impecável."},
                        {"role": "user", "content": prompt}
                    ],
                    options={"temperature": 0.4, "num_predict": 5000, "repeat_penalty": 1.15}
                )
            )
            
            return response['message']['content']
            
        except Exception as e:
            return f"# Glossário\n\nNão foi possível gerar o glossário: {str(e)}"

