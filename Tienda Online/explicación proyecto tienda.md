### Con esta breve explicación, me ayuda a completar la rúbrica el dia de la entrega ###
Este proyecto de tienda online está realizado con Python y Flask en el que:
- Muestra un catálogo.
- Permite ver productos.
- Añadir productos a un carrito.
- Guardar el carrito usando sesiones.
- Finalizar la compra.


Con este comando; (from flask import Flask, request, session) importa Flask y herramientas necesarias


### Con esto creo la aplicación web y la password para los usuarios###

app = Flask(__name__)
app.secret_key = "clave-muy-simple"

### Esta función crea una plantilla HTML básico
def pagina_base(contenido_html):

### muestra links para ver el catalogo y el carrito
def vista_catalogo():


### Muestra un producto:
def vista_producto(producto_id):

### Muestra el carrito:
def vista_carrito():

### Productos del carrito:
def vista_finalizacion():

### Ruta principal:
@app.route("/", methods=["GET"])
def index():

 Esta función decide que mostrar segun la URL

 ### Selecciona vista:
 if operacion == "producto":

producto → muestra producto

carrito → muestra carrito

finalizacion → muestra compra

nada → catálogo

### Añadir al carrito:
@app.route("/add", methods=["POST"])
def add_carrito():


### Vaciar carrito:
@app.route("/vaciar", methods=["POST"])


### ejecución e inicio del servidor:
if __name__ == "__main__":
    app.run(debug=True)





 
