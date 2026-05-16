from functools import wraps
from flask import session, redirect, url_for

from database import query_one


def usuario_actual():
    usuario_id = session.get("usuario_id")

    if not usuario_id:
        return None

    return query_one("""
        SELECT usuarios.*, perfiles.nombre AS perfil
        FROM usuarios
        JOIN perfiles ON perfiles.id = usuarios.perfil_id
        WHERE usuarios.id = ? AND usuarios.activo = 1
    """, (usuario_id,))


def login_usuario(email, password):
    usuario = query_one("""
        SELECT *
        FROM usuarios
        WHERE email = ? AND activo = 1
    """, (email,))

    if not usuario:
        return False

    if usuario["password"] != password:
        return False

    session["usuario_id"] = usuario["id"]
    return True


def cerrar_sesion():
    session.clear()


def requiere_login(funcion):
    @wraps(funcion)
    def wrapper(*args, **kwargs):
        if not usuario_actual():
            return redirect(url_for("login"))

        return funcion(*args, **kwargs)

    return wrapper


def es_admin(usuario):
    return usuario and usuario["perfil"] == "administrador"


def es_profesor(usuario):
    return usuario and usuario["perfil"] in ["profesor", "administrador"]


def es_alumno(usuario):
    return usuario and usuario["perfil"] == "alumno"
