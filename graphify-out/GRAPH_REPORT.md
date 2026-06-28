# Graph Report - .  (2026-06-25)

## Corpus Check
- Corpus is ~8,854 words - fits in a single context window. You may not need a graph.

## Summary
- 77 nodes · 191 edges · 11 communities (10 shown, 1 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 8 edges (avg confidence: 0.79)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY__extract_text_doc()  _extract_text_docx()|_extract_text_doc() / _extract_text_docx()]]
- [[_COMMUNITY_Flask Media Conversion Service  HTML to Image Conversion|Flask Media Conversion Service / HTML to Image Conversion]]
- [[_COMMUNITY__add_bullet()  _add_section_title()|_add_bullet() / _add_section_title()]]
- [[_COMMUNITY_float  compute_trim()|float / compute_trim()]]
- [[_COMMUNITY_bool  has_wkhtmltoimage()|bool / has_wkhtmltoimage()]]
- [[_COMMUNITY_app.py  _cors_headers()|app.py / _cors_headers()]]
- [[_COMMUNITY__build_text_blocks_from_payload()  gerar_docx_de_template()|_build_text_blocks_from_payload() / gerar_docx_de_template()]]
- [[_COMMUNITY_chromium_screenshot()  file_url()|chromium_screenshot() / file_url()]]
- [[_COMMUNITY_cortar_redimensionar_imagem()  pdf_para_docx()|cortar_redimensionar_imagem() / pdf_para_docx()]]
- [[_COMMUNITY_html_para_pdf()  Grava o HTML recebido (texto ou arquivo enviado) no tmpdir e retorna o caminho.|html_para_pdf() / Grava o HTML recebido (texto ou arquivo enviado) no tmpdir e retorna o caminho.]]
- [[_COMMUNITY__needs_modern_renderer()  Heurística detecta uso de CSS moderno (gridflex) e outras pistas.     Se enco|_needs_modern_renderer() / Heurística: detecta uso de CSS moderno (grid/flex) e outras pistas.     Se enco]]

## God Nodes (most connected - your core abstractions)
1. `str` - 32 edges
2. `Path` - 14 edges
3. `html_para_imagem()` - 14 edges
4. `render()` - 12 edges
5. `int` - 11 edges
6. `chromium_screenshot()` - 11 edges
7. `gerar_curriculo_docx()` - 10 edges
8. `record_webm()` - 9 edges
9. `Flask Media Conversion Service` - 9 edges
10. `float` - 8 edges

## Surprising Connections (you probably didn't know these)
- `PR Deploy Trigger Workflow` --rationale_for--> `Flask Media Conversion Service`  [INFERRED]
  .github/workflows/main.yml → app.py
- `Python Runtime Dependencies` --rationale_for--> `Flask Media Conversion Service`  [INFERRED]
  requirements.txt → app.py
- `Python Runtime Dependencies` --rationale_for--> `Document Text Extraction`  [INFERRED]
  requirements.txt → app.py
- `Project Feature Overview` --references--> `HTML to PDF Conversion`  [EXTRACTED]
  README.md → app.py
- `Python Runtime Dependencies` --rationale_for--> `HTML to MP4 Rendering`  [INFERRED]
  requirements.txt → app.py

## Hyperedges (group relationships)
- **Media Generation Endpoints** — app_html_pdf_conversion, app_html_image_conversion, app_html_video_rendering [INFERRED 0.87]
- **Document Transformation Endpoints** — app_text_extraction, app_pdf_placeholder_fill, app_pdf_docx_conversion [INFERRED 0.84]

## Communities (11 total, 1 thin omitted)

### Community 0 - "_extract_text_doc() / _extract_text_docx()"
Cohesion: 0.24
Nodes (11): _extract_text_doc(), _extract_text_docx(), _extract_text_pdf(), extrair_texto(), gerar_imagem_vaga(), pdf_para_imagem(), pptx_para_imagens(), pptx_para_pdf() (+3 more)

### Community 1 - "Flask Media Conversion Service / HTML to Image Conversion"
Cohesion: 0.44
Nodes (10): Flask Media Conversion Service, HTML to Image Conversion, HTML to PDF Conversion, HTML to MP4 Rendering, PDF to DOCX Conversion, PDF Placeholder Filling, Document Text Extraction, Project Feature Overview (+2 more)

### Community 2 - "_add_bullet() / _add_section_title()"
Cohesion: 0.20
Nodes (10): _add_bullet(), _add_section_title(), _add_text_paragraphs(), gerar_curriculo_docx(), Adiciona uma borda inferior (linha) ao parágrafo via OXML.     size_eights: esp, Configura tamanho de página, margens e fonte padrão conforme especificação., Adiciona parágrafos simples (respeitando quebras de linha)., Gera um .docx de currículo a partir do JSON fornecido na especificação.      A (+2 more)

