Esta pequeña guia explica el código del proyecto:

# Imports:
Flask: crea la aplicación web.

request: para leer lo que el usuario envía (POST).

redirect: para redirigir a otra página.

session: para recordar si el admin está logueado.

render_template_string: para escribir HTML dentro del propio Python.

mysql.connector: para conectarse a MySQL.

# Crear app y config

app = Flask(__name__) crea la aplicación.

secret_key es obligatoria para que funcionen las sesiones (session).

# Datos de la base de datos y admin:
DB: datos para conectarse a MySQL.

ADMIN_USER y ADMIN_PASS: usuario/contraseña del panel.

ESTADOS: lista simple de estados CRM

# Conectar MySQL:

def conectar():
    return mysql.connector.connect(**DB)


# Leer columnas de la tabla:
def get_columnas():
    con = conectar()
    cur = con.cursor(dictionary=True)

# Decidir qué columnas NO se ponen en el formulario/insert

def es_excluida(col):
    if col["COLUMN_KEY"] == "PRI":
        return True
    if col["COLUMN_DEFAULT"] == "CURRENT_TIMESTAMP":
        return True
    return False



# Crear tabla auxiliar para estados CRM

def crear_tabla_crm_si_no_existe():

# Encontrar la columna que es PK (id)
def get_pk():
    cols = get_columnas()
    for c in cols:
        if c["COLUMN_KEY"] == "PRI":
            return c["COLUMN_NAME"]
    return None


 # Ruta / : formulario + guardar
@app.route("/", methods=["GET", "POST"])
def formulario():

 # Login admin /admin/login

 @app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

# Logout /admin/logout

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect("/admin/login")
    
# Panel admin /admin

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("admin"):
        return redirect("/admin/login")


# Ejecutar el servidor
if __name__ == "__main__":
    app.run(debug=True)
        
