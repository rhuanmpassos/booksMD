"""Divisor de texto em capítulos."""

import re
import logging
import tiktoken
from typing import List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger("booksMD.splitter")


@dataclass
class Chapter:
    """Representa um capítulo do livro."""
    number: int
    title: str
    content: str
    start_position: int
    token_count: int


class ChapterSplitter:
    """
    Divide o texto do livro em capítulos.
    
    Detecta automaticamente padrões de capítulos ou divide por tamanho.
    """
    
    # Padrões FORTES de capítulos (mais confiáveis)
    STRONG_PATTERNS = [
        # Português - Chapter/Capítulo com número
        r'^[#\s]*Capítulo\s+(\d+)[:\.\s\-—]*(.*)$',
        r'^[#\s]*CAPÍTULO\s+(\d+)[:\.\s\-—]*(.*)$',
        r'^[#\s]*Cap\.\s*(\d+)[:\.\s\-—]*(.*)$',
        
        # Inglês - Chapter com número
        r'^[#\s]*Chapter\s+(\d+)[:\.\s\-—]*(.*)$',
        r'^[#\s]*CHAPTER\s+(\d+)[:\.\s\-—]*(.*)$',
        
        # Parte/Part com número
        r'^[#\s]*Parte\s+(\d+|[IVX]+)[:\.\s\-—]*(.*)$',
        r'^[#\s]*Part\s+(\d+|[IVX]+)[:\.\s\-—]*(.*)$',
        r'^[#\s]*PART\s+(\d+|[IVX]+)[:\.\s\-—]*(.*)$',
    ]
    
    # Padrões FRACOS (usados apenas como fallback)
    WEAK_PATTERNS = [
        # Numeração romana isolada (só no início de linha)
        r'^(I{1,3}|IV|V|VI{1,3}|IX|X|XI{1,3}|XIV|XV)\.\s+(.+)$',
        
        # Numeração simples com título longo (mínimo 20 chars de título)
        r'^(\d{1,2})\.\s+([A-Z][a-zA-Z\s]{20,})$',
    ]
    
    # Tamanho mínimo de um capítulo válido (em tokens)
    MIN_CHAPTER_TOKENS = 30  # Reduzido para não descartar capítulos curtos reais
    
    def __init__(self, max_tokens: int = 12000, overlap_tokens: int = 200):
        """
        Inicializa o splitter.
        
        Args:
            max_tokens: Máximo de tokens por chunk
            overlap_tokens: Tokens de sobreposição entre chunks
        """
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.tokenizer = tiktoken.encoding_for_model("gpt-4o")
    
    def count_tokens(self, text: str) -> int:
        """Conta tokens no texto."""
        return len(self.tokenizer.encode(text))
    
    def find_chapters(self, text: str) -> List[Tuple[int, str, int]]:
        """
        Encontra marcadores de capítulos no texto.
        
        Usa estratégia em duas fases:
        1. Primeiro tenta padrões fortes (CHAPTER X, Capítulo X)
        2. Se não encontrar, usa padrões fracos como fallback
        
        Returns:
            Lista de (número, título, posição)
        """
        # Fase 1: Tentar padrões fortes
        chapters = self._find_with_patterns(text, self.STRONG_PATTERNS)
        
        if len(chapters) >= 3:
            # Verifica qualidade dos capítulos detectados
            if self._are_chapters_valid(chapters):
                logger.debug(f"  Usando padrões fortes: {len(chapters)} capítulos")
                return chapters
            else:
                logger.debug(f"  {len(chapters)} capítulos detectados mas muitos duplicados/inválidos")
        
        # Fase 2: Fallback para padrões fracos
        logger.debug("  Padrões fortes insuficientes, tentando padrões fracos...")
        chapters = self._find_with_patterns(text, self.STRONG_PATTERNS + self.WEAK_PATTERNS)
        
        if len(chapters) >= 3:
            # Verifica qualidade novamente
            if self._are_chapters_valid(chapters):
                logger.debug(f"  Usando padrões fracos: {len(chapters)} capítulos")
                return chapters
            else:
                logger.debug(f"  {len(chapters)} capítulos detectados mas muitos duplicados/inválidos")
        
        logger.debug("  Nenhum padrão de capítulo encontrado")
        return []
    
    def _are_chapters_valid(self, chapters: List[Tuple[int, str, int]]) -> bool:
        """Verifica se os capítulos detectados são válidos (não são todos duplicatas)."""
        if len(chapters) < 3:
            return False
        
        # Conta títulos únicos
        titles = [title[:50].lower().strip() for _, title, _ in chapters]
        unique_titles = set(titles)
        
        # Se mais de 70% são duplicatas, provavelmente são falsos positivos
        uniqueness_ratio = len(unique_titles) / len(titles)
        
        if uniqueness_ratio < 0.3:
            logger.debug(f"    ⚠ Muitos títulos duplicados: {len(unique_titles)} únicos de {len(titles)} total ({uniqueness_ratio:.1%})")
            return False
        
        # Verifica se há pelo menos alguns títulos com mais de 20 caracteres
        long_titles = [t for t in titles if len(t) > 20]
        if len(long_titles) < len(titles) * 0.3:
            logger.debug(f"    ⚠ Poucos títulos longos: {len(long_titles)} de {len(titles)}")
            return False
        
        return True
    
    def _find_with_patterns(self, text: str, patterns: List[str]) -> List[Tuple[int, str, int]]:
        """Encontra capítulos usando lista de padrões."""
        chapters = []
        lines = text.split('\n')
        current_pos = 0
        chapter_num = 0
        seen_titles = set()  # Para evitar duplicatas
        last_title = None
        
        for line in lines:
            stripped = line.strip()
            
            # Ignora linhas muito curtas ou muito longas
            if len(stripped) < 5 or len(stripped) > 200:
                current_pos += len(line) + 1
                continue
            
            for pattern in patterns:
                match = re.match(pattern, stripped, re.IGNORECASE)
                if match:
                    # Tenta extrair título
                    groups = match.groups()
                    if len(groups) >= 2 and groups[1]:
                        title = groups[1].strip()
                    else:
                        title = stripped
                    
                    # Normaliza título para comparação (primeiros 50 chars, lowercase)
                    title_normalized = title[:50].lower().strip()
                    
                    # FILTRO 1: Ignora se for duplicata exata
                    if title_normalized in seen_titles:
                        continue
                    
                    # FILTRO 2: Ignora se for muito similar ao anterior (90% similaridade)
                    if last_title and self._similarity(title_normalized, last_title) > 0.9:
                        continue
                    
                    # FILTRO 3: Ignora títulos que são apenas perguntas curtas
                    if self._is_question_only(title):
                        continue
                    
                    # FILTRO 4: Verifica se o título tem conteúdo real (não só palavras comuns)
                    if not self._has_substantive_content(title):
                        continue
                    
                    chapter_num += 1
                    chapters.append((chapter_num, title, current_pos))
                    seen_titles.add(title_normalized)
                    last_title = title_normalized
                    break
            
            current_pos += len(line) + 1
        
        # FILTRO 5: Se muitos capítulos detectados, verifica se há numeração sequencial
        if len(chapters) > 50:
            chapters = self._filter_by_sequential_numbering(chapters, text)
        
        return chapters
    
    def _is_question_only(self, title: str) -> bool:
        """Verifica se o título é apenas uma pergunta curta sem contexto."""
        # Perguntas comuns que não devem ser capítulos
        question_patterns = [
            r'^Are the (customers|users|people|clients)',
            r'^Are (you|they|we)',
            r'^Do you',
            r'^Have you',
            r'^Is (this|that|it)',
            r'^What (is|are)',
            r'^How (do|does|can|will)',
            r'^Why (do|does|is|are)',
            r'^When (do|does|will|is)',
            r'^Where (do|does|is|are)',
            r'^Who (is|are|do|does)',
            r'^Which (is|are|do|does)',
        ]
        
        for pattern in question_patterns:
            if re.match(pattern, title, re.IGNORECASE):
                # Se for muito curto, provavelmente é só uma pergunta
                if len(title) < 80:
                    return True
        
        # Verifica se termina com interrogação e é curto
        if title.strip().endswith('?') and len(title) < 100:
            return True
        
        return False
    
    def _has_substantive_content(self, title: str) -> bool:
        """Verifica se o título tem conteúdo substantivo (não só palavras comuns)."""
        # Palavras muito comuns que sozinhas não indicam capítulo
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        
        words = title.lower().split()
        # Remove palavras comuns
        substantive_words = [w for w in words if w not in common_words and len(w) > 3]
        
        # Precisa ter pelo menos 2 palavras substantivas ou ser um título longo
        return len(substantive_words) >= 2 or len(title) > 40
    
    def _similarity(self, s1: str, s2: str) -> float:
        """Calcula similaridade simples entre duas strings."""
        if not s1 or not s2:
            return 0.0
        
        # Usa Jaccard similarity simples
        set1 = set(s1.split())
        set2 = set(s2.split())
        
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def _filter_by_sequential_numbering(self, chapters: List[Tuple[int, str, int]], text: str) -> List[Tuple[int, str, int]]:
        """Filtra capítulos verificando se há numeração sequencial real."""
        # Se há muitos capítulos, verifica se realmente há numeração
        numbered = []
        unnumbered = []
        
        for num, title, pos in chapters:
            # Verifica se o título ou contexto próximo tem número
            context_start = max(0, pos - 100)
            context_end = min(len(text), pos + 200)
            context = text[context_start:context_end]
            
            # Procura por padrões de numeração no contexto
            has_number = re.search(r'(?:chapter|capítulo|parte|part)\s*(\d+)', context, re.IGNORECASE)
            
            if has_number:
                numbered.append((num, title, pos))
            else:
                unnumbered.append((num, title, pos))
        
        # Se a maioria tem numeração, usa só os numerados
        if len(numbered) > len(unnumbered) * 0.5:
            logger.debug(f"  Filtrando: {len(numbered)} numerados vs {len(unnumbered)} não-numerados")
            return numbered
        
        # Se não, retorna todos mas ordena por posição e remove muito próximos
        filtered = []
        last_pos = -1000
        
        for num, title, pos in sorted(chapters, key=lambda x: x[2]):
            # Remove capítulos muito próximos (menos de 500 chars)
            if pos - last_pos < 500:
                continue
            
            filtered.append((len(filtered) + 1, title, pos))
            last_pos = pos
        
        logger.debug(f"  Após filtro de proximidade: {len(filtered)} capítulos")
        return filtered
    
    def split_by_chapters(self, text: str) -> List[Chapter]:
        """
        Divide o texto pelos capítulos detectados.
        
        Args:
            text: Texto completo do livro
            
        Returns:
            Lista de capítulos
        """
        logger.info(f"Procurando capítulos no texto ({len(text):,} caracteres)...")
        chapter_markers = self.find_chapters(text)
        
        # Se não encontrou capítulos suficientes, divide por tamanho
        if len(chapter_markers) < 3:
            logger.info(f"  Poucos marcadores encontrados ({len(chapter_markers)}), dividindo por tamanho")
            return self.split_by_size(text)
        
        logger.info(f"  Encontrados {len(chapter_markers)} marcadores de capítulo")
        
        chapters = []
        skipped = 0
        
        for i, (num, title, start) in enumerate(chapter_markers):
            # Define fim do capítulo
            if i < len(chapter_markers) - 1:
                end = chapter_markers[i + 1][2]
            else:
                end = len(text)
            
            content = text[start:end].strip()
            token_count = self.count_tokens(content)
            
            # Ignora capítulos muito pequenos (provavelmente falsos positivos)
            if token_count < self.MIN_CHAPTER_TOKENS:
                skipped += 1
                logger.debug(f"    ⏭ Ignorando '{title[:30]}...' - muito pequeno ({token_count} tokens)")
                continue
            
            chapter = Chapter(
                number=len(chapters) + 1,  # Renumera sequencialmente
                title=title[:100],
                content=content,
                start_position=start,
                token_count=token_count
            )
            
            logger.debug(f"    Cap {chapter.number}: '{title[:40]}...' - {token_count:,} tokens")
            
            # Se capítulo for muito grande, subdivide
            if token_count > self.max_tokens:
                logger.debug(f"    ⚠ Capítulo muito grande, subdividindo...")
                sub_chapters = self._split_large_chapter(chapter)
                chapters.extend(sub_chapters)
            else:
                chapters.append(chapter)
        
        # Se após filtrar ficou com poucos capítulos, divide por tamanho
        if len(chapters) < 3:
            logger.info(f"  Poucos capítulos válidos após filtro ({len(chapters)}), dividindo por tamanho")
            return self.split_by_size(text)
        
        if skipped > 0:
            logger.info(f"  Ignorados {skipped} marcadores pequenos (< {self.MIN_CHAPTER_TOKENS} tokens)")
        
        logger.info(f"  Total de capítulos válidos: {len(chapters)}")
        return chapters
    
    def split_by_size(self, text: str, base_title: str = "Seção") -> List[Chapter]:
        """
        Divide o texto por tamanho quando não há capítulos detectáveis.
        
        Args:
            text: Texto para dividir
            base_title: Título base para as seções
            
        Returns:
            Lista de capítulos/seções
        """
        chapters = []
        
        # Divide por parágrafos
        paragraphs = text.split('\n\n')
        current_chunk = []
        current_tokens = 0
        chapter_num = 0
        
        for para in paragraphs:
            para_tokens = self.count_tokens(para)
            
            # Se adicionar este parágrafo estoura o limite
            if current_tokens + para_tokens > self.max_tokens and current_chunk:
                chapter_num += 1
                content = '\n\n'.join(current_chunk)
                
                chapters.append(Chapter(
                    number=chapter_num,
                    title=f"{base_title} {chapter_num}",
                    content=content,
                    start_position=0,
                    token_count=current_tokens
                ))
                
                # Inicia novo chunk com sobreposição
                overlap_paras = self._get_overlap_paragraphs(current_chunk)
                current_chunk = overlap_paras + [para]
                current_tokens = self.count_tokens('\n\n'.join(current_chunk))
            else:
                current_chunk.append(para)
                current_tokens += para_tokens
        
        # Adiciona último chunk
        if current_chunk:
            chapter_num += 1
            content = '\n\n'.join(current_chunk)
            chapters.append(Chapter(
                number=chapter_num,
                title=f"{base_title} {chapter_num}",
                content=content,
                start_position=0,
                token_count=self.count_tokens(content)
            ))
        
        return chapters
    
    def _split_large_chapter(self, chapter: Chapter) -> List[Chapter]:
        """Divide um capítulo muito grande em partes menores."""
        sub_chapters = self.split_by_size(
            chapter.content, 
            f"{chapter.title} - Parte"
        )
        
        # Renumera as partes
        for i, sub in enumerate(sub_chapters):
            sub.number = chapter.number
            sub.title = f"{chapter.title} (Parte {i + 1}/{len(sub_chapters)})"
        
        return sub_chapters
    
    def _get_overlap_paragraphs(self, paragraphs: List[str]) -> List[str]:
        """Retorna parágrafos finais para overlap."""
        if not paragraphs:
            return []
        
        overlap = []
        tokens = 0
        
        for para in reversed(paragraphs):
            para_tokens = self.count_tokens(para)
            if tokens + para_tokens > self.overlap_tokens:
                break
            overlap.insert(0, para)
            tokens += para_tokens
        
        return overlap[-2:] if len(overlap) > 2 else overlap  # Máximo 2 parágrafos
    
    def get_book_stats(self, chapters: List[Chapter]) -> dict:
        """Retorna estatísticas do livro."""
        total_tokens = sum(c.token_count for c in chapters)
        total_words = sum(len(c.content.split()) for c in chapters)
        
        return {
            "total_chapters": len(chapters),
            "total_tokens": total_tokens,
            "total_words": total_words,
            "avg_tokens_per_chapter": total_tokens // len(chapters) if chapters else 0,
            "chapters": [
                {
                    "number": c.number,
                    "title": c.title,
                    "tokens": c.token_count
                }
                for c in chapters
            ]
        }

