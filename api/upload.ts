// Função serverless do Vercel para fazer proxy do upload de arquivo
import type { VercelRequest, VercelResponse } from '@vercel/node';
import { Readable } from 'stream';

const BACKEND_URL = 'http://52.87.194.234:8000';

export const config = {
  api: {
    bodyParser: false, // Importante: desabilita bodyParser para receber FormData raw
  },
};

export default async function handler(
  req: VercelRequest,
  res: VercelResponse
) {
  // Permite CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  // Handle preflight
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // O Vercel passa o body como stream quando bodyParser está desabilitado
    const chunks: Buffer[] = [];
    const stream = req as any;
    
    // Lê o stream do body
    for await (const chunk of stream) {
      chunks.push(Buffer.from(chunk));
    }

    const bodyBuffer = Buffer.concat(chunks);

    // Faz requisição para o backend com o body raw e Content-Type correto
    const contentType = req.headers['content-type'] || 'multipart/form-data';
    
    const response = await fetch(`${BACKEND_URL}/api/upload`, {
      method: 'POST',
      body: bodyBuffer,
      headers: {
        'Content-Type': contentType,
        'Content-Length': bodyBuffer.length.toString(),
      }
    });

    const data = await response.text();
    
    res.setHeader('Content-Type', response.headers.get('content-type') || 'application/json');
    res.status(response.status).send(data);
  } catch (error: any) {
    console.error('Upload proxy error:', error);
    res.status(500).json({ 
      error: 'Proxy error', 
      message: error.message
    });
  }
}
