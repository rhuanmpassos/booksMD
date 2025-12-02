// POST /api/generate - Gera o documento Markdown final
import { put, list } from '@vercel/blob';
import type { VercelRequest, VercelResponse } from '@vercel/node';

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

  const { jobId } = req.body;

  if (!jobId) {
    return res.status(400).json({ error: 'Job ID is required' });
  }

  try {
    // Busca metadata do job
    const { blobs: metadataBlobs } = await list({ prefix: `jobs/${jobId}/metadata.json` });
    
    if (metadataBlobs.length === 0) {
      return res.status(404).json({ error: 'Job not found' });
    }

    const metadataResponse = await fetch(metadataBlobs[0].url);
    const metadata = await metadataResponse.json();

    // Atualiza status
    metadata.status = 'generating';
    metadata.currentStep = 'Gerando documento Markdown...';
    metadata.progress = 90;

    await put(`jobs/${jobId}/metadata.json`, JSON.stringify(metadata), {
      access: 'public',
      contentType: 'application/json',
    });

    // Busca todas as análises
    const { blobs: analysisBlobs } = await list({ prefix: `jobs/${jobId}/analysis/` });
    
    const analyses: any[] = [];
    for (const blob of analysisBlobs) {
      const response = await fetch(blob.url);
      const analysis = await response.json();
      analyses.push(analysis);
    }

    // Ordena por índice
    analyses.sort((a, b) => a.chapterIndex - b.chapterIndex);

    // Gera Markdown
    const markdown = generateMarkdown(metadata, analyses);

    // Salva o arquivo Markdown
    const filename = `${metadata.bookMetadata?.title || 'analise'}_analise.md`;
    const blob = await put(
      `outputs/${jobId}/${filename}`,
      markdown,
      { access: 'public', contentType: 'text/markdown' }
    );

    // Atualiza metadata
    metadata.status = 'completed';
    metadata.currentStep = 'Concluído!';
    metadata.progress = 100;
    metadata.outputUrl = blob.url;
    metadata.outputFilename = filename;
    metadata.completedAt = new Date().toISOString();

    await put(`jobs/${jobId}/metadata.json`, JSON.stringify(metadata), {
      access: 'public',
      contentType: 'application/json',
    });

    return res.status(200).json({
      success: true,
      outputUrl: blob.url,
      filename,
    });

  } catch (error: any) {
    console.error('Generate error:', error);
    return res.status(500).json({ 
      error: 'Generation failed', 
      message: error.message 
    });
  }
}

// Gera documento Markdown
function generateMarkdown(metadata: any, analyses: any[]): string {
  const book = metadata.bookMetadata || {};
  const now = new Date().toLocaleDateString('pt-BR');

  let md = `# 📚 Análise: ${book.title || 'Livro'}

> **Autor**: ${book.author || 'Desconhecido'}  
> **Idioma**: ${book.language === 'pt' ? 'Português' : 'Inglês'}  
> **Total de Capítulos**: ${book.total_chapters || analyses.length}  
> **Total de Palavras**: ${book.total_words?.toLocaleString() || 'N/A'}  
> **Gerado em**: ${now}

---

## 📋 Índice

`;

  // Índice
  analyses.forEach((a, idx) => {
    md += `${idx + 1}. [${a.title}](#capitulo-${idx + 1})\n`;
  });

  md += `\n---\n\n`;

  // Capítulos
  analyses.forEach((a, idx) => {
    md += `## <a name="capitulo-${idx + 1}"></a>${idx + 1}. ${a.title}\n\n`;
    md += a.analysis || '*Análise não disponível*';
    md += `\n\n---\n\n`;
  });

  // Rodapé
  md += `\n## 📝 Sobre esta Análise

Este documento foi gerado automaticamente pelo **BooksMD** - Sistema de Análise Inteligente de Livros.

- **Processado em**: ${now}
- **Capítulos analisados**: ${analyses.length}
- **Powered by**: IA + Vercel

---

*BooksMD © ${new Date().getFullYear()}*
`;

  return md;
}

