import re
import hashlib
import requests
import chromadb

from config import (
    TXT_OUTPUT,
    CHROMA_DIR,
    COLLECTION_NAME,
    OLLAMA_EMBED_URL,
    EMBED_MODEL,
    CHUNK_WORDS,
    CHUNK_OVERLAP
)


def limpiar_texto(texto):
    texto = texto.replace("\x00", " ")
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def dividir_en_fragmentos(texto):
    palabras = limpiar_texto(texto).split()
    fragmentos = []
    inicio = 0
    indice = 0

    while inicio < len(palabras):
        fin = inicio + CHUNK_WORDS
        bloque = palabras[inicio:fin]

        if len(bloque) < 40:
            break

        fragmento = " ".join(bloque)

        fragmentos.append({
            "indice": indice,
            "texto": fragmento
        })

        indice += 1
        inicio += CHUNK_WORDS - CHUNK_OVERLAP

    return fragmentos


def obtener_embedding(texto):
    datos = {
        "model": EMBED_MODEL,
        "input": texto
    }

    respuesta = requests.post(
        OLLAMA_EMBED_URL,
        json=datos,
        timeout=120
    )

    respuesta.raise_for_status()

    resultado = respuesta.json()

    if "embeddings" in resultado:
        return resultado["embeddings"][0]

    return resultado["embedding"]


def crear_id(texto, indice):
    resumen = hashlib.md5(texto.encode("utf-8")).hexdigest()
    return f"fragmento_{indice}_{resumen}"


def indexar_documento():
    with open(TXT_OUTPUT, "r", encoding="utf-8", errors="ignore") as archivo:
        texto = archivo.read()

    fragmentos = dividir_en_fragmentos(texto)

    print(f"Fragmentos generados: {len(fragmentos)}")

    cliente = chromadb.PersistentClient(path=CHROMA_DIR)

    try:
        cliente.delete_collection(COLLECTION_NAME)
        print("Colección anterior eliminada.")
    except Exception:
        print("No había colección anterior.")

    coleccion = cliente.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    for fragmento in fragmentos:
        print(f"Indexando fragmento {fragmento['indice']}")

        embedding = obtener_embedding(fragmento["texto"])

        coleccion.add(
            ids=[crear_id(fragmento["texto"], fragmento["indice"])],
            documents=[fragmento["texto"]],
            embeddings=[embedding],
            metadatas=[{
                "indice": fragmento["indice"],
                "palabras": len(fragmento["texto"].split())
            }]
        )

    print("Documento indexado correctamente.")


if __name__ == "__main__":
    indexar_documento()
