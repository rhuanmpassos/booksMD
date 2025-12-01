// Função serverless do Vercel para fazer proxy do upload de arquivo
import type { VercelRequest, VercelResponse } from '@vercel/node';

const BACKEND_URL = 'http://52.87.194.234:8000';

export const config = {
  api: {
    bodyParser: false, // Desabilita bodyParser para receber FormData raw
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
    // Lê o body como stream e repassa para o backend
    const chunks: Buffer[] = [];
    
    // Se req.body é um stream, lê ele
    if (req.body && typeof req.body.pipe === 'function') {
      for await (const chunk of req.body) {
        chunks.push(chunk);
      }
    } else if (req.body) {
      chunks.push(Buffer.from(req.body));
    }

    const bodyBuffer = Buffer.concat(chunks);

    // Faz requisição para o backend com o body raw
    const response = await fetch(`${BACKEND_URL}/api/upload`, {
      method: 'POST',
      body: bodyBuffer,
      headers: {
        'Content-Type': req.headers['content-type'] || 'multipart/form-data',
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
