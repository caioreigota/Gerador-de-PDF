from flask import Flask, request, send_file, jsonify, after_this_request
import fitz  # PyMuPDF
import tempfile
import json
import requests
import zipfile
import os
import re
import shutil
import time
from pathlib import Path
from pptx import Presentation
from PIL import Image, ImageDraw, ImageChops, ImageOps
from io import BytesIO
import subprocess
import gc
from playwright.sync_api import sync_playwright
from werkzeug.utils import secure_filename
from urllib.parse import urlparse, unquote
from PIL import ImageFont
import imgkit
from io import BytesIO

# Suporte a DOCX e DOC
try:
    from docx import Document  # python-docx
except Exception:
    Document = None

try:
    import textract  # para .doc (requer 'antiword' no sistema)
except Exception:
    textract = None

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # Limite de 50MB por upload

def substituir_textos(doc, substituicoes):
    for page in doc:
        insercoes = []
        aplicar_redaction = False

        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    texto_original = span["text"]
                    for chave, novo_valor in substituicoes.items():
                        marcador = f"[{chave}]"
                        if marcador in texto_original:
                            bbox = span["bbox"]
                            tamanho = span["size"]
                            cor_int = span["color"]
                            r = (cor_int >> 16) & 255
                            g = (cor_int >> 8) & 255
                            b = cor_int & 255
                            cor = (r / 255, g / 255, b / 255)

                            # Marcar para redaction
                            page.add_redact_annot(bbox, fill=(1, 1, 1), cross_out=False)
                            aplicar_redaction = True

                            novo_texto = texto_original.replace(marcador, novo_valor)
                            insercoes.append((bbox, novo_texto, tamanho, cor))

        if aplicar_redaction:
            page.apply_redactions()

        for bbox, texto, tamanho, cor in insercoes:
            x = bbox[0]
            y = bbox[1] + tamanho * 0.8  # ajuste fino vertical
            page.insert_text(
                (x, y),
                texto,
                fontsize=tamanho,
                color=cor,
                fontname="helv",
                overlay=True,
            )

@app.route('/extrair-texto', methods=['POST'])
def extrair_texto():
    """
    Recebe um arquivo (PDF, DOC ou DOCX) via multipart/form-data (campo 'file')
    e retorna o texto extraído em JSON.
    Resposta: { "texto": "..." }
    """
    uploaded = request.files.get('file')
    if not uploaded:
        return jsonify({"error": "Envie o arquivo no campo 'file' (multipart/form-data)."}), 400

    filename = secure_filename(uploaded.filename or '')
    if not filename:
        return jsonify({"error": "Nome de arquivo inválido."}), 400

    _, ext = os.path.splitext(filename)
    ext = (ext or '').lower()

    # Salva em arquivo temporário para lidar com libs que precisam de caminho (ex: textract)
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp_path = tmp.name
        uploaded.stream.seek(0)
        shutil.copyfileobj(uploaded.stream, tmp)

    try:
        if ext == '.pdf':
            texto = _extract_text_pdf(tmp_path)
        elif ext == '.docx':
            texto = _extract_text_docx(tmp_path)
        elif ext == '.doc':
            texto = _extract_text_doc(tmp_path)
        else:
            return jsonify({"error": f"Extensão não suportada: {ext}. Use PDF, DOC ou DOCX."}), 415

        return jsonify({"texto": texto})
    except Exception as e:
        return jsonify({"error": f"Falha ao extrair texto: {str(e)}"}), 500
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


def _extract_text_pdf(path: str) -> str:
    doc = fitz.open(path)
    try:
        parts = []
        for page in doc:
            parts.append(page.get_text("text"))
        return "\n".join(parts).strip()
    finally:
        doc.close()


def _extract_text_docx(path: str) -> str:
    if Document is None:
        raise RuntimeError("Suporte a DOCX requer 'python-docx' instalado.")
    d = Document(path)
    # Parágrafos
    paras = [p.text for p in d.paragraphs if p.text]
    # Tabelas
    tables_text = []
    for t in d.tables:
        for row in t.rows:
            cells = [c.text.strip() for c in row.cells]
            if any(cells):
                tables_text.append("\t".join(cells))
    parts = []
    if paras:
        parts.append("\n".join(paras))
    if tables_text:
        parts.append("\n".join(tables_text))
    return "\n\n".join(parts).strip()


