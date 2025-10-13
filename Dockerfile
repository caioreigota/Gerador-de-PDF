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
    # Fontes para renderização consistente (Chromium/wkhtml)
    fonts-dejavu-core \
    fonts-dejavu-extra \
    fonts-liberation2 \
    fonts-roboto \
    fonts-noto-core \
    fonts-noto-color-emoji \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Instala a fonte Inter (opcional). Se falhar o download, seguimos com fallbacks.
RUN set -eux; \
    mkdir -p /usr/local/share/fonts/inter; \
    curl -fL -o /usr/local/share/fonts/inter/InterVariable.ttf \
      https://github.com/rsms/inter/releases/latest/download/InterVariable.ttf || true; \
    fc-cache -f -v || true

# Define diretório de trabalho
WORKDIR /app

# Copia os arquivos do projeto
COPY . .

# Instala as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# (Opcional, mas recomendado) Instala navegadores do Playwright e dependências do SO
# Isso garante que o renderer Chromium esteja disponível como fallback, e para o endpoint /render
RUN python -m playwright install --with-deps || true

# Expõe a porta 5000 (usada pelo Flask)
EXPOSE 5000

# Comando para iniciar o Flask
CMD ["python", "app.py"]
