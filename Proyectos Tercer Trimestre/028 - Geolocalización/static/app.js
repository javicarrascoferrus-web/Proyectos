let mapa;
let marcadores = {};

const inputNombre = document.getElementById("nombreUsuario");
const botonUbicacion = document.getElementById("btnUbicacion");
const botonBorrarNombre = document.getElementById("btnBorrarNombre");

const mensaje = document.getElementById("mensaje");
const listaUsuarios = document.getElementById("listaUsuarios");
const totalUsuarios = document.getElementById("totalUsuarios");

const nombreGuardado = localStorage.getItem("nombre_localizador");

if (nombreGuardado) {
    inputNombre.value = nombreGuardado;
}

function iniciarMapa() {

    mapa = L.map("mapa").setView([39.4699, -0.3763], 6);

    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            attribution: "&copy; OpenStreetMap contributors"
        }
    ).addTo(mapa);
}

function mostrarMensaje(texto) {
    mensaje.textContent = texto;
}

function obtenerUbicacion() {

    const nombre = inputNombre.value.trim();

    if (nombre === "") {
        mostrarMensaje("Debes escribir un nombre.");
        return;
    }

    localStorage.setItem("nombre_localizador", nombre);

    if (!navigator.geolocation) {
        mostrarMensaje("Tu navegador no soporta geolocalización.");
        return;
    }

    mostrarMensaje("Obteniendo ubicación actual...");

    navigator.geolocation.getCurrentPosition(

        function(posicion) {

            const latitud = posicion.coords.latitude;
            const longitud = posicion.coords.longitude;

            guardarUbicacion(nombre, latitud, longitud);
        },

        function(error) {

            mostrarMensaje(
                "Error al obtener ubicación: " + error.message
            );
        },

        {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 0
        }
    );
}

async function guardarUbicacion(nombre, latitud, longitud) {

    try {

        const respuesta = await fetch("/guardar", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                nombre: nombre,
                latitud: latitud,
                longitud: longitud
            })
        });

        const datos = await respuesta.json();

        if (datos.ok) {

            mostrarMensaje("Ubicación guardada correctamente.");

            mapa.setView([latitud, longitud], 14);

            cargarUsuarios();

        } else {

            mostrarMensaje("Error: " + datos.error);
        }

    } catch (error) {

        console.error(error);

        mostrarMensaje(
            "No se pudo conectar con el servidor."
        );
    }
}

async function cargarUsuarios() {

    try {

        const respuesta = await fetch("/usuarios");

        const datos = await respuesta.json();

        if (!datos.ok) {

            mostrarMensaje("No se pudieron cargar usuarios.");

            return;
        }

        totalUsuarios.textContent = datos.usuarios.length;

        listaUsuarios.innerHTML = "";

        datos.usuarios.forEach(function(usuario) {

            const latitud = parseFloat(usuario.latitud);
            const longitud = parseFloat(usuario.longitud);

            const popup = `
                <strong>${limpiarHTML(usuario.nombre)}</strong><br>
                Latitud: ${latitud}<br>
                Longitud: ${longitud}<br>
                Actualizado: ${limpiarHTML(usuario.actualizado)}
            `;

            if (marcadores[usuario.nombre]) {

                marcadores[usuario.nombre]
                    .setLatLng([latitud, longitud]);

                marcadores[usuario.nombre]
                    .setPopupContent(popup);

            } else {

                marcadores[usuario.nombre] = L.marker(
                    [latitud, longitud]
                )
                .addTo(mapa)
                .bindPopup(popup);
            }

            const item = document.createElement("li");

            item.innerHTML = `
                <strong>${limpiarHTML(usuario.nombre)}</strong><br>
                ${limpiarHTML(usuario.actualizado)}
            `;

            item.addEventListener("click", function() {

                mapa.setView([latitud, longitud], 15);

                marcadores[usuario.nombre].openPopup();
            });

            listaUsuarios.appendChild(item);
        });

    } catch (error) {

        console.error(error);

        mostrarMensaje("Error cargando usuarios.");
    }
}

function limpiarHTML(texto) {

    return String(texto)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

botonUbicacion.addEventListener(
    "click",
    obtenerUbicacion
);

botonBorrarNombre.addEventListener(
    "click",
    function() {

        localStorage.removeItem("nombre_localizador");

        inputNombre.value = "";

        mostrarMensaje(
            "Nombre guardado eliminado."
        );
    }
);

iniciarMapa();

cargarUsuarios();

setInterval(cargarUsuarios, 10000);
