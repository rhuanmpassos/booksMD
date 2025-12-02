// POST /api/upload - Gera URL de upload para Vercel Blob (client-side upload)
import { handleUpload, type HandleUploadBody } from '@vercel/blob/client';
import { put } from '@vercel/blob';
import type { VercelRequest, VercelResponse } from '@vercel/node';
import { v4 as uuidv4 } from 'uuid';

// Tipos de arquivo suportados
const SUPPORTED_TYPES = ['application/pdf', 'application/epub+zip', 'text/plain'];
const SUPPORTED_EXTENSIONS = ['pdf', 'epub', 'txt'];

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
    
    // Gera job ID antes do upload
    const jobId = uuidv4();

    const jsonResponse = await handleUpload({
      body,
      request: req,
      onBeforeGenerateToken: async (pathname) => {
        // Valida extensão do arquivo
        const ext = pathname.split('.').pop()?.toLowerCase();
        if (!ext || !SUPPORTED_EXTENSIONS.includes(ext)) {
          throw new Error(`Tipo de arquivo não suportado. Use: PDF, EPUB ou TXT`);
        }
        
        return {
          allowedContentTypes: SUPPORTED_TYPES,
          maximumSizeInBytes: 1024 * 1024 * 500, // 500MB máximo
          tokenPayload: JSON.stringify({ jobId }),
          addRandomSuffix: false,
          pathname: `books/${jobId}/${pathname}`, // Organiza por jobId
        };
      },
      onUploadCompleted: async ({ blob, tokenPayload }) => {
        // Chamado quando o upload termina (webhook)
        try {
          const payload = JSON.parse(tokenPayload || '{}');
          const currentJobId = payload.jobId;
          const filename = blob.pathname.split('/').pop() || 'unknown';
          const ext = filename.split('.').pop()?.toLowerCase() || '';

          // Cria metadata do job
          const jobMetadata = {
            id: currentJobId,
            filename,
            fileType: ext,
            fileUrl: blob.url,
            status: 'pending',
            progress: 0,
            currentStep: 'Arquivo enviado. Aguardando processamento.',
            chapters: [] as string[],
            totalChapters: 0,
            analyzedChapters: 0,
            createdAt: new Date().toISOString(),
          };

          // Salva metadata do job no Blob
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
      jobId,
    });

  } catch (error: any) {
    console.error('Upload error:', error);
    return res.status(500).json({ 
      error: 'Upload failed', 
      message: error.message 
    });
  }
}

