// Teste simples para verificar se o Vercel está reconhecendo funções serverless
import type { VercelRequest, VercelResponse } from '@vercel/node';

export default async function handler(
  req: VercelRequest,
  res: VercelResponse
) {
  res.status(200).json({ 
    message: 'Função serverless funcionando!',
    method: req.method,
    url: req.url
  });
}

