from flask import Flask, render_template_string, url_for
import json
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(BASE_DIR, "canal_videos.json")
STATIC_DIR = os.path.join(BASE_DIR, "static")
CSS_DIR = os.path.join(STATIC_DIR, "css")
THUMBS_DIR = os.path.join(STATIC_DIR, "thumbs")
CSS_FILE = os.path.join(CSS_DIR, "estilo.css")
PLACEHOLDER_SVG = os.path.join(THUMBS_DIR, "placeholder.svg")


HTML = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <link rel="stylesheet" href="{{ url_for('static', filename='css/estilo.css') }}">
  <title>Videos</title>
</head>
<body>

<h1>Playlists</h1>

{% if not playlists %}
  <p>No hay playlists o no se pudo leer el JSON.</p>
{% endif %}

{% for pl in playlists %}
  <h2>{{ pl.title }}</h2>

  {% if not pl.videos %}
    <p>Sin vídeos</p>
  {% endif %}

  {% for v in pl.videos %}
    <div class="video">
      {% if v.thumb_file %}
        <img src="{{ url_for('static', filename=v.thumb_file) }}" alt="miniatura">
      {% else %}
        <img src="{{ url_for('static', filename='thumbs/placeholder.svg') }}" alt="sin miniatura">
      {% endif %}

      <div class="info">
        <div class="title">{{ v.title }}</div>
        <a href="{{ v.url }}" target="_blank" rel="noopener">Abrir vídeo</a>
      </div>
    </div>
  {% endfor %}

{% endfor %}

</body>
</html>
"""





def asegurar_archivos():
 
    os.makedirs(CSS_DIR, exist_ok=True)
    os.makedirs(THUMBS_DIR, exist_ok=True)


    if not os.path.exists(JSON_FILE):
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(EJEMPLO_JSON, f, ensure_ascii=False, indent=2)

    if not os.path.exists(CSS_FILE):
        with open(CSS_FILE, "w", encoding="utf-8") as f:
            f.write(CSS_EJEMPLO)


    if not os.path.exists(PLACEHOLDER_SVG):
        with open(PLACEHOLDER_SVG, "w", encoding="utf-8") as f:
            f.write(PLACEHOLDER_SVG_CONTENT)


def leer_json():
   
    if not os.path.exists(JSON_FILE):
        return []

    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

 
    if isinstance(data, list):
        playlists = data
    elif isinstance(data, dict):
        playlists = data.get("playlists", [])
    else:
        return []

    if not isinstance(playlists, list):
        return []

    resultado = []
    for pl in playlists:
        if not isinstance(pl, dict):
            continue

        pl_title = pl.get("title", "Sin título")
        videos = pl.get("videos", [])
        if not isinstance(videos, list):
            videos = []

        lista_videos = []
        for v in videos:
            if not isinstance(v, dict):
                continue

            title = v.get("title", "Sin título")
            url = v.get("url", "#")

        
            thumb_rel = v.get("thumbnail_file", "")
            thumb_file = None

            if isinstance(thumb_rel, str) and thumb_rel.strip():
                thumb_path = os.path.join(STATIC_DIR, thumb_rel)
                if os.path.exists(thumb_path):
                    thumb_file = thumb_rel

            lista_videos.append({
                "title": title,
                "url": url,
                "thumb_file": thumb_file
            })

        resultado.append({
            "title": pl_title,
            "videos": lista_videos
        })

    return resultado


@app.route("/")
def home():
    playlists = leer_json()
    return render_template_string(HTML, playlists=playlists)


if __name__ == "__main__":
    asegurar_archivos()
    app.run(debug=True)
