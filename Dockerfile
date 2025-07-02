FROM python:3.11-slim

# Instala dependências do sistema e do LibreOffice
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    xfonts-base \
    libjpeg62-turbo \
    libxrender1 \
    libxtst6 \
    libxext6 \
    libfontconfig1 \
    libfreetype6 \
    libpng16-16 \
    && apt-get clean \
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