def _extract_text_doc(path: str) -> str:
    # Usa textract + antiword (no SO) para .doc
    if textract is None:
        raise RuntimeError("Suporte a .doc requer 'textract' instalado e o utilitário 'antiword' no sistema.")
    content = textract.process(path)  # retorna bytes
    return content.decode('utf-8', errors='replace').strip()

@app.route('/pdf-para-imagem', methods=['POST'])
def pdf_para_imagem():
    data = request.get_json()
    if not data or 'pdf_url' not in data:
        return {'error': 'pdf_url é obrigatório'}, 400

    try:
        response = requests.get(data['pdf_url'])
        response.raise_for_status()
    except Exception as e:
        return {'error': f'Erro ao baixar PDF: {str(e)}'}, 400

    try:
        parsed_url = urlparse(data['pdf_url'])
        pdf_filename = os.path.basename(parsed_url.path)
        pdf_filename = unquote(pdf_filename)
        nome_base = os.path.splitext(pdf_filename)[0]
        nome_imagem = f"{nome_base}.png"

        doc = fitz.open(stream=response.content, filetype="pdf")
        if len(doc) == 0:
            return {'error': 'PDF sem páginas'}, 400

        page = doc[0]
        pix = page.get_pixmap(dpi=150)

        img_bytes = BytesIO()
        img_bytes.write(pix.tobytes("png"))
        img_bytes.seek(0)

        doc.close()
        gc.collect()

        return send_file(
            img_bytes,
            mimetype="image/png",
            as_attachment=True,
            download_name=nome_imagem
        )

    except Exception as e:
        return {'error': f'Erro ao processar PDF: {str(e)}'}, 500


@app.route('/preencher-pdf-url', methods=['POST'])
def preencher_pdf_url():
    data = request.get_json()
    if not data or 'pdf_url' not in data or 'substituicoes' not in data:
        return {'error': 'pdf_url e substituicoes são obrigatórios'}, 400

    try:
        response = requests.get(data['pdf_url'])
        response.raise_for_status()
    except Exception as e:
        return {'error': f'Erro ao baixar PDF: {str(e)}'}, 400

    substituicoes = data['substituicoes']
    if not isinstance(substituicoes, dict) or not substituicoes:
        return {'error': 'Substituições inválidas ou vazias'}, 400

    try:
        doc = fitz.open(stream=response.content, filetype="pdf")
        substituir_textos(doc, substituicoes)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_out:
            doc.save(tmp_out.name, deflate=True, garbage=4, clean=True)
            doc.close()
            gc.collect()
            return send_file(
                tmp_out.name,
                mimetype="application/pdf",
                as_attachment=True,
                download_name="preenchido.pdf"
            )
    except Exception as e:
        return {'error': f'Erro ao processar PDF: {str(e)}'}, 500
    

@app.route('/preencher-html-url', methods=['POST'])
def preencher_html_url():
    data = request.get_json()
    if not data or 'html_url' not in data or 'substituicoes' not in data:
        return {'error': 'html_url e substituicoes são obrigatórios'}, 400

    try:
        response = requests.get(data['html_url'])
        response.raise_for_status()
        html = response.text
    except Exception as e:
        return {'error': f'Erro ao baixar HTML: {str(e)}'}, 400

    substituicoes = data['substituicoes']
    if not isinstance(substituicoes, dict) or not substituicoes:
        return {'error': 'Substituições inválidas ou vazias'}, 400

    try:
        for chave, valor in substituicoes.items():
            html = html.replace(f"{{{{ {chave} }}}}", valor)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as img_file:
            imgkit.from_string(html, img_file.name, options={"format": "png", "width": 1080, "height": 1080})
            return send_file(
                img_file.name,
                mimetype="image/png",
                as_attachment=True,
                download_name="imagem_gerada.png"
            )
    except Exception as e:
        return {'error': f'Erro ao processar HTML: {str(e)}'}, 500

