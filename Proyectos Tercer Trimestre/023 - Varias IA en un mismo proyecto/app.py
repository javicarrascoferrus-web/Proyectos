import os
import requests

URL_OLLAMA = "http://localhost:11434/api/generate"

MODELO_EXPLICACION = "llama3.1:8b"
MODELO_CODIGO = "codellama:7b"

ARCHIVO_TEMARIO = "programacion.txt"
ARCHIVO_RESULTADO = "resultado.md"


def consultar_ia(modelo, prompt):
    datos = {
        "model": modelo,
        "prompt": prompt,
        "stream": False
    }

    try:
        respuesta = requests.post(URL_OLLAMA, json=datos, timeout=300)
        respuesta.raise_for_status()
        return respuesta.json().get("response", "")
    except requests.exceptions.ConnectionError:
        return "Error: no se pudo conectar con Ollama. Comprueba que Ollama está abierto."
    except Exception as error:
        return f"Error al consultar la IA: {error}"


def comprobar_archivo_temario():
    if not os.path.exists(ARCHIVO_TEMARIO):
        print(f"No existe el archivo {ARCHIVO_TEMARIO}")
        return False
    return True


def leer_temario():
    with open(ARCHIVO_TEMARIO, "r", encoding="utf-8") as archivo:
        return archivo.readlines()


def preparar_resultado():
    with open(ARCHIVO_RESULTADO, "w", encoding="utf-8") as archivo:
        archivo.write("# Manual generado con varias IA\n\n")
        archivo.write("Este documento ha sido creado automáticamente usando dos modelos de inteligencia artificial.\n\n")
        archivo.write("- Una IA genera explicaciones teóricas.\n")
        archivo.write("- Otra IA genera ejemplos de código.\n\n")
        archivo.write("---\n\n")


def guardar_resultado(texto):
    with open(ARCHIVO_RESULTADO, "a", encoding="utf-8") as archivo:
        archivo.write(texto + "\n\n")


def limpiar_subtema(linea):
    return linea.replace("−", "").strip()


def main():
    if not comprobar_archivo_temario():
        return

    preparar_resultado()
    lineas = leer_temario()

    tema_actual = ""

    for linea in lineas:
        linea = linea.strip()

        if not linea:
            continue

        print(f"Procesando: {linea}")

        if linea.endswith(":"):
            tema_actual = linea.replace(":", "")

            guardar_resultado(f"# {tema_actual}")

            prompt = f"""
Explica de forma clara y breve este tema de programación en C++: {tema_actual}.
No incluyas código.
Escribe en español.
"""

            explicacion = consultar_ia(MODELO_EXPLICACION, prompt)
            guardar_resultado(explicacion)
            guardar_resultado("---")

        elif linea.startswith("−"):
            subtema = limpiar_subtema(linea)

            guardar_resultado(f"## {subtema}")

            prompt_teoria = f"""
Explica el concepto de {subtema} en C++.
No incluyas código.
Escribe en español de forma didáctica.
"""

            teoria = consultar_ia(MODELO_EXPLICACION, prompt_teoria)

            guardar_resultado("### Explicación")
            guardar_resultado(teoria)

            prompt_codigo = f"""
Genera un ejemplo sencillo de código en C++ sobre {subtema}.
Devuelve solo el código, sin explicación.
No uses using namespace std.
"""

            codigo = consultar_ia(MODELO_CODIGO, prompt_codigo)

            guardar_resultado("### Ejemplo de código")
            guardar_resultado("```cpp\n" + codigo.strip() + "\n```")
            guardar_resultado("---")

    print("Proceso completado.")
    print(f"Resultado guardado en {ARCHIVO_RESULTADO}")


if __name__ == "__main__":
    main()
