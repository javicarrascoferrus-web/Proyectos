import os
import tempfile
import cv2
from ollama import chat


MODELO_IA = "qwen3.5:4b"


def analizar_imagen(frame, pregunta):
    archivo_temporal = None

    try:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            archivo_temporal = tmp.name

        cv2.imwrite(archivo_temporal, frame)

        respuesta = chat(
            model=MODELO_IA,
            messages=[
                {
                    "role": "user",
                    "content": pregunta,
                    "images": [archivo_temporal]
                }
            ]
        )

        return respuesta["message"]["content"].strip()

    except Exception as error:
        return f"Error al analizar la imagen: {error}"

    finally:
        if archivo_temporal and os.path.exists(archivo_temporal):
            os.remove(archivo_temporal)
