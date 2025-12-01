// Função serverless do Vercel para fazer proxy do upload de arquivo
import type { VercelRequest, VercelResponse } from '@vercel/node';

const BACKEND_URL = 'http://52.87.194.234:8000';

export const config = {
  api: {
    bodyParser: false, // Desabilita para receber FormData raw
  },
};

export default async function handler(
  req: VercelRequest,
  res: VercelResponse
) {
  // Log para debug
  console.log('Upload handler called:', {
    method: req.method,
    url: req.url,
    headers: req.headers,
  });

  // Permite CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  // Handle preflight
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // Aceita POST ou qualquer método (pode ser que o Vercel mude o método)
  if (req.method && req.method !== 'POST' && req.method !== 'OPTIONS') {
    console.log('Method not allowed:', req.method);
    return res.status(405).json({ 
      error: 'Method not allowed', 
      receivedMethod: req.method,
      allowedMethods: ['POST', 'OPTIONS']
    });
  }

  try {
    // Lê o body como buffer
    const chunks: Buffer[] = [];
    const stream = req as any;
    
    // Lê o stream do body
    for await (const chunk of stream) {
      chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
    }

    const bodyBuffer = Buffer.concat(chunks);
    const contentType = req.headers['content-type'] || 'multipart/form-data';

    console.log('Forwarding to backend:', {
      url: `${BACKEND_URL}/api/upload`,
      contentType,
      bodySize: bodyBuffer.length
    });

    // Faz requisição para o backend passando o body raw
    const response = await fetch(`${BACKEND_URL}/api/upload`, {
      method: 'POST',
      body: bodyBuffer,
      headers: {
        'Content-Type': contentType,
      }
    });

    const data = await response.text();
    
    console.log('Backend response:', {
      status: response.status,
      contentType: response.headers.get('content-type')
    });

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
