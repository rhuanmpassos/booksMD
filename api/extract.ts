// POST /api/extract - Extrai texto e divide em capítulos
import { put, list } from '@vercel/blob';
import type { VercelRequest, VercelResponse } from '@vercel/node';

// Importa pdf-parse de forma dinâmica para evitar problemas
let pdfParse: any;

async function getPdfParser() {
  if (!pdfParse) {
    // @ts-ignore
    pdfParse = (await import('pdf-parse')).default;
  }
  return pdfParse;
}

// Verifica se o buffer parece ser um PDF válido
function isPdfBuffer(buffer: Buffer): boolean {
  // PDF começa com %PDF-
  if (buffer.length < 5) return false;
  const header = buffer.slice(0, 5).toString('ascii');
  return header === '%PDF-';
}

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

  const { jobId, fileUrl, filename, fileType } = req.body;

  if (!jobId) {
    return res.status(400).json({ error: 'Job ID is required' });
  }

  console.log('Extract request:', { jobId, fileUrl, filename, fileType });

  try {
    let metadata: any = null;

    // Se o frontend passou a URL do arquivo, usa direto
    if (fileUrl) {
      metadata = {
        id: jobId,
        filename: filename || 'unknown',
        fileType: fileType || fileUrl.split('.').pop()?.toLowerCase() || 'pdf',
        fileUrl: fileUrl,
        status: 'extracting',
        progress: 10,
        currentStep: 'Extraindo texto do arquivo...',
        chapters: [],
        totalChapters: 0,
        analyzedChapters: 0,
        createdAt: new Date().toISOString(),
      };
    } else {
      // Busca metadata do job (com retry para esperar o webhook)
      let retries = 5;
      
      console.log('Searching for job metadata...');
      
      while (retries > 0) {
        try {
          const listResult = await list({ prefix: `jobs/${jobId}/` });
          console.log(`List result for jobs/${jobId}/:`, listResult.blobs.map(b => b.pathname));
          
          const metadataBlob = listResult.blobs.find(b => b.pathname.includes('metadata.json'));
          
          if (metadataBlob) {
            console.log('Found metadata blob:', metadataBlob.url);
            const metadataResponse = await fetch(metadataBlob.url);
            metadata = await metadataResponse.json();
            console.log('Metadata:', metadata);
            
            // Se tem fileUrl, está pronto
            if (metadata.fileUrl) {
              break;
            }
          }
          
          // Busca o arquivo diretamente
          const bookListResult = await list({ prefix: `books/${jobId}/` });
          console.log(`List result for books/${jobId}/:`, bookListResult.blobs.map(b => b.pathname));
          
          if (bookListResult.blobs.length > 0) {
            const bookBlob = bookListResult.blobs[0];
            if (!metadata) {
              metadata = {
                id: jobId,
                filename: bookBlob.pathname.split('/').pop() || 'unknown',
                fileType: bookBlob.pathname.split('.').pop()?.toLowerCase() || 'pdf',
                fileUrl: bookBlob.url,
                status: 'extracting',
                progress: 10,
                currentStep: 'Extraindo texto do arquivo...',
                chapters: [],
                totalChapters: 0,
                analyzedChapters: 0,
                createdAt: new Date().toISOString(),
              };
            } else {
              metadata.fileUrl = bookBlob.url;
            }
            break;
          }
        } catch (listError) {
          console.error('List error:', listError);
        }
        
        retries--;
        if (retries > 0) {
          console.log(`Retry ${5 - retries}/5...`);
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      }
    }
    
    if (!metadata || !metadata.fileUrl) {
      console.error('Job not found or no fileUrl:', { jobId, metadata });
      return res.status(404).json({ error: 'Job not found', jobId });
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
    console.log('Downloading file from:', metadata.fileUrl);
    const fileResponse = await fetch(metadata.fileUrl);
    
    if (!fileResponse.ok) {
      throw new Error(`Failed to download file: ${fileResponse.status} ${fileResponse.statusText}`);
    }
    
    const contentType = fileResponse.headers.get('content-type');
    const contentLength = fileResponse.headers.get('content-length');
    console.log('Download response:', { contentType, contentLength });
    
    const fileBuffer = Buffer.from(await fileResponse.arrayBuffer());
    console.log('File buffer size:', fileBuffer.length, 'bytes');

    // Extrai texto baseado no tipo
    let text = '';
    let bookTitle = metadata.filename.replace(/\.[^/.]+$/, '');

    if (metadata.fileType === 'pdf') {
      // Valida que é realmente um PDF
      if (!isPdfBuffer(fileBuffer)) {
        console.error('Invalid PDF header. First 20 bytes:', fileBuffer.slice(0, 20).toString('hex'));
        throw new Error('O arquivo não parece ser um PDF válido. Verifique se o arquivo não está corrompido.');
      }
      
      console.log('PDF header validated, parsing...');
      
      try {
        const parser = await getPdfParser();
        // Opções para pdf-parse com timeout aumentado
        const options = {
          // Não renderizar páginas, apenas extrair texto
          max: 0, // 0 = todas as páginas
        };
        const pdfData = await parser(fileBuffer, options);
        text = pdfData.text || '';
        bookTitle = pdfData.info?.Title || bookTitle;
        console.log('PDF parsed successfully. Pages:', pdfData.numpages, 'Text length:', text.length);
      } catch (pdfError: any) {
        console.error('PDF parse error:', pdfError);
        
        // Tenta identificar o tipo de erro
        if (pdfError.message?.includes('password')) {
          throw new Error('O PDF está protegido por senha. Por favor, remova a proteção antes de enviar.');
        } else if (pdfError.message?.includes('encrypt')) {
          throw new Error('O PDF está criptografado. Por favor, use um PDF sem criptografia.');
        } else if (pdfError.message?.includes('Invalid') || pdfError.message?.includes('structure')) {
          throw new Error('Estrutura do PDF inválida. O arquivo pode estar corrompido ou usar um formato não suportado. Tente converter o PDF para um novo arquivo.');
        }
        
        throw new Error(`Erro ao processar PDF: ${pdfError.message}`);
      }
    } else if (metadata.fileType === 'txt') {
      text = fileBuffer.toString('utf-8');
    } else if (metadata.fileType === 'epub') {
      // Para EPUB, usaremos uma abordagem simplificada
      // Em produção, usar epub-parser ou similar
      text = fileBuffer.toString('utf-8').replace(/<[^>]*>/g, ' ');
    }
    
    // Verifica se conseguiu extrair algum texto
    if (!text || text.trim().length < 100) {
      console.warn('Very little text extracted:', text.length, 'characters');
      throw new Error('Não foi possível extrair texto suficiente do arquivo. O PDF pode conter apenas imagens ou estar em formato escaneado.');
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
    
    // Tenta atualizar o status do job para erro
    if (req.body?.jobId) {
      try {
        await put(`jobs/${req.body.jobId}/metadata.json`, JSON.stringify({
          id: req.body.jobId,
          status: 'error',
          error: error.message,
          currentStep: 'Erro na extração',
          progress: 0,
        }), {
          access: 'public',
          contentType: 'application/json',
        });
      } catch (e) {
        console.error('Failed to update job status:', e);
      }
    }
    
    return res.status(500).json({ 
      error: 'Extraction failed', 
      message: error.message,
      tip: 'Dicas: 1) Verifique se o PDF não está protegido por senha. 2) Tente converter o PDF para um novo arquivo. 3) Se o PDF é escaneado, o texto não pode ser extraído automaticamente.'
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

