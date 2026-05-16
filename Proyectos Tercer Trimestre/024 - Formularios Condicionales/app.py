from flask import Flask, render_template, request
from flask import Flask, render_template
import re
import hashlib

app = Flask(__name__)

ARCHIVO_PLANTILLA = "plantilla.md"


def normalizar_nombre(texto):
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9]+", "_", texto)
    texto = texto.strip("_")
    return texto or "campo"


def contar_tabs(linea):
    return len(linea) - len(linea.lstrip("\t"))


def leer_plantilla():
    with open(ARCHIVO_PLANTILLA, "r", encoding="utf-8") as archivo:
        return archivo.readlines()


def parsear_bloque(lineas, indice, nivel=0, prefijo="campo"):
    estructura = []

    while indice < len(lineas):
        linea_original = lineas[indice].rstrip("\n")

        if not linea_original.strip():
            indice += 1
            continue

        nivel_actual = contar_tabs(linea_original)

        if nivel_actual < nivel:
            break

        if nivel_actual > nivel:
            indice += 1
            continue

        linea = linea_original.strip()

        tipos_simples = ["text", "number", "email", "date", "textarea"]
        tipos_condicionales = ["radio", "select", "checkbox"]

        tipo_detectado = None

        for tipo in tipos_simples + tipos_condicionales:
            if linea.startswith(f"[{tipo}]"):
                tipo_detectado = tipo
                break

        if not tipo_detectado:
            indice += 1
            continue

        etiqueta = linea.replace(f"[{tipo_detectado}]", "").strip()

        if tipo_detectado in tipos_simples:
            estructura.append({
                "tipo": tipo_detectado,
                "etiqueta": etiqueta,
                "name": normalizar_nombre(prefijo + "_" + etiqueta)
            })
            indice += 1
            continue

        if tipo_detectado in tipos_condicionales:
            nombre_campo = normalizar_nombre(prefijo + "_" + etiqueta)

            campo = {
                "tipo": tipo_detectado,
                "etiqueta": etiqueta,
                "name": nombre_campo,
                "opciones": []
            }

            indice += 1

            while indice < len(lineas):
                sublinea_original = lineas[indice].rstrip("\n")

                if not sublinea_original.strip():
                    indice += 1
                    continue

                subnivel = contar_tabs(sublinea_original)
                sublinea = sublinea_original.strip()

                if subnivel < nivel + 1:
                    break

                if subnivel == nivel + 1 and sublinea.startswith("[case]"):
                    valor = sublinea.replace("[case]", "").strip()
                    indice += 1

                    hijos, indice = parsear_bloque(
                        lineas,
                        indice,
                        nivel + 2,
                        prefijo + "_" + etiqueta + "_" + valor
                    )

                    campo["opciones"].append({
                        "valor": valor,
                        "hijos": hijos
                    })
                else:
                    indice += 1

            estructura.append(campo)

    return estructura, indice


def crear_id_condicional(nombre, valor):
    texto = nombre + "_" + valor
    return "cond_" + hashlib.md5(texto.encode()).hexdigest()


@app.route("/", methods=["GET", "POST"])
def index():
    lineas = leer_plantilla()
    estructura, _ = parsear_bloque(lineas, 0)

    if request.method == "POST":
        datos = request.form.to_dict(flat=False)

        return render_template(
            "resultado.html",
            datos=datos
        )

    return render_template(
        "index.html",
        estructura=estructura,
        crear_id_condicional=crear_id_condicional
    )


if __name__ == "__main__":
    app.run(debug=True)
