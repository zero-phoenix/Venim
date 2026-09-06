Write-Host "=== QUIEN ESCUCHA QUE ==="
foreach ($pt in 1420..1425) {
  $c = Get-NetTCPConnection -State Listen -LocalPort $pt -ErrorAction SilentlyContinue
  if (-not $c) { continue }
  $proc = (Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue).ProcessName
  $quien = "(no se identifica)"
  try {
    $r = Invoke-WebRequest "http://127.0.0.1:$pt/venim.json" -UseBasicParsing -TimeoutSec 2
    $quien = "se identifica como " + ($r.Content | ConvertFrom-Json).programa
  } catch { }
  Write-Host ("  puerto {0}  proceso {1,-14} {2}" -f $pt, $proc, $quien)
}
Write-Host "=== LO QUE SIRVE VENIM ==="
try {
  $r = Invoke-WebRequest "http://127.0.0.1:1421" -UseBasicParsing -TimeoutSec 6
  if ($r.Content -match "<title>(.*?)</title>") { Write-Host "  titulo: $($Matches[1])" }
  $js = [regex]::Match($r.Content, 'src="(/assets/[^"]+\.js)"').Groups[1].Value
  $a = Invoke-WebRequest ("http://127.0.0.1:1421" + $js) -UseBasicParsing -TimeoutSec 10
  foreach ($m in @("MAGI SYSTEM IDE", "EVANGELION", "Supercomputadora")) {
    if ($a.Content.Contains($m)) { Write-Host "  $m : PRESENTE <-- MAL" }
    else { Write-Host "  $m : no aparece" }
  }
  if ($a.Content.Contains("imagen, v")) { Write-Host "  el lema de Venim: presente" }
} catch { Write-Host "  no responde: $($_.Exception.Message)" }
