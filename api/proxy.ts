// Função serverless do Vercel para fazer proxy das requisições
import type { VercelRequest, VercelResponse } from '@vercel/node';

const BACKEND_URL = 'http://52.87.194.234:8000';

export default async function handler(
  req: VercelRequest,
  res: VercelResponse
) {
  // Permite CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  // Handle preflight
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  // Remove /api do path
  const path = req.url?.replace('/api', '') || req.url || '';
  const targetUrl = `${BACKEND_URL}${path}`;

  try {
    // Para requisições com body
    const options: RequestInit = {
      method: req.method,
      headers: {
        ...(req.headers as any),
        host: undefined, // Remove host header
        'content-type': req.headers['content-type'] || 'application/json',
      }
    };

    // Adiciona body se não for GET/HEAD
    if (req.method !== 'GET' && req.method !== 'HEAD' && req.body) {
      if (req.headers['content-type']?.includes('application/json')) {
        options.body = JSON.stringify(req.body);
      } else {
        // Para FormData, precisa passar o body original
        options.body = req.body as any;
      }
    }

    const response = await fetch(targetUrl, options);
    const data = await response.text();
    
    // Copia headers importantes
    res.setHeader('Content-Type', response.headers.get('content-type') || 'application/json');
    res.status(response.status).send(data);
  } catch (error: any) {
    console.error('Proxy error:', error);
    res.status(500).json({ 
      error: 'Proxy error', 
      message: error.message,
      targetUrl 
    });
  }
}
