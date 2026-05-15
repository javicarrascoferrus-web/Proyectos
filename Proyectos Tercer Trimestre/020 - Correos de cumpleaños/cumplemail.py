import csv
import os
import smtplib
import ssl
from io import StringIO
from datetime import date, datetime
from email.message import EmailMessage

import requests


URL_CONTACTOS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSpa0iay6LTbzksUx8qel9uPSrfg0UPGDyKfu6k6CI_JlTEPWxR4lgoN9C4I3NmLU5P53GifGRkSorf/pub?output=csv"

MODO_PRUEBA = True


def leer_contactos_csv(url):
    respuesta = requests.get(url, timeout=30)
    respuesta.raise_for_status()
    respuesta.encoding = "utf-8"

    archivo = StringIO(respuesta.text)
    lector = csv.DictReader(archivo)

    return list(lector)


def convertir_fecha(texto):
    return datetime.strptime(texto.strip(), "%Y-%m-%d").date()


def cumple_hoy(fecha_nacimiento, hoy):
    return fecha_nacimiento.day == hoy.day and fecha_nacimiento.month == hoy.month


def calcular_edad(fecha_nacimiento, hoy):
    edad = hoy.year - fecha_nacimiento.year

    if (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
        edad -= 1

    return edad


def obtener_variable(nombre, obligatorio=True, valor_por_defecto=None):
    valor = os.environ.get(nombre, valor_por_defecto)

    if obligatorio and not valor:
        raise RuntimeError(f"Falta configurar la variable de entorno: {nombre}")

    return valor


def crear_email(remitente, destinatario, nombre, apellidos, edad):
    mensaje = EmailMessage()

    mensaje["From"] = remitente
    mensaje["To"] = destinatario
    mensaje["Subject"] = f"¡Feliz cumpleaños, {nombre}!"

    texto = f"""Hola {nombre} {apellidos},

¡Feliz cumpleaños!

Hoy cumples {edad} años.
Te deseamos un día lleno de alegría y buenos momentos.

Un saludo.
"""

    html = f"""
    <!doctype html>
    <html lang="es">
    <body style="margin:0;background:#f4f6fb;font-family:Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6fb;padding:40px 0;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background:white;border-radius:18px;overflow:hidden;">
                        <tr>
                            <td style="background:linear-gradient(135deg,#4f46e5,#9333ea);padding:36px;text-align:center;color:white;">
                                <div style="font-size:46px;">🎉</div>
                                <h1 style="margin:10px 0 0;">¡Feliz cumpleaños!</h1>
                            </td>
                        </tr>

                        <tr>
                            <td style="padding:34px;color:#1f2937;">
                                <p style="font-size:18px;">Hola <strong>{nombre} {apellidos}</strong>,</p>

                                <p style="font-size:16px;line-height:1.7;">
                                    Hoy cumples <strong>{edad} años</strong> y queremos desearte un día maravilloso.
                                </p>

                                <p style="font-size:16px;line-height:1.7;">
                                    Esperamos que este nuevo año venga acompañado de salud, ilusión y muchos éxitos.
                                </p>

                                <div style="margin:28px 0;padding:20px;border-radius:14px;background:#eef2ff;text-align:center;">
                                    <p style="margin:0;color:#4f46e5;font-size:14px;">Hoy celebramos a</p>
                                    <h2 style="margin:8px 0;color:#312e81;">{nombre}</h2>
                                    <p style="margin:0;color:#4338ca;">{edad} años</p>
                                </div>

                                <p style="font-size:16px;line-height:1.7;">
                                    Recibe un cordial saludo y nuestros mejores deseos.
                                </p>
                            </td>
                        </tr>

                        <tr>
                            <td style="padding:20px;text-align:center;color:#6b7280;font-size:13px;">
                                Mensaje enviado automáticamente por CumpleMail.
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    mensaje.set_content(texto)
    mensaje.add_alternative(html, subtype="html")

    return mensaje


def enviar_email(mensaje):
    smtp_host = obtener_variable("SMTP_HOST")
    smtp_port = int(obtener_variable("SMTP_PORT"))
    smtp_user = obtener_variable("SMTP_USER")
    smtp_password = obtener_variable("SMTP_PASSWORD")
    smtp_security = obtener_variable("SMTP_SECURITY", obligatorio=False, valor_por_defecto="starttls").lower()

    if smtp_security == "ssl":
        contexto = ssl.create_default_context()

        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=contexto, timeout=30) as servidor:
            servidor.login(smtp_user, smtp_password)
            servidor.send_message(mensaje)

    else:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as servidor:
            servidor.ehlo()

            if smtp_security == "starttls":
                contexto = ssl.create_default_context()
                servidor.starttls(context=contexto)
                servidor.ehlo()

            servidor.login(smtp_user, smtp_password)
            servidor.send_message(mensaje)


def procesar_cumpleanos():
    contactos = leer_contactos_csv(URL_CONTACTOS)
    hoy = date.today()

    remitente = obtener_variable("SMTP_FROM", obligatorio=False, valor_por_defecto=os.environ.get("SMTP_USER"))

    encontrados = 0
    enviados = 0

    print("Iniciando revisión de cumpleaños...")
    print(f"Fecha actual: {hoy}")
    print("-" * 50)

    for fila in contactos:
        try:
            nombre = fila.get("Name", "").strip()
            apellidos = fila.get("Surnames", "").strip()
            email = fila.get("Email", "").strip()
            nacimiento = convertir_fecha(fila.get("Birth Date", ""))

            if not nombre or not email:
                print("Fila omitida por datos incompletos.")
                continue

            if cumple_hoy(nacimiento, hoy):
                edad = calcular_edad(nacimiento, hoy)
                encontrados += 1

                print(f"Cumpleaños encontrado: {nombre} {apellidos}")
                print(f"Email: {email}")
                print(f"Edad: {edad}")

                mensaje = crear_email(
                    remitente=remitente,
                    destinatario=email,
                    nombre=nombre,
                    apellidos=apellidos,
                    edad=edad
                )

                if MODO_PRUEBA:
                    print("Modo prueba activo: el email no se ha enviado.")
                else:
                    enviar_email(mensaje)
                    enviados += 1
                    print("Email enviado correctamente.")

                print("-" * 50)

        except Exception as error:
            print(f"Error procesando fila: {error}")
            print("-" * 50)

    if encontrados == 0:
        print("Hoy no hay cumpleaños.")

    print("Resumen final")
    print(f"Cumpleaños encontrados: {encontrados}")
    print(f"Emails enviados: {enviados}")


if __name__ == "__main__":
    procesar_cumpleanos()
