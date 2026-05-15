import json
from flask import Flask, render_template, request

app = Flask(__name__)


def cargar_modulos():
    with open("datos/modulos.json", "r", encoding="utf-8") as archivo:
        datos = json.load(archivo)
    return datos.get("modulos", [])


@app.route("/")
def inicio():
    busqueda = request.args.get("buscar", "").lower()
    modulos = cargar_modulos()

    if busqueda:
        modulos = [
            modulo for modulo in modulos
            if busqueda in modulo["nombre"].lower()
        ]

    return render_template(
        "index.html",
        modulos=modulos,
        busqueda=busqueda
    )


if __name__ == "__main__":
    app.run(debug=True)
