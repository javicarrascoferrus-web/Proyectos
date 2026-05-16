from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import secrets
import re
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "clave_secreta_multiformularios"

BASE_DATOS = "database.db"


def conectar_db():
    conexion = sqlite3.connect(BASE_DATOS)
    conexion.row_factory = sqlite3.Row
    return conexion


def crear_base_datos():
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            rol TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS formularios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            hash TEXT NOT NULL UNIQUE,
            plantilla TEXT NOT NULL,
            activo INTEGER DEFAULT 1,
            creado_en TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS respuestas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            formulario_id INTEGER NOT NULL,
            enviado_en TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS respuestas_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            respuesta_id INTEGER NOT NULL,
            campo TEXT NOT NULL,
            valor TEXT
        )
    """)

    conexion.commit()

    admin = cursor.execute(
        "SELECT * FROM usuarios WHERE usuario = ?",
        ("admin",)
    ).fetchone()

    if admin is None:
        password_segura = generate_password_hash("admin123")

        cursor.execute(
            "INSERT INTO usuarios (usuario, password, rol) VALUES (?, ?, ?)",
            ("admin", password_segura, "superadmin")
        )

        conexion.commit()

    conexion.close()


def login_requerido():
    return "usuario_id" in session


def normalizar_nombre(texto):
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9]+", "_", texto)
    texto = texto.strip("_")
    return texto or "campo"


def contar_tabs(linea):
    return len(linea) - len(linea.lstrip("\t"))


def parsear_bloque(lineas, indice, nivel=0, prefijo="campo"):
    estructura = []

    while indice < len(lineas):
        linea_original = lineas[indice].rstrip("\n")

        if not linea_original.strip():
            indice += 1
            continue

        nivel_actual = contar_tabs(linea_original)

        if nivel_actual < nivel:
            break

        if nivel_actual > nivel:
            indice += 1
            continue

        linea = linea_original.strip()

        tipos_simples = ["text", "number", "email", "date", "textarea"]
        tipos_condicionales = ["radio", "select", "checkbox"]

        tipo_detectado = None

        for tipo in tipos_simples + tipos_condicionales:
            if linea.startswith(f"[{tipo}]"):
                tipo_detectado = tipo
                break

        if not tipo_detectado:
            indice += 1
            continue

        etiqueta = linea.replace(f"[{tipo_detectado}]", "").strip()

        if tipo_detectado in tipos_simples:
            estructura.append({
                "tipo": tipo_detectado,
                "etiqueta": etiqueta,
                "name": normalizar_nombre(prefijo + "_" + etiqueta)
            })
            indice += 1
            continue

        if tipo_detectado in tipos_condicionales:
            nombre_campo = normalizar_nombre(prefijo + "_" + etiqueta)

            campo = {
                "tipo": tipo_detectado,
                "etiqueta": etiqueta,
                "name": nombre_campo,
                "opciones": []
            }

            indice += 1

            while indice < len(lineas):
                sublinea_original = lineas[indice].rstrip("\n")

                if not sublinea_original.strip():
                    indice += 1
                    continue

                subnivel = contar_tabs(sublinea_original)
                sublinea = sublinea_original.strip()

                if subnivel < nivel + 1:
                    break

                if subnivel == nivel + 1 and sublinea.startswith("[case]"):
                    valor = sublinea.replace("[case]", "").strip()
                    indice += 1

                    hijos, indice = parsear_bloque(
                        lineas,
                        indice,
                        nivel + 2,
                        prefijo + "_" + etiqueta + "_" + valor
                    )

                    campo["opciones"].append({
                        "valor": valor,
                        "hijos": hijos
                    })
                else:
                    indice += 1

            estructura.append(campo)

    return estructura, indice


def crear_id_condicional(nombre, valor):
    texto = nombre + "_" + valor
    return "cond_" + hashlib.md5(texto.encode()).hexdigest()


@app.route("/")
def inicio():
    if login_requerido():
        return redirect(url_for("panel"))

    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    mensaje = ""

    if request.method == "POST":
        usuario = request.form.get("usuario")
        password = request.form.get("password")

        conexion = conectar_db()
        user = conexion.execute(
            "SELECT * FROM usuarios WHERE usuario = ?",
            (usuario,)
        ).fetchone()
        conexion.close()

        if user and check_password_hash(user["password"], password):
            session["usuario_id"] = user["id"]
            session["usuario"] = user["usuario"]
            session["rol"] = user["rol"]

            return redirect(url_for("panel"))
        else:
            mensaje = "Usuario o contraseña incorrectos."

    return render_template("login.html", mensaje=mensaje)


@app.route("/panel")
def panel():
    if not login_requerido():
        return redirect(url_for("login"))

    conexion = conectar_db()
    formularios = conexion.execute(
        "SELECT * FROM formularios ORDER BY id DESC"
    ).fetchall()
    conexion.close()

    return render_template(
        "panel.html",
        usuario=session["usuario"],
        formularios=formularios
    )


@app.route("/crear", methods=["GET", "POST"])
def crear_formulario():
    if not login_requerido():
        return redirect(url_for("login"))

    if request.method == "POST":
        titulo = request.form.get("titulo")
        plantilla = request.form.get("plantilla")
        hash_formulario = secrets.token_hex(8)

        conexion = conectar_db()
        conexion.execute(
            """
            INSERT INTO formularios (usuario_id, titulo, hash, plantilla)
            VALUES (?, ?, ?, ?)
            """,
            (
                session["usuario_id"],
                titulo,
                hash_formulario,
                plantilla
            )
        )
        conexion.commit()
        conexion.close()

        return redirect(url_for("panel"))

    plantilla_ejemplo = """[text] Nombre
