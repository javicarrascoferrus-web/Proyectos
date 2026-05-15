
from flask import Flask, render_template, request, abort
from config import Config
from services.correo_service import obtener_correos
from services.analisis_service import analizar_correos

app = Flask(__name__)

cache_correos = {
    "cantidad": None,
    "datos": [],
    "por_id": {}
}


def cargar_bandeja(cantidad: int):
    if cache_correos["cantidad"] != cantidad or not cache_correos["datos"]:
        correos = obtener_correos(cantidad)
        analizados = analizar_correos(correos)

        cache_correos["cantidad"] = cantidad
        cache_correos["datos"] = analizados
        cache_correos["por_id"] = {
            correo["id"]: correo for correo in analizados
        }


@app.route("/")
def panel():
    cantidad = int(request.args.get("cantidad", Config.CANTIDAD_CORREOS))
    cantidad = max(1, min(100, cantidad))

    cargar_bandeja(cantidad)

    categoria = request.args.get("categoria", "urgente")

    correos_filtrados = [
        correo for correo in cache_correos["datos"]
        if correo["categoria"] == categoria
    ]

    conteos = {}
    for correo in cache_correos["datos"]:
        conteos[correo["categoria"]] = conteos.get(correo["categoria"], 0) + 1

    return render_template(
        "panel.html",
        correos=correos_filtrados,
        categoria=categoria,
        conteos=conteos,
        cantidad=cantidad
    )


@app.route("/correo/<correo_id>")
def detalle(correo_id):
    cantidad = int(request.args.get("cantidad", Config.CANTIDAD_CORREOS))
    cargar_bandeja(cantidad)

    correo = cache_correos["por_id"].get(correo_id)

    if not correo:
        abort(404)

    return render_template(
        "detalle.html",
        correo=correo,
        cantidad=cantidad
    )


@app.route("/actualizar")
def actualizar():
    cache_correos["cantidad"] = None
    cache_correos["datos"] = []
    cache_correos["por_id"] = {}
    return "Caché reiniciada correctamente"


if __name__ == "__main__":
    app.run(debug=True)
