Explicación del código del proyecto plataforma de videos:

# Importaciones: 
Flask → crea la aplicación web.

render_template_string → permite generar HTML desde Python.

json → sirve para leer el archivo .json.

os → sirve para comprobar si existen archivos (miniaturas)

# Crear la aplicación web
app = Flask(__name__)

# Nombre archivo JSON:
JSON_FILE = "canal_videos.json"

# Función que lee JSON:
def leer_json():


# Ruta web principal:
@app.route("/")
def home():


# Arrancar servidor:
if __name__ == "__main__":
    app.run(debug=True)


Cuando visitas la web:
1. Flask recibe la petición /
2. Ejecuta home()
3. home() llama leer_json()
4. leer_json() lee el archivo JSON
5. devuelve playlists
6. Flask genera HTML con los datos
7. el navegador muestra la página
