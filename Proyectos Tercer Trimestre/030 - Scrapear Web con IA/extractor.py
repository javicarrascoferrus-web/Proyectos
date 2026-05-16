import requests
from bs4 import BeautifulSoup

def obtener_texto_web(url):

    respuesta = requests.get(url)

    soup = BeautifulSoup(respuesta.text, "html.parser")

    # eliminar scripts y estilos
    for etiqueta in soup(["script", "style", "noscript"]):
        etiqueta.decompose()

    texto = soup.get_text(separator=" ")

    # limpiar espacios
    texto = " ".join(texto.split())

    return texto[:6000]
