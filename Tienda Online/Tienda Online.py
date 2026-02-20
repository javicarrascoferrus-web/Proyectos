from flask import Flask, request, session

app = Flask(__name__)
app.secret_key = "clave-muy-simple"  


def pagina_base(contenido_html: str) -> str:
    return f"""
    <!doctype html>
    <html lang="es">
    <head>
        <meta charset="utf-8">
        <link rel="stylesheet" href="/static/css/estilo.css">
        <title>Tienda online</title>
        <style>
        </style>
    </head>
    <body>
        <header>
            <a href="/"><h1>Tienda online</h1></a>
        </header>
        <main>
            {contenido_html}
        </main>
        <footer>
            (c) Javier Carrasco
        </footer>
    </body>
    </html>
    """



def vista_catalogo() -> str:
    return """
    <h2>Catálogo</h2>
    <p>Elige un producto:</p>
    <a class="btn" href="/?operacion=producto&id=1">Ver Producto 1</a><br>
    <a class="btn" href="/?operacion=producto&id=2">Ver Producto 2</a><br>
    <a class="btn" href="/?operacion=carrito">Ver Carrito</a><br>
    """


def vista_producto(producto_id: str) -> str:
    return f"""
    <h2>Producto {producto_id}</h2>
    <p>Este es un producto de ejemplo.</p>

    <form method="POST" action="/add">
        <input type="hidden" name="id" value="{producto_id}">
        <button class="btn" type="submit">Añadir al carrito</button>
    </form>

    <a class="btn" href="/?operacion=carrito">Ir al carrito</a><br>
    <a class="btn" href="/">Volver al catálogo</a>
    """


def vista_carrito() -> str:
    carrito = session.get("carrito", [])
    if len(carrito) == 0:
        lista = "<p>El carrito está vacío.</p>"
    else:
        items = "".join(f"<li>Producto {pid}</li>" for pid in carrito)
        lista = f"<ul>{items}</ul>"

    return f"""
    <h2>Carrito</h2>
    {lista}
    <a class="btn" href="/">Seguir comprando</a><br>
    <a class="btn" href="/?operacion=finalizacion">Finalizar compra</a><br>
    <form method="POST" action="/vaciar">
        <button class="btn" type="submit">Vaciar carrito</button>
    </form>
    """


def vista_finalizacion() -> str:
    carrito = session.get("carrito", [])
    total_items = len(carrito)
    return f"""
    <h2>Finalización</h2>
    <p>Gracias por tu compra.</p>
    <p>Has comprado {total_items} producto(s).</p>
    <a class="btn" href="/">Volver al inicio</a>
    """


@app.route("/", methods=["GET"])
def index():

    if "carrito" not in session:
        session["carrito"] = []

 
    operacion = request.args.get("operacion")

    if operacion == "producto":
        producto_id = request.args.get("id", "1")
        contenido = vista_producto(producto_id)
    elif operacion == "carrito":
        contenido = vista_carrito()
    elif operacion == "finalizacion":
        contenido = vista_finalizacion()
    else:
        contenido = vista_catalogo()

    return pagina_base(contenido)


@app.route("/add", methods=["POST"])
def add_carrito():
    if "carrito" not in session:
        session["carrito"] = []

    producto_id = request.form.get("id", "1")
    session["carrito"].append(producto_id)
    return pagina_base(f"""
        <p> Producto {producto_id} añadido al carrito.</p>
        <a class="btn" href="/?operacion=carrito">Ver carrito</a><br>
        <a class="btn" href="/">Volver al catálogo</a>
    """)


@app.route("/vaciar", methods=["POST"])
def vaciar_carrito():
    session["carrito"] = []
    return pagina_base("""
        <p>Carrito vaciado.</p>
        <a class="btn" href="/">Volver al catálogo</a>
    """)


if __name__ == "__main__":
    app.run(debug=True)
