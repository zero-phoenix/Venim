# Compila Venim en local Y COMPRUEBA QUE EL BINARIO ARRANCA.
#
#   powershell -ExecutionPolicy Bypass -File scripts\compilar_local.ps1
#
# POR QUE NO BASTA CON QUE PYINSTALLER TERMINE
# ============================================
# El 2026-09-06 PyInstaller termino sin un solo error y produjo un .exe que
# moria en el arranque, antes de ejecutar una linea del proyecto:
#
#     File "pyimod01_archive.py", line 134, in extract
#     zlib.error: Error -3 while decompressing data: incorrect header check
#
# La causa: dos instancias del programa abiertas impedian sobrescribir
# dist\Venim.exe, y lo que se probaba era un binario viejo a medio escribir.
# La ventana abria en negro porque su servidor no llegaba a levantarse, y eso
# se parece muchisimo a "la interfaz no compila".
#
# Por eso este script no termina cuando termina PyInstaller: cierra lo que
# bloquee el binario, ARRANCA el .exe, espera a que su servidor conteste, y
# solo entonces dice que salio bien. Es la cuarta regla del proyecto
# —arrancar encuentra fallos que leer no encuentra— aplicada a la compilacion.
#
# Nada de $ErrorActionPreference = "Stop": Vite y PyInstaller escriben avisos
# normales en stderr y con "Stop" PowerShell aborta una compilacion que va
# bien. El exito se comprueba por el ARTEFACTO, que es la evidencia.
$raiz = "C:\Users\D\magi-port\VeniceMAGI"
Set-Location $raiz
$py = Join-Path $raiz ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

Write-Host "=== 0/4 nadie bloqueando el binario ==="
Get-Process Venim, VeniceMAGI -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
Remove-Item (Join-Path $raiz "dist\Venim.exe") -Force -ErrorAction SilentlyContinue

Write-Host "=== 1/4 FRONTEND ==="
Set-Location (Join-Path $raiz "venim-gui")
cmd /c "npm run build 2>&1" | Select-Object -Last 4
Set-Location $raiz
if (-not (Test-Path (Join-Path $raiz "venim-gui\dist\index.html"))) {
  Write-Host "FALLO: no hay venim-gui/dist/index.html"; exit 1
}
$kb = (Get-ChildItem (Join-Path $raiz "venim-gui\dist\assets") -Filter *.js |
       Measure-Object Length -Sum).Sum / 1KB
Write-Host ("frontend OK - {0:N0} KB de JS" -f $kb)

Write-Host "=== 2/4 PYINSTALLER ==="
& $py -m PyInstaller --clean --noconfirm Venim.spec 2>&1 | Select-Object -Last 6
$exe = Join-Path $raiz "dist\Venim.exe"
if (-not (Test-Path $exe)) { Write-Host "FALLO: no se produjo el .exe"; exit 1 }
Write-Host ("exe: {0} MB" -f [math]::Round((Get-Item $exe).Length / 1MB, 1))

Write-Host "=== 3/4 LO QUE TIENE QUE VIAJAR DENTRO ==="
$toc = Join-Path $raiz "build\Venim\Analysis-00.toc"
if (-not (Select-String -Path $toc -Pattern "python-embed" -Quiet)) {
  Write-Host "FALLO: el Python embebido no entro; el .exe no podria ejecutar nada"
  exit 1
}
Write-Host "python embebido: dentro (verificado en el inventario)"

Write-Host "=== 4/4 ¿ARRANCA? ==="
$err = Join-Path $raiz "build\arranque.err"
Remove-Item $err -ErrorAction SilentlyContinue
$p = Start-Process $exe -PassThru -RedirectStandardError $err
$vivo = $false
for ($i = 0; $i -lt 40; $i++) {
  Start-Sleep -Seconds 3
  try {
    $r = Invoke-WebRequest "http://127.0.0.1:1420" -UseBasicParsing -TimeoutSec 3
    if ($r.StatusCode -eq 200) { $vivo = $true; break }
  } catch { }
  if ($p.HasExited) { break }
}
if (-not $vivo) {
  Write-Host "FALLO: el .exe no sirvio la interfaz en 120 s."
  if ((Test-Path $err) -and (Get-Item $err).Length -gt 0) {
    Write-Host "--- lo que dijo antes de morir ---"; Get-Content $err -Tail 20
  }
  Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
  exit 1
}
Write-Host "ARRANCA: la interfaz responde en http://127.0.0.1:1420"
Write-Host "--- COMPILACION VERIFICADA ---"
