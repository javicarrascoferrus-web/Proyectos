from flask import Flask, request, render_template_string
import requests

app = Flask(__name__)

PAGE = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <link rel="stylesheet" href="css/estilo.css">
  <title>Ollama Web (simple)</title>

</head>
<body>
  <h2>Ollama Web (simple)</h2>

  <form method="post">
    <label>Petición (presupuesto + uso)</label>
    <textarea name="prompt" rows="6">{{ prompt }}</textarea>

    <div class="row">
      <div>
        <label>Modelo</label>
        <input name="model" value="{{ model }}">
      </div>
      <div>
        <label>Ollama URL</label>
        <input name="baseUrl" value="{{ baseUrl }}">
      </div>
    </div>

    <button type="submit">Enviar</button>
  </form>

  {% if err %}
    <p style="color:#b00020"><b>Error:</b> {{ err }}</p>
  {% endif %}

  {% if out %}
    <h3>Respuesta</h3>
    <pre>{{ out }}</pre>
  {% endif %}
</body>
</html>
"""

SYSTEM_TEMPLATE = """Eres un asesor informático. El usuario te dará un presupuesto y el uso del PC.

Tu respuesta DEBE cumplir estas reglas:
1) Propón una configuración por componentes (CPU, placa, RAM, GPU si aplica, SSD, PSU, caja, disipación si aplica).
2) Para cada componente indica un precio aproximado en EUR como número (sin rangos; un único valor).
3) Incluye una tabla final "DESGLOSE" con columnas: Componente | Modelo | Precio_EUR.
4) Después incluye un bloque "SUMA" con:
   - Lista de precios usados (solo números) en una línea.
   - Total_EUR = suma exacta de esos números.
5) Vuelve a comprobar la suma: repite el total en una segunda línea "Total_verificado_EUR" y debe coincidir.
6) Si el total supera el presupuesto, ajusta componentes hasta que Total_EUR <= presupuesto y deja margen para envío (si procede).
7) No inventes monedas ni uses USD. No uses rangos. Solo un número por precio.

Usuario:
{user_prompt}
"""

@app.route("/", methods=["GET", "POST"])
def home():
    prompt  = request.form.get("prompt", "")
    model   = request.form.get("model", "llama3:latest")
    baseUrl = request.form.get("baseUrl", "http://127.0.0.1:11434")

    out, err = "", ""

    if request.method == "POST":
        user_prompt = (prompt or "").strip()
        system_prompt = SYSTEM_TEMPLATE.format(user_prompt=user_prompt)

        url = baseUrl.rstrip("/") + "/api/generate"
        payload = {"model": model, "prompt": system_prompt, "stream": False}

        try:
            r = requests.post(url, json=payload, timeout=60)
            if not r.ok:
                err = f"HTTP {r.status_code}: {r.text}"
            else:
                data = r.json()
                out = str(data.get("response", ""))
        except Exception as e:
            err = str(e)

    return render_template_string(PAGE, prompt=prompt, model=model, baseUrl=baseUrl, out=out, err=err)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
