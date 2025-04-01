from flask import Flask, request, send_file
import subprocess
import os
import uuid

app = Flask(__name__)

UPLOAD_FOLDER = "/tmp"
OUTPUT_FOLDER = "/tmp"

@app.route('/convert', methods=['POST'])
def convert_to_pdf():
    if 'file' not in request.files:
        return 'Nenhum arquivo enviado.', 400

    file = request.files['file']
    unique_name = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_FOLDER, unique_name + ".docx")
    output_path = os.path.join(OUTPUT_FOLDER, unique_name + ".pdf")

    file.save(input_path)

    result = subprocess.run([
        "libreoffice",
        "--headless",
        "--convert-to", "pdf",
        "--outdir", OUTPUT_FOLDER,
        input_path
    ])

    if result.returncode != 0 or not os.path.exists(output_path):
        return "Erro ao converter o arquivo.", 500

    return send_file(output_path, as_attachment=True, download_name="convertido.pdf")

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)

