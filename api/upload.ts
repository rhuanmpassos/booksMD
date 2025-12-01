// Função serverless do Vercel para fazer proxy do upload
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

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Para upload de arquivo, precisa passar o FormData
    const formData = new FormData();
    
    // Se tiver arquivo no body
    if (req.body && typeof req.body === 'object') {
      // Converte body para FormData
      for (const [key, value] of Object.entries(req.body)) {
        if (value instanceof File || value instanceof Blob) {
          formData.append(key, value);
        } else {
          formData.append(key, String(value));
        }
      }
    }

    // Faz requisição para o backend
    const response = await fetch(`${BACKEND_URL}/api/upload`, {
      method: 'POST',
      body: formData,
      headers: {
        // Não passa Content-Type, deixa o fetch definir automaticamente para FormData
      }
    });

    const data = await response.text();
    
    res.setHeader('Content-Type', response.headers.get('content-type') || 'application/json');
    res.status(response.status).send(data);
  } catch (error: any) {
    console.error('Proxy error:', error);
    res.status(500).json({ 
      error: 'Proxy error', 
      message: error.message
    });
  }
}

