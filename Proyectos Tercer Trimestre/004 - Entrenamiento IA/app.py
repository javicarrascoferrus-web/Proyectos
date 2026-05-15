from flask import Flask, render_template, request, redirect, url_for, session
from services.asistente_service import generar_respuesta

app = Flask(__name__)
app.secret_key = "clave-desarrollo-cambiar"


def obtener_conversacion():
    if "conversacion" not in session:
        session["conversacion"] = []
    return session["conversacion"]


@app.route("/")
def inicio():
    conversacion = obtener_conversacion()
    return render_template("chat.html", conversacion=conversacion)


@app.route("/enviar", methods=["POST"])
def enviar():
    mensaje = request.form.get("mensaje", "").strip()

    if mensaje:
        conversacion = obtener_conversacion()

        conversacion.append({
            "tipo": "usuario",
            "texto": mensaje
        })

        respuesta = generar_respuesta(mensaje)

        conversacion.append({
            "tipo": "bot",
            "texto": respuesta
        })

        session["conversacion"] = conversacion

    return redirect(url_for("inicio"))


@app.route("/reiniciar", methods=["POST"])
def reiniciar():
    session.pop("conversacion", None)
    return redirect(url_for("inicio"))


if __name__ == "__main__":
    app.run(debug=True)
