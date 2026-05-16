const STORAGE_KEY = "esquemadraw_svg";

const svg = document.getElementById("lienzo");
const escenario = document.getElementById("escenario");
const fileInput = document.getElementById("fileInput");

const herramientas = document.querySelectorAll(".tool");
const colorInput = document.getElementById("colorInput");
const widthInput = document.getElementById("widthInput");

const btnNuevo = document.getElementById("btnNuevo");
const btnGuardar = document.getElementById("btnGuardar");
const btnAbrir = document.getElementById("btnAbrir");

let herramienta = "select";
let colorActual = "#1f2937";
let grosorActual = 2;

let dibujando = false;
let moviendo = false;
let desplazando = false;

let elementoActual = null;
let elementoSeleccionado = null;

let puntos = [];
let puntoInicio = null;

let escala = 1;
let desplazamientoX = 0;
let desplazamientoY = 0;

let inicioPanX = 0;
let inicioPanY = 0;
let panOffsetX = 0;
let panOffsetY = 0;

let puntoMovimiento = null;
let atributosOriginales = null;

const DISTANCIA_MINIMA = 6;

function actualizarTransformacion() {
    escenario.setAttribute(
        "transform",
        `translate(${desplazamientoX}, ${desplazamientoY}) scale(${escala})`
    );
}

function pantallaAMundo(x, y) {
    return {
        x: (x - desplazamientoX) / escala,
        y: (y - desplazamientoY) / escala
    };
}

function obtenerPunto(evento) {
    const rect = svg.getBoundingClientRect();

    return pantallaAMundo(
        evento.clientX - rect.left,
        evento.clientY - rect.top
    );
}

function distancia(a, b) {
    return Math.hypot(a.x - b.x, a.y - b.y);
}

function puntosAPath(listaPuntos) {
    if (listaPuntos.length < 2) return "";

    let d = `M ${listaPuntos[0].x} ${listaPuntos[0].y}`;

    for (let i = 1; i < listaPuntos.length - 1; i++) {
        const actual = listaPuntos[i];
        const siguiente = listaPuntos[i + 1];

        const medioX = (actual.x + siguiente.x) / 2;
        const medioY = (actual.y + siguiente.y) / 2;

        d += ` Q ${actual.x} ${actual.y} ${medioX} ${medioY}`;
    }

    const ultimo = listaPuntos[listaPuntos.length - 1];
    d += ` L ${ultimo.x} ${ultimo.y}`;

    return d;
}

function estiloComun(elemento) {
    elemento.setAttribute("fill", "none");
    elemento.setAttribute("stroke", colorActual);
    elemento.setAttribute("stroke-width", grosorActual);
    elemento.setAttribute("stroke-linecap", "round");
    elemento.setAttribute("stroke-linejoin", "round");
}

function crearLapiz(punto) {
    puntos = [punto];

    elementoActual = document.createElementNS("http://www.w3.org/2000/svg", "path");
    estiloComun(elementoActual);

    escenario.appendChild(elementoActual);
}

function crearFlecha(punto) {
    elementoActual = document.createElementNS("http://www.w3.org/2000/svg", "line");

    elementoActual.setAttribute("x1", punto.x);
    elementoActual.setAttribute("y1", punto.y);
    elementoActual.setAttribute("x2", punto.x);
    elementoActual.setAttribute("y2", punto.y);
    elementoActual.setAttribute("stroke", colorActual);
    elementoActual.setAttribute("stroke-width", grosorActual);
    elementoActual.setAttribute("stroke-linecap", "round");
    elementoActual.setAttribute("marker-end", "url(#puntaFlecha)");

    escenario.appendChild(elementoActual);
}

function crearRectangulo(punto) {
    elementoActual = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    estiloComun(elementoActual);

    elementoActual.setAttribute("x", punto.x);
    elementoActual.setAttribute("y", punto.y);
    elementoActual.setAttribute("width", 0);
    elementoActual.setAttribute("height", 0);

    escenario.appendChild(elementoActual);
}

function actualizarRectangulo(punto) {
    const x = Math.min(puntoInicio.x, punto.x);
    const y = Math.min(puntoInicio.y, punto.y);
    const ancho = Math.abs(punto.x - puntoInicio.x);
    const alto = Math.abs(punto.y - puntoInicio.y);

    elementoActual.setAttribute("x", x);
    elementoActual.setAttribute("y", y);
    elementoActual.setAttribute("width", ancho);
    elementoActual.setAttribute("height", alto);
}

