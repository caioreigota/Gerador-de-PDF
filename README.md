# Gerador de PDF/Imagem/Vídeo (Flask)

Aplicação Flask com utilitários para manipulação de PDF, HTML e geração de mídia. Inclui endpoints para:
- Converter a primeira página do PDF em imagem PNG
- Preencher marcadores em PDFs e HTML (placeholders)
- Gerar imagem de vaga a partir de um PDF base
- Renderizar HTML em vídeo MP4 (via Playwright + FFmpeg)
- Extrair texto de PDF, DOC e DOCX


## Requisitos

- Python 3.11
- Dependências Python listadas em `requirements.txt`
- Binários do SO usados por alguns recursos:
  - wkhtmltoimage/wkhtmltopdf (para `imgkit`)
  - FFmpeg (para `/render`)
  - Playwright (browsers instalados; para `/render`)
  - antiword (necessário para extrair texto de `.doc` com `textract`)

No Docker, o `Dockerfile` já instala `wkhtmltopdf` e `antiword`. Para o endpoint `/render`, é recomendável adicionar a instalação dos browsers do Playwright durante o build (ver notas abaixo).


## Como executar (local)

1) Crie e ative um virtualenv, depois instale as dependências:

```
python -m venv .venv
. .venv/bin/activate    # Linux/Mac
# .venv\Scripts\activate  # Windows PowerShell
pip install -r requirements.txt
```

2) (Opcional, apenas se for usar `/render`) instale os browsers do Playwright e garanta o FFmpeg instalado no sistema:

```
python -m playwright install --with-deps  # Linux
# ou
python -m playwright install              # Windows/macOS
```

3) Execute a aplicação:

```
python app.py
```

A API ficará disponível em `http://localhost:5000`.


## Como executar (Docker)

```
docker build -t gerador-pdf .
docker run --rm -p 5000:5000 gerador-pdf
```

Se precisar do endpoint `/render`, considere adicionar ao Dockerfile um passo para instalar os browsers do Playwright durante o build, por exemplo:

```
RUN python -m playwright install --with-deps
```


## Endpoints

- Saúde
  - GET `/healthz`
  - Retorna `{ "ok": true }`

- PDF → Imagem (primeira página)
  - POST `/pdf-para-imagem`
  - Body (JSON): `{ "pdf_url": "https://.../arquivo.pdf" }`
  - Resposta: arquivo PNG (attachment)

- Preencher marcadores em PDF remoto
  - POST `/preencher-pdf-url`
  - Body (JSON): `{ "pdf_url": "https://.../arquivo.pdf", "substituicoes": { "CHAVE": "valor" } }`
  - Observação: substitui ocorrências de `[CHAVE]` pelo valor informado
  - Resposta: arquivo PDF (attachment)

- Preencher placeholders em HTML remoto e gerar imagem
  - POST `/preencher-html-url`
  - Body (JSON): `{ "html_url": "https://.../arquivo.html", "substituicoes": { "nome": "João" } }`
  - Resposta: arquivo PNG (attachment)

- HTML → PDF
  - POST `/html-para-pdf`
  - Form-data (multipart):
    - `file` (arquivo .html) ou `html` (string com HTML)
    - Opcionais: `format` (ex.: A4), `margin_top`, `margin_right`, `margin_bottom`, `margin_left`, `filename` (ou `nome_arquivo`) para definir o nome do PDF de saída
  - Resposta: arquivo PDF (attachment)

- HTML ? Imagem
  - POST /html-para-imagem`n  - Form-data (multipart):
    - ile (arquivo .html) ou html (string com HTML)
    - Opcionais: ormat (png|jpeg|webp, padr�o: png), width, height (tamanho de renderiza��o), out_width, out_height (tamanho FINAL), it (contain/cover/ill), g (hex para padding), quality (1�100 p/ JPEG/WEBP), 	ransparent (PNG/WEBP), ilename`n  - Resposta: arquivo de imagem (attachment)

- Gerar imagem de vaga a partir de PDF base
  - POST `/gerar-imagem-vaga`
  - Body (JSON): `{ "pdf_url": "https://.../modelo.pdf", "substituicoes": { "cargo": "...", "localizacao": "...", ... } }`
  - Resposta: arquivo PNG (attachment)

- Renderizar HTML em vídeo MP4 (Story/Reels)
  - POST `/render`
  - Form-data (multipart):
    - `file` (arquivo .html) ou `html` (string com HTML)
    - Parâmetros opcionais: `content_seconds`, `width`, `height`, `target_fps`, `auto_trim_head`, `auto_trim_tail`, `zero_anim_delay`, `scene_threshold`, `head_pad`, `tail_pad`
  - Resposta: arquivo MP4 (attachment)
  - Requer Playwright + FFmpeg instalados

- Extrair texto de PDF/DOC/DOCX
  - POST `/extrair-texto`
  - Form-data (multipart): `file=@/caminho/arquivo.pdf|.doc|.docx`
  - Resposta (JSON): `{ "texto": "conteúdo extraído" }`
  - Observação: `.doc` requer `textract` + `antiword` no sistema (no Dockerfile já incluído)


## Exemplos de uso (curl)

- Extrair texto (PDF/DOC/DOCX):
```
curl -F "file=@/caminho/arquivo.pdf" http://localhost:5000/extrair-texto
```

- PDF → Imagem:
```
curl -X POST http://localhost:5000/pdf-para-imagem \
  -H "Content-Type: application/json" \
  -d '{"pdf_url":"https://exemplo.com/arquivo.pdf"}' --output pagina.png
```

- Preencher PDF com marcadores:
```
curl -X POST http://localhost:5000/preencher-pdf-url \
  -H "Content-Type: application/json" \
  -d '{"pdf_url":"https://exemplo.com/modelo.pdf","substituicoes":{"NOME":"Maria","CPF":"123"}}' \
  --output preenchido.pdf
```

- Render (HTML → MP4):
```
curl -X POST http://localhost:5000/render \
  -F "file=@/caminho/index.html" \
  -F "content_seconds=6" -F "target_fps=30" --output render.mp4
```

- HTML → PDF:
```
curl -X POST http://localhost:5000/html-para-pdf \
  -F "file=@/caminho/arquivo.html" \
  -F "format=A4" \
  -F "filename=meu-documento.pdf" \
  --output meu-documento.pdf
```

- HTML → Imagem (PNG):
```
curl -X POST http://localhost:5000/html-para-imagem \
  -F "file=@/caminho/arquivo.html" \
  -F "format=png" -F "width=1080" -F "height=1080" \
  --output saida.png
```

- HTML → Imagem (JPEG com qualidade):
```
curl -X POST http://localhost:5000/html-para-imagem \
  -F "html=<h1>Olá</h1>" \
  -F "format=jpeg" -F "quality=90" \
  --output saida.jpg
```


## Configurações

- Tamanho máximo de upload: 50 MB (definido em `app.py:1` via `app.config['MAX_CONTENT_LENGTH']`).
- Procfile para deploy (ex.: Render/Heroku): ver `Procfile:1`.
- Dependências: ver `requirements.txt:1`.
- Dockerfile com pacotes de SO necessários: ver `Dockerfile:1`.


## Estrutura básica

- Código principal: `app.py:1`
- Dependências Python: `requirements.txt:1`
- Docker: `Dockerfile:1`
- Procfile: `Procfile:1`


## Notas

- Em Windows, exclusão de temporários é feita após resposta para evitar lock de arquivo.
- Se não for usar `/render`, Playwright/FFmpeg podem ser opcionais.



