import sqlite3
from pathlib import Path


DB_PATH = Path("campus.db")


def get_db():
    conexion = sqlite3.connect(DB_PATH)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def query_one(sql, params=()):
    conexion = get_db()
    cursor = conexion.execute(sql, params)
    fila = cursor.fetchone()
    conexion.close()
    return fila


def query_all(sql, params=()):
    conexion = get_db()
    cursor = conexion.execute(sql, params)
    filas = cursor.fetchall()
    conexion.close()
    return filas


def execute(sql, params=()):
    conexion = get_db()
    cursor = conexion.execute(sql, params)
    conexion.commit()
    conexion.close()
    return cursor.lastrowid


def init_db():
    conexion = get_db()

    with open("schema.sql", "r", encoding="utf-8") as archivo:
        conexion.executescript(archivo.read())

    with open("seed.sql", "r", encoding="utf-8") as archivo:
        conexion.executescript(archivo.read())

    conexion.commit()
    conexion.close()