function crearCirculo(punto) {
    elementoActual = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    estiloComun(elementoActual);

    elementoActual.setAttribute("cx", punto.x);
    elementoActual.setAttribute("cy", punto.y);
    elementoActual.setAttribute("r", 0);

    escenario.appendChild(elementoActual);
}

function actualizarCirculo(punto) {
    const radio = distancia(puntoInicio, punto);

    elementoActual.setAttribute("cx", puntoInicio.x);
    elementoActual.setAttribute("cy", puntoInicio.y);
    elementoActual.setAttribute("r", radio);
}

function crearElipse(punto) {
    elementoActual = document.createElementNS("http://www.w3.org/2000/svg", "ellipse");
    estiloComun(elementoActual);

    elementoActual.setAttribute("cx", punto.x);
    elementoActual.setAttribute("cy", punto.y);
    elementoActual.setAttribute("rx", 0);
    elementoActual.setAttribute("ry", 0);

    escenario.appendChild(elementoActual);
}

function actualizarElipse(punto) {
    const cx = (puntoInicio.x + punto.x) / 2;
    const cy = (puntoInicio.y + punto.y) / 2;
    const rx = Math.abs(punto.x - puntoInicio.x) / 2;
    const ry = Math.abs(punto.y - puntoInicio.y) / 2;

    elementoActual.setAttribute("cx", cx);
    elementoActual.setAttribute("cy", cy);
    elementoActual.setAttribute("rx", rx);
    elementoActual.setAttribute("ry", ry);
}

function crearTexto(punto) {
    const contenido = prompt("Introduce el texto:");

    if (!contenido) return;

    const texto = document.createElementNS("http://www.w3.org/2000/svg", "text");

    texto.setAttribute("x", punto.x);
    texto.setAttribute("y", punto.y);
    texto.setAttribute("fill", colorActual);
    texto.setAttribute("font-size", grosorActual * 8 + 12);
    texto.setAttribute("font-family", "Arial, sans-serif");
    texto.setAttribute("data-editable", "true");
    texto.textContent = contenido;

    escenario.appendChild(texto);
    guardarAutomatico();
}

function editarTexto(elemento) {
    const nuevoTexto = prompt("Editar texto:", elemento.textContent);

    if (nuevoTexto === null) return;

    if (nuevoTexto.trim() === "") {
        elemento.remove();
        limpiarSeleccion();
    } else {
        elemento.textContent = nuevoTexto;
    }

    guardarAutomatico();
}

function limpiarSeleccion() {
    if (elementoSeleccionado) {
        elementoSeleccionado.classList.remove("elemento-seleccionado");
    }

    elementoSeleccionado = null;
}

function seleccionarElemento(elemento) {
    limpiarSeleccion();

    elementoSeleccionado = elemento;
    elementoSeleccionado.classList.add("elemento-seleccionado");
}

function esElementoDibujado(elemento) {
    return elemento && elemento.parentNode === escenario;
}

function obtenerAtributos(elemento) {
    const datos = {};

    Array.from(elemento.attributes).forEach(attr => {
        datos[attr.name] = attr.value;
    });

    return datos;
}

function moverElemento(elemento, dx, dy) {
    if (elemento.tagName === "line") {
        elemento.setAttribute("x1", parseFloat(atributosOriginales.x1) + dx);
        elemento.setAttribute("y1", parseFloat(atributosOriginales.y1) + dy);
        elemento.setAttribute("x2", parseFloat(atributosOriginales.x2) + dx);
        elemento.setAttribute("y2", parseFloat(atributosOriginales.y2) + dy);
        return;
    }

    if (elemento.tagName === "text") {
        elemento.setAttribute("x", parseFloat(atributosOriginales.x) + dx);
        elemento.setAttribute("y", parseFloat(atributosOriginales.y) + dy);
        return;
    }

    if (elemento.tagName === "rect") {
        elemento.setAttribute("x", parseFloat(atributosOriginales.x) + dx);
        elemento.setAttribute("y", parseFloat(atributosOriginales.y) + dy);
        return;
    }

    if (elemento.tagName === "circle") {
        elemento.setAttribute("cx", parseFloat(atributosOriginales.cx) + dx);
        elemento.setAttribute("cy", parseFloat(atributosOriginales.cy) + dy);
        return;
    }

    if (elemento.tagName === "ellipse") {
        elemento.setAttribute("cx", parseFloat(atributosOriginales.cx) + dx);
        elemento.setAttribute("cy", parseFloat(atributosOriginales.cy) + dy);
        return;
    }

    elemento.setAttribute(
        "transform",
        `${atributosOriginales.transform || ""} translate(${dx}, ${dy})`
    );
}

