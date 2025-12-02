// POST /api/upload - Upload de livro para análise
import { put } from '@vercel/blob';
import type { VercelRequest, VercelResponse } from '@vercel/node';
import { v4 as uuidv4 } from 'uuid';

// Tipos de arquivo suportados
const SUPPORTED_TYPES = {
  'application/pdf': 'pdf',
  'application/epub+zip': 'epub',
  'text/plain': 'txt',
};

// Tamanho máximo: 1GB
const MAX_SIZE = 1024 * 1024 * 1024;

export const config = {
  api: {
    bodyParser: false, // Necessário para upload de arquivos grandes
  },
};

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

  try {
    // Lê o body como buffer
    const chunks: Buffer[] = [];
    for await (const chunk of req) {
      chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
    }
    const body = Buffer.concat(chunks);

    // Parse multipart form data manualmente (simplificado)
    const contentType = req.headers['content-type'] || '';
    const boundary = contentType.split('boundary=')[1];
    
    if (!boundary) {
      return res.status(400).json({ error: 'Invalid content type' });
    }

    // Extrai o arquivo do multipart
    const { filename, fileBuffer, mimeType } = parseMultipart(body, boundary);

    if (!filename || !fileBuffer) {
      return res.status(400).json({ error: 'No file provided' });
    }

    // Valida tipo de arquivo
    const fileType = SUPPORTED_TYPES[mimeType as keyof typeof SUPPORTED_TYPES];
    if (!fileType) {
      return res.status(400).json({ 
        error: `Unsupported file type: ${mimeType}. Supported: PDF, EPUB, TXT` 
      });
    }

    // Valida tamanho
    if (fileBuffer.length > MAX_SIZE) {
      return res.status(413).json({ 
        error: `File too large. Maximum size: 1GB` 
      });
    }

    // Gera job ID
    const jobId = uuidv4();

    // Salva no Vercel Blob
    const blob = await put(`books/${jobId}/${filename}`, fileBuffer, {
      access: 'public',
      contentType: mimeType,
    });

    // Cria metadata do job
    const jobMetadata = {
      id: jobId,
      filename,
      fileType,
      fileUrl: blob.url,
      status: 'pending',
      progress: 0,
      currentStep: 'Aguardando processamento',
      chapters: [],
      totalChapters: 0,
      analyzedChapters: 0,
      createdAt: new Date().toISOString(),
    };

    // Salva metadata do job no Blob
    await put(`jobs/${jobId}/metadata.json`, JSON.stringify(jobMetadata), {
      access: 'public',
      contentType: 'application/json',
    });

    return res.status(200).json({
      job_id: jobId,
      message: 'Upload successful. Processing will start.',
      filename,
    });

  } catch (error: any) {
    console.error('Upload error:', error);
    return res.status(500).json({ 
      error: 'Upload failed', 
      message: error.message 
    });
  }
}

// Parser simples de multipart form data
function parseMultipart(body: Buffer, boundary: string): { 
  filename: string | null; 
  fileBuffer: Buffer | null; 
  mimeType: string;
} {
  const boundaryBuffer = Buffer.from(`--${boundary}`);
  const parts = [];
  let start = 0;
  let idx;

  while ((idx = body.indexOf(boundaryBuffer, start)) !== -1) {
    if (start > 0) {
      parts.push(body.slice(start, idx - 2)); // -2 para remover \r\n
    }
    start = idx + boundaryBuffer.length + 2; // +2 para pular \r\n
  }

  for (const part of parts) {
    const headerEnd = part.indexOf('\r\n\r\n');
    if (headerEnd === -1) continue;

    const headers = part.slice(0, headerEnd).toString();
    const content = part.slice(headerEnd + 4);

    if (headers.includes('filename=')) {
      const filenameMatch = headers.match(/filename="([^"]+)"/);
      const contentTypeMatch = headers.match(/Content-Type:\s*([^\r\n]+)/i);
      
      return {
        filename: filenameMatch ? filenameMatch[1] : null,
        fileBuffer: content,
        mimeType: contentTypeMatch ? contentTypeMatch[1].trim() : 'application/octet-stream',
      };
    }
  }

  return { filename: null, fileBuffer: null, mimeType: '' };
}

