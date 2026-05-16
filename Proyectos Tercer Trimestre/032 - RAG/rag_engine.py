import requests
import chromadb

from config import (
    CHROMA_DIR,
    COLLECTION_NAME,
    OLLAMA_EMBED_URL,
    OLLAMA_GENERATE_URL,
    EMBED_MODEL,
    TEXT_MODEL,
    TOP_K
)


def obtener_embedding(texto):
    datos = {
        "model": EMBED_MODEL,
        "input": texto.strip()
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


def buscar_contexto(pregunta):
    cliente = chromadb.PersistentClient(path=CHROMA_DIR)
    coleccion = cliente.get_collection(COLLECTION_NAME)

    embedding_pregunta = obtener_embedding(pregunta)

    resultados = coleccion.query(
        query_embeddings=[embedding_pregunta],
        n_results=TOP_K,
        include=["documents", "metadatas", "distances"]
    )

    documentos = resultados["documents"][0]

    contexto = "\n\n---\n\n".join(documentos)

    return contexto


def generar_respuesta(pregunta, contexto):
    prompt = f"""
Eres un asistente especializado en responder preguntas usando documentos técnicos.

REGLAS:
- Responde en español.
- Usa principalmente el contexto proporcionado.
- No inventes información.
- Si el contexto no contiene la respuesta, dilo claramente.
- Explica de forma sencilla y útil para un estudiante.

PREGUNTA:
{pregunta}

CONTEXTO:
{contexto}

RESPUESTA:
"""

    datos = {
        "model": TEXT_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2
        }
    }

    respuesta = requests.post(
        OLLAMA_GENERATE_URL,
        json=datos,
        timeout=300
    )

    respuesta.raise_for_status()

    return respuesta.json()["response"].strip()


def preguntar_al_documento(pregunta):
    contexto = buscar_contexto(pregunta)
    respuesta = generar_respuesta(pregunta, contexto)

    return respuesta
