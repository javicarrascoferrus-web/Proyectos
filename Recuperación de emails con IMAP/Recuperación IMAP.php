<?php

$hostname = '{imap.ionos.es:993/imap/ssl}INBOX';
$username = 'python@jocarsa.com';
$password = 'CAMBIA_ESTA_CLAVE';

define('MAX_POSTS', 15);
define('EXCERPT_LENGTH', 400);


function decodePart($content, $encoding) {
  return match($encoding) {
    3 => base64_decode($content),            
    4 => quoted_printable_decode($content),  
    default => $content
  };
}

function excerpt($html, $len = EXCERPT_LENGTH) {
  $txt = trim(preg_replace('/\s+/', ' ', strip_tags($html)));
  if (function_exists('mb_strlen')) {
    return (mb_strlen($txt,'UTF-8') <= $len) ? $txt : (mb_substr($txt,0,$len,'UTF-8').'…');
  }
  return (strlen($txt) <= $len) ? $txt : (substr($txt,0,$len).'…');
}

function getEmailParts($imap, $msgno) {
  $st = imap_fetchstructure($imap, $msgno);
  $out = ['html'=>null,'text'=>null,'image'=>null];

  
  if (!isset($st->parts)) {
    $body = decodePart(imap_body($imap, $msgno), $st->encoding ?? 0);
    $sub = strtoupper($st->subtype ?? '');
    if (($st->type ?? null) === 0) {
      if ($sub === 'HTML') $out['html'] = $body;
      else $out['text'] = nl2br(htmlspecialchars($body, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8'));
    }
    return $out;
  }

  $stack = [];
  foreach ($st->parts as $i => $p) $stack[] = [$p, (string)($i+1)];

  while ($stack) {
    [$part, $num] = array_shift($stack);


    if (isset($part->parts) && count($part->parts)) {
      foreach ($part->parts as $i => $sp) $stack[] = [$sp, $num.'.'.($i+1)];
      continue;
    }

    $type = $part->type ?? null;
    $sub  = strtoupper($part->subtype ?? '');
    $raw  = imap_fetchbody($imap, $msgno, $num);
    $raw  = decodePart($raw, $part->encoding ?? 0);
    $ctype = ($type === 0) ? 'text/'.$sub : (($type === 5) ? 'image/'.$sub : '');


    if ($type === 0 && $sub === 'HTML' && $out['html'] === null) {
      $out['html'] = $raw;
    }

    if ($type === 0 && $sub === 'PLAIN' && $out['text'] === null) {
      $out['text'] = nl2br(htmlspecialchars($raw, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8'));
    }

    if ($type === 5 && $out['image'] === null) {
      $filename = null;

      foreach (['dparameters','parameters'] as $arrName) {
        if (!empty($part->$arrName)) {
          foreach ($part->$arrName as $param) {
            $attr = strtoupper($param->attribute ?? '');
            if (in_array($attr, ['NAME','FILENAME'], true)) { $filename = $param->value; break 2; }
          }
        }
      }

      $subLow = strtolower($sub ?: 'jpeg');
      $mime   = 'image/'.$subLow;
      $out['image'] = [
        'filename' => $filename ?: ('imagen_'.$num.'.'.$subLow),
        'dataUri'  => 'data:'.$mime.';base64,'.base64_encode($raw),
      ];
    }

   
  
  }

  return $out;
}


$inbox = @imap_open($hostname, $username, $password);
if (!$inbox) die('Error IMAP: '.imap_last_error());


$isDetail = isset($_GET['id']) && (int)$_GET['id'] > 0;
$selected = $isDetail ? (int)$_GET['id'] : null;

$emails = $isDetail ? [$selected] : (imap_search($inbox, 'ALL') ?: []);
if (!$isDetail) { rsort($emails); $emails = array_slice($emails, 0, MAX_POSTS); }

$baseUrl = strtok($_SERVER['REQUEST_URI'], '?');
?>
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title><?= $isDetail ? 'Entrada' : 'Blog de correos' ?></title>
  <style>
    body{margin:0;font-family:system-ui;background:#f4f4f5;color:#111}
    .wrap{max-width:960px;margin:auto;padding:24px}
    .post{background:#fff;border:1px solid #e4e4e7;border-radius:14px;overflow:hidden;margin:16px 0}
    .hero img{width:100%;display:block;max-height:260px;object-fit:cover}
    .content{padding:16px}
    h1{margin:0 0 10px}
    h2{margin:0 0 6px;font-size:18px}
    .meta{color:#71717a;font-size:13px}
    .more a{color:#2563eb;text-decoration:none}
    .more a:hover{text-decoration:underline}
    .back{display:inline-block;margin:10px 0;color:#2563eb;text-decoration:none}
    .back:hover{text-decoration:underline}
  </style>
</head>
<body>
<div class="wrap">
  <h1><?= $isDetail ? 'Entrada del blog' : 'Blog de correos' ?></h1>

  <?php if ($isDetail): ?>
    <a class="back" href="<?= $baseUrl ?>">← Volver</a>
  <?php endif; ?>

  <?php if (!$emails): ?>
    <p style="color:#71717a">No se han encontrado correos para mostrar.</p>
  <?php else: ?>

    <?php foreach ($emails as $num):
      $ov = imap_fetch_overview($inbox, $num, 0)[0] ?? null;
      if (!$ov) continue;

      $subject = htmlspecialchars(imap_utf8($ov->subject ?? '(Sin asunto)'), ENT_QUOTES,'UTF-8');
      $from    = htmlspecialchars(imap_utf8($ov->from ?? '(Desconocido)'), ENT_QUOTES,'UTF-8');
      $date    = htmlspecialchars($ov->date ?? '', ENT_QUOTES,'UTF-8');

      $parts = getEmailParts($inbox, $num);
      $bodyFull = $parts['html'] ?? $parts['text'] ?? '<em>Sin contenido legible.</em>';

      $bodyToShow = $isDetail
        ? $bodyFull
        : '<p>'.htmlspecialchars(excerpt($bodyFull), ENT_QUOTES,'UTF-8').'</p>';

      $detailUrl = $baseUrl.'?id='.(int)$num;
    ?>
      <article class="post">
        <?php if (!empty($parts['image'])): ?>
          <div class="hero">
            <img src="<?= $parts['image']['dataUri'] ?>"
                 alt="<?= htmlspecialchars($parts['image']['filename'], ENT_QUOTES,'UTF-8') ?>">
          </div>
        <?php endif; ?>

        <div class="content">
          <h2><a href="<?= $detailUrl ?>" style="color:inherit;text-decoration:none"><?= $subject ?></a></h2>
          <div class="meta">De: <?= $from ?> <?= $date ? "• $date" : "" ?></div>
          <div style="margin-top:10px;line-height:1.6"><?= $bodyToShow ?></div>

          <?php if (!$isDetail): ?>
            <div class="more" style="margin-top:10px"><a href="<?= $detailUrl ?>">Leer más →</a></div>
          <?php endif; ?>
        </div>
      </article>

      <?php if ($isDetail) break; ?>
    <?php endforeach; ?>

  <?php endif; ?>

</div>
</body>
</html>
<?php imap_close($inbox); ?>
