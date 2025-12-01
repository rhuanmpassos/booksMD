/**
 * Script para substituir a URL da API no environment.prod.ts
 * Uso: node replace-api-url.js https://seu-backend.railway.app
 */

const fs = require('fs');
const path = require('path');

const apiUrl = process.argv[2] || '';

if (!apiUrl) {
  console.log('Uso: node replace-api-url.js <URL_DO_BACKEND>');
  console.log('Exemplo: node replace-api-url.js https://booksmd-backend.railway.app');
  process.exit(1);
}

const envFile = path.join(__dirname, 'src', 'environments', 'environment.prod.ts');

try {
  let content = fs.readFileSync(envFile, 'utf8');
  
  // Substitui a URL da API
  content = content.replace(
    /apiUrl:\s*['"`][^'"`]*['"`]/,
    `apiUrl: '${apiUrl}'`
  );
  
  fs.writeFileSync(envFile, content, 'utf8');
  console.log(`✅ URL da API atualizada para: ${apiUrl}`);
} catch (error) {
  console.error('❌ Erro ao atualizar environment.prod.ts:', error.message);
  process.exit(1);
}

