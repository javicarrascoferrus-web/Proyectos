En este proyecto he creado una web muy simple hecha con Flask que envía un prompt a Ollama, recibe la respuesta del modelo y la muestra en pantalla.

## Explicación del proyecto y sus comandos

Flask → crea la web.

request → permite leer datos enviados desde el formulario HTML.

render_template_string → renderiza HTML directamente desde un string (sin archivos .html).

requests → hace peticiones HTTP (para hablar con Ollama).

### Crear servidor web Flask:
app = Flask(__name__)


### Sustituye el texto del ususario:
{user_prompt}


### Ruta principal:
@app.route("/", methods=["GET", "POST"])
def home():

GET → cuando abres la página

POST → cuando pulsas enviar

### Leer datos del formulario:
prompt  = request.form.get("prompt", "")
model   = request.form.get("model", "llama3:latest")
baseUrl = request.form.get("baseUrl", "http://127.0.0.1:11434")

### Variables de salida:
out, err = "", ""
out = respuesta del modelo

err = mensaje de error

### Usuario pulsa enviar
if request.method == "POST":


### Preparar prompt:
user_prompt = (prompt or "").strip()
system_prompt = SYSTEM_TEMPLATE.format(user_prompt=user_prompt)


### Construir URL:
url = baseUrl.rstrip("/") + "/api/generate"


### JSON enviado a Ollama:
payload = {
    "model": model,
    "prompt": system_prompt,
    "stream": False
}


### Llamada HTTP:
r = requests.post(url, json=payload, timeout=60)


### Leer respuesta:
data = r.json()
out = str(data.get("response", ""))


### Mostrar todo en la página:
return render_template_string(...)


### Arranca el server:
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)



# Esquema del proyecto:
Navegador
   ↓
Flask (web simple)
   ↓
crea prompt reforzado
   ↓
requests.post()
   ↓
Ollama local
   ↓
respuesta JSON
   ↓
Flask la muestra en HTML
