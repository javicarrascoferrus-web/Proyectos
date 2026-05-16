import subprocess

def analizar_con_ia(texto_web):

    prompt = f"""
    Analiza el siguiente contenido extraído de una página web.

    Explica:
    - De qué trata la web
    - Qué tipo de empresa o proyecto parece
    - Qué servicios ofrece
    - Público objetivo

    Responde únicamente en español.
    Sé claro y profesional.

    CONTENIDO:
    {texto_web}
    """

    resultado = subprocess.run(
        ["ollama", "run", "phi4-mini:latest", prompt],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    return resultado.stdout
