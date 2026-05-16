
from flask import Flask, render_template, request, redirect, url_for

from database import init_db, query_all, query_one
from auth import (
    login_usuario,
    cerrar_sesion,
    usuario_actual,
    requiere_login,
    es_profesor
)


app = Flask(__name__)
app.secret_key = "clave_secreta_nan_campus"


@app.route("/")
@requiere_login
def dashboard():
    usuario = usuario_actual()

    if usuario["perfil"] == "administrador":
        asignaturas = query_all("""
            SELECT asignaturas.*, cursos.nombre AS curso
            FROM asignaturas
            JOIN cursos ON cursos.id = asignaturas.curso_id
            WHERE asignaturas.activo = 1
            ORDER BY cursos.nombre, asignaturas.orden
        """)
    else:
        asignaturas = query_all("""
            SELECT asignaturas.*, cursos.nombre AS curso
            FROM matriculas
            JOIN asignaturas ON asignaturas.id = matriculas.asignatura_id
            JOIN cursos ON cursos.id = asignaturas.curso_id
            WHERE matriculas.usuario_id = ?
            AND matriculas.tipo = ?
            AND matriculas.activo = 1
            ORDER BY cursos.nombre, asignaturas.orden
        """, (usuario["id"], usuario["perfil"]))

    return render_template(
        "dashboard.html",
        usuario=usuario,
        asignaturas=asignaturas
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if login_usuario(email, password):
            return redirect(url_for("dashboard"))

        error = "Correo o contraseña incorrectos."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    cerrar_sesion()
    return redirect(url_for("login"))


@app.route("/asignatura/<int:asignatura_id>")
@requiere_login
def asignatura(asignatura_id):
    usuario = usuario_actual()

    asignatura = query_one("""
        SELECT asignaturas.*, cursos.nombre AS curso
        FROM asignaturas
        JOIN cursos ON cursos.id = asignaturas.curso_id
        WHERE asignaturas.id = ?
    """, (asignatura_id,))

    if not asignatura:
        return redirect(url_for("dashboard"))

    unidades = query_all("""
        SELECT *
        FROM unidades
        WHERE asignatura_id = ?
        ORDER BY orden, id
    """, (asignatura_id,))

    temas = query_all("""
        SELECT temas.*
        FROM temas
        JOIN unidades ON unidades.id = temas.unidad_id
        WHERE unidades.asignatura_id = ?
        ORDER BY temas.orden, temas.id
    """, (asignatura_id,))

    lecciones = query_all("""
        SELECT lecciones.*
        FROM lecciones
        JOIN temas ON temas.id = lecciones.tema_id
        JOIN unidades ON unidades.id = temas.unidad_id
        WHERE unidades.asignatura_id = ?
        ORDER BY lecciones.orden, lecciones.id
    """, (asignatura_id,))

    sesiones = query_all("""
        SELECT sesiones.*
        FROM sesiones
        JOIN lecciones ON lecciones.id = sesiones.leccion_id
        JOIN temas ON temas.id = lecciones.tema_id
        JOIN unidades ON unidades.id = temas.unidad_id
        WHERE unidades.asignatura_id = ?
        ORDER BY sesiones.fecha, sesiones.id
    """, (asignatura_id,))

    recursos = query_all("""
        SELECT recursos.*
        FROM recursos
        JOIN lecciones ON lecciones.id = recursos.leccion_id
        JOIN temas ON temas.id = lecciones.tema_id
        JOIN unidades ON unidades.id = temas.unidad_id
        WHERE unidades.asignatura_id = ?
        ORDER BY recursos.id
    """, (asignatura_id,))

    tareas = query_all("""
        SELECT tareas.*
        FROM tareas
        JOIN lecciones ON lecciones.id = tareas.leccion_id
        JOIN temas ON temas.id = lecciones.tema_id
        JOIN unidades ON unidades.id = temas.unidad_id
        WHERE unidades.asignatura_id = ?
        ORDER BY tareas.fecha_entrega, tareas.id
    """, (asignatura_id,))

    return render_template(
        "subject.html",
        usuario=usuario,
        asignatura=asignatura,
        unidades=unidades,
        temas=temas,
        lecciones=lecciones,
        sesiones=sesiones,
        recursos=recursos,
        tareas=tareas,
        es_profesor=es_profesor(usuario)
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
