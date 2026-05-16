from flask import Flask, render_template, request
from extractor import obtener_texto_web
from analizador import analizar_con_ia

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def inicio():
    resultado = None
    url = ""

    if request.method == "POST":
        url = request.form.get("url", "").strip()

        if url:
            try:
                texto_web = obtener_texto_web(url)
                resultado = analizar_con_ia(texto_web)
            except Exception as error:
                resultado = f"Ha ocurrido un error: {error}"

    return render_template(
        "index.html",
        resultado=resultado,
        url=url
    )


if __name__ == "__main__":
    app.run(debug=True)
