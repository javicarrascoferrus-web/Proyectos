from pathlib import Path
import requests
from textwrap import dedent

def resumir_cv(md_file: str, model="qwen2.5:3b-instruct", host="http://localhost:11434") -> str:
    cv = Path(md_file).read_text(encoding="utf-8")

    prompt = dedent(f"""
    Eres experto en selección y redacción de perfiles.
    Resume el CV en 7–10 líneas (~200 palabras), en tercera persona, español, estilo neutro.
    Añade una opinión: ¿es válido para profesor de ciclos formativos de FP? (justifica breve).

    CV:
    ---
    {cv}
    ---
    """).strip()

    r = requests.post(f"{host}/api/generate", json={"model": model.strip(), "prompt": prompt, "stream": False}, timeout=600)
    r.raise_for_status()
    return r.json().get("response", "").strip()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python resumir_cv.py archivo.md [modelo] [host]")
        raise SystemExit(2)
    print(resumir_cv(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "qwen2.5:3b-instruct",
                     sys.argv[3] if len(sys.argv) > 3 else "http://localhost:11434"))
