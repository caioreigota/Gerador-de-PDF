FROM python:3.11-slim

# Instala dependências do sistema e do LibreOffice
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice \
    curl \
    unzip \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    fonts-dejavu-core \
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
