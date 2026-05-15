const listaProyectos = document.getElementById("listaProyectos");

function obtenerProyectos() {
    return JSON.parse(localStorage.getItem("proyectosPortfolio")) || [];
}

function guardarProyectos(proyectos) {
    localStorage.setItem("proyectosPortfolio", JSON.stringify(proyectos));
}

function mostrarProyectos() {
    if (!listaProyectos) return;

    const proyectos = obtenerProyectos();

    if (proyectos.length === 0) {
        listaProyectos.innerHTML = `
            <div class="vacio">
                Todavía no hay proyectos guardados.
            </div>
        `;
        return;
    }

    listaProyectos.innerHTML = "";

    proyectos.forEach((proyecto, index) => {
        const tarjeta = document.createElement("article");
        tarjeta.className = "proyecto";

        tarjeta.innerHTML = `
            <h3>${proyecto.titulo}</h3>
            <p>${proyecto.descripcion}</p>
            <a class="boton" href="editor.html?id=${index}">Editar</a>
        `;

        listaProyectos.appendChild(tarjeta);
    });
}

mostrarProyectos();
