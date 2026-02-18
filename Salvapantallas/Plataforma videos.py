from flask import Flask, render_template_string
import json
import os

app = Flask(__name__)

JSON_FILE = "canal_videos.json"

HTML = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <link rel="stylesheet" href="css/estilo.css">
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
      {% if v.thumb_exists %}
        <img src="{{ v.thumb }}" alt="miniatura">
      {% else %}
        <img src="" alt="">
      {% endif %}

      <div>
        <div class="title">{{ v.title }}</div>
        <a href="{{ v.url }}" target="_blank">Abrir vídeo</a>
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

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    playlists = data.get("playlists", [])

    resultado = []
    for pl in playlists:
        pl_title = pl.get("title", "Sin título")
        videos = pl.get("videos", [])

        lista_videos = []
        for v in videos:
            title = v.get("title", "Sin título")
            url = v.get("url", "#")
            thumb = v.get("thumbnail_file", "")

            thumb_exists = False
            if thumb and os.path.exists(thumb):
                thumb_exists = True

            lista_videos.append({
                "title": title,
                "url": url,
                "thumb": thumb,
                "thumb_exists": thumb_exists
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
