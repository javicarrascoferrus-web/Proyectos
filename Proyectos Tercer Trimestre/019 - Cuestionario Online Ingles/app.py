from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import csv
import requests
from io import StringIO
from datetime import datetime

app = Flask(__name__)
app.secret_key = "clave_secreta_test_ingles"

DB_NAME = "test_nivel.sqlite"

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQeVmlAFCtirR1M95fvI7bPn7n5IjVtpAQaWkajA-JQ9-JnXSxBec1XyIyYPOiO2PIWlnAUB3SW0e9E/pub?output=csv"

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
        CREATE TABLE IF NOT EXISTS intentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT NOT NULL,
            telefono TEXT NOT NULL,
            curso TEXT NOT NULL,
            puntos INTEGER NOT NULL,
            nivel TEXT NOT NULL,
            total_preguntas INTEGER NOT NULL,
            fecha TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS respuestas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            intento_id INTEGER NOT NULL,
            numero_pregunta INTEGER NOT NULL,
            pregunta TEXT NOT NULL,
            respuesta_usuario TEXT,
            respuesta_correcta TEXT NOT NULL,
            correcta INTEGER NOT NULL,
            FOREIGN KEY (intento_id) REFERENCES intentos(id)
        )
    """)

    conexion.commit()
    conexion.close()


def cargar_preguntas():
    respuesta = requests.get(CSV_URL, timeout=15)
    respuesta.raise_for_status()

    archivo = StringIO(respuesta.text)
    lector = csv.DictReader(archivo)

    preguntas = []

    for fila in lector:
        preguntas.append({
            "pregunta": fila.get("Pregunta", "").strip(),
            "respuesta_1": fila.get("Respuesta 1", "").strip(),
            "respuesta_2": fila.get("Respuesta 2", "").strip(),
            "respuesta_3": fila.get("Respuesta 3", "").strip(),
            "respuesta_4": fila.get("Respuesta 4", "").strip(),
            "correcta": fila.get("Respuesta correcta", "").strip()
        })

    return preguntas


def obtener_nivel(puntos):
    if 1 <= puntos <= 10:
        return "A1"
    elif 11 <= puntos <= 20:
        return "A2"
    elif 21 <= puntos <= 30:
        return "B1"
    elif 31 <= puntos <= 40:
        return "B2"
    elif 41 <= puntos <= 50:
        return "C1"
    return "Sin nivel"


@app.route("/", methods=["GET", "POST"])
def cuestionario():
    crear_tablas()

    try:
        preguntas = cargar_preguntas()
    except Exception as e:
        return f"Error al cargar preguntas: {e}"

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip()
        telefono = request.form.get("telefono", "").strip()
        curso = request.form.get("curso", "").strip()

        puntos = 0
        detalle = []

        for i, pregunta in enumerate(preguntas):
            campo = f"pregunta_{i}"
            respuesta_usuario = request.form.get(campo, "").strip()
            respuesta_correcta = pregunta["correcta"]

            correcta = respuesta_usuario == respuesta_correcta

            if correcta:
                puntos += 1

            detalle.append({
                "numero": i + 1,
                "pregunta": pregunta["pregunta"],
                "respuesta_usuario": respuesta_usuario,
                "respuesta_correcta": respuesta_correcta,
                "correcta": correcta
            })

        nivel = obtener_nivel(puntos)
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conexion = conectar_db()
        cursor = conexion.cursor()

        cursor.execute("""
            INSERT INTO intentos 
            (nombre, email, telefono, curso, puntos, nivel, total_preguntas, fecha)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nombre,
            email,
            telefono,
            curso,
            puntos,
            nivel,
            len(preguntas),
            fecha
        ))

        intento_id = cursor.lastrowid

        for item in detalle:
            cursor.execute("""
                INSERT INTO respuestas
                (intento_id, numero_pregunta, pregunta, respuesta_usuario, respuesta_correcta, correcta)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                intento_id,
                item["numero"],
                item["pregunta"],
                item["respuesta_usuario"],
                item["respuesta_correcta"],
                1 if item["correcta"] else 0
            ))

        conexion.commit()
        conexion.close()

        return redirect(url_for("resultado", intento_id=intento_id))

    return render_template("cuestionario.html", preguntas=preguntas)


@app.route("/resultado/<int:intento_id>")
def resultado(intento_id):
    conexion = conectar_db()
    intento = conexion.execute(
        "SELECT * FROM intentos WHERE id = ?",
        (intento_id,)
    ).fetchone()

    respuestas = conexion.execute(
        "SELECT * FROM respuestas WHERE intento_id = ? ORDER BY numero_pregunta",
        (intento_id,)
    ).fetchall()

    conexion.close()

    return render_template(
        "resultado.html",
        intento=intento,
        respuestas=respuestas
    )


@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    error = ""

    if request.method == "POST":
        usuario = request.form.get("usuario", "")
        password = request.form.get("password", "")

        if usuario == ADMIN_USER and password == ADMIN_PASS:
            session["admin"] = True
            return redirect(url_for("admin_panel"))
        else:
            error = "Usuario o contraseña incorrectos."

    return render_template("admin_login.html", error=error)


@app.route("/admin/panel")
def admin_panel():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    conexion = conectar_db()
    intentos = conexion.execute(
        "SELECT * FROM intentos ORDER BY fecha DESC"
    ).fetchall()
    conexion.close()

    return render_template("admin.html", intentos=intentos)


@app.route("/admin/informe/<int:intento_id>")
def informe(intento_id):
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    conexion = conectar_db()

    intento = conexion.execute(
        "SELECT * FROM intentos WHERE id = ?",
        (intento_id,)
    ).fetchone()

    respuestas = conexion.execute(
        "SELECT * FROM respuestas WHERE intento_id = ? ORDER BY numero_pregunta",
        (intento_id,)
    ).fetchall()

    conexion.close()

    return render_template(
        "informe.html",
        intento=intento,
        respuestas=respuestas
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("cuestionario"))


if __name__ == "__main__":
    crear_tablas()
    app.run(debug=True)
