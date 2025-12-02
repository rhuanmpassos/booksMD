// GET /api/status/[jobId] - Retorna status do job
import { list } from '@vercel/blob';
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

  const { jobId } = req.query;

  if (!jobId || typeof jobId !== 'string') {
    return res.status(400).json({ error: 'Job ID is required' });
  }

  try {
    // Busca metadata do job
    const { blobs } = await list({ prefix: `jobs/${jobId}/metadata.json` });
    
    if (blobs.length === 0) {
      return res.status(404).json({ error: 'Job not found' });
    }

    // Lê o metadata
    const response = await fetch(blobs[0].url);
    const metadata = await response.json();

    // Verifica se tem output pronto
    const { blobs: outputBlobs } = await list({ prefix: `outputs/${jobId}/` });
    const mdReady = outputBlobs.some(b => b.pathname.endsWith('.md'));
    const pdfReady = outputBlobs.some(b => b.pathname.endsWith('.pdf'));

    return res.status(200).json({
      job_id: metadata.id,
      status: metadata.status,
      progress: metadata.progress,
      current_step: metadata.currentStep,
      error_message: metadata.errorMessage,
      metadata: metadata.bookMetadata,
      output_ready: mdReady || pdfReady,
      md_ready: mdReady,
      pdf_ready: pdfReady,
    });

  } catch (error: any) {
    console.error('Status error:', error);
    return res.status(500).json({ 
      error: 'Failed to get status', 
      message: error.message 
    });
  }
}

