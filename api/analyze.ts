// POST /api/analyze - Analisa UM capítulo com LLM
import { put, list } from '@vercel/blob';
import type { VercelRequest, VercelResponse } from '@vercel/node';

// Configuração do Gradio (mesmo do Python)
const GRADIO_SPACE = 'burak/Llama-4-Maverick-17B-Websearch';
const GRADIO_API_URL = `https://${GRADIO_SPACE.replace('/', '-')}.hf.space/api/predict`;

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { jobId, chapterIndex } = req.body;

  if (!jobId || chapterIndex === undefined) {
    return res.status(400).json({ error: 'Job ID and chapter index are required' });
  }

  try {
    // Busca metadata do job
    const { blobs: metadataBlobs } = await list({ prefix: `jobs/${jobId}/metadata.json` });
    
    if (metadataBlobs.length === 0) {
      return res.status(404).json({ error: 'Job not found' });
    }

    const metadataResponse = await fetch(metadataBlobs[0].url);
    const metadata = await metadataResponse.json();

    // Busca o capítulo
    const { blobs: chapterBlobs } = await list({ prefix: `jobs/${jobId}/chapters/${chapterIndex}.json` });
    
    if (chapterBlobs.length === 0) {
      return res.status(404).json({ error: 'Chapter not found' });
    }

    const chapterResponse = await fetch(chapterBlobs[0].url);
    const chapter = await chapterResponse.json();

    // Atualiza status
    metadata.status = 'analyzing';
    metadata.currentStep = `Analisando capítulo ${chapterIndex + 1} de ${metadata.totalChapters}...`;
    metadata.progress = 20 + (chapterIndex / metadata.totalChapters) * 60;

    await put(`jobs/${jobId}/metadata.json`, JSON.stringify(metadata), {
      access: 'public',
      contentType: 'application/json',
    });

    // Monta o prompt
    const prompt = buildAnalysisPrompt(chapter, metadata.bookMetadata);

    // Chama o LLM (Gradio)
    const analysis = await callGradioLLM(prompt);

    // Salva análise do capítulo
    await put(
      `jobs/${jobId}/analysis/${chapterIndex}.json`,
      JSON.stringify({
        chapterIndex,
        title: chapter.title,
        analysis,
        analyzedAt: new Date().toISOString(),
      }),
      { access: 'public', contentType: 'application/json' }
    );

    // Atualiza metadata
    metadata.analyzedChapters = (metadata.analyzedChapters || 0) + 1;
    if (metadata.chapters[chapterIndex]) {
      metadata.chapters[chapterIndex].analyzed = true;
    }

    // Verifica se terminou
    if (metadata.analyzedChapters >= metadata.totalChapters) {
      metadata.status = 'generating';
      metadata.currentStep = 'Gerando documento final...';
      metadata.progress = 85;
    }

    await put(`jobs/${jobId}/metadata.json`, JSON.stringify(metadata), {
      access: 'public',
      contentType: 'application/json',
    });

    return res.status(200).json({
      success: true,
      chapterIndex,
      analyzedChapters: metadata.analyzedChapters,
      totalChapters: metadata.totalChapters,
      completed: metadata.analyzedChapters >= metadata.totalChapters,
    });

  } catch (error: any) {
    console.error('Analyze error:', error);
    return res.status(500).json({ 
      error: 'Analysis failed', 
      message: error.message 
    });
  }
}

// Monta prompt de análise
function buildAnalysisPrompt(chapter: any, bookMetadata: any): string {
  return `Você é um especialista em análise literária. Analise o seguinte capítulo do livro "${bookMetadata?.title || 'Desconhecido'}".

## Capítulo: ${chapter.title}

${chapter.content.substring(0, 8000)}

---

Por favor, forneça uma análise detalhada incluindo:

1. **Resumo**: Um resumo conciso do capítulo (2-3 parágrafos)
2. **Temas Principais**: Os principais temas abordados
3. **Conceitos-Chave**: Conceitos importantes introduzidos ou desenvolvidos
4. **Pontos de Destaque**: Citações ou passagens importantes
5. **Conexões**: Como este capítulo se relaciona com temas mais amplos

Responda em Markdown formatado.`;
}

// Chama Gradio LLM
async function callGradioLLM(prompt: string): Promise<string> {
  try {
    // Tenta Gradio Space
    const response = await fetch(GRADIO_API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        data: [prompt, [], ''],
        fn_index: 0,
      }),
    });

    if (response.ok) {
      const result = await response.json();
      if (result.data && result.data[0]) {
        return result.data[0];
      }
    }

    // Fallback: retorna análise básica
    return generateFallbackAnalysis(prompt);
  } catch (error) {
    console.error('Gradio error:', error);
    return generateFallbackAnalysis(prompt);
  }
}

// Análise fallback se LLM falhar
function generateFallbackAnalysis(prompt: string): string {
  return `## Análise do Capítulo

*Análise automática gerada.*

O capítulo apresenta conteúdo relevante para o tema do livro. 
Uma análise mais detalhada requer processamento manual.

---

*Nota: A análise por IA não estava disponível no momento do processamento.*`;
}

