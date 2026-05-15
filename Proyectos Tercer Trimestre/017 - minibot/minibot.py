import requests
import sqlite3
import time
import sys
import re
import csv
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
from collections import deque
from datetime import datetime

URL_INICIAL = "https://josevicentecarratala.com"
BASE_DATOS = "crawler.sqlite"
CSV_SALIDA = "resultados.csv"

ESPERA = 1
TIMEOUT = 15
MAX_PAGINAS = 30

sesion = requests.Session()
sesion.headers.update({
    "User-Agent": "Mozilla/5.0 MinibotEducativo/2.0"
})


def iniciar_db():
    conexion = sqlite3.connect(BASE_DATOS)
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS paginas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            titulo TEXT,
            emails TEXT,
            codigo_http INTEGER,
            fecha_rastreo TEXT
        )
    """)

    conexion.commit()
    return conexion


def normalizar_url(url):
    partes = urlparse(url)

    esquema = partes.scheme.lower()
    dominio = partes.netloc.lower()
    ruta = partes.path or "/"

    if ruta != "/" and ruta.endswith("/"):
        ruta = ruta[:-1]

    return urlunparse((
        esquema,
        dominio,
        ruta,
        partes.params,
        partes.query,
        ""
    ))


def url_valida(url):
    partes = urlparse(url)
    return partes.scheme in ("http", "https")


def mismo_dominio(url, dominio_base):
    return urlparse(url).netloc.lower() == dominio_base.lower()


def extraer_titulo(soup):
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    return "Sin título"


def extraer_emails(html):
    encontrados = set()

    patron = r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"

    for email in re.findall(patron, html):
        encontrados.add(email.lower())

    soup = BeautifulSoup(html, "html.parser")

    for enlace in soup.find_all("a", href=True):
        href = enlace["href"].strip()

        if href.lower().startswith("mailto:"):
            correo = href[7:].split("?")[0]
            encontrados.add(correo.lower())

    return ", ".join(sorted(encontrados))


def obtener_enlaces(html, url_actual, dominio_base):
    soup = BeautifulSoup(html, "html.parser")
    enlaces = []

    for enlace in soup.find_all("a", href=True):
        href = enlace["href"].strip()

        if href == "":
            continue

        if href.startswith("#"):
            continue

        if href.startswith("mailto:") or href.startswith("tel:"):
            continue

        if href.startswith("javascript:"):
            continue

        url_completa = urljoin(url_actual, href)
        url_completa = normalizar_url(url_completa)

        if not url_valida(url_completa):
            continue

        if not mismo_dominio(url_completa, dominio_base):
            continue

        enlaces.append(url_completa)

    return enlaces


def guardar_pagina(conexion, url, titulo, emails, codigo_http):
    cursor = conexion.cursor()

    cursor.execute("""
        INSERT INTO paginas (url, titulo, emails, codigo_http, fecha_rastreo)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(url) DO UPDATE SET
            titulo = excluded.titulo,
            emails = excluded.emails,
            codigo_http = excluded.codigo_http,
            fecha_rastreo = excluded.fecha_rastreo
    """, (
        url,
        titulo,
        emails,
        codigo_http,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conexion.commit()


def exportar_csv():
    conexion = sqlite3.connect(BASE_DATOS)
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT url, titulo, emails, codigo_http, fecha_rastreo
        FROM paginas
        ORDER BY id
    """)

    filas = cursor.fetchall()
    conexion.close()

    with open(CSV_SALIDA, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(["URL", "Título", "Emails", "Código HTTP", "Fecha rastreo"])
        escritor.writerows(filas)


def rastrear(url_inicial):
    url_inicial = normalizar_url(url_inicial)
    dominio_base = urlparse(url_inicial).netloc.lower()

    conexion = iniciar_db()

    visitadas = set()
    en_cola = set([url_inicial])
    cola = deque([url_inicial])

    total_emails = 0

    while cola and len(visitadas) < MAX_PAGINAS:
        url_actual = cola.popleft()

        if url_actual in visitadas:
            continue

        print(f"Visitando: {url_actual}")

        visitadas.add(url_actual)

        try:
            respuesta = sesion.get(
                url_actual,
                timeout=TIMEOUT,
                allow_redirects=True
            )

            time.sleep(ESPERA)

            codigo_http = respuesta.status_code
            tipo = respuesta.headers.get("Content-Type", "").lower()

            if "text/html" not in tipo:
                print("  Saltado: no es HTML")
                continue

            url_final = normalizar_url(respuesta.url)

            html = respuesta.text
            soup = BeautifulSoup(html, "html.parser")

            titulo = extraer_titulo(soup)
            emails = extraer_emails(html)

            if emails:
                total_emails += len(emails.split(","))

            guardar_pagina(
                conexion,
                url_final,
                titulo,
                emails,
                codigo_http
            )

            print(f"  Título: {titulo}")
            print(f"  HTTP: {codigo_http}")
            print(f"  Emails: {emails if emails else 'Ninguno'}")

            enlaces = obtener_enlaces(html, url_final, dominio_base)

            for enlace in enlaces:
                if enlace not in visitadas and enlace not in en_cola:
                    cola.append(enlace)
                    en_cola.add(enlace)

        except requests.RequestException as error:
            print(f"  Error: {error}")

    conexion.close()
    exportar_csv()

    print("\nRastreo terminado")
    print(f"Páginas visitadas: {len(visitadas)}")
    print(f"Emails encontrados: {total_emails}")
    print(f"Base de datos: {BASE_DATOS}")
    print(f"CSV generado: {CSV_SALIDA}")


if __name__ == "__main__":
    url = URL_INICIAL

    if len(sys.argv) > 1:
        url = sys.argv[1]

    if not url_valida(url):
        print("Error: introduce una URL válida con http:// o https://")
        sys.exit(1)

    rastrear(url)
