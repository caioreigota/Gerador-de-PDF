# Mapeamento do Repositorio

## Visao geral

Este projeto e uma API Flask concentrada principalmente em [`app.py`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\app.py), voltada para conversao e manipulacao de documentos e midias. O repositorio e pequeno, com pouca fragmentacao de codigo, o que facilita localizar regras, mas concentra muitas responsabilidades em um unico arquivo.

O grafo gerado com Graphify identificou `77` nos, `191` arestas e `11` comunidades. Na pratica, essas comunidades se agrupam em cinco areas funcionais:

1. Extracao e conversao de documentos.
2. Geracao de DOCX a partir de payload estruturado.
3. Conversao de HTML para imagem, PDF e video.
4. Utilitarios de renderizacao, arquivos temporarios e CORS.
5. Infraestrutura de execucao e deploy.

## Estrutura principal

- [`app.py`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\app.py): API Flask, regras de negocio, helpers de renderizacao e endpoints.
- [`README.md`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\README.md): descricao funcional da API e exemplos de uso.
- [`requirements.txt`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\requirements.txt): dependencias Python do runtime.
- [`Dockerfile`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\Dockerfile): imagem base com binarios de sistema para renderizacao e extracao.
- [`Procfile`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\Procfile): ponto de entrada para deploy estilo Heroku/Render.
- [`.github/workflows/main.yml`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\.github\workflows\main.yml): workflow que dispara deploy em PR para `main`.

## Mapa funcional

### 1. Extracao e transformacao de documentos

Endpoints e funcoes ligados a PDF, DOC, DOCX e PPTX:

- [`extrair_texto()`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\app.py:159)
- [`pdf_para_imagem()`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\app.py:742)
- [`preencher_pdf_url()`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\app.py:786)
- [`gerar_imagem_vaga()`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\app.py:852)
- [`pptx_para_imagens()`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\app.py:930)
- [`pptx_para_pdf()`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\app.py:1116)
- [`pdf_para_docx()`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\app.py:2235)

Dependencias mais relevantes:

- `PyMuPDF` para leitura e rasterizacao de PDF.
- `textract` e `antiword` para `.doc`.
- `python-pptx` para leitura de apresentacoes.
- `pdf2docx` para conversao editavel de PDF para DOCX.

### 2. Geracao de curriculo e preenchimento de template DOCX

Esse bloco transforma um payload JSON em curriculo `.docx` ou usa um template remoto com placeholders:

- [`gerar_curriculo_docx()`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\app.py:329)
- [`gerar_docx_de_template()`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\app.py:680)
- [`_build_text_blocks_from_payload()`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\app.py:546)
- [`_replace_placeholders_in_doc()`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\app.py:665)

Esse conjunto forma uma subarea coesa do sistema e aparece como comunidade propria no grafo.

### 3. Renderizacao HTML para imagem, PDF e video

Esse e o nucleo multimidia da API:

- [`html_para_imagem()`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\app.py:1591)
- [`html_para_pdf()`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\app.py:2015)
- [`render()`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\app.py:2103)

Helpers centrais:

- [`chromium_screenshot()`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\app.py:1322)
- [`record_webm()`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\app.py:1399)
- [`compute_trim()`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\app.py:1479)
- [`write_temp_html()`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\app.py:1545)
- [`_needs_modern_renderer()`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\app.py:1568)

O grafo mostrou que `html_para_imagem()` e `render()` funcionam como nos-ponte entre varias comunidades, o que reforca que a pipeline de renderizacao e um dos eixos arquiteturais mais importantes do projeto.

### 4. Utilitarios transversais

Alguns helpers sustentam varios fluxos:

- [`_resolve_cors_origin()`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\app.py:77)
- [`_cors_preflight()`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\app.py:86)
- [`_cors_headers()`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\app.py:102)
- [`health()`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\app.py:1564)
- [`ensure_ffmpeg()`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\app.py:1206)
- [`has_wkhtmltopdf()`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\app.py:1215)
- [`has_wkhtmltoimage()`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\app.py:1219)

## Dependencias externas e runtime

O sistema depende de bibliotecas Python e tambem de binarios do sistema operacional:

- `wkhtmltopdf` e `wkhtmltoimage` para HTML -> PDF/imagem.
- `FFmpeg` para a etapa de video.
- `Playwright` com browsers instalados para renderizacao Chromium.
- `antiword` para extracao de `.doc`.

O [`Dockerfile`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\Dockerfile) prepara esse ambiente e o [`requirements.txt`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\requirements.txt) explica boa parte dos acoplamentos do dominio.

## Observacoes arquiteturais

- O projeto esta funcionalmente bem definido, mas muito concentrado em um unico modulo.
- A maior parte dos fluxos compartilha tratamento de arquivos temporarios, envio de arquivos e validacao de entrada.
- A ausencia de divisao por modulos sugere uma oportunidade clara de extrair camadas como `routes`, `services`, `renderers` e `document_handlers`.
- O workflow de CI atual esta focado em deploy por PR e aparece como um no relativamente isolado no grafo, o que indica pouca integracao com testes automatizados ou validacoes de qualidade.

## Artefatos do grafo

Os arquivos gerados pelo mapeamento estao em [`graphify-out`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\graphify-out):

- [`graph.html`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\graphify-out\graph.html)
- [`graph.json`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\graphify-out\graph.json)
- [`GRAPH_REPORT.md`](C:\Users\caior\Documents\Projetos Programação\Gerador-de-PDF-1\graphify-out\GRAPH_REPORT.md)

Esses arquivos servem como base para navegacao futura e para novas consultas sobre relacoes entre endpoints, helpers e dependencias.
