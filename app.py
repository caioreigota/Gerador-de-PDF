from flask import Flask, request, send_file
import fitz  # PyMuPDF
import tempfile
import json
import requests

app = Flask(__name__)

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

                            # Apaga o texto original
                            page.add_redact_annot(bbox, fill=(1, 1, 1))
                            page.apply_redactions()

                            # Insere o novo texto
                            novo_texto = texto_original.replace(marcador, novo_valor)
                            page.insert_text(
                                (bbox[0], bbox[1] + tamanho),
                                novo_texto,
                                fontsize=tamanho,
                                color=cor,
                                fontname="helv",  # use fonte embutida válida
                            )

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
            doc.save(tmp_out.name)
            return send_file(
                tmp_out.name,
                mimetype="application/pdf",
                as_attachment=True,
                download_name="preenchido.pdf"
            )
    except Exception as e:
        return {'error': f'Erro ao processar PDF: {str(e)}'}, 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
