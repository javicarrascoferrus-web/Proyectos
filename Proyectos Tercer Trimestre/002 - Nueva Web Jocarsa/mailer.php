<?php
declare(strict_types=1);

function limpiarTexto(string $texto): string
{
    return htmlspecialchars($texto, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function leerRespuestaServidor($conexion): string
{
    $respuesta = '';

    while (!feof($conexion)) {
        $linea = fgets($conexion, 515);

        if ($linea === false) {
            break;
        }

        $respuesta .= $linea;

        if (isset($linea[3]) && $linea[3] === ' ') {
            break;
        }
    }

    return $respuesta;
}

function enviarComando($conexion, string $comando, array $codigosValidos): string
{
    fwrite($conexion, $comando . "\r\n");

    $respuesta = leerRespuestaServidor($conexion);
    $codigo = (int) substr($respuesta, 0, 3);

    if (!in_array($codigo, $codigosValidos, true)) {
        throw new RuntimeException("Error SMTP: {$respuesta}");
    }

    return $respuesta;
}

function crearMensajeCorreo(
    string $origen,
    string $destino,
    string $asunto,
    string $contenido
): string {
    $asuntoCodificado = '=?UTF-8?B?' . base64_encode($asunto) . '?=';

    $cabeceras = [
        'Date: ' . date('r'),
        'From: <' . $origen . '>',
        'To: <' . $destino . '>',
        'Subject: ' . $asuntoCodificado,
        'MIME-Version: 1.0',
        'Content-Type: text/plain; charset=UTF-8',
        'Content-Transfer-Encoding: 8bit',
    ];

    $contenido = preg_replace("/\r\n|\r|\n/", "\r\n", $contenido);

    return implode("\r\n", $cabeceras) . "\r\n\r\n" . $contenido . "\r\n";
}

function enviarCorreoSMTP(array $config, string $asunto, string $contenido): void
{
    if ($config['smtp_pass'] === '') {
        throw new RuntimeException('No se ha configurado la contraseña SMTP.');
    }

    $conexion = fsockopen(
        $config['smtp_host'],
        $config['smtp_port'],
        $numeroError,
        $textoError,
        20
    );

    if (!$conexion) {
        throw new RuntimeException("No se pudo conectar al servidor SMTP: {$textoError}");
    }

    stream_set_timeout($conexion, 20);

    $banner = leerRespuestaServidor($conexion);

    if ((int) substr($banner, 0, 3) !== 220) {
        fclose($conexion);
        throw new RuntimeException('Respuesta inicial SMTP no válida.');
    }

    enviarComando($conexion, 'EHLO nueva-web-jocarsa', [250]);
    enviarComando($conexion, 'STARTTLS', [220]);

    $tls = stream_socket_enable_crypto(
        $conexion,
        true,
        STREAM_CRYPTO_METHOD_TLS_CLIENT
    );

    if ($tls !== true) {
        fclose($conexion);
        throw new RuntimeException('No se pudo activar STARTTLS.');
    }

    enviarComando($conexion, 'EHLO nueva-web-jocarsa', [250]);
    enviarComando($conexion, 'AUTH LOGIN', [334]);
    enviarComando($conexion, base64_encode($config['smtp_user']), [334]);
    enviarComando($conexion, base64_encode($config['smtp_pass']), [235]);

    enviarComando($conexion, 'MAIL FROM:<' . $config['correo_origen'] . '>', [250]);
    enviarComando($conexion, 'RCPT TO:<' . $config['correo_destino'] . '>', [250, 251]);
    enviarComando($conexion, 'DATA', [354]);

    $mensaje = crearMensajeCorreo(
        $config['correo_origen'],
        $config['correo_destino'],
        $asunto,
        $contenido
    );

    fwrite($conexion, $mensaje . "\r\n.\r\n");

    $respuesta = leerRespuestaServidor($conexion);

    if ((int) substr($respuesta, 0, 3) !== 250) {
        fclose($conexion);
        throw new RuntimeException('El servidor no aceptó el mensaje.');
    }

    enviarComando($conexion, 'QUIT', [221, 250]);

    fclose($conexion);
}
