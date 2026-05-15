<!doctype html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Portfolio Javier Carrasco</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="style.css">
</head>
<body>

<header class="cabecera">
    <div>
        <h1>Portfolio Javier Carrasco </h1>
        <p>Crea y guarda ideas de páginas web desde tu navegador.</p>
    </div>

    <a class="boton" href="editor.html">Crear proyecto</a>
</header>

<main class="contenedor">
    <section class="hero">
        <div>
            <h2>Tu generador de portfolios web</h2>
            <p>
                Escribe una idea, crea una vista previa y guarda tus proyectos
                usando HTML, CSS y JavaScript.
            </p>
            <a class="boton grande" href="editor.html">Empezar ahora</a>
        </div>

        <div class="tarjeta-demo">
            <span>Prompt ejemplo</span>
            <p>Crear una web personal para un diseñador gráfico.</p>
        </div>
    </section>

    <section>
        <h2>Proyectos guardados</h2>
        <div id="listaProyectos" class="grid"></div>
    </section>
</main>

<script src="app.js"></script>
</body>
</html>
