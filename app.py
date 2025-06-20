from flask import Flask, request, send_file
import fitz  # PyMuPDF
import tempfile
import json
import requests
import zipfile
import os
from pptx import Presentation
from PIL import Image, ImageDraw
from io import BytesIO
import subprocess
import gc
from werkzeug.utils import secure_filename
from urllib.parse import urlparse, unquote

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # Limite de 50MB por upload


def substituir_textos(doc, substituicoes):
    for page in doc:
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

                            page.add_redact_annot(bbox, fill=(1, 1, 1))
                            page.apply_redactions()

                            novo_texto = texto_original.replace(marcador, novo_valor)
                            page.insert_text(
                                (bbox[0], bbox[1] + tamanho),
                                novo_texto,
                                fontsize=tamanho,
                                color=cor,
                                fontname="helv"
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