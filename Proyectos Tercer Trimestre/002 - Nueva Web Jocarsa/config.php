<?php
declare(strict_types=1);

function obtenerVariable(string $nombre, string $valorPorDefecto = ''): string
{
    $valor = getenv($nombre);

    if ($valor === false || $valor === '') {
        return $valorPorDefecto;
    }

    return $valor;
}

return [
    'smtp_host' => obtenerVariable('SMTP_HOST', 'smtp.ionos.es'),
    'smtp_port' => (int) obtenerVariable('SMTP_PORT', '587'),
    'smtp_user' => obtenerVariable('SMTP_USER', 'info@jocarsa.com'),
    'smtp_pass' => obtenerVariable('SMTP_PASS', ''),
    'correo_destino' => obtenerVariable('MAIL_TO', 'info@jocarsa.com'),
    'correo_origen' => obtenerVariable('MAIL_FROM', 'info@jocarsa.com'),
];
