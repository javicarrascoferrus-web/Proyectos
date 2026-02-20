from flask import Flask, render_template_string, url_for
import json
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(BASE_DIR, "canal_videos.json")
STATIC_DIR = os.path.join(BASE_DIR, "static")

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
        <img src="{{ url_for('static', filename='thumbs/placeholder.png') }}" alt="sin miniatura">
      {% endif %}

      <div>
        <div class="title">{{ v.title }}</div>
        <a href="{{ v.url }}" target="_blank" rel="noopener">Abrir vídeo</a>
      </div>
    </div>
  {% endfor %}

{% endfor %}

</body>
</html>
"""

def leer_json():
 
    if not os.path.exists(JSON_FILE):
        return []

    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

    playlists = data.get("playlists", [])
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

            # En el JSON: "thumbnail_file": "thumbs/imagen.jpg" (relativo a /static)
            thumb_rel = v.get("thumbnail_file", "")
            thumb_file = None

            if isinstance(thumb_rel, str) and thumb_rel.strip():
                # Comprobamos si existe dentro de static/
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
    app.run(debug=True)
