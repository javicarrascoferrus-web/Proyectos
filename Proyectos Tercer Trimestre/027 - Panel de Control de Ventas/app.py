from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

BASE_DATOS = "ventas.db"
TABLAS_PERMITIDAS = ["clientes", "productos", "pedidos", "lineas_pedido"]


def conectar_db():
    conexion = sqlite3.connect(BASE_DATOS)
    conexion.row_factory = sqlite3.Row
    return conexion


def crear_base_datos():
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT NOT NULL,
            telefono TEXT,
            ciudad TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            precio REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            total REAL DEFAULT 0,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lineas_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            cantidad INTEGER NOT NULL,
            precio_unitario REAL NOT NULL,
            total_linea REAL NOT NULL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )
    """)

    conexion.commit()
    conexion.close()


def insertar_datos_ejemplo():
    conexion = conectar_db()
    total_clientes = conexion.execute(
        "SELECT COUNT(*) AS total FROM clientes"
    ).fetchone()["total"]

    if total_clientes == 0:
        conexion.execute("""
            INSERT INTO clientes (nombre, email, telefono, ciudad)
            VALUES
            ('Laura Martínez', 'laura@email.com', '600111222', 'Madrid'),
            ('Carlos Pérez', 'carlos@email.com', '600333444', 'Valencia'),
            ('Ana Gómez', 'ana@email.com', '600555666', 'Barcelona')
        """)

        conexion.execute("""
            INSERT INTO productos (nombre, descripcion, precio, stock)
            VALUES
            ('Portátil Lenovo', 'Ordenador portátil para oficina', 699.99, 12),
            ('Ratón inalámbrico', 'Ratón ergonómico USB', 19.99, 80),
            ('Monitor 24 pulgadas', 'Monitor Full HD', 149.99, 25)
        """)

        conexion.execute("""
            INSERT INTO pedidos (cliente_id, fecha, total)
            VALUES
            (1, '2026-04-20', 719.98),
            (2, '2026-04-22', 149.99)
        """)

        conexion.execute("""
            INSERT INTO lineas_pedido (pedido_id, producto_id, cantidad, precio_unitario, total_linea)
            VALUES
            (1, 1, 1, 699.99, 699.99),
            (1, 2, 1, 19.99, 19.99),
            (2, 3, 1, 149.99, 149.99)
        """)

        conexion.commit()

    conexion.close()


def obtener_columnas(tabla):
    conexion = conectar_db()
    columnas = conexion.execute(f"PRAGMA table_info({tabla})").fetchall()
    conexion.close()
    return [columna["name"] for columna in columnas]


def obtener_opciones_fk(columna):
    conexion = conectar_db()

    if columna == "cliente_id":
        opciones = conexion.execute("SELECT id, nombre FROM clientes").fetchall()
    elif columna == "producto_id":
        opciones = conexion.execute("SELECT id, nombre FROM productos").fetchall()
    elif columna == "pedido_id":
        opciones = conexion.execute("SELECT id, id AS nombre FROM pedidos").fetchall()
    else:
        opciones = []

    conexion.close()
    return opciones


def actualizar_total_pedido(conexion, pedido_id):
    conexion.execute(
        """
        UPDATE pedidos
        SET total = (
            SELECT IFNULL(SUM(total_linea), 0)
            FROM lineas_pedido
            WHERE pedido_id = ?
        )
        WHERE id = ?
        """,
        (pedido_id, pedido_id)
    )


@app.route("/")
def inicio():
    return redirect(url_for("listar", tabla="clientes"))


@app.route("/tabla/<tabla>")
def listar(tabla):
    if tabla not in TABLAS_PERMITIDAS:
        return "Tabla no permitida"

    busqueda = request.args.get("buscar", "")
    pagina = int(request.args.get("pagina", 1))
    por_pagina = 10
    offset = (pagina - 1) * por_pagina

    columnas = obtener_columnas(tabla)

    conexion = conectar_db()

    if busqueda:
        condiciones = []
        valores = []

        for columna in columnas:
            if columna != "id":
                condiciones.append(f"{columna} LIKE ?")
                valores.append(f"%{busqueda}%")

        where = "WHERE " + " OR ".join(condiciones)
    else:
        where = ""
        valores = []

    total = conexion.execute(
        f"SELECT COUNT(*) AS total FROM {tabla} {where}",
        valores
    ).fetchone()["total"]

    registros = conexion.execute(
        f"SELECT * FROM {tabla} {where} LIMIT ? OFFSET ?",
        valores + [por_pagina, offset]
    ).fetchall()

    conexion.close()

    total_paginas = max(1, (total + por_pagina - 1) // por_pagina)

    return render_template(
        "listado.html",
        tabla=tabla,
        columnas=columnas,
        registros=registros,
        busqueda=busqueda,
        pagina=pagina,
        total_paginas=total_paginas
    )


@app.route("/tabla/<tabla>/crear", methods=["GET", "POST"])
def crear(tabla):
    if tabla not in TABLAS_PERMITIDAS:
        return "Tabla no permitida"

    columnas = obtener_columnas(tabla)
    columnas_formulario = [col for col in columnas if col != "id"]

    if tabla == "pedidos":
        columnas_formulario = [col for col in columnas_formulario if col != "total"]

    if tabla == "lineas_pedido":
        columnas_formulario = [col for col in columnas_formulario if col != "total_linea"]

    if request.method == "POST":
        datos = {}

        for columna in columnas_formulario:
            datos[columna] = request.form.get(columna)

        if tabla == "lineas_pedido":
            cantidad = int(datos.get("cantidad", 0))
            precio = float(datos.get("precio_unitario", 0))
            datos["total_linea"] = cantidad * precio

        columnas_insert = list(datos.keys())
        valores = list(datos.values())
        interrogantes = ["?"] * len(columnas_insert)

        conexion = conectar_db()

        conexion.execute(
            f"""
            INSERT INTO {tabla} ({", ".join(columnas_insert)})
            VALUES ({", ".join(interrogantes)})
            """,
            valores
        )

        if tabla == "lineas_pedido":
            actualizar_total_pedido(conexion, datos["pedido_id"])

        conexion.commit()
        conexion.close()

        return redirect(url_for("listar", tabla=tabla))

    opciones_fk = {
        columna: obtener_opciones_fk(columna)
        for columna in columnas_formulario
        if columna.endswith("_id")
    }

    return render_template(
        "formulario.html",
        tabla=tabla,
        columnas=columnas_formulario,
        registro=None,
        opciones_fk=opciones_fk,
        accion="Crear"
    )


@app.route("/tabla/<tabla>/editar/<int:id>", methods=["GET", "POST"])
def editar(tabla, id):
    if tabla not in TABLAS_PERMITIDAS:
        return "Tabla no permitida"

    columnas = obtener_columnas(tabla)
    columnas_formulario = [col for col in columnas if col != "id"]

    if tabla == "pedidos":
        columnas_formulario = [col for col in columnas_formulario if col != "total"]

    if tabla == "lineas_pedido":
        columnas_formulario = [col for col in columnas_formulario if col != "total_linea"]

    conexion = conectar_db()
    registro = conexion.execute(
        f"SELECT * FROM {tabla} WHERE id = ?",
        (id,)
    ).fetchone()

    if request.method == "POST":
        datos = {}

        for columna in columnas_formulario:
            datos[columna] = request.form.get(columna)

        if tabla == "lineas_pedido":
            cantidad = int(datos.get("cantidad", 0))
            precio = float(datos.get("precio_unitario", 0))
            datos["total_linea"] = cantidad * precio

        asignaciones = [f"{columna} = ?" for columna in datos.keys()]
        valores = list(datos.values())
        valores.append(id)

        conexion.execute(
            f"""
            UPDATE {tabla}
            SET {", ".join(asignaciones)}
            WHERE id = ?
            """,
            valores
        )

        if tabla == "lineas_pedido":
            actualizar_total_pedido(conexion, datos["pedido_id"])

        conexion.commit()
        conexion.close()

        return redirect(url_for("listar", tabla=tabla))

    conexion.close()

    opciones_fk = {
        columna: obtener_opciones_fk(columna)
        for columna in columnas_formulario
        if columna.endswith("_id")
    }

    return render_template(
        "formulario.html",
        tabla=tabla,
        columnas=columnas_formulario,
        registro=registro,
        opciones_fk=opciones_fk,
        accion="Editar"
    )


@app.route("/tabla/<tabla>/eliminar/<int:id>")
def eliminar(tabla, id):
    if tabla not in TABLAS_PERMITIDAS:
        return "Tabla no permitida"

    conexion = conectar_db()

    pedido_id = None

    if tabla == "lineas_pedido":
        linea = conexion.execute(
            "SELECT pedido_id FROM lineas_pedido WHERE id = ?",
            (id,)
        ).fetchone()

        if linea:
            pedido_id = linea["pedido_id"]

    conexion.execute(f"DELETE FROM {tabla} WHERE id = ?", (id,))

    if pedido_id:
        actualizar_total_pedido(conexion, pedido_id)

    conexion.commit()
    conexion.close()

    return redirect(url_for("listar", tabla=tabla))


@app.route("/informes")
def informes():
    conexion = conectar_db()

    total_ventas = conexion.execute(
        "SELECT IFNULL(SUM(total), 0) AS total FROM pedidos"
    ).fetchone()["total"]

    total_clientes = conexion.execute(
        "SELECT COUNT(*) AS total FROM clientes"
    ).fetchone()["total"]

    total_productos = conexion.execute(
        "SELECT COUNT(*) AS total FROM productos"
    ).fetchone()["total"]

    total_pedidos = conexion.execute(
        "SELECT COUNT(*) AS total FROM pedidos"
    ).fetchone()["total"]

    productos_vendidos = conexion.execute("""
        SELECT productos.nombre, SUM(lineas_pedido.cantidad) AS cantidad
        FROM lineas_pedido
        JOIN productos ON productos.id = lineas_pedido.producto_id
        GROUP BY productos.id
        ORDER BY cantidad DESC
        LIMIT 5
    """).fetchall()

    conexion.close()

    return render_template(
        "informes.html",
        total_ventas=total_ventas,
        total_clientes=total_clientes,
        total_productos=total_productos,
        total_pedidos=total_pedidos,
        productos_vendidos=productos_vendidos
    )


if __name__ == "__main__":
    crear_base_datos()
    insertar_datos_ejemplo()
    app.run(debug=True)
