from flask import Flask, request, render_template_string
import requests

app = Flask(__name__)

PAGE = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <link rel="stylesheet" href="/static/css/estilo.css">
  <title>IA de Dietética (Ollama)</title>
  <style>
    body{font-family:system-ui;margin:24px;max-width:980px}
    textarea,input{width:100%;padding:10px;margin:6px 0}
    .row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
    pre{white-space:pre-wrap;background:#f4f4f5;padding:12px;border-radius:10px}
    label{font-weight:600}
    button{padding:10px 14px}
  </style>
</head>
<body>
  <h2>IA de Dietética (Ollama)</h2>

  <form method="post">
    <label>Datos del usuario (objetivo + datos personales + preferencias)</label>
    <textarea name="prompt" rows="10" placeholder="Ej: Tengo 24 años, hombre, 1.78m, 76kg. Objetivo: perder grasa sin perder músculo. Actividad: 4 días gym/semana. Alergias: ninguna. Prefiero dieta mediterránea, no como cerdo. Presupuesto medio. Horarios: desayuno 8h, comida 14h, cena 21h.">{{ prompt }}</textarea>

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

    <button type="submit">Generar plan</button>
  </form>

  {% if err %}
    <p style="color:#b00020"><b>Error:</b> {{ err }}</p>
  {% endif %}

  {% if out %}
    <h3>Resultado</h3>
    <pre>{{ out }}</pre>
  {% endif %}
</body>
</html>
"""

SYSTEM_TEMPLATE = """Eres una IA de dietética y nutrición práctica (nivel divulgación), orientada a ayudar a personas sanas.
Tu objetivo es crear planes de alimentación realistas y seguros.

REGLAS DE SEGURIDAD:
- No diagnostiques ni trates enfermedades.
- Si el usuario menciona diabetes, enfermedad renal/hepática, trastornos de conducta alimentaria, embarazo/lactancia, medicación relevante, o síntomas preocupantes,
  responde que debe consultar a un profesional sanitario y ofrece recomendaciones generales no médicas.
- No promuevas prácticas extremas (ayunos agresivos, dietas <1200 kcal sin supervisión, "detox", etc.).
- No inventes estudios ni enlaces.

TAREA:
Con la información del usuario, crea:
1) Estimación de calorías diarias (TDEE) y calorías objetivo según meta (déficit/superávit/mantenimiento)
   - Si faltan datos (edad, sexo, altura, peso, actividad), pide lo mínimo necesario en 3-6 preguntas cortas.
2) Reparto de macronutrientes diario (proteína, carbohidratos, grasa) en gramos y %.
3) Plan de comidas de 7 días (desayuno, comida, cena + 1-2 snacks si procede).
   - Para cada comida: alimentos y cantidades aproximadas (g, unidades) + calorías estimadas.
4) Lista de la compra semanal agrupada por categorías.
5) Sustituciones (al menos 6) por alergias/preferencias (p.ej. alternativas a lácteos, gluten, carne).
6) Consejos prácticos (meal prep, hidratación, fibra, adherencia).
7) Aviso final: “Esto es orientación general y no sustituye a un dietista-nutricionista”.

FORMATO DE SALIDA (OBLIGATORIO):
- Usa Markdown.
- Incluye estas secciones EXACTAS con estos títulos:
  ## Resumen
  ## Calorías y objetivo
  ## Macronutrientes
  ## Plan semanal (7 días)
  ## Lista de la compra
  ## Sustituciones
  ## Consejos
  ## Aviso

Usuario: {user_prompt}
"""

def safe_format_system_template(user_prompt: str) -> str:
  
    user_prompt = user_prompt.replace("{", "{{").replace("}", "}}")
    return SYSTEM_TEMPLATE.format(user_prompt=user_prompt)

@app.route("/", methods=["GET", "POST"])
def home():
    prompt  = request.form.get("prompt", "")
    model   = request.form.get("model", "llama3:latest")
    baseUrl = request.form.get("baseUrl", "http://127.0.0.1:11434")

    out, err = "", ""

    if request.method == "POST":
        user_prompt = (prompt or "").strip()
        system_prompt = safe_format_system_template(user_prompt)

        url = baseUrl.rstrip("/") + "/api/generate"
        payload = {"model": model, "prompt": system_prompt, "stream": False}

        try:
            r = requests.post(url, json=payload, timeout=120)
            if not r.ok:
                err = f"HTTP {r.status_code}: {r.text}"
            else:
                try:
                    data = r.json()
                except ValueError:
                    err = f"Respuesta no JSON: {r.text[:500]}"
                else:
                    out = str(data.get("response", "")).strip()
                    if not out:
                        err = "La IA devolvió una respuesta vacía."
        except requests.RequestException as e:
            err = f"Error de red: {e}"
        except Exception as e:
            err = str(e)

    return render_template_string(
        PAGE, prompt=prompt, model=model, baseUrl=baseUrl, out=out, err=err
    )

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
