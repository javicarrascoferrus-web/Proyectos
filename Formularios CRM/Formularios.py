from flask import Flask, request, redirect, session, url_for, render_template_string
import mysql.connector

app = Flask(__name__)
app.secret_key = "1234"  

DB = {
    "host": "localhost",
    "user": "training_center",
    "password": "training_center",
    "database": "training_center",
}

ADMIN_USER = "Javier Carrasco"
ADMIN_PASS = "Javier Carrasco"

ESTADOS = ["Nuevo", "Contactado", "En seguimiento", "Ganado", "Perdido"]


def conectar():
    return mysql.connector.connect(**DB)


def get_columnas():
    con = conectar()
    cur = con.cursor(dictionary=True)
    cur.execute("""
        SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_KEY, COLUMN_DEFAULT, COLUMN_COMMENT
        FROM information_schema.columns
        WHERE table_schema=%s AND table_name='inscripciones'
        ORDER BY ORDINAL_POSITION
    """, (DB["database"],))
    cols = cur.fetchall()
    cur.close()
    con.close()
    return cols


def es_excluida(col):

    if col["COLUMN_KEY"] == "PRI":
        return True
    if col["COLUMN_DEFAULT"] == "CURRENT_TIMESTAMP":
        return True
    return False


def crear_tabla_crm_si_no_existe():
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS crm_estados_inscripciones (
            id INT AUTO_INCREMENT PRIMARY KEY,
            id_registro VARCHAR(255) UNIQUE,
            estado VARCHAR(50)
        );
    """)
    con.commit()
    cur.close()
    con.close()


def get_pk():
    cols = get_columnas()
    for c in cols:
        if c["COLUMN_KEY"] == "PRI":
            return c["COLUMN_NAME"]
    return None



@app.route("/", methods=["GET", "POST"])
def formulario():
    cols = [c for c in get_columnas() if not es_excluida(c)]
    msg = ""

    if request.method == "POST":
        try:
            campos = []
            placeholders = []
            valores = []

            for c in cols:
                nombre = c["COLUMN_NAME"]
                campos.append(nombre)
                placeholders.append("%s")

       
                if "tinyint" in c["COLUMN_TYPE"].lower():
                    valores.append(1 if request.form.get(nombre) == "on" else 0)
                else:
                    valores.append(request.form.get(nombre, "") or None)

            sql = f"INSERT INTO inscripciones ({','.join(campos)}) VALUES ({','.join(placeholders)})"

            con = conectar()
            cur = con.cursor()
            cur.execute(sql, valores)
            con.commit()
            cur.close()
            con.close()

            msg = " Guardado"
        except Exception as e:
            msg = f" Error: {e}"

    html = """
    <!doctype html><html lang="es"><head>
    <meta charset="utf-8">
    <link rel="stylesheet" href="css/estilo.css">
    <title>Formulario</title>
    
    </head><body>
      <div class="card">
        <div class="top">
          <h2 style="margin:0;color:crimson;">Formulario</h2>
          <a href="/admin">Admin</a>
        </div>

        {% if msg %}<p>{{msg}}</p>{% endif %}

        <form method="post">
          {% for c in cols %}
            <div class="row">
              <label>Introduce {{c.COLUMN_NAME}}</label>
              {% if c.COLUMN_COMMENT %}
                <div style="font-size:.85em;color:#666;">{{c.COLUMN_COMMENT}}</div>
              {% endif %}

              {% if "tinyint" in c.COLUMN_TYPE.lower() %}
                <input type="checkbox" name="{{c.COLUMN_NAME}}">
              {% elif "text" == c.COLUMN_TYPE.lower() %}
                <textarea name="{{c.COLUMN_NAME}}"></textarea>
              {% else %}
                <input type="text" name="{{c.COLUMN_NAME}}">
              {% endif %}
            </div>
          {% endfor %}
          <button type="submit">Enviar</button>
        </form>
      </div>
    </body></html>
    """
    return render_template_string(html, cols=cols, msg=msg)



@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    err = ""
    if request.method == "POST":
        u = request.form.get("user", "")
        p = request.form.get("pw", "")
        if u == ADMIN_USER and p == ADMIN_PASS:
            session["admin"] = True
            return redirect("/admin")
        err = "Usuario o contraseña incorrectos"

    html = """
    <html><head><meta charset="utf-8"><title>Login</title>
    <style>
      body{font-family:Segoe UI;background:#f2f2f2;padding:30px;}
      .card{background:white;max-width:420px;margin:auto;padding:20px;border-radius:10px;border-top:8px solid crimson;}
      label{color:crimson;font-weight:600;}
      input{width:100%;padding:10px;border:1px solid #ddd;border-radius:6px;margin-top:6px;}
      .row{margin-bottom:15px;}
      button{background:crimson;color:white;border:none;padding:10px 14px;border-radius:6px;cursor:pointer;}
    </style>
    </head><body>
      <div class="card">
        <h2 style="margin:0 0 10px;color:crimson;">Login admin</h2>
        {% if err %}<p style="color:#b30000;">{{err}}</p>{% endif %}
        <form method="post">
          <div class="row"><label>Usuario</label><input name="user"></div>
          <div class="row"><label>Contraseña</label><input name="pw" type="password"></div>
          <button>Entrar</button>
        </form>
      </div>
    </body></html>
    """
    return render_template_string(html, err=err)


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect("/admin/login")


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("admin"):
        return redirect("/admin/login")

    crear_tabla_crm_si_no_existe()
    pk = get_pk()


    if request.method == "POST":
        rid = request.form.get("rid")
        estado = request.form.get("estado")
        if rid and estado:
            con = conectar()
            cur = con.cursor()
            cur.execute("""
                INSERT INTO crm_estados_inscripciones (id_registro, estado)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE estado=%s
            """, (rid, estado, estado))
            con.commit()
            cur.close()
            con.close()
        return redirect("/admin")

    con = conectar()
    cur = con.cursor(dictionary=True)
    cur.execute("SELECT id_registro, estado FROM crm_estados_inscripciones")
    crm = {r["id_registro"]: r["estado"] for r in cur.fetchall()}


    cur.execute("SELECT * FROM inscripciones")
    rows = cur.fetchall()
    cur.close()
    con.close()

    cols = list(rows[0].keys()) if rows else []

    html = """
    <html><head><meta charset="utf-8"><title>Admin</title>
    <style>
      body{font-family:Segoe UI;background:#f2f2f2;padding:30px;}
      .card{background:white;max-width:1000px;margin:auto;padding:20px;border-radius:10px;border-top:8px solid crimson;}
      table{width:100%;border-collapse:collapse;font-size:.9em;}
      th,td{padding:8px;border-bottom:1px solid #eee;text-align:left;}
      th{color:crimson;}
      select{padding:6px;border:1px solid #ddd;border-radius:6px;}
      button{background:crimson;color:white;border:none;padding:6px 10px;border-radius:6px;cursor:pointer;}
      a{color:crimson;text-decoration:none;}
      .top{display:flex;justify-content:space-between;align-items:center;}
    </style>
    </head><body>
      <div class="card">
        <div class="top">
          <h2 style="margin:0;color:crimson;">Panel admin</h2>
          <div><a href="/">Formulario</a> | <a href="/admin/logout">Salir</a></div>
        </div>

        <table>
          <thead>
            <tr>
              {% for c in cols %}<th>{{c}}</th>{% endfor %}
              <th>Estado</th>
              <th>Cambiar</th>
            </tr>
          </thead>
          <tbody>
            {% for r in rows %}
              {% set rid = r[pk] %}
              <tr>
                {% for c in cols %}<td>{{r[c]}}</td>{% endfor %}
                <td>{{ crm.get(rid|string, "Sin estado") }}</td>
                <td>
                  <form method="post" style="display:flex;gap:6px;align-items:center;">
                    <input type="hidden" name="rid" value="{{rid}}">
                    <select name="estado">
                      {% for e in estados %}
                        <option value="{{e}}" {% if crm.get(rid|string)==e %}selected{% endif %}>{{e}}</option>
                      {% endfor %}
                    </select>
                    <button>Guardar</button>
                  </form>
                </td>
              </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </body></html>
    """
    return render_template_string(html, rows=rows, cols=cols, pk=pk, crm=crm, estados=ESTADOS)


if __name__ == "__main__":
    app.run(debug=True)
