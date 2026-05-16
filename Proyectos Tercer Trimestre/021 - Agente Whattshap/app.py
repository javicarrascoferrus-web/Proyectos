from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "clave_secreta_agente_whatsapp"

DB_NAME = "admin.sqlite"

ADMIN_USER = "admin"
ADMIN_PASS = "admin"


def conectar_db():
    conexion = sqlite3.connect(DB_NAME)
    conexion.row_factory = sqlite3.Row
    return conexion


def crear_tablas():
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            apellidos TEXT NOT NULL,
            email TEXT NOT NULL,
            telefono TEXT NOT NULL UNIQUE,
            curso_matriculado TEXT NOT NULL,
            creado_en TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chatbot_qa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pregunta TEXT NOT NULL,
            respuesta TEXT NOT NULL,
            creado_en TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ifttt_acciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resumen_if TEXT NOT NULL,
            destinatario_email TEXT NOT NULL,
            asunto TEXT NOT NULL,
            creado_en TEXT NOT NULL
        )
    """)

    conexion.commit()
    conexion.close()


def fecha_actual():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def buscar_usuario_por_telefono(telefono):
    conexion = conectar_db()
    usuario = conexion.execute(
        "SELECT * FROM usuarios WHERE telefono = ?",
        (telefono,)
    ).fetchone()
    conexion.close()
    return usuario


def buscar_respuesta_chatbot(mensaje):
    conexion = conectar_db()

    preguntas = conexion.execute(
        "SELECT * FROM chatbot_qa ORDER BY id DESC"
    ).fetchall()

    conexion.close()

    mensaje_limpio = mensaje.lower().strip()

    for item in preguntas:
        pregunta = item["pregunta"].lower().strip()

        if pregunta in mensaje_limpio or mensaje_limpio in pregunta:
            return item["respuesta"]

    return "Lo siento, todavía no tengo una respuesta para esa pregunta."


@app.route("/")
def chat():
    crear_tablas()
    return render_template("chat.html")


@app.route("/api/identificar", methods=["POST"])
def api_identificar():
    datos = request.get_json()
    telefono = datos.get("telefono", "").strip()

    usuario = buscar_usuario_por_telefono(telefono)

    if usuario:
        return jsonify({
            "existe": True,
            "nombre": usuario["nombre"],
            "apellidos": usuario["apellidos"],
            "email": usuario["email"],
            "telefono": usuario["telefono"],
            "curso_matriculado": usuario["curso_matriculado"]
        })

    return jsonify({
        "existe": False,
        "telefono": telefono
    })


@app.route("/api/chat", methods=["POST"])
def api_chat():
    datos = request.get_json()
    mensaje = datos.get("mensaje", "").strip()

    respuesta = buscar_respuesta_chatbot(mensaje)

    return jsonify({
        "respuesta": respuesta
    })


@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    error = ""

    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        password = request.form.get("password", "").strip()

        if usuario == ADMIN_USER and password == ADMIN_PASS:
            session["admin"] = True
            return redirect(url_for("admin_usuarios"))
        else:
            error = "Usuario o contraseña incorrectos."

    return render_template("admin_login.html", error=error)


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


def comprobar_admin():
    return session.get("admin") is True


@app.route("/admin/usuarios", methods=["GET", "POST"])
def admin_usuarios():
    if not comprobar_admin():
        return redirect(url_for("admin_login"))

    conexion = conectar_db()

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        apellidos = request.form.get("apellidos", "").strip()
        email = request.form.get("email", "").strip()
        telefono = request.form.get("telefono", "").strip()
        curso = request.form.get("curso_matriculado", "").strip()

        if nombre and apellidos and email and telefono and curso:
            conexion.execute("""
                INSERT OR REPLACE INTO usuarios
                (nombre, apellidos, email, telefono, curso_matriculado, creado_en)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                nombre,
                apellidos,
                email,
                telefono,
                curso,
                fecha_actual()
            ))
            conexion.commit()

        conexion.close()
        return redirect(url_for("admin_usuarios"))

    usuarios = conexion.execute(
        "SELECT * FROM usuarios ORDER BY id DESC"
    ).fetchall()

    conexion.close()

    return render_template("admin_usuarios.html", usuarios=usuarios)


@app.route("/admin/usuarios/eliminar/<int:usuario_id>")
def eliminar_usuario(usuario_id):
    if not comprobar_admin():
        return redirect(url_for("admin_login"))

    conexion = conectar_db()
    conexion.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
    conexion.commit()
    conexion.close()

    return redirect(url_for("admin_usuarios"))


@app.route("/admin/chatbot", methods=["GET", "POST"])
def admin_chatbot():
    if not comprobar_admin():
        return redirect(url_for("admin_login"))

    conexion = conectar_db()

    if request.method == "POST":
        pregunta = request.form.get("pregunta", "").strip()
        respuesta = request.form.get("respuesta", "").strip()

        if pregunta and respuesta:
            conexion.execute("""
                INSERT INTO chatbot_qa (pregunta, respuesta, creado_en)
                VALUES (?, ?, ?)
            """, (
                pregunta,
                respuesta,
                fecha_actual()
            ))
            conexion.commit()

        conexion.close()
        return redirect(url_for("admin_chatbot"))

    items = conexion.execute(
        "SELECT * FROM chatbot_qa ORDER BY id DESC"
    ).fetchall()

    conexion.close()

    return render_template("admin_chatbot.html", items=items)


@app.route("/admin/chatbot/eliminar/<int:item_id>")
def eliminar_chatbot(item_id):
    if not comprobar_admin():
        return redirect(url_for("admin_login"))

    conexion = conectar_db()
    conexion.execute("DELETE FROM chatbot_qa WHERE id = ?", (item_id,))
    conexion.commit()
    conexion.close()

    return redirect(url_for("admin_chatbot"))


@app.route("/admin/ifttt", methods=["GET", "POST"])
def admin_ifttt():
    if not comprobar_admin():
        return redirect(url_for("admin_login"))

    conexion = conectar_db()

    if request.method == "POST":
        resumen_if = request.form.get("resumen_if", "").strip()
        destinatario_email = request.form.get("destinatario_email", "").strip()
        asunto = request.form.get("asunto", "").strip()

        if resumen_if and destinatario_email and asunto:
            conexion.execute("""
                INSERT INTO ifttt_acciones
                (resumen_if, destinatario_email, asunto, creado_en)
                VALUES (?, ?, ?, ?)
            """, (
                resumen_if,
                destinatario_email,
                asunto,
                fecha_actual()
            ))
            conexion.commit()

        conexion.close()
        return redirect(url_for("admin_ifttt"))

    acciones = conexion.execute(
        "SELECT * FROM ifttt_acciones ORDER BY id DESC"
    ).fetchall()

    conexion.close()

    return render_template("admin_ifttt.html", acciones=acciones)


@app.route("/admin/ifttt/eliminar/<int:accion_id>")
def eliminar_ifttt(accion_id):
    if not comprobar_admin():
        return redirect(url_for("admin_login"))

    conexion = conectar_db()
    conexion.execute("DELETE FROM ifttt_acciones WHERE id = ?", (accion_id,))
    conexion.commit()
    conexion.close()

    return redirect(url_for("admin_ifttt"))


if __name__ == "__main__":
    crear_tablas()
    app.run(debug=True)
