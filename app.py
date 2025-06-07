from flask import Flask, request, send_file
from weasyprint import HTML
import tempfile

app = Flask(__name__)

@app.route('/gerar-pdf', methods=['POST'])
def gerar_pdf():
    html_content = request.json.get('html')
    if not html_content:
        return {'error': 'HTML não fornecido'}, 400

    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
        HTML(string=html_content).write_pdf(tmp_pdf.name)
        return send_file(
            tmp_pdf.name,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='documento.pdf'
        )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
