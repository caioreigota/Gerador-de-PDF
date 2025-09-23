FROM python:3.11-bullseye

# Evita prompts interativos no apt
ENV DEBIAN_FRONTEND=noninteractive

# Dependências do sistema:
# - wkhtmltopdf (inclui wkhtmltoimage) para o endpoint de imagem HTML
# - antiword para extrair .doc com textract
# - fontes e libs gráficas necessárias
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    wkhtmltopdf \
    antiword \
    xfonts-base \
    fontconfig \
    libjpeg62-turbo \
    libxrender1 \
    libxtst6 \
    libxext6 \
    libfontconfig1 \
    libfreetype6 \
    && rm -rf /var/lib/apt/lists/*

# Define diretório de trabalho
WORKDIR /app

# Copia os arquivos do projeto
COPY . .

# Instala as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta 5000 (usada pelo Flask)
EXPOSE 5000

# Comando para iniciar o Flask
CMD ["python", "app.py"]
