const visor = document.getElementById("visor");
const navegacion = document.getElementById("navegacion");
const zonaDrop = document.getElementById("zonaDrop");

let diapositivas = [];
let puntos = [];
let actual = 0;

const presentacionInicial = `
portada
    MiniSlides
    Crea presentaciones interactivas usando HTML, CSS y JavaScript.

lista
    Funciones principales
    Navegación horizontal
    Control con teclado
    Carga desde archivo TXT
    Plantillas visuales reutilizables

texto
    Proyecto web
    MiniSlides permite convertir texto estructurado en diapositivas visuales.

frase
    Una buena presentación guía la atención.
    MiniSlides

media
    Recursos visuales
    Puedes combinar texto con imágenes o bloques gráficos.

cierre
    Gracias
    Fin de la presentación
`;

function parsearTexto(texto) {
    const lineas = texto.replace(/\r/g, "").split("\n");
    const slides = [];
    let slideActual = null;

    lineas.forEach(linea => {
        if (linea.trim() === "") return;

        if (!linea.startsWith("    ") && !linea.startsWith("\t")) {
            slideActual = {
                tipo: linea.trim(),
                contenido: []
            };
            slides.push(slideActual);
        } else if (slideActual) {
            slideActual.contenido.push(linea.trim());
        }
    });

    return slides;
}

function escaparHTML(texto) {
    return String(texto)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function crearDiapositiva(slide) {
    const article = document.createElement("article");
    article.className = "diapositiva " + slide.tipo;

    const contenido = slide.contenido.map(escaparHTML);
    const titulo = contenido[0] || "";
    const resto = contenido.slice(1);

    if (slide.tipo === "portada") {
        article.innerHTML = `
            <div class="etiqueta">Presentación</div>
            <h2>${titulo}</h2>
            <p>${resto.join("<br>")}</p>
        `;
    } else if (slide.tipo === "lista") {
        article.innerHTML = `
            <div class="etiqueta">Puntos clave</div>
            <h2>${titulo}</h2>
            <ul>
                ${resto.map(item => `<li>${item}</li>`).join("")}
            </ul>
        `;
    } else if (slide.tipo === "texto") {
        article.innerHTML = `
            <div class="caja">
                <div class="etiqueta">Contenido</div>
                <h2>${titulo}</h2>
                ${resto.map(parrafo => `<p>${parrafo}</p>`).join("")}
            </div>
        `;
    } else if (slide.tipo === "frase") {
        article.innerHTML = `
            <blockquote>“${titulo}”</blockquote>
            <cite>${resto[0] || ""}</cite>
        `;
    } else if (slide.tipo === "media") {
        const texto = resto[0] || "";
        const imagen = resto[1] || "";

        article.innerHTML = `
            <div>
                <div class="etiqueta">Media</div>
                <h2>${titulo}</h2>
                <p>${texto}</p>
            </div>
            ${
                imagen
                ? `<img src="${imagen}" alt="">`
                : `<div class="imagen-falsa"></div>`
            }
        `;
    } else if (slide.tipo === "cierre") {
        article.innerHTML = `
            <h2>${titulo}</h2>
            <p>${resto.join("<br>")}</p>
        `;
    } else {
        article.className = "diapositiva texto";
        article.innerHTML = `
            <div class="caja">
                <h2>${titulo}</h2>
                ${resto.map(parrafo => `<p>${parrafo}</p>`).join("")}
            </div>
        `;
    }

    return article;
}

function renderizar(slides) {
    visor.innerHTML = "";
    navegacion.innerHTML = "";
    actual = 0;

    slides.forEach((slide, indice) => {
        const article = crearDiapositiva(slide);
        visor.appendChild(article);

        const punto = document.createElement("button");
        punto.className = "punto";
        punto.addEventListener("click", () => irA(indice));

        navegacion.appendChild(punto);
    });

    diapositivas = document.querySelectorAll(".diapositiva");
    puntos = document.querySelectorAll(".punto");

    irA(0);
}

function irA(indice) {
    indice = Math.max(0, Math.min(indice, diapositivas.length - 1));
    actual = indice;

    visor.scrollTo({
        left: actual * window.innerWidth,
        behavior: "smooth"
    });

    actualizarPuntos();
}

function actualizarPuntos() {
    puntos.forEach((punto, indice) => {
        punto.classList.toggle("activo", indice === actual);
    });
}

document.addEventListener("keydown", event => {
    if (event.key === "ArrowRight") {
        irA(actual + 1);
    }

    if (event.key === "ArrowLeft") {
        irA(actual - 1);
    }
});

visor.addEventListener("scroll", () => {
    actual = Math.round(visor.scrollLeft / window.innerWidth);
    actualizarPuntos();
});

window.addEventListener("resize", () => {
    irA(actual);
});

document.addEventListener("dragover", event => {
    event.preventDefault();
    zonaDrop.classList.add("visible");
});

document.addEventListener("dragleave", event => {
    if (event.clientX === 0 || event.clientY === 0) {
        zonaDrop.classList.remove("visible");
    }
});

document.addEventListener("drop", event => {
    event.preventDefault();
    zonaDrop.classList.remove("visible");

    const archivo = event.dataTransfer.files[0];

    if (!archivo) return;

    if (!archivo.name.toLowerCase().endsWith(".txt")) {
        alert("Debes soltar un archivo .txt");
        return;
    }

    const lector = new FileReader();

    lector.onload = () => {
        const texto = lector.result;
        renderizar(parsearTexto(texto));
    };

    lector.readAsText(archivo);
});

fetch("presentacion.txt")
    .then(respuesta => {
        if (!respuesta.ok) {
            throw new Error("No existe presentacion.txt");
        }

        return respuesta.text();
    })
    .then(texto => {
        renderizar(parsearTexto(texto));
    })
    .catch(() => {
        renderizar(parsearTexto(presentacionInicial));
    });
