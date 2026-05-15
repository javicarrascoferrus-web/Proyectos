from flask import Flask, render_template, request, jsonify
import json
import os

app = Flask(__name__)

def cargar_productos():
    with open("productos.json", "r", encoding="utf-8") as archivo:
        return json.load(archivo)

@app.route("/")
def inicio():
    productos = cargar_productos()
    return render_template("index.html", productos=productos)

@app.route("/comprar", methods=["POST"])
def comprar():
    datos = request.json

    pedido = {
        "cliente": datos["cliente"],
        "productos": datos["productos"],
        "total": datos["total"]
    }

    if os.path.exists("pedidos.json"):
        with open("pedidos.json", "r", encoding="utf-8") as f:
            pedidos = json.load(f)
    else:
        pedidos = []

    pedidos.append(pedido)

    with open("pedidos.json", "w", encoding="utf-8") as f:
        json.dump(pedidos, f, indent=4)

    return jsonify({
        "mensaje": "Pedido guardado correctamente"
    })

if __name__ == "__main__":
    app.run(debug=True)
