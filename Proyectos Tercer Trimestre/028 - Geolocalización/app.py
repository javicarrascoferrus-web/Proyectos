from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

DB_NAME = "usuarios.db"

def crear_tabla():
    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL,
            latitud REAL NOT NULL,
            longitud REAL NOT NULL,
            actualizado TEXT NOT NULL
        )
    """)

    conexion.commit()
    conexion.close()

@app.route("/")
def inicio():
    return render_template("index.html")

@app.route("/guardar", methods=["POST"])
def guardar():
    datos = request.get_json()

    nombre = datos.get("nombre")
    latitud = datos.get("latitud")
    longitud = datos.get("longitud")

    if not nombre or latitud is None or longitud is None:
        return jsonify({"ok": False, "error": "Datos incompletos"}), 400

    conexion = sqlite3.connect(DB_NAME)
    cursor = conexion.cursor()

    cursor.execute("""
        INSERT INTO usuarios (nombre, latitud, longitud, actualizado)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(nombre) DO UPDATE SET
            latitud = excluded.latitud,
            longitud = excluded.longitud,
            actualizado = excluded.actualizado
    """, (nombre, latitud, longitud, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    conexion.commit()
    conexion.close()

    return jsonify({"ok": True})

@app.route("/usuarios")
def usuarios():
    conexion = sqlite3.connect(DB_NAME)
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    cursor.execute("SELECT nombre, latitud, longitud, actualizado FROM usuarios ORDER BY nombre")
    filas = cursor.fetchall()

    conexion.close()

    return jsonify({
        "ok": True,
        "usuarios": [dict(fila) for fila in filas]
    })

if __name__ == "__main__":
    crear_tabla()
    app.run(debug=True)
