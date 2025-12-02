// GET /api/download/[jobId]/[type] - Download e auto-delete
import { list, del } from '@vercel/blob';
import type { VercelRequest, VercelResponse } from '@vercel/node';

export default async function handler(req: VercelRequest, res: VercelResponse) {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { jobId, type } = req.query;

  if (!jobId || typeof jobId !== 'string') {
    return res.status(400).json({ error: 'Job ID is required' });
  }

  if (!type || (type !== 'md' && type !== 'pdf')) {
    return res.status(400).json({ error: 'Type must be "md" or "pdf"' });
  }

  try {
    // Busca o arquivo de output
    const extension = type === 'md' ? '.md' : '.pdf';
    const { blobs: outputBlobs } = await list({ prefix: `outputs/${jobId}/` });
    
    const outputBlob = outputBlobs.find(b => b.pathname.endsWith(extension));
    
    if (!outputBlob) {
      return res.status(404).json({ error: 'Output file not found' });
    }

    // Baixa o conteúdo
    const response = await fetch(outputBlob.url);
    const content = await response.arrayBuffer();

    // Extrai nome do arquivo
    const filename = outputBlob.pathname.split('/').pop() || `output${extension}`;

    // Define headers para download
    res.setHeader('Content-Type', type === 'md' ? 'text/markdown' : 'application/pdf');
    res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
    res.setHeader('Content-Length', content.byteLength.toString());

    // Envia o arquivo
    res.status(200).send(Buffer.from(content));

    // AUTO-DELETE: Remove todos os arquivos do job após o download
    // Isso é feito de forma assíncrona para não bloquear a resposta
    deleteJobFiles(jobId).catch(err => {
      console.error('Error deleting job files:', err);
    });

  } catch (error: any) {
    console.error('Download error:', error);
    return res.status(500).json({ 
      error: 'Download failed', 
      message: error.message 
    });
  }
}

// Deleta todos os arquivos de um job
async function deleteJobFiles(jobId: string): Promise<void> {
  console.log(`Deleting files for job ${jobId}...`);

  // Lista todos os arquivos do job
  const prefixes = [
    `jobs/${jobId}/`,
    `books/${jobId}/`,
    `outputs/${jobId}/`,
  ];

  for (const prefix of prefixes) {
    const { blobs } = await list({ prefix });
    
    for (const blob of blobs) {
      try {
        await del(blob.url);
        console.log(`Deleted: ${blob.pathname}`);
      } catch (err) {
        console.error(`Failed to delete ${blob.pathname}:`, err);
      }
    }
  }

  console.log(`Job ${jobId} files deleted.`);
}