@app.route('/gerar-imagem-vaga', methods=['POST'])
def gerar_imagem_vaga():
    def draw_text_wrap(draw, text, font, max_width, x, y, line_spacing=10):
        words = text.split()
        line = ""
        lines = []
        for word in words:
            test_line = f"{line} {word}".strip()
            width, _ = draw.textsize(test_line, font=font)
            if width <= max_width:
                line = test_line
            else:
                lines.append(line)
                line = word
        lines.append(line)

        for i, line in enumerate(lines):
            draw.text((x, y + i * (font.size + line_spacing)), line, font=font, fill="black")

    data = request.get_json()
    if not data or 'pdf_url' not in data or 'substituicoes' not in data:
        return {'error': 'pdf_url e substituicoes são obrigatórios'}, 400

    try:
        response = requests.get(data['pdf_url'])
        response.raise_for_status()
    except Exception as e:
        return {'error': f'Erro ao baixar PDF: {str(e)}'}, 400

    try:
        doc = fitz.open(stream=response.content, filetype="pdf")
        page = doc[0]
        pix = page.get_pixmap(dpi=300)
        img = Image.open(BytesIO(pix.tobytes("png"))).convert("RGB")
        draw = ImageDraw.Draw(img)

        # Fonte segura para ambientes Linux/Docker
        try:
            font_padrao = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size=28)
        except:
            font_padrao = ImageFont.load_default()

        campos = data["substituicoes"]

        # Coordenadas ajustadas com base no modelo
        coordenadas = {
            "cargo": (130, 420),
            "complemento": (130, 470),
            "Requisito 1": (130, 540),
            "Requisito 2": (130, 580),
            "Requisito 3": (130, 620),
            "Requisito 4": (130, 660),
            "Requisito 5": (130, 700),
            "localizacao": (200, 820),
            "modalidade": (530, 820)
        }

        for chave, pos in coordenadas.items():
            texto = campos.get(chave, "")
            if texto:
                draw_text_wrap(draw, texto, font_padrao, max_width=580, x=pos[0], y=pos[1])

        img_bytes = BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        doc.close()
        gc.collect()

        return send_file(
            img_bytes,
            mimetype="image/png",
            as_attachment=True,
            download_name="vaga_preenchida.png"
        )

    except Exception as e:
        return {'error': f'Erro ao gerar imagem: {str(e)}'}, 500

@app.route('/pptx-para-imagens', methods=['POST'])
def pptx_para_imagens():
    data = request.get_json()
    if not data or 'pptx_url' not in data:
        return {'error': 'pptx_url é obrigatório'}, 400

    try:
        response = requests.get(data['pptx_url'])
        response.raise_for_status()
    except Exception as e:
        return {'error': f'Erro ao baixar PPTX: {str(e)}'}, 400

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pptx") as tmp_pptx:
            tmp_pptx.write(response.content)
            pptx_path = tmp_pptx.name

        output_dir = tempfile.mkdtemp()

        subprocess.run([
            "libreoffice",
            "--headless",
            "--convert-to", "png",
            "--outdir", output_dir,
            pptx_path
        ], check=True)

        zip_path = os.path.join(output_dir, "slides.zip")
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file_name in sorted(os.listdir(output_dir)):
                if file_name.endswith(".png"):
                    file_path = os.path.join(output_dir, file_name)
                    zipf.write(file_path, arcname=file_name)

        gc.collect()

        return send_file(
            zip_path,
            mimetype="application/zip",
            as_attachment=True,
            download_name="slides_imagens.zip"
        )

    except subprocess.CalledProcessError as e:
        return {'error': f'Erro ao converter com LibreOffice: {str(e)}'}, 500
    except Exception as e:
        return {'error': f'Erro ao processar PPTX: {str(e)}'}, 500


