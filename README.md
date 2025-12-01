# 📚 BooksMD - Análise Inteligente de Livros

Sistema completo para análise profunda de livros com inteligência artificial. Transforma qualquer livro (PDF, EPUB, TXT) em uma análise detalhada e estruturada em Markdown ou PDF.

![BooksMD](https://img.shields.io/badge/BooksMD-v1.0.0-gold)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Angular](https://img.shields.io/badge/Angular-18-red)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-green)

## ✨ Funcionalidades

- 📖 **Upload de livros** - Suporta PDF, EPUB e TXT
- 🔍 **Extração inteligente** - Detecta e divide automaticamente em capítulos
- 🤖 **Análise com IA** - Usa GPT-4o para análise profunda de cada capítulo
- 🌐 **Tradução automática** - Traduz livros em inglês para português
- 📝 **Explicações didáticas** - Não apenas resume, mas explica conceitos
- 📊 **Glossário técnico** - Lista e explica termos técnicos
- 📥 **Export MD & PDF** - Baixe a análise em Markdown ou PDF formatado

## 🏗️ Arquitetura

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend   │────▶│   OpenAI    │
│   Angular   │     │   FastAPI   │     │   GPT-4o    │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │             │
              ┌─────▼─────┐ ┌─────▼─────┐
              │  Storage  │ │   Redis   │
              │   JSON    │ │  (Celery) │
              └───────────┘ └───────────┘
```

## 🚀 Quick Start

### Pré-requisitos

- Python 3.11+
- Node.js 18+
- Redis (opcional, para processamento em fila)

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/booksmd.git
cd booksmd
```

### 2. Configure o Backend

```bash
cd backend

# Crie ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instale dependências
pip install -r requirements.txt

# Configure variáveis de ambiente
copy .env.example .env
# Edite .env e adicione sua OPENAI_API_KEY
```

### 3. Configure o Frontend

```bash
cd frontend

# Instale dependências
npm install
```

### 4. Execute

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

Acesse: http://localhost:4200

## 📁 Estrutura do Projeto

```
booksmd/
├── backend/
│   ├── app/
│   │   ├── extractors/      # Extração de PDF, EPUB, TXT
│   │   ├── splitter/        # Divisão em capítulos
│   │   ├── analyzer/        # Análise com OpenAI
│   │   ├── generator/       # Geração de MD e PDF
│   │   ├── storage/         # Armazenamento de jobs
│   │   ├── tasks/           # Celery tasks
│   │   └── api/             # Rotas FastAPI
│   ├── main.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/  # Componentes compartilhados
│   │   │   ├── pages/       # Páginas (Home, Status)
│   │   │   └── services/    # Serviços (API)
│   │   └── styles.scss
│   ├── angular.json
│   └── package.json
│
└── README.md
```

## 🔧 Configuração

### Variáveis de Ambiente (Backend)

| Variável | Descrição | Default |
|----------|-----------|---------|
| `OPENAI_API_KEY` | Chave da API OpenAI | (obrigatório) |
| `OPENAI_MODEL` | Modelo a usar | `gpt-4o` |
| `REDIS_URL` | URL do Redis | `redis://localhost:6379/0` |
| `MAX_FILE_SIZE_MB` | Tamanho máximo de upload | `50` |
| `MAX_TOKENS_PER_CHUNK` | Tokens por capítulo | `12000` |

## 📖 Como Funciona

### 1. Upload
O usuário envia um livro em PDF, EPUB ou TXT.

### 2. Extração
O sistema extrai o texto usando:
- **PDF**: PyMuPDF
- **EPUB**: ebooklib + BeautifulSoup
- **TXT**: Detecção automática de encoding

### 3. Divisão em Capítulos
O `ChapterSplitter` detecta capítulos usando padrões:
- "Capítulo X", "Chapter X"
- Numeração romana
- Títulos em caixa alta
- Se não detectar, divide por tamanho (12k tokens)

### 4. Análise com IA
Cada capítulo é enviado ao GPT-4o com um prompt especializado que:
- Explica ideias profundamente
- Traduz para português
- Explica termos técnicos
- Dá exemplos práticos
- Não resume superficialmente

### 5. Geração de Documentos
O sistema gera:
- **Markdown**: Arquivo .md estruturado com sumário
- **PDF**: Documento formatado profissionalmente

## 🎨 Interface

A interface usa:
- **Angular 18** com standalone components
- **Tailwind CSS** com tema personalizado
- **Animações** suaves e elegantes
- **Design** inspirado em livros e tinta

## 📄 Formato da Análise

```markdown
# Análise Completa do Livro: {Título}

**Autor:** {Autor}
**Idioma Original:** {Idioma}

---

# Sumário
- [Capítulo 1](#capítulo-1)
- [Capítulo 2](#capítulo-2)
- [Glossário](#glossário)
- [Conclusões](#conclusões-gerais-da-obra)

---

# Capítulo 1 — Título

## Visão Geral do Capítulo
...

## Ideias Centrais Explicadas
...

## Conceitos Importantes e Definições
...

## Exemplos Práticos
...

## Termos Técnicos Traduzidos e Explicados
...

---

# Glossário
- **Termo A** — definição
- **Termo B** — definição

---

# Conclusões Gerais da Obra
...
```

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor, abra uma issue ou pull request.

## 📜 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.

---

Feito com ❤️ e ☕ por [Seu Nome]