[email] Correo electrónico
[number] Edad

[radio] Ciclo
\t[case] DAM
\t\t[text] Lenguaje favorito
\t[case] SMR
\t\t[text] Módulo favorito
"""

    return render_template(
        "crear_formulario.html",
        plantilla_ejemplo=plantilla_ejemplo
    )


@app.route("/form/<hash_formulario>", methods=["GET", "POST"])
def formulario_publico(hash_formulario):
    conexion = conectar_db()

    formulario = conexion.execute(
        "SELECT * FROM formularios WHERE hash = ? AND activo = 1",
        (hash_formulario,)
    ).fetchone()

    if formulario is None:
        conexion.close()
        return "Formulario no encontrado o desactivado."

    lineas = formulario["plantilla"].splitlines()
    estructura, _ = parsear_bloque(lineas, 0)

    if request.method == "POST":
        cursor = conexion.cursor()

        cursor.execute(
            "INSERT INTO respuestas (formulario_id) VALUES (?)",
            (formulario["id"],)
        )

        respuesta_id = cursor.lastrowid

        for campo, valores in request.form.lists():
            for valor in valores:
                cursor.execute(
                    """
                    INSERT INTO respuestas_items (respuesta_id, campo, valor)
                    VALUES (?, ?, ?)
                    """,
                    (respuesta_id, campo, valor)
                )

        conexion.commit()
        conexion.close()

        return render_template("gracias.html", titulo=formulario["titulo"])

    conexion.close()

    return render_template(
        "formulario_publico.html",
        formulario=formulario,
        estructura=estructura,
        crear_id_condicional=crear_id_condicional
    )


@app.route("/respuestas/<int:formulario_id>")
def ver_respuestas(formulario_id):
    if not login_requerido():
        return redirect(url_for("login"))

    conexion = conectar_db()

    formulario = conexion.execute(
        "SELECT * FROM formularios WHERE id = ?",
        (formulario_id,)
    ).fetchone()

    if formulario is None:
        conexion.close()
        return "Formulario no encontrado."

    respuestas = conexion.execute(
        """
        SELECT * FROM respuestas
        WHERE formulario_id = ?
        ORDER BY id DESC
        """,
        (formulario_id,)
    ).fetchall()

    datos_respuestas = []

    for respuesta in respuestas:
        items = conexion.execute(
            """
            SELECT * FROM respuestas_items
            WHERE respuesta_id = ?
            """,
            (respuesta["id"],)
        ).fetchall()

        datos_respuestas.append({
            "respuesta": respuesta,
            "items": items
        })

    conexion.close()

    return render_template(
        "respuestas.html",
        formulario=formulario,
        datos_respuestas=datos_respuestas
    )


@app.route("/cambiar_estado/<int:formulario_id>")
def cambiar_estado(formulario_id):
    if not login_requerido():
        return redirect(url_for("login"))

    conexion = conectar_db()

    formulario = conexion.execute(
        "SELECT * FROM formularios WHERE id = ?",
        (formulario_id,)
    ).fetchone()

    if formulario:
        nuevo_estado = 0 if formulario["activo"] == 1 else 1

        conexion.execute(
            "UPDATE formularios SET activo = ? WHERE id = ?",
            (nuevo_estado, formulario_id)
        )

        conexion.commit()

    conexion.close()

    return redirect(url_for("panel"))


@app.route("/eliminar_formulario/<int:formulario_id>")
def eliminar_formulario(formulario_id):
    if not login_requerido():
        return redirect(url_for("login"))

    conexion = conectar_db()

    respuestas = conexion.execute(
        "SELECT id FROM respuestas WHERE formulario_id = ?",
        (formulario_id,)
    ).fetchall()

    for respuesta in respuestas:
        conexion.execute(
            "DELETE FROM respuestas_items WHERE respuesta_id = ?",
            (respuesta["id"],)
        )

    conexion.execute(
        "DELETE FROM respuestas WHERE formulario_id = ?",
        (formulario_id,)
    )

    conexion.execute(
        "DELETE FROM formularios WHERE id = ?",
        (formulario_id,)
    )

    conexion.commit()
    conexion.close()

    return redirect(url_for("panel"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    crear_base_datos()
    app.run(debug=True)
