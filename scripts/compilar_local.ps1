# Compila Venim en local Y COMPRUEBA QUE ARRANCA EL BINARIO NUEVO.
#
#   powershell -ExecutionPolicy Bypass -File scripts\compilar_local.ps1
#
# DOS FALLOS QUE ESTE SCRIPT EXISTE PARA NO REPETIR
# =================================================
# 1. PyInstaller puede terminar sin un solo error y producir un .exe que muere
#    al arrancar. Pasó: dos instancias abiertas impedian sobrescribir
#    dist\Venim.exe y lo que se probaba era un binario viejo a medio escribir.
#    Por eso este script cierra lo que bloquee el binario y ARRANCA el .exe.
#
# 2. Y el fallo del propio verificador, que es peor. La version anterior daba
#    la compilacion por buena cuando "algo responde en el puerto 1420".
#    Respondia MAGI-IDE-v5.exe, que estaba corriendo en esta maquina y tenia
#    ese puerto. El script confirmaba que Venim arrancaba usando como prueba
#    la respuesta del programa que le impedia arrancar.
#
#    Ahora se pregunta /venim.json: no vale "hay algo escuchando", tiene que
#    contestar que es Venim. El instrumento de medida es el mejor escondite.
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

Write-Host "=== 3/4 LO QUE TIENE QUE VIAJAR DENTRO (Y LO QUE NO) ==="
$toc = Join-Path $raiz "build\Venim\Analysis-00.toc"
if (-not (Select-String -Path $toc -Pattern "python-embed" -Quiet)) {
  Write-Host "FALLO: el Python embebido no entro; el .exe no podria ejecutar nada"
  exit 1
}
Write-Host "  python embebido: dentro"
if (Select-String -Path $toc -Pattern "modelo-interfaz|magi-interfaz|magi_sound" -Quiet) {
  Write-Host "FALLO: restos de MAGI dentro del binario de Venim"; exit 1
}
Write-Host "  sin restos de MAGI"

Write-Host "=== 4/4 ¿ARRANCA, Y ES EL NUESTRO? ==="
$err = Join-Path $raiz "build\arranque.err"
Remove-Item $err -ErrorAction SilentlyContinue
$p = Start-Process $exe -PassThru -RedirectStandardError $err
$nuestro = $false
$puerto = 0
for ($i = 0; $i -lt 40; $i++) {
  Start-Sleep -Seconds 3
  # Se barre el mismo rango que busca el servidor, y se pregunta QUIEN ES.
  foreach ($pt in 1420..1431) {
    try {
      $r = Invoke-WebRequest "http://127.0.0.1:$pt/venim.json" -UseBasicParsing -TimeoutSec 2
      if (($r.Content | ConvertFrom-Json).programa -eq "Venim") {
        $nuestro = $true; $puerto = $pt; break
      }
    } catch { }
  }
  if ($nuestro -or $p.HasExited) { break }
}
if (-not $nuestro) {
  Write-Host "FALLO: en 120 s no contesto NINGUN servidor que se identifique"
  Write-Host "       como Venim. Si hay algo escuchando en 1420, es de otro."
  if ((Test-Path $err) -and (Get-Item $err).Length -gt 0) {
    Write-Host "--- lo que dijo antes de morir ---"; Get-Content $err -Tail 20
  }
  Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
  exit 1
}
Write-Host "ARRANCA: el servidor de VENIM responde en el puerto $puerto"
Write-Host "--- COMPILACION VERIFICADA ---"