@app.route('/redimensionar-imagem', methods=['POST'])
def redimensionar_imagem():
    if 'image' not in request.files:
        return {'error': 'Imagem é obrigatória'}, 400

    largura = request.form.get('largura') or request.form.get('width')
    altura = request.form.get('altura') or request.form.get('height')
    if not largura or not altura:
        return {'error': 'Largura e altura são obrigatórios'}, 400

    try:
        largura = int(largura)
        altura = int(altura)
        if largura <= 0 or altura <= 0:
            raise ValueError
    except ValueError:
        return {'error': 'Largura e altura devem ser números inteiros positivos'}, 400

    try:
        img_file = request.files['image']
        img = Image.open(img_file.stream)
        img = img.resize((largura, altura))

        output = BytesIO()
        formato = img.format or 'PNG'
        img.save(output, format=formato)
        output.seek(0)

        mimetype = img_file.mimetype or f'image/{formato.lower()}'
        ext = formato.lower()
        return send_file(
            output,
            mimetype=mimetype,
            as_attachment=True,
            download_name=f'resized.{ext}'
        )
    except Exception as e:
        return {'error': f'Erro ao redimensionar imagem: {str(e)}'}, 500


@app.route('/cortar-redimensionar-imagem', methods=['POST'])
def cortar_redimensionar_imagem():
    if 'image' not in request.files:
        return {'error': 'Imagem é obrigatória'}, 400

    largura = request.form.get('largura') or request.form.get('width')
    altura = request.form.get('altura') or request.form.get('height')
    top = request.form.get('top') or request.form.get('crop_top') or '0'
    right = request.form.get('right') or request.form.get('crop_right') or '0'
    left = request.form.get('left') or request.form.get('crop_left') or '0'
    bottom = (
        request.form.get('bottom')
        or request.form.get('footer')
        or request.form.get('crop_bottom')
        or '0'
    )
    if not largura or not altura:
        return {'error': 'Largura e altura são obrigatórios'}, 400

    try:
        largura = int(largura)
        altura = int(altura)
        top = int(top)
        right = int(right)
        left = int(left)
        bottom = int(bottom)
        if (
            largura <= 0
            or altura <= 0
            or top < 0
            or right < 0
            or left < 0
            or bottom < 0
        ):
            raise ValueError
    except ValueError:
        return {'error': 'Parâmetros de corte devem ser inteiros não negativos e largura/altura positivos'}, 400

    try:
        img_file = request.files['image']
        img = Image.open(img_file.stream).convert('RGB')
        background_color = img.getpixel((0, 0))

        def crop_blank_top_bottom(im, threshold=250, blank_ratio=0.99):
            gray = im.convert('L')
            width, height = gray.size
            pixels = gray.load()

            def row_is_blank(y):
                blank = 0
                for x in range(width):
                    if pixels[x, y] >= threshold:
                        blank += 1
                return blank / width >= blank_ratio

            top = 0
            bottom = height - 1
            while top < height and row_is_blank(top):
                top += 1
            while bottom > top and row_is_blank(bottom):
                bottom -= 1
            return im.crop((0, top, width, bottom + 1))

        img = crop_blank_top_bottom(img)


        width, height = img.size
        left = max(0, min(left, width - 1))
        top = max(0, min(top, height - 1))
        right = max(0, min(right, width - left - 1))
        bottom = max(0, min(bottom, height - top - 1))
        img = img.crop((left, top, width - right, height - bottom))


        img.thumbnail((largura, altura), Image.LANCZOS)

        background = Image.new("RGB", (largura, altura), background_color)
        offset = ((largura - img.size[0]) // 2, (altura - img.size[1]) // 2)
        background.paste(img, offset)

        output = BytesIO()
        formato = img_file.mimetype.split('/')[-1].upper() if img_file.mimetype else 'PNG'
        background.save(output, format=formato)
        output.seek(0)

        mimetype = img_file.mimetype or f'image/{formato.lower()}'
        ext = formato.lower()
        return send_file(
            output,
            mimetype=mimetype,
            as_attachment=True,
            download_name=f'resized.{ext}'
        )
    except Exception as e:
        return {'error': f'Erro ao processar imagem: {str(e)}'}, 500


@app.route('/pptx-para-pdf', methods=['POST'])
def pptx_para_pdf():
    data = request.get_json()
    if not data or 'pptx_url' not in data or 'substituicoes' not in data:
        return {'error': 'pptx_url e substituicoes são obrigatórios'}, 400

    try:
        response = requests.get(data['pptx_url'])
        response.raise_for_status()
    except Exception as e:
        return {'error': f'Erro ao baixar PPTX: {str(e)}'}, 400

    try:
        substituicoes = data['substituicoes']
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pptx") as tmp_pptx:
            tmp_pptx.write(response.content)
            pptx_path = tmp_pptx.name

        prs = Presentation(pptx_path)
        imagens = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for par in shape.text_frame.paragraphs:
                        for run in par.runs:
                            for chave, valor in substituicoes.items():
                                marcador = f"[{chave}]"
                                if marcador in run.text:
                                    run.text = run.text.replace(marcador, valor)

        for slide in prs.slides:
            img = Image.new("RGB", (1280, 720), color="white")
            draw = ImageDraw.Draw(img)
            y = 20
            for shape in slide.shapes:
                if shape.has_text_frame:
                    draw.text((20, y), shape.text, fill="black")
                    y += 30
            img_bytes = BytesIO()
            img.save(img_bytes, format="PNG", optimize=True)
            img_bytes.seek(0)
            imagens.append(img_bytes)

        pdf_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
        doc = fitz.open()
        for img_bytes in imagens:
            img = Image.open(img_bytes)
            rect = fitz.Rect(0, 0, img.width, img.height)
            page = doc.new_page(width=img.width, height=img.height)
            page.insert_image(rect, stream=img_bytes.read())
        doc.save(pdf_path)
        doc.close()
        gc.collect()

        return send_file(
            pdf_path,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="slides_convertidos.pdf"
        )

    except Exception as e:
        return {'error': f'Erro ao processar PPTX: {str(e)}'}, 500


# ================= Vídeo a partir de HTML =================

# =============== Defaults (pode ajustar) ===============
TARGET_FPS       = 30        # fps do MP4 final
CONTENT_SECONDS  = 10.0      # conteúdo útil aproximado
BUFFER_HEAD_S    = 2.0       # buffer antes
BUFFER_TAIL_S    = 2.0       # buffer depois
SCENE_THRESHOLD  = 0.0015    # sensibilidade do auto-trim do início
HEAD_PAD_S       = 0.05      # margem antes do 1º movimento
TAIL_PAD_S       = 0.10      # margem após o último movimento (apenas se cortar o final)
AUTO_TRIM_HEAD   = True      # corta automaticamente o início ESTÁTICO
AUTO_TRIM_TAIL   = False     # não corta o final por padrão
ZERO_ANIM_DELAY  = True      # zera animation/transition-delay (padrão; pode sobrescrever por requisição)
WAIT_NETWORK_IDLE= True
TIMEZONE_ID      = "America/Sao_Paulo"
AUTO_SIZE_BODY   = True      # mede o <body> e grava no tamanho exato
MAX_DIM          = 4096      # limite por dimensão para o viewport gravado
# Qualidade/compat do MP4
CRF              = 20
PRESET           = "medium"
PIX_FMT          = "yuv420p"
PROFILE          = "high"
LEVEL            = "4.0"
# =======================================================


def ensure_ffmpeg():
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise RuntimeError("FFmpeg/ffprobe não encontrados no PATH.")


def file_url(p: Path) -> str:
    return p.resolve().as_uri()


def measure_body_size(html_path: Path) -> tuple[int, int]:
    """Abre SEM gravação, mede o tamanho real do <body> e devolve (w,h)."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1080, "height": 1350},
            device_scale_factor=1.0,
            java_script_enabled=True,
            timezone_id=TIMEZONE_ID,
        )
        page = ctx.new_page()
        page.goto(file_url(html_path), wait_until="load")
        if WAIT_NETWORK_IDLE:
            try:
                page.wait_for_load_state("networkidle", timeout=8000)
            except Exception:
                pass
        try:
            page.evaluate("document.fonts && document.fonts.ready && document.fonts.ready.then(()=>{})")
            page.wait_for_timeout(50)
        except Exception:
            pass
        dims = page.evaluate(
            """
        () => {
          const b = document.body, d = document.documentElement;
          const w = Math.max(b.scrollWidth, d.scrollWidth, b.offsetWidth, d.offsetWidth, d.clientWidth);
          const h = Math.max(b.scrollHeight, d.scrollHeight, b.offsetHeight, d.offsetHeight, d.clientHeight);
          return {w, h};
        }
        """
        )
        ctx.close()
        browser.close()
    w = max(1, int(dims["w"]))
    h = max(1, int(dims["h"]))
    if w > MAX_DIM or h > MAX_DIM:
        r = min(MAX_DIM / w, MAX_DIM / h)
        w, h = max(1, int(w * r)), max(1, int(h * r))
    return w, h


def prepare_page(page, *, zero_anim_delay: bool):
    page.wait_for_load_state("load")
    if WAIT_NETWORK_IDLE:
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
    try:
        page.evaluate("document.fonts && document.fonts.ready && document.fonts.ready.then(()=>{})")
        page.wait_for_timeout(50)
    except Exception:
        pass
    if zero_anim_delay:
        page.add_style_tag(
            content="""
            * { animation-delay: 0s !important; transition-delay: 0s !important; }
        """
        )


def record_webm(
    html_path: Path,
    total_seconds: float,
    width: int,
    height: int,
    out_dir: Path,
    *,
    zero_anim_delay: bool,
) -> Path:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": width, "height": height},
            record_video_dir=str(out_dir),
            record_video_size={"width": width, "height": height},
            device_scale_factor=1.0,
            java_script_enabled=True,
            timezone_id=TIMEZONE_ID,
        )
        page = ctx.new_page()
        page.goto(file_url(html_path), wait_until="load")
        prepare_page(page, zero_anim_delay=zero_anim_delay)
        page.wait_for_timeout(500)  # warmup
        page.wait_for_timeout(int(total_seconds * 1000))
        page.close()
        ctx.close()
        browser.close()
    vids = sorted(out_dir.rglob("*.webm"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not vids:
        raise RuntimeError("Nenhum WEBM gravado.")
    return vids[0]


def video_duration(path: Path) -> float:
    out = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nokey=1:noprint_wrappers=1",
            str(path),
        ]
    ).decode().strip()
    try:
        return float(out)
    except Exception:
        return 0.0


def detect_scene_changes(path: Path, threshold: float) -> list[float]:
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-i",
        str(path),
        "-filter:v",
        f"select='gt(scene,{threshold})',showinfo",
        "-an",
        "-f",
        "null",
        "-",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    times = []
    for line in proc.stderr.splitlines():
        m = re.search(r"pts_time:([0-9]+\.[0-9]+)", line)
        if m:
            try:
                times.append(float(m.group(1)))
            except Exception:
                pass
    return times


def compute_trim(
    webm: Path,
    *,
    auto_head=True,
    auto_tail=False,
    head_pad=0.05,
    tail_pad=0.10,
    scene_threshold: float = SCENE_THRESHOLD,
) -> tuple[float, float]:
    dur = max(0.01, video_duration(webm))
    if not (auto_head or auto_tail):
        return 0.0, dur
    sc = detect_scene_changes(webm, scene_threshold)
    if not sc:
        return 0.0, dur
    start = max(0.0, sc[0] - head_pad) if auto_head else 0.0
    if auto_tail:
        end = min(dur, sc[-1] + tail_pad)
        take = max(0.01, end - start)
    else:
        take = max(0.01, dur - start)
    return start, take


def webm_to_mp4_precise(
    webm_path: Path,
    mp4_path: Path,
    start: float,
    take: float,
    out_w: int,
    out_h: int,
    fps: int,
):
    # Usa -ss DEPOIS do -i para seek preciso; mantém a mesma dimensão (sem barras).
    vf_chain = f"fps={fps}"
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(webm_path),
        "-ss",
        f"{start}",
        "-t",
        f"{take}",
        "-vf",
        vf_chain,
        "-c:v",
        "libx264",
        "-pix_fmt",
        PIX_FMT,
        "-profile:v",
        PROFILE,
        "-level:v",
        LEVEL,
        "-preset",
        PRESET,
        "-crf",
        str(CRF),
        "-movflags",
        "+faststart",
        "-an",
        str(mp4_path),
    ]
    subprocess.run(cmd, check=True)


def write_temp_html(tmpdir: Path, *, html_text: str = None, html_file=None) -> Path:
    """
    Grava o HTML recebido (texto ou arquivo enviado) no tmpdir e retorna o caminho.
    Mantém o nome base do upload (caso tenha assets relativos ao lado).
    """
    if html_text is not None:
        p = tmpdir / "index.html"
        p.write_text(html_text, encoding="utf-8")
        return p
    else:
        if html_file is None:
            raise ValueError("Nenhum HTML fornecido.")
        filename = getattr(html_file, "filename", None) or "upload.html"
        p = tmpdir / Path(filename).name
        html_file.save(p)
        return p


@app.route("/healthz")
def health():
    return {"ok": True}


@app.route('/html-para-pdf', methods=['POST'])
def html_para_pdf():
    """
    Converte um HTML recebido em PDF.
    Aceita:
      - multipart/form-data com campo 'file' (arquivo .html)
      - OU multipart/form-data com campo 'html' (texto bruto do HTML)

    Parâmetros opcionais (form-data):
      - format: tamanho da página (ex.: A4, Letter). Padrão: A4
      - margin_top, margin_right, margin_bottom, margin_left (em mm, px, etc. wkhtmltopdf)

    Resposta: application/pdf (attachment)
    """
    html_file = request.files.get('file')
    html_text = request.form.get('html')
    if not html_file and not html_text:
        return jsonify({"error": "Envie 'file' (multipart) OU 'html' (texto)."}), 400

    # Parâmetros opcionais de página/margem
    page_format = request.form.get('format', 'A4')
    m_top = request.form.get('margin_top')
    m_right = request.form.get('margin_right')
    m_bottom = request.form.get('margin_bottom')
    m_left = request.form.get('margin_left')

    # Diretório temporário com limpeza pós-resposta (compatível com Windows)
    tmpdir_obj = tempfile.TemporaryDirectory(prefix="html2pdf_")
    tmpdir = Path(tmpdir_obj.name)

    @after_this_request
    def _cleanup(response):
        for _ in range(10):
            try:
                tmpdir_obj.cleanup()
                break
            except PermissionError:
                time.sleep(0.3)
        return response

    try:
        html_path = write_temp_html(tmpdir, html_text=html_text, html_file=html_file)
        pdf_path = tmpdir / "output.pdf"

        # Monta comando wkhtmltopdf
        cmd = [
            "wkhtmltopdf",
            "--enable-local-file-access",
            "--print-media-type",
        ]
        if page_format:
            cmd += ["-s", str(page_format)]
        if m_top:
            cmd += ["-T", str(m_top)]
        if m_right:
            cmd += ["-R", str(m_right)]
        if m_bottom:
            cmd += ["-B", str(m_bottom)]
        if m_left:
            cmd += ["-L", str(m_left)]

        cmd += [str(html_path), str(pdf_path)]

        try:
            subprocess.run(cmd, check=True)
        except FileNotFoundError:
            return jsonify({
                "error": "wkhtmltopdf não encontrado. Instale-o no sistema ou use a imagem Docker fornecida."
            }), 500

        return send_file(
            str(pdf_path),
            mimetype="application/pdf",
            as_attachment=True,
            download_name="convertido.pdf",
        )
    except Exception as e:
        return jsonify({"error": f"Falha ao converter HTML em PDF: {str(e)}"}), 500


@app.route("/render", methods=["POST"])
def render():
    """
    POST /render
    Form-data:
      - file: arquivo .html  (opcional se mandar 'html')
      - html: texto bruto do HTML (opcional se mandar 'file')
      - content_seconds (float, opcional) | default CONTENT_SECONDS
      - width,height (int, opcionais) | se omitidos e AUTO_SIZE_BODY=True → usa tamanho do <body>
      - target_fps (int, opcional) | default TARGET_FPS
      - auto_trim_head (bool), auto_trim_tail (bool) [0/1, true/false]
      - zero_anim_delay (bool)
      - scene_threshold, head_pad, tail_pad (opcionais)
    Resposta: video/mp4 (attachment)
    """
    try:
        ensure_ffmpeg()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    html_file = request.files.get("file")
    html_text = request.form.get("html")
    if not html_file and not html_text:
        return jsonify({"error": "Envie 'file' (multipart) OU 'html' (texto)."}), 400

    # parâmetros opcionais
    try:
        content_seconds = float(request.form.get("content_seconds", CONTENT_SECONDS))
    except ValueError:
        return jsonify({"error": "content_seconds inválido"}), 400
    try:
        target_fps = int(request.form.get("target_fps", TARGET_FPS))
    except ValueError:
        return jsonify({"error": "target_fps inválido"}), 400

    auto_trim_head = (
        str(request.form.get("auto_trim_head", str(AUTO_TRIM_HEAD))).lower()
        in ("1", "true", "t", "yes", "y")
    )
    auto_trim_tail = (
        str(request.form.get("auto_trim_tail", str(AUTO_TRIM_TAIL))).lower()
        in ("1", "true", "t", "yes", "y")
    )
    zero_anim_delay = (
        str(request.form.get("zero_anim_delay", str(ZERO_ANIM_DELAY))).lower()
        in ("1", "true", "t", "yes", "y")
    )

    scene_threshold = request.form.get("scene_threshold")
    head_pad = request.form.get("head_pad")
    tail_pad = request.form.get("tail_pad")
    try:
        scene_threshold = (
            float(scene_threshold) if scene_threshold is not None else SCENE_THRESHOLD
        )
        head_pad = float(head_pad) if head_pad is not None else HEAD_PAD_S
        tail_pad = float(tail_pad) if tail_pad is not None else TAIL_PAD_S
    except ValueError:
        return jsonify({"error": "scene_threshold/head_pad/tail_pad inválidos"}), 400

    width = request.form.get("width")
    height = request.form.get("height")
    try:
        width = int(width) if width else None
        height = int(height) if height else None
    except ValueError:
        return jsonify({"error": "width/height inválidos"}), 400

    # -------- NÃO usar TemporaryDirectory como context manager (Windows lock) --------
    tmpdir_obj = tempfile.TemporaryDirectory(prefix="html2mp4_")
    tmpdir = Path(tmpdir_obj.name)

    @after_this_request
    def _cleanup(response):
        # Tenta limpar após o envio (Windows pode segurar handle por um pouco)
        for _ in range(10):
            try:
                tmpdir_obj.cleanup()
                break
            except PermissionError:
                time.sleep(0.3)
        return response

    try:
        html_path = write_temp_html(
            tmpdir, html_text=html_text, html_file=html_file
        )

        # 1) descobrir tamanho
        if AUTO_SIZE_BODY and (width is None or height is None):
            w, h = measure_body_size(html_path)
        else:
            w = width or 1080
            h = height or 1350

        # 2) gravar WEBM com buffers
        total = content_seconds + BUFFER_HEAD_S + BUFFER_TAIL_S
        webm = record_webm(
            html_path, total, w, h, tmpdir, zero_anim_delay=zero_anim_delay
        )

        # 3) auto-trim do início (e opcional do final), SEM cortar conteúdo
        start, take = compute_trim(
            webm,
            auto_head=auto_trim_head,
            auto_tail=auto_trim_tail,
            head_pad=head_pad,
            tail_pad=tail_pad,
            scene_threshold=scene_threshold,
        )

        # 4) converter para MP4 com seek preciso (sem barras)
        mp4_path = tmpdir / "output.mp4"
        webm_to_mp4_precise(webm, mp4_path, start, take, w, h, target_fps)

        # 5) devolver (passe string; Flask abre/fecha o arquivo)
        resp = send_file(
            str(mp4_path),
            mimetype="video/mp4",
            as_attachment=True,
            download_name="render.mp4",
            max_age=0,
            conditional=True,
        )
        # Evita cache agressivo de proxies/browsers
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        resp.headers["Pragma"] = "no-cache"
        return resp
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
