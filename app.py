from flask import Flask, request, send_file
import fitz  # PyMuPDF
import tempfile
import json
import requests
import zipfile
import os
from pptx import Presentation
from PIL import Image, ImageDraw, ImageChops, ImageOps
from io import BytesIO
import subprocess
import gc
from werkzeug.utils import secure_filename
from urllib.parse import urlparse, unquote
from PIL import ImageFont
import imgkit

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


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
