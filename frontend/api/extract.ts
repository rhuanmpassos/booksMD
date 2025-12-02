// POST /api/extract - Extrai texto e divide em capítulos
import { put, list } from '@vercel/blob';
import type { VercelRequest, VercelResponse } from '@vercel/node';
import pdfParse from 'pdf-parse';

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
    // Busca metadata do job (com retry para esperar o webhook)
    let metadata: any = null;
    let retries = 5;
    
    while (retries > 0) {
      const { blobs: metadataBlobs } = await list({ prefix: `jobs/${jobId}/metadata.json` });
      
      if (metadataBlobs.length > 0) {
        const metadataResponse = await fetch(metadataBlobs[0].url);
        metadata = await metadataResponse.json();
        
        // Se tem fileUrl, está pronto
        if (metadata.fileUrl) {
          break;
        }
        
        // Se ainda está em uploading, busca o arquivo diretamente
        if (metadata.status === 'uploading') {
          const { blobs: bookBlobs } = await list({ prefix: `books/${jobId}/` });
          if (bookBlobs.length > 0) {
            metadata.fileUrl = bookBlobs[0].url;
            break;
          }
        }
      }
      
      retries--;
      if (retries > 0) {
        // Espera 1 segundo antes de tentar novamente
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
    
    if (!metadata) {
      return res.status(404).json({ error: 'Job not found' });
    }

    // Se ainda não tem fileUrl, tenta buscar o arquivo diretamente
    if (!metadata.fileUrl) {
      const { blobs: bookBlobs } = await list({ prefix: `books/${jobId}/` });
      if (bookBlobs.length > 0) {
        metadata.fileUrl = bookBlobs[0].url;
      } else {
        return res.status(404).json({ error: 'File not found for job' });
      }
    }

    // Atualiza status
    metadata.status = 'extracting';
    metadata.currentStep = 'Extraindo texto do arquivo...';
    metadata.progress = 10;

    await put(`jobs/${jobId}/metadata.json`, JSON.stringify(metadata), {
      access: 'public',
      contentType: 'application/json',
    });

    // Baixa o arquivo
    const fileResponse = await fetch(metadata.fileUrl);
    const fileBuffer = Buffer.from(await fileResponse.arrayBuffer());

    // Extrai texto baseado no tipo
    let text = '';
    let bookTitle = metadata.filename.replace(/\.[^/.]+$/, '');

    if (metadata.fileType === 'pdf') {
      const pdfData = await pdfParse(fileBuffer);
      text = pdfData.text;
      bookTitle = pdfData.info?.Title || bookTitle;
    } else if (metadata.fileType === 'txt') {
      text = fileBuffer.toString('utf-8');
    } else if (metadata.fileType === 'epub') {
      // Para EPUB, usaremos uma abordagem simplificada
      // Em produção, usar epub-parser ou similar
      text = fileBuffer.toString('utf-8').replace(/<[^>]*>/g, ' ');
    }

    // Divide em capítulos
    const chapters = splitIntoChapters(text);

    // Atualiza metadata
    metadata.status = 'splitting';
    metadata.currentStep = 'Dividindo em capítulos...';
    metadata.progress = 15;
    metadata.totalChapters = chapters.length;
    metadata.chapters = chapters.map((ch, idx) => ({
      index: idx,
      title: ch.title,
      wordCount: ch.content.split(/\s+/).length,
      analyzed: false,
    }));
    metadata.bookMetadata = {
      title: bookTitle,
      author: 'Desconhecido',
      language: detectLanguage(text),
      total_chapters: chapters.length,
      total_words: text.split(/\s+/).length,
    };

    // Salva capítulos individualmente
    for (let i = 0; i < chapters.length; i++) {
      await put(
        `jobs/${jobId}/chapters/${i}.json`,
        JSON.stringify(chapters[i]),
        { access: 'public', contentType: 'application/json' }
      );
    }

    // Salva metadata atualizado
    await put(`jobs/${jobId}/metadata.json`, JSON.stringify(metadata), {
      access: 'public',
      contentType: 'application/json',
    });

    return res.status(200).json({
      success: true,
      totalChapters: chapters.length,
      bookMetadata: metadata.bookMetadata,
    });

  } catch (error: any) {
    console.error('Extract error:', error);
    return res.status(500).json({ 
      error: 'Extraction failed', 
      message: error.message 
    });
  }
}

// Divide texto em capítulos
function splitIntoChapters(text: string): { title: string; content: string }[] {
  const chapterPatterns = [
    /^(chapter|capítulo|cap\.?)\s*(\d+|[ivxlc]+)/im,
    /^(parte|part)\s*(\d+|[ivxlc]+)/im,
    /^(\d+)\.\s+[A-Z]/m,
  ];

  const lines = text.split('\n');
  const chapters: { title: string; content: string }[] = [];
  let currentChapter: { title: string; content: string[] } | null = null;

  for (const line of lines) {
    const isChapterStart = chapterPatterns.some(p => p.test(line.trim()));
    
    if (isChapterStart && line.trim().length < 100) {
      if (currentChapter) {
        chapters.push({
          title: currentChapter.title,
          content: currentChapter.content.join('\n'),
        });
      }
      currentChapter = { title: line.trim(), content: [] };
    } else if (currentChapter) {
      currentChapter.content.push(line);
    }
  }

  // Adiciona último capítulo
  if (currentChapter) {
    chapters.push({
      title: currentChapter.title,
      content: currentChapter.content.join('\n'),
    });
  }

  // Se não encontrou capítulos, divide por tamanho
  if (chapters.length === 0) {
    const words = text.split(/\s+/);
    const chunkSize = 3000; // palavras por capítulo
    
    for (let i = 0; i < words.length; i += chunkSize) {
      chapters.push({
        title: `Parte ${Math.floor(i / chunkSize) + 1}`,
        content: words.slice(i, i + chunkSize).join(' '),
      });
    }
  }

  return chapters;
}

// Detecta idioma (simplificado)
function detectLanguage(text: string): string {
  const ptWords = ['de', 'que', 'não', 'para', 'com', 'uma', 'os', 'no', 'se', 'na'];
  const enWords = ['the', 'of', 'and', 'to', 'in', 'is', 'it', 'for', 'on', 'with'];
  
  const words = text.toLowerCase().split(/\s+/).slice(0, 1000);
  
  const ptCount = words.filter(w => ptWords.includes(w)).length;
  const enCount = words.filter(w => enWords.includes(w)).length;
  
  return ptCount > enCount ? 'pt' : 'en';
}