function iniciarPan(evento) {
    desplazando = true;

    inicioPanX = evento.clientX;
    inicioPanY = evento.clientY;

    panOffsetX = desplazamientoX;
    panOffsetY = desplazamientoY;

    svg.style.cursor = "grabbing";
}

function iniciarMovimiento(evento, elemento) {
    moviendo = true;

    puntoMovimiento = obtenerPunto(evento);
    atributosOriginales = obtenerAtributos(elemento);

    seleccionarElemento(elemento);
    svg.style.cursor = "move";
}

function iniciarDibujo(evento) {
    if (evento.target.closest("#barraHerramientas")) return;

    if (evento.button === 1) {
        evento.preventDefault();
        iniciarPan(evento);
        return;
    }

    if (evento.button !== 0) return;

    const punto = obtenerPunto(evento);
    puntoInicio = punto;

    if (herramienta === "select") {
        if (esElementoDibujado(evento.target)) {
            iniciarMovimiento(evento, evento.target);
        } else {
            limpiarSeleccion();
        }

        return;
    }

    if (herramienta === "text") {
        crearTexto(punto);
        return;
    }

    dibujando = true;

    if (herramienta === "pen") crearLapiz(punto);
    if (herramienta === "arrow") crearFlecha(punto);
    if (herramienta === "rect") crearRectangulo(punto);
    if (herramienta === "circle") crearCirculo(punto);
    if (herramienta === "ellipse") crearElipse(punto);
}

function dibujar(evento) {
    if (desplazando) {
        desplazamientoX = panOffsetX + (evento.clientX - inicioPanX);
        desplazamientoY = panOffsetY + (evento.clientY - inicioPanY);
        actualizarTransformacion();
        return;
    }

    if (moviendo && elementoSeleccionado) {
        const punto = obtenerPunto(evento);
        const dx = punto.x - puntoMovimiento.x;
        const dy = punto.y - puntoMovimiento.y;

        moverElemento(elementoSeleccionado, dx, dy);
        return;
    }

    if (!dibujando || !elementoActual) return;

    const punto = obtenerPunto(evento);

    if (herramienta === "pen") {
        const ultimo = puntos[puntos.length - 1];

        if (distancia(punto, ultimo) < DISTANCIA_MINIMA) return;

        puntos.push(punto);
        elementoActual.setAttribute("d", puntosAPath(puntos));
    }

    if (herramienta === "arrow") {
        elementoActual.setAttribute("x2", punto.x);
        elementoActual.setAttribute("y2", punto.y);
    }

    if (herramienta === "rect") actualizarRectangulo(punto);
    if (herramienta === "circle") actualizarCirculo(punto);
    if (herramienta === "ellipse") actualizarElipse(punto);
}

function finalizarDibujo() {
    if (dibujando || moviendo) {
        guardarAutomatico();
    }

    dibujando = false;
    moviendo = false;
    desplazando = false;

    elementoActual = null;
    puntos = [];
    puntoInicio = null;
    puntoMovimiento = null;
    atributosOriginales = null;

    svg.style.cursor = herramienta === "select" ? "default" : "crosshair";
}

function cambiarHerramienta(nuevaHerramienta) {
    herramienta = nuevaHerramienta;

    herramientas.forEach(btn => {
        btn.classList.toggle("active", btn.dataset.tool === herramienta);
    });

    svg.style.cursor = herramienta === "select" ? "default" : "crosshair";
}

function guardarAutomatico() {
    localStorage.setItem(STORAGE_KEY, escenario.innerHTML);
}

function cargarAutomatico() {
    const guardado = localStorage.getItem(STORAGE_KEY);

    if (guardado) {
        escenario.innerHTML = guardado;
    }
}

