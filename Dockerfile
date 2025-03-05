# Usar uma imagem oficial do Python
FROM python:3.12-slim

# Definir diretório de trabalho dentro do container
WORKDIR /app

# Copiar os arquivos do projeto para dentro do container
COPY . /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    wget \
    libnss3 \
    libx11-xcb1 \
    libxcb-dri3-0 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libgbm1 \
    libgtk-3-0 \
    libasound2 \
    libxss1 \
    libxtst6 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Instalar o Playwright e seus navegadores
RUN playwright install --with-deps

# Expor a porta que o Flask vai rodar
EXPOSE 5000

# Comando para rodar o Flask
CMD ["python", "server.py"]
