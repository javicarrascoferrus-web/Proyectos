const lista = document.getElementById("lista");
const contador = document.getElementById("contador");
const inputArchivo = document.getElementById("inputArchivo");

const btnNuevo = document.getElementById("btnNuevo");
const btnGuardar = document.getElementById("btnGuardar");
const btnAbrir = document.getElementById("btnAbrir");

const STORAGE_KEY = "bulletpad_items";

cargarDatos();

lista.addEventListener("input", guardarDatos);

lista.addEventListener("keydown", function(e) {
    const actual = document.activeElement;

    if (!actual || actual.tagName !== "LI") return;

    if (e.key === "Enter") {
        e.preventDefault();

        const nuevo = crearElemento("");
        actual.insertAdjacentElement("afterend", nuevo);
        nuevo.focus();

        guardarDatos();
    }

    if (e.key === "Backspace") {
        if (actual.textContent.trim() === "") {
            e.preventDefault();

            if (lista.children.length === 1) return;

            const anterior = actual.previousElementSibling;
            const siguiente = actual.nextElementSibling;

            actual.classList.add("removing");

            setTimeout(function() {
                actual.remove();

                if (anterior) {
                    moverCursorFinal(anterior);
                } else if (siguiente) {
                    moverCursorFinal(siguiente);
                }

                guardarDatos();
            }, 200);
        }
    }

    if (e.key === "ArrowUp") {
        e.preventDefault();

        if (actual.previousElementSibling) {
            moverCursorFinal(actual.previousElementSibling);
        }
    }

    if (e.key === "ArrowDown") {
        e.preventDefault();

        if (actual.nextElementSibling) {
            moverCursorFinal(actual.nextElementSibling);
        }
    }
});

btnNuevo.addEventListener("click", function() {
    reiniciarLista();
});

btnGuardar.addEventListener("click", function() {
    descargarTxt();
});

btnAbrir.addEventListener("click", function() {
    inputArchivo.click();
});

inputArchivo.addEventListener("change", function() {
    const archivo = inputArchivo.files[0];

    if (!archivo) return;

    const lector = new FileReader();

    lector.onload = function() {
        cargarDesdeTexto(lector.result);
        guardarDatos();
        inputArchivo.value = "";
    };

    lector.readAsText(archivo);
});

document.addEventListener("keydown", function(e) {
    if (!e.ctrlKey) return;

    const tecla = e.key.toLowerCase();

    if (tecla === "n") {
        e.preventDefault();
        reiniciarLista();
    }

    if (tecla === "s") {
        e.preventDefault();
        descargarTxt();
    }

    if (tecla === "o") {
        e.preventDefault();
        inputArchivo.click();
    }
});

document.addEventListener("dragover", function(e) {
    e.preventDefault();
});

document.addEventListener("drop", function(e) {
    e.preventDefault();

    const archivo = e.dataTransfer.files[0];

    if (!archivo) return;

    if (!archivo.name.toLowerCase().endsWith(".txt")) {
        alert("Solo se permiten archivos .txt");
        return;
    }

    const lector = new FileReader();

    lector.onload = function() {
        cargarDesdeTexto(lector.result);
        guardarDatos();
    };

    lector.readAsText(archivo);
});

function crearElemento(texto) {
    const li = document.createElement("li");

    li.contentEditable = true;
    li.spellcheck = false;
    li.textContent = texto;

    return li;
}

function obtenerLista() {
    return [...lista.querySelectorAll("li")]
        .map(li => li.textContent.trim())
        .filter(texto => texto !== "");
}

function guardarDatos() {
    localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify(obtenerLista())
    );

    actualizarContador();
}

function cargarDatos() {
    const datos = localStorage.getItem(STORAGE_KEY);

    if (!datos) {
        cargarItems(["Presentación"]);
        return;
    }

    try {
        const items = JSON.parse(datos);
        cargarItems(items.length ? items : ["Presentación"]);
    } catch {
        cargarItems(["Presentación"]);
    }
}

function cargarItems(items) {
    lista.innerHTML = "";

    items.forEach(function(texto) {
        lista.appendChild(crearElemento(texto));
    });

    if (lista.children.length === 0) {
        lista.appendChild(crearElemento("Presentación"));
    }

    actualizarContador();
}

function cargarDesdeTexto(texto) {
    const items = texto
        .split(/\r?\n/)
        .map(linea => linea.trim())
        .filter(linea => linea !== "");

    cargarItems(items.length ? items : ["Presentación"]);
}

function reiniciarLista() {
    localStorage.removeItem(STORAGE_KEY);
    cargarItems(["Presentación"]);
    lista.children[0].focus();
    guardarDatos();
}

function descargarTxt() {
    const contenido = obtenerLista().join("\n");

    const blob = new Blob([contenido], {
        type: "text/plain;charset=utf-8"
    });

    const url = URL.createObjectURL(blob);

    const enlace = document.createElement("a");
    enlace.href = url;
    enlace.download = "bulletpad.txt";
    enlace.click();

    URL.revokeObjectURL(url);
}

function actualizarContador() {
    contador.textContent = lista.children.length;
}

function moverCursorFinal(elemento) {
    elemento.focus();

    const rango = document.createRange();
    rango.selectNodeContents(elemento);
    rango.collapse(false);

    const seleccion = window.getSelection();
    seleccion.removeAllRanges();
    seleccion.addRange(rango);
}