function nuevoDocumento() {
    if (!confirm("¿Crear un esquema nuevo? Se borrará el actual.")) return;

    escenario.innerHTML = "";
    localStorage.removeItem(STORAGE_KEY);

    escala = 1;
    desplazamientoX = 0;
    desplazamientoY = 0;

    limpiarSeleccion();
    actualizarTransformacion();
}

function obtenerSVGCompleto() {
    const copia = svg.cloneNode(true);

    copia.setAttribute("xmlns", "http://www.w3.org/2000/svg");
    copia.setAttribute("width", window.innerWidth);
    copia.setAttribute("height", window.innerHeight);
    copia.setAttribute("viewBox", `0 0 ${window.innerWidth} ${window.innerHeight}`);

    copia.querySelectorAll(".elemento-seleccionado").forEach(elemento => {
        elemento.classList.remove("elemento-seleccionado");
    });

    return `<?xml version="1.0" encoding="UTF-8"?>\n` + copia.outerHTML;
}

function guardarSVG() {
    const blob = new Blob([obtenerSVGCompleto()], {
        type: "image/svg+xml"
    });

    const url = URL.createObjectURL(blob);

    const enlace = document.createElement("a");
    enlace.href = url;
    enlace.download = "esquema-draw.svg";
    enlace.click();

    URL.revokeObjectURL(url);
}

function abrirSVG(archivo) {
    const lector = new FileReader();

    lector.onload = function() {
        const parser = new DOMParser();
        const doc = parser.parseFromString(lector.result, "image/svg+xml");

        const escenarioCargado = doc.querySelector("#escenario");

        if (escenarioCargado) {
            escenario.innerHTML = escenarioCargado.innerHTML;
        } else {
            const svgCargado = doc.querySelector("svg");
            escenario.innerHTML = svgCargado ? svgCargado.innerHTML : "";
        }

        limpiarSeleccion();
        guardarAutomatico();
    };

    lector.readAsText(archivo);
}

herramientas.forEach(btn => {
    btn.addEventListener("click", function() {
        cambiarHerramienta(btn.dataset.tool);
    });
});

colorInput.addEventListener("input", function() {
    colorActual = colorInput.value;
});

widthInput.addEventListener("change", function() {
    grosorActual = Number(widthInput.value);
});

btnNuevo.addEventListener("click", nuevoDocumento);
btnGuardar.addEventListener("click", guardarSVG);
btnAbrir.addEventListener("click", function() {
    fileInput.click();
});

fileInput.addEventListener("change", function() {
    if (fileInput.files[0]) {
        abrirSVG(fileInput.files[0]);
    }

    fileInput.value = "";
});

svg.addEventListener("contextmenu", evento => evento.preventDefault());
svg.addEventListener("pointerdown", iniciarDibujo);
svg.addEventListener("pointermove", dibujar);
window.addEventListener("pointerup", finalizarDibujo);

svg.addEventListener("dblclick", function(evento) {
    if (evento.target.tagName === "text" && evento.target.dataset.editable === "true") {
        editarTexto(evento.target);
    }
});

svg.addEventListener("wheel", function(evento) {
    evento.preventDefault();

    const rect = svg.getBoundingClientRect();

    const mouseX = evento.clientX - rect.left;
    const mouseY = evento.clientY - rect.top;

    const mundoX = (mouseX - desplazamientoX) / escala;
    const mundoY = (mouseY - desplazamientoY) / escala;

    const zoom = evento.deltaY < 0 ? 1.1 : 0.9;

    escala *= zoom;
    escala = Math.max(0.1, Math.min(escala, 20));

    desplazamientoX = mouseX - mundoX * escala;
    desplazamientoY = mouseY - mundoY * escala;

    actualizarTransformacion();
}, { passive: false });

window.addEventListener("keydown", function(evento) {
    if (evento.ctrlKey && evento.key.toLowerCase() === "s") {
        evento.preventDefault();
        guardarSVG();
    }

    if (evento.ctrlKey && evento.key.toLowerCase() === "o") {
        evento.preventDefault();
        fileInput.click();
    }

    if ((evento.key === "Delete" || evento.key === "Backspace") && elementoSeleccionado) {
        elementoSeleccionado.remove();
        limpiarSeleccion();
        guardarAutomatico();
    }
});

window.addEventListener("beforeunload", guardarAutomatico);

cargarAutomatico();
actualizarTransformacion();
cambiarHerramienta("select");