### Community 3 - "float / compute_trim()"
Cohesion: 0.39
Nodes (8): float, compute_trim(), detect_scene_changes(), ensure_ffmpeg(), POST /render     Form-data:       - file: arquivo .html  (opcional se mandar ', render(), video_duration(), webm_to_mp4_precise()

### Community 4 - "bool / has_wkhtmltoimage()"
Cohesion: 0.39
Nodes (8): bool, has_wkhtmltoimage(), has_wkhtmltopdf(), html_para_imagem(), prepare_page(), Verifica se o binário wkhtmltoimage está disponível no PATH., Converte um HTML em imagem.     Aceita:       - multipart/form-data com campo, record_webm()

### Community 5 - "app.py / _cors_headers()"
Cohesion: 0.43
Nodes (5): _cors_headers(), _cors_preflight(), preencher_pdf_url(), _resolve_cors_origin(), substituir_textos()

### Community 6 - "_build_text_blocks_from_payload() / gerar_docx_de_template()"
Cohesion: 0.33
Nodes (6): _build_text_blocks_from_payload(), gerar_docx_de_template(), Monta mapeamento de placeholders -> texto a partir do JSON de entrada., Baixa um arquivo .docx de 'template_url' e substitui placeholders [CHAVE]     c, _replace_placeholders_in_doc(), _replace_placeholders_in_paragraph()

### Community 7 - "chromium_screenshot() / file_url()"
Cohesion: 0.53
Nodes (6): chromium_screenshot(), file_url(), measure_body_size(), Abre SEM gravação, mede o tamanho real do <body> e devolve (w,h)., Renderiza o HTML com Chromium/Playwright e retorna o caminho de um PNG temporári, Path

### Community 8 - "cortar_redimensionar_imagem() / pdf_para_docx()"
Cohesion: 0.40
Nodes (5): cortar_redimensionar_imagem(), pdf_para_docx(), Converte um PDF em um arquivo .docx com opção EDITÁVEL.     - Modo 'editable' (, redimensionar_imagem(), int

### Community 9 - "html_para_pdf() / Grava o HTML recebido (texto ou arquivo enviado) no tmpdir e retorna o caminho."
Cohesion: 0.50
Nodes (4): html_para_pdf(), Grava o HTML recebido (texto ou arquivo enviado) no tmpdir e retorna o caminho., Converte um HTML recebido em PDF.     Aceita:       - multipart/form-data com, write_temp_html()

## Knowledge Gaps
- **1 isolated node(s):** `PR Deploy Trigger Workflow`
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `str` connect `_extract_text_doc() / _extract_text_docx()` to `_add_bullet() / _add_section_title()`, `float / compute_trim()`, `bool / has_wkhtmltoimage()`, `app.py / _cors_headers()`, `_build_text_blocks_from_payload() / gerar_docx_de_template()`, `chromium_screenshot() / file_url()`, `cortar_redimensionar_imagem() / pdf_para_docx()`, `html_para_pdf() / Grava o HTML recebido (texto ou arquivo enviado) no tmpdir e retorna o caminho.`?**
  _High betweenness centrality (0.156) - this node is a cross-community bridge._
- **Why does `html_para_imagem()` connect `bool / has_wkhtmltoimage()` to `_extract_text_doc() / _extract_text_docx()`, `float / compute_trim()`, `app.py / _cors_headers()`, `chromium_screenshot() / file_url()`, `cortar_redimensionar_imagem() / pdf_para_docx()`, `html_para_pdf() / Grava o HTML recebido (texto ou arquivo enviado) no tmpdir e retorna o caminho.`, `_needs_modern_renderer() / Heurística: detecta uso de CSS moderno (grid/flex) e outras pistas.     Se enco`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Why does `render()` connect `float / compute_trim()` to `_extract_text_doc() / _extract_text_docx()`, `bool / has_wkhtmltoimage()`, `app.py / _cors_headers()`, `chromium_screenshot() / file_url()`, `cortar_redimensionar_imagem() / pdf_para_docx()`, `html_para_pdf() / Grava o HTML recebido (texto ou arquivo enviado) no tmpdir e retorna o caminho.`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **What connects `Recebe um arquivo (PDF, DOC ou DOCX) via multipart/form-data (campo 'file')`, `Adiciona uma borda inferior (linha) ao parágrafo via OXML.     size_eights: esp`, `Configura tamanho de página, margens e fonte padrão conforme especificação.` to the rest of the system?**
  _17 weakly-connected nodes found - possible documentation gaps or missing edges._