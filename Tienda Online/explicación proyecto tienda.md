### Con esta breve explicación, me ayuda a completar la rúbrica el dia de la entrega ###
Este proyecto de tienda online está realizado con Python y Flask en el que:
- Muestra un catálogo.
- Permite ver productos.
- Añadir productos a un carrito.
- Guardar el carrito usando sesiones.
- Finalizar la compra.


Con este comando; (from flask import Flask, request, session) importa Flask y herramientas necesarias

###Con esto creo la aplicación web y la password para los usuarios###

app = Flask(__name__)
app.secret_key = "clave-muy-simple"
