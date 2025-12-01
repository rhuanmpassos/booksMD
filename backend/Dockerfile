FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema para WeasyPrint
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código
COPY . .

# Cria diretórios necessários
RUN mkdir -p uploads outputs data

# Expõe porta
EXPOSE 8000

# Comando de start
# Usa variável PORT do Render (ou 8000 como fallback)
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}

