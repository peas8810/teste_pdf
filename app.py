import os
import shutil
import subprocess
from typing import List
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from pdf2docx import Converter
from pdf2image import convert_from_path
import pytesseract

# Configurações
POPPLER_PATH = "/usr/bin"
WORK_DIR = "documentos"
os.makedirs(WORK_DIR, exist_ok=True)

app = FastAPI()

# ROTA PRINCIPAL – evita 502 no Railway
@app.get("/")
def root():
    return {"mensagem": "API funcionando com sucesso 🚀"}

@app.get("/status")
def status():
    return {"status": "API online"}

def salvar_arquivos(uploaded_files: List[UploadFile]) -> List[str]:
    caminhos = []
    for arquivo in uploaded_files:
        nome_base, extensao = os.path.splitext(arquivo.filename)
        nome_limpo = (nome_base.replace(" ", "_")
                      .replace("ç", "c").replace("ã", "a")
                      .replace("á", "a").replace("é", "e")
                      .replace("í", "i").replace("ó", "o")
                      .replace("ú", "u").replace("ñ", "n")) + extensao.lower()

        caminho = os.path.join(WORK_DIR, nome_limpo)
        with open(caminho, "wb") as f:
            shutil.copyfileobj(arquivo.file, f)
        caminhos.append(caminho)
    return caminhos

@app.post("/pdf-para-word")
def pdf_para_word(file: UploadFile = File(...)):
    try:
        caminho = salvar_arquivos([file])[0]
        nome_base = os.path.splitext(os.path.basename(caminho))[0]
        saida = os.path.join(WORK_DIR, f"pdf2docx_{nome_base}.docx")
        if os.path.exists(saida): os.remove(saida)
        cv = Converter(caminho)
        cv.convert(saida)
        cv.close()
        return FileResponse(saida, filename=os.path.basename(saida))
    except Exception as e:
        return JSONResponse(content={"erro": str(e)}, status_code=500)

@app.post("/jpg-para-pdf")
def jpg_para_pdf(files: List[UploadFile] = File(...)):
    try:
        caminhos = salvar_arquivos(files)
        nome_saida = "img2pdf_resultado.pdf"
        caminho_pdf = os.path.join(WORK_DIR, nome_saida)
        if os.path.exists(caminho_pdf): os.remove(caminho_pdf)
        imagens = [Image.open(c).convert("RGB") for c in caminhos]
        if imagens:
            imagens[0].save(caminho_pdf, save_all=True, append_images=imagens[1:])
            return FileResponse(caminho_pdf, filename=nome_saida)
        return JSONResponse(content={"erro": "Falha na geração do PDF."}, status_code=500)
    except Exception as e:
        return JSONResponse(content={"erro": str(e)}, status_code=500)

@app.post("/juntar-pdfs")
def juntar_pdfs(files: List[UploadFile] = File(...)):
    try:
        caminhos = salvar_arquivos(files)
        if len(caminhos) < 2:
            return JSONResponse(content={"erro": "Envie ao menos 2 PDFs."}, status_code=400)
        nome_saida = os.path.join(WORK_DIR, "merge_resultado.pdf")
        merger = PdfMerger()
        for c in caminhos:
            merger.append(c)
        merger.write(nome_saida)
        merger.close()
        return FileResponse(nome_saida, filename="merge_resultado.pdf")
    except Exception as e:
        return JSONResponse(content={"erro": str(e)}, status_code=500)

@app.post("/dividir-pdf")
def dividir_pdf(file: UploadFile = File(...)):
    try:
        caminho = salvar_arquivos([file])[0]
        nome_base = os.path.splitext(os.path.basename(caminho))[0]
        reader = PdfReader(caminho)
        arquivos = []
        for i, page in enumerate(reader.pages):
            writer = PdfWriter()
            writer.add_page(page)
            nome_saida = os.path.join(WORK_DIR, f"split_{nome_base}_pag{i+1}.pdf")
            with open(nome_saida, "wb") as f:
                writer.write(f)
            arquivos.append(nome_saida)
        return {"arquivos": arquivos}
    except Exception as e:
        return JSONResponse(content={"erro": str(e)}, status_code=500)

@app.post("/ocr-pdf")
def ocr_pdf(file: UploadFile = File(...)):
    try:
        caminho = salvar_arquivos([file])[0]
        nome_base = os.path.splitext(os.path.basename(caminho))[0]
        saida = os.path.join(WORK_DIR, f"ocrpdf_{nome_base}.txt")
        imagens = convert_from_path(caminho, poppler_path=POPPLER_PATH)
        texto = ""
        for i, img in enumerate(imagens):
            texto += f"\n\n--- Página {i+1} ---\n\n"
            texto += pytesseract.image_to_string(img, lang='por')
        with open(saida, "w", encoding="utf-8") as f:
            f.write(texto)
        return FileResponse(saida, filename=os.path.basename(saida))
    except Exception as e:
        return JSONResponse(content={"erro": str(e)}, status_code=500)

@app.post("/ocr-imagem")
def ocr_imagem(files: List[UploadFile] = File(...)):
    try:
        caminhos = salvar_arquivos(files)
        saida = os.path.join(WORK_DIR, "ocrimg_resultado.txt")
        texto = ""
        for i, caminho in enumerate(caminhos):
            img = Image.open(caminho)
            texto += f"\n\n--- Imagem {i+1} ---\n\n"
            texto += pytesseract.image_to_string(img, lang='por')
        with open(saida, "w", encoding="utf-8") as f:
            f.write(texto)
        return FileResponse(saida, filename=os.path.basename(saida))
    except Exception as e:
        return JSONResponse(content={"erro": str(e)}, status_code=500)

@app.post("/pdf-para-pdfa")
def pdf_para_pdfa(file: UploadFile = File(...)):
    try:
        caminho = salvar_arquivos([file])[0]
        nome_base = os.path.splitext(os.path.basename(caminho))[0]
        saida = os.path.join(WORK_DIR, f"pdfa_{nome_base}.pdf")
        gs_path = "/usr/bin/gs"
        comando = [
            gs_path, "-dPDFA=2", "-dBATCH", "-dNOPAUSE", "-dNOOUTERSAVE",
            "-sProcessColorModel=DeviceRGB", "-sDEVICE=pdfwrite",
            "-sPDFACompatibilityPolicy=1", f"-sOutputFile={saida}", caminho
        ]
        resultado = subprocess.run(comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if os.path.exists(saida) and resultado.returncode == 0:
            return FileResponse(saida, filename=os.path.basename(saida))
        return JSONResponse(content={"erro": "Falha ao converter para PDF/A."}, status_code=500)
    except Exception as e:
        return JSONResponse(content={"erro": str(e)}, status_code=500)
