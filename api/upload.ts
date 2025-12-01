// Função serverless do Vercel para fazer proxy do upload de arquivo
import type { VercelRequest, VercelResponse } from '@vercel/node';

const BACKEND_URL = 'http://52.87.194.234:8000';

// IMPORTANTE: bodyParser deve ser false para FormData
export const config = {
  api: {
    bodyParser: false,
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
    hasBody: !!req.body,
  });

  // Permite CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Content-Length');

  // Handle preflight
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // Verifica método
  if (!req.method || (req.method !== 'POST' && req.method !== 'OPTIONS')) {
    console.error('Method not allowed:', req.method);
    return res.status(405).json({ 
      error: 'Method not allowed', 
      receivedMethod: req.method || 'undefined',
      allowedMethods: ['POST', 'OPTIONS']
    });
  }

  try {
    // Lê o body como buffer usando a API do Node.js
    const chunks: Buffer[] = [];
    
    // req é um stream quando bodyParser está desabilitado
    const stream = req as any;
    
    // Lê o stream do body
    if (stream.readable) {
      for await (const chunk of stream) {
        chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
      }
    } else if (req.body) {
      // Fallback: se o body já estiver disponível
      if (Buffer.isBuffer(req.body)) {
        chunks.push(req.body);
      } else if (typeof req.body === 'string') {
        chunks.push(Buffer.from(req.body));
      } else {
        chunks.push(Buffer.from(JSON.stringify(req.body)));
      }
    }

    if (chunks.length === 0) {
      console.error('No body received');
      return res.status(400).json({ error: 'No body received' });
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
        'Content-Length': bodyBuffer.length.toString(),
      }
    });

    const data = await response.text();
    
    console.log('Backend response:', {
      status: response.status,
      contentType: response.headers.get('content-type'),
      dataLength: data.length
    });

    // Copia headers relevantes
    const responseContentType = response.headers.get('content-type');
    if (responseContentType) {
      res.setHeader('Content-Type', responseContentType);
    }

    res.status(response.status).send(data);
  } catch (error: any) {
    console.error('Upload proxy error:', error);
    res.status(500).json({ 
      error: 'Proxy error', 
      message: error.message,
      stack: error.stack
    });
  }
}
