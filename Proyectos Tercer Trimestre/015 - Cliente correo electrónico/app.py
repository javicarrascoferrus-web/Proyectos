from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import imaplib
import smtplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
from email.message import EmailMessage

app = Flask(__name__)
app.secret_key = "clave_secreta_cliente_correo"

DB_NAME = "correo.sqlite"


def conectar_db():
    conexion = sqlite3.connect(DB_NAME)
    conexion.row_factory = sqlite3.Row
    return conexion


def crear_tabla():
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cuentas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            imap_server TEXT NOT NULL,
            smtp_server TEXT NOT NULL
        )
    """)

    conexion.commit()
    conexion.close()


def buscar_cuenta(email_usuario):
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute(
        "SELECT * FROM cuentas WHERE lower(email) = lower(?)",
        (email_usuario,)
    )

    cuenta = cursor.fetchone()
    conexion.close()

    return cuenta


def guardar_cuenta(email_usuario, imap_server, smtp_server):
    conexion = conectar_db()
    cursor = conexion.cursor()

    cuenta = buscar_cuenta(email_usuario)

    if cuenta:
        cursor.execute("""
            UPDATE cuentas
            SET imap_server = ?, smtp_server = ?
            WHERE lower(email) = lower(?)
        """, (imap_server, smtp_server, email_usuario))
    else:
        cursor.execute("""
            INSERT INTO cuentas (email, imap_server, smtp_server)
            VALUES (?, ?, ?)
        """, (email_usuario, imap_server, smtp_server))

    conexion.commit()
    conexion.close()


def decodificar_texto(texto):
    if texto is None:
        return ""

    partes = decode_header(texto)
    resultado = ""

    for contenido, charset in partes:
        if isinstance(contenido, bytes):
            resultado += contenido.decode(charset or "utf-8", errors="ignore")
        else:
            resultado += contenido

    return resultado


def extraer_cuerpo(mensaje):
    cuerpo = ""

    if mensaje.is_multipart():
        for parte in mensaje.walk():
            tipo = parte.get_content_type()
            disposicion = str(parte.get("Content-Disposition"))

            if tipo == "text/plain" and "attachment" not in disposicion:
                contenido = parte.get_payload(decode=True)

                if contenido:
                    cuerpo = contenido.decode(
                        parte.get_content_charset() or "utf-8",
                        errors="ignore"
                    )
                    break
    else:
        contenido = mensaje.get_payload(decode=True)

        if contenido:
            cuerpo = contenido.decode(
                mensaje.get_content_charset() or "utf-8",
                errors="ignore"
            )

    return cuerpo.strip()


def cargar_mensajes(email_usuario, password, imap_server, limite=20):
    mensajes = []

    correo = imaplib.IMAP4_SSL(imap_server)
    correo.login(email_usuario, password)
    correo.select("INBOX")

    estado, datos = correo.search(None, "ALL")

    if estado != "OK":
        correo.logout()
        return mensajes

    ids = datos[0].split()
    ultimos_ids = ids[-limite:]
    ultimos_ids.reverse()

    for id_mensaje in ultimos_ids:
        estado, datos_mensaje = correo.fetch(id_mensaje, "(RFC822)")

        if estado != "OK":
            continue

        raw_email = datos_mensaje[0][1]
        mensaje = email.message_from_bytes(raw_email)

        asunto = decodificar_texto(mensaje["Subject"])
        remitente = decodificar_texto(mensaje["From"])
        destinatario = decodificar_texto(mensaje["To"])

        fecha = mensaje["Date"]

        try:
            fecha_formateada = parsedate_to_datetime(fecha).strftime("%Y-%m-%d %H:%M")
        except Exception:
            fecha_formateada = fecha or ""

        cuerpo = extraer_cuerpo(mensaje)
        resumen = cuerpo.replace("\n", " ")[:160]

        mensajes.append({
            "id": id_mensaje.decode(),
            "subject": asunto or "(Sin asunto)",
            "from": remitente,
            "to": destinatario,
            "date": fecha_formateada,
            "body": cuerpo,
            "resumen": resumen
        })

    correo.logout()
    return mensajes


def obtener_mensajes_sesion():
    return cargar_mensajes(
        session["email"],
        session["password"],
        session["imap_server"]
    )


@app.route("/", methods=["GET", "POST"])
def login():
    crear_tabla()

    error = ""

    if request.method == "POST":
        email_usuario = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        imap_server = request.form.get("imap_server", "").strip()
        smtp_server = request.form.get("smtp_server", "").strip()

        cuenta = buscar_cuenta(email_usuario)

        if cuenta:
            imap_server = cuenta["imap_server"]
            smtp_server = cuenta["smtp_server"]
        else:
            if imap_server == "" or smtp_server == "":
                error = "Debes indicar servidor IMAP y SMTP la primera vez."

        if error == "":
            try:
                prueba = imaplib.IMAP4_SSL(imap_server)
                prueba.login(email_usuario, password)
                prueba.logout()

                guardar_cuenta(email_usuario, imap_server, smtp_server)

                session["email"] = email_usuario
                session["password"] = password
                session["imap_server"] = imap_server
                session["smtp_server"] = smtp_server

                return redirect(url_for("bandeja"))

            except Exception as e:
                error = "No se pudo iniciar sesión: " + str(e)

    return render_template("login.html", error=error)


@app.route("/bandeja")
def bandeja():
    if "email" not in session:
        return redirect(url_for("login"))

    try:
        mensajes = obtener_mensajes_sesion()
    except Exception:
        session.clear()
        return redirect(url_for("login"))

    mensaje_actual = mensajes[0] if mensajes else None

    return render_template(
        "bandeja.html",
        mensajes=mensajes,
        mensaje_actual=mensaje_actual
    )


@app.route("/mensaje/<id_mensaje>")
def ver_mensaje(id_mensaje):
    if "email" not in session:
        return redirect(url_for("login"))

    mensajes = obtener_mensajes_sesion()
    mensaje_actual = None

    for mensaje in mensajes:
        if mensaje["id"] == id_mensaje:
            mensaje_actual = mensaje
            break

    return render_template(
        "bandeja.html",
        mensajes=mensajes,
        mensaje_actual=mensaje_actual
    )


@app.route("/actualizar")
def actualizar():
    if "email" not in session:
        return redirect(url_for("login"))

    return redirect(url_for("bandeja"))


@app.route("/nuevo", methods=["GET", "POST"])
def nuevo():
    if "email" not in session:
        return redirect(url_for("login"))

    error = ""
    mensaje_ok = ""

    if request.method == "POST":
        destinatario = request.form.get("destinatario", "").strip()
        asunto = request.form.get("asunto", "").strip()
        cuerpo = request.form.get("cuerpo", "").strip()

        if destinatario == "" or asunto == "" or cuerpo == "":
            error = "Completa todos los campos."
        else:
            try:
                msg = EmailMessage()
                msg["From"] = session["email"]
                msg["To"] = destinatario
                msg["Subject"] = asunto
                msg.set_content(cuerpo)

                servidor = smtplib.SMTP(session["smtp_server"], 587)
                servidor.starttls()
                servidor.login(session["email"], session["password"])
                servidor.send_message(msg)
                servidor.quit()

                mensaje_ok = "Correo enviado correctamente."

            except Exception as e:
                error = "No se pudo enviar el correo: " + str(e)

    return render_template(
        "nuevo.html",
        error=error,
        mensaje=mensaje_ok
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    crear_tabla()
    app.run(debug=True)
