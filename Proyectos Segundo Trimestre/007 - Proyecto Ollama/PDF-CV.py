from pathlib import Path
from pypdf import PdfReader
import requests
from textwrap import dedent


def extraer_texto_pdf(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)

    texto = "\n\n".join(
        (pagina.extract_text() or "").strip()
        for pagina in reader.pages
    ).strip()

    return texto


def resumir_cv(texto_cv: str,
                model="qwen2.5:3b-instruct",
                host="http://localhost:11434") -> str:

    prompt = dedent(f"""
    Eres experto en selección y redacción de perfiles.

    Resume el siguiente CV en:
    - 7 a 10 líneas
    - unas 200 palabras
    - tercera persona
    - español
    - estilo profesional y neutro

    Además indica si sería válido para profesor de FP
    y justifica brevemente.

    CV:

    {texto_cv}
    """).strip()

    respuesta = requests.post(
        f"{host}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False
        },
        timeout=600
    )

    respuesta.raise_for_status()

    return respuesta.json()["response"].strip()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python resumir_cv.py archivo.pdf")
        raise SystemExit(2)

    pdf = sys.argv[1]

    print("Extrayendo texto del PDF...")
    texto = extraer_texto_pdf(pdf)

    print("Consultando IA...")
    resumen = resumir_cv(texto)

    print("\n===== RESUMEN =====\n")
    print(resumen)
