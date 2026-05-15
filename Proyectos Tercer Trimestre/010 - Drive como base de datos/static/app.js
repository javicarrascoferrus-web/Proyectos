let carrito = [];

const botonesAnadir = document.querySelectorAll(".anadir");
const carritoPanel = document.getElementById("carrito");
const overlay = document.getElementById("overlay");
const abrirCarrito = document.getElementById("abrirCarrito");
const cerrarCarrito = document.getElementById("cerrarCarrito");
const listaCarrito = document.getElementById("listaCarrito");
const contador = document.getElementById("contador");
const total = document.getElementById("total");

const vaciar = document.getElementById("vaciar");
const comprar = document.getElementById("comprar");

const modal = document.getElementById("modal");
const cerrarModal = document.getElementById("cerrarModal");
const formularioCompra = document.getElementById("formularioCompra");
const mensaje = document.getElementById("mensaje");

function abrirPanel() {
    carritoPanel.classList.add("abierto");
    overlay.classList.add("visible");
}

function cerrarPanel() {
    carritoPanel.classList.remove("abierto");
    overlay.classList.remove("visible");
}

function calcularTotal() {
    return carrito.reduce((suma, producto) => {
        return suma + producto.precio * producto.cantidad;
    }, 0);
}

function calcularCantidad() {
    return carrito.reduce((suma, producto) => {
        return suma + producto.cantidad;
    }, 0);
}

function formatoPrecio(numero) {
    return numero.toFixed(2).replace(".", ",") + " €";
}

function pintarCarrito() {
    contador.textContent = calcularCantidad();
    total.textContent = formatoPrecio(calcularTotal());

    if (carrito.length === 0) {
        listaCarrito.innerHTML = `
            <p style="color:#64748b;text-align:center;margin-top:30px;">
                El carrito está vacío.
            </p>
        `;
        return;
    }

    listaCarrito.innerHTML = "";

    carrito.forEach((producto, index) => {
        const item = document.createElement("div");
        item.className = "item-carrito";

        item.innerHTML = `
            <h4>${producto.nombre}</h4>
            <p>${formatoPrecio(producto.precio)} x ${producto.cantidad}</p>

            <div class="item-controles">
                <div>
                    <button data-accion="restar" data-index="${index}">-</button>
                    <button data-accion="sumar" data-index="${index}">+</button>
                </div>

                <button class="eliminar" data-accion="eliminar" data-index="${index}">
                    Eliminar
                </button>
            </div>
        `;

        listaCarrito.appendChild(item);
    });
}

function anadirProducto(id, nombre, precio) {
    const encontrado = carrito.find(producto => producto.id === id);

    if (encontrado) {
        encontrado.cantidad++;
    } else {
        carrito.push({
            id: id,
            nombre: nombre,
            precio: precio,
            cantidad: 1
        });
    }

    pintarCarrito();
    abrirPanel();
}

botonesAnadir.forEach(boton => {
    boton.addEventListener("click", () => {
        const id = Number(boton.dataset.id);
        const nombre = boton.dataset.nombre;
        const precio = Number(boton.dataset.precio);

        anadirProducto(id, nombre, precio);
    });
});

listaCarrito.addEventListener("click", e => {
    const accion = e.target.dataset.accion;
    const index = Number(e.target.dataset.index);

    if (!accion || isNaN(index)) return;

    if (accion === "sumar") {
        carrito[index].cantidad++;
    }

    if (accion === "restar") {
        carrito[index].cantidad--;

        if (carrito[index].cantidad <= 0) {
            carrito.splice(index, 1);
        }
    }

    if (accion === "eliminar") {
        carrito.splice(index, 1);
    }

    pintarCarrito();
});

abrirCarrito.addEventListener("click", abrirPanel);
cerrarCarrito.addEventListener("click", cerrarPanel);
overlay.addEventListener("click", cerrarPanel);

vaciar.addEventListener("click", () => {
    carrito = [];
    pintarCarrito();
});

comprar.addEventListener("click", () => {
    if (carrito.length === 0) {
        alert("Primero añade algún producto.");
        return;
    }

    modal.classList.add("visible");
});

cerrarModal.addEventListener("click", () => {
    modal.classList.remove("visible");
});

formularioCompra.addEventListener("submit", async e => {
    e.preventDefault();

    const pedido = {
        cliente: {
            nombre: document.getElementById("nombre").value,
            email: document.getElementById("email").value,
            direccion: document.getElementById("direccion").value
        },
        productos: carrito,
        total: calcularTotal()
    };

    const respuesta = await fetch("/comprar", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(pedido)
    });

    const resultado = await respuesta.json();

    mensaje.textContent = resultado.mensaje;

    carrito = [];
    pintarCarrito();
    formularioCompra.reset();

    setTimeout(() => {
        modal.classList.remove("visible");
        cerrarPanel();
        mensaje.textContent = "";
    }, 1600);
});

pintarCarrito();
