# De Venim a Venim: el renombrado completo, con git para no perder historia.
#
# Se hace con `git mv` y no copiando: asi el historial de cada fichero sigue
# siendo el suyo y `git log --follow` funciona. Copiar y borrar habria dejado
# 251 ficheros "nuevos" sin pasado, y este proyecto usa su historia como
# documentacion.
$ErrorActionPreference = "Stop"
Set-Location "C:\Users\D\magi-port\Venim"

Write-Host "=== 1/2 carpetas ==="
if (Test-Path "venim") { git mv venim venim; Write-Host "  venim -> venim" }
if (Test-Path "venim-gui") { git mv venim-gui venim-gui; Write-Host "  venim-gui -> venim-gui" }
if (Test-Path "Venim.spec") { git mv Venim.spec Venim.spec; Write-Host "  Venim.spec -> Venim.spec" }

Write-Host "=== 2/2 comprobacion ==="
foreach ($d in @("venim", "venim-gui", "Venim.spec")) {
  if (Test-Path $d) { Write-Host "  OK  $d" } else { Write-Host "  FALTA $d" }
}
git status --porcelain | Select-Object -First 3
