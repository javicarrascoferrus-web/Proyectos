<?php
declare(strict_types=1);



header('Content-Type: text/css; charset=UTF-8');

require __DIR__ . '/colores.php';            
require __DIR__ . '/familiasfuentes.php';   




$MAX_PX = 300;      
$MAX_GRID = 12;       
$MAX_BORDER = 10;   
$STEP = 1;          
$emitPct = true;      

$alineaciones = ['left','right','center','justify'];

$borderStyles = [
  "none","hidden","solid","dashed","dotted","double","groove","ridge","inset","outset"
];




function out(string $css): void {
  echo $css, "\n";
}

function lc(string $s): string {
  return strtolower(trim($s));
}


function classToken(string $s): string {
  $s = lc($s);
  $s = preg_replace('/\s+/', '-', $s);
  return preg_replace('/[^a-z0-9\-]/', '', $s) ?: 'color';
}

function rule(string $selector, string $body): void {
  out($selector . '{' . $body . '}');
}



rule('.flex', 'display:flex;');
rule('.grid', 'display:grid;');
rule('.fd-row', 'flex-direction:row;');
rule('.fd-column', 'flex-direction:column;');
rule('.fj-center', 'justify-content:center;');
rule('.fa-center', 'align-items:center;');
rule('.td-none', 'text-decoration:none;');




if (isset($colores) && is_array($colores)) {
  foreach ($colores as $color) {
    $name = classToken((string)$color);
    $value = lc((string)$color);
    rule(".b-$name", "background:$value;");
    rule(".c-$name", "color:$value;");
  }
}



if (isset($familias) && is_array($familias)) {
  foreach ($familias as $familia) {
    $name = classToken((string)$familia);
  
    $value = trim((string)$familia);
    $valueCss = (strpos($value, ' ') !== false) ? "\"$value\"" : $value;
    rule(".ff-$name", "font-family:$valueCss;");
  }
}



for ($i = 0; $i <= $MAX_PX; $i += $STEP) {
  rule(".p-$i", "padding:{$i}px;");
  rule(".m-$i", "margin:{$i}px;");
  rule(".w-$i", "width:{$i}px;");
  rule(".h-$i", "height:{$i}px;");
  rule(".fs-$i", "font-size:{$i}px;");
  rule(".g-$i", "gap:{$i}px;");
  rule(".bradius-$i", "border-radius:{$i}px;");
  rule(".f-$i", "flex:$i;");

  if ($emitPct && $i <= 100) {
    // clases claras para porcentaje
    rule(".wpc-$i", "width:{$i}%;");
    rule(".hpc-$i", "height:{$i}%;");
  }
}


for ($i = 1; $i <= $MAX_GRID; $i++) {
  rule(".gc-$i", "grid-template-columns:repeat($i,1fr);");
}


foreach ($alineaciones as $a) {
  $a = lc($a);
  rule(".ta-$a", "text-align:$a;");
}


if (isset($colores) && is_array($colores)) {
  for ($i = 0; $i <= $MAX_BORDER; $i++) {
    foreach ($borderStyles as $style) {
      foreach ($colores as $color) {
        $cName = classToken((string)$color);
        $cVal = lc((string)$color);
        // Ej: .br-2-solid-red { border:2px solid red; }
        rule(".br-$i-$style-$cName", "border:{$i}px $style $cVal;");
      }
    }
  }
}
