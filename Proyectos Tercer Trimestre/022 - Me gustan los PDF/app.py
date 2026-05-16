import zipfile
from flask import send_file
import os
from flask import Flask, render_template, request, send_from_directory
from pypdf import PdfReader, PdfWriter
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "paginas_generadas"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def dividir_pdf(ruta_pdf, nombre_base):
    lector = PdfReader(ruta_pdf)
    archivos_generados = []

    for numero, pagina in enumerate(lector.pages, start=1):
        escritor = PdfWriter()
        escritor.add_page(pagina)

        nombre_archivo = f"{nombre_base}_pagina_{numero}.pdf"
        ruta_salida = os.path.join(OUTPUT_FOLDER, nombre_archivo)

        with open(ruta_salida, "wb") as archivo:
            escritor.write(archivo)

        archivos_generados.append(nombre_archivo)

    return archivos_generados


@app.route("/", methods=["GET", "POST"])
def index():
    mensaje = ""
    archivos = []

    if request.method == "POST":
        archivo = request.files.get("pdf")

        if archivo and archivo.filename.lower().endswith(".pdf"):
            nombre_seguro = secure_filename(archivo.filename)
            nombre_base = os.path.splitext(nombre_seguro)[0]

            ruta_pdf = os.path.join(UPLOAD_FOLDER, nombre_seguro)
            archivo.save(ruta_pdf)

            archivos = dividir_pdf(ruta_pdf, nombre_base)
            mensaje = "PDF dividido correctamente."
        else:
            mensaje = "Debes subir un archivo PDF válido."

    return render_template("index.html", mensaje=mensaje, archivos=archivos)


@app.route("/descargar/<nombre_archivo>")
def descargar(nombre_archivo):
    return send_from_directory(
        OUTPUT_FOLDER,
        nombre_archivo,
        as_attachment=True
    )


@app.route("/descargar_zip")
def descargar_zip():
    nombre_zip = "paginas_pdf.zip"
    ruta_zip = os.path.join("resultados", nombre_zip)

    os.makedirs("resultados", exist_ok=True)

    with zipfile.ZipFile(ruta_zip, "w") as zipf:
        for archivo in os.listdir(OUTPUT_FOLDER):
            if archivo.lower().endswith(".pdf"):
                ruta_archivo = os.path.join(OUTPUT_FOLDER, archivo)
                zipf.write(ruta_archivo, archivo)

    return send_file(ruta_zip, as_attachment=True)
if __name__ == "__main__":
    app.run(debug=True)
