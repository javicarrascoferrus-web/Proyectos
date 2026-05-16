from flask import Flask, render_template, request
from rag_engine import preguntar_al_documento
from config import EMBED_MODEL, TEXT_MODEL


app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    pregunta = ""
    respuesta = ""

    if request.method == "POST":
        pregunta = request.form.get("pregunta", "").strip()

        if pregunta:
            try:
                respuesta = preguntar_al_documento(pregunta)
            except Exception as error:
                respuesta = f"Error al procesar la pregunta: {error}"

    return render_template(
        "index.html",
        pregunta=pregunta,
        respuesta=respuesta,
        embed_model=EMBED_MODEL,
        text_model=TEXT_MODEL
    )


if __name__ == "__main__":
    app.run(debug=True)
