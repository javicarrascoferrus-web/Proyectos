<!doctype html>
<html lang="es" class="wpc-100 hpc-100 p-0 m-0">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Iniciar sesión</title>

  
    <link rel="stylesheet" href="JVestilo/JVestilo.php" />
  </head>

  <body class="b-lightgray wpc-100 hpc-100 p-0 m-0">
    <main class="wpc-100 hpc-100 flex fa-center fj-center p-20">
      <form
        class="b-white p-20 bradius-10 flex fd-column g-12"
        style="width: min(360px, 100%);"
        method="post"
        action="login.php"
        autocomplete="on"
      >
        <h1 class="m-0 fs-20 ta-center">Acceso</h1>

        <label class="fs-14" for="usuario">Usuario</label>
        <input
          id="usuario"
          name="usuario"
          type="text"
          placeholder="usuario"
          class="p-10 br-1-solid-lightgray bradius-5"
          autocomplete="username"
          required
        />

        <label class="fs-14" for="password">Contraseña</label>
        <input
          id="password"
          name="password"
          type="password"
          placeholder="contraseña"
          class="p-10 br-1-solid-lightgray bradius-5"
          autocomplete="current-password"
          required
        />

        <button type="submit" class="p-10 bradius-5 b-lightgray br-1-solid-lightgray">
          Entrar
        </button>
      </form>
    </main>
  </body>
</html>
