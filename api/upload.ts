// POST /api/upload - Gera URL de upload para Vercel Blob (client-side upload)
import { handleUpload, type HandleUploadBody } from '@vercel/blob/client';
import { put } from '@vercel/blob';
import type { VercelRequest, VercelResponse } from '@vercel/node';

// Tipos de arquivo suportados
const SUPPORTED_TYPES = ['application/pdf', 'application/epub+zip', 'text/plain'];
const SUPPORTED_EXTENSIONS = ['pdf', 'epub', 'txt'];

// Extrai jobId e filename real do pathname
// Formato: __jobId__<uuid>__<filename>
function parsePathname(pathname: string): { jobId: string; filename: string } {
  const match = pathname.match(/^__jobId__([a-f0-9-]{36})__(.+)$/i);
  if (match) {
    return { jobId: match[1], filename: match[2] };
  }
  // Fallback: usa um jobId baseado no hash do pathname
  return { 
    jobId: pathname.split('').reduce((a, b) => ((a << 5) - a + b.charCodeAt(0)) | 0, 0).toString(16).replace('-', ''),
    filename: pathname 
  };
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

  try {
    // Usa handleUpload do Vercel Blob para client-side upload
    const body = req.body as HandleUploadBody;
    
    let extractedJobId = '';

    const jsonResponse = await handleUpload({
      body,
      request: req,
      onBeforeGenerateToken: async (pathname) => {
        // Extrai o jobId do pathname (vem do frontend)
        const { jobId, filename } = parsePathname(pathname);
        extractedJobId = jobId;
        
        console.log('Extracted from pathname:', { jobId, filename, originalPathname: pathname });
        
        // Valida extensão do arquivo
        const ext = filename.split('.').pop()?.toLowerCase();
        if (!ext || !SUPPORTED_EXTENSIONS.includes(ext)) {
          throw new Error(`Tipo de arquivo não suportado. Use: PDF, EPUB ou TXT`);
        }

        // Cria metadata do job ANTES do upload começar
        const jobMetadata = {
          id: jobId,
          filename: filename,
          fileType: ext,
          fileUrl: '', // Será preenchido após upload
          status: 'uploading',
          progress: 0,
          currentStep: 'Enviando arquivo...',
          chapters: [] as string[],
          totalChapters: 0,
          analyzedChapters: 0,
          createdAt: new Date().toISOString(),
        };

        // Salva metadata inicial do job no Blob
        await put(`jobs/${jobId}/metadata.json`, JSON.stringify(jobMetadata), {
          access: 'public',
          contentType: 'application/json',
        });

        console.log('Job created:', { jobId, filename });
        
        return {
          allowedContentTypes: SUPPORTED_TYPES,
          maximumSizeInBytes: 1024 * 1024 * 500, // 500MB máximo
          tokenPayload: JSON.stringify({ jobId, filename, fileType: ext }),
          addRandomSuffix: false,
          pathname: `books/${jobId}/${filename}`, // Organiza por jobId com filename limpo
        };
      },
      onUploadCompleted: async ({ blob, tokenPayload }) => {
        // Chamado quando o upload termina (webhook)
        try {
          const payload = JSON.parse(tokenPayload || '{}');
          const currentJobId = payload.jobId;
          const filename = payload.filename || blob.pathname.split('/').pop() || 'unknown';
          const ext = payload.fileType || filename.split('.').pop()?.toLowerCase() || '';

          // Atualiza metadata do job com a URL do arquivo
          const jobMetadata = {
            id: currentJobId,
            filename,
            fileType: ext,
            fileUrl: blob.url,
            status: 'pending',
            progress: 5,
            currentStep: 'Arquivo enviado. Pronto para processamento.',
            chapters: [] as string[],
            totalChapters: 0,
            analyzedChapters: 0,
            createdAt: new Date().toISOString(),
          };

          // Salva metadata atualizada
          await put(`jobs/${currentJobId}/metadata.json`, JSON.stringify(jobMetadata), {
            access: 'public',
            contentType: 'application/json',
          });

          console.log('Upload completed:', { jobId: currentJobId, filename, url: blob.url });
        } catch (err) {
          console.error('onUploadCompleted error:', err);
        }
      },
    });

    // Adiciona jobId na resposta para o cliente
    return res.status(200).json({
      ...jsonResponse,
      jobId: extractedJobId,
    });

  } catch (error: any) {
    console.error('Upload error:', error);
    return res.status(500).json({ 
      error: 'Upload failed', 
      message: error.message 
    });
  }
}

