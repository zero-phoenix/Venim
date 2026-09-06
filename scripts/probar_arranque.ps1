# ¿Arranca el .exe que hay en dist/ y sirve la interfaz?
#
# Se separa de la compilacion porque son dos preguntas distintas: "compila" y
# "funciona". Confundirlas fue lo que dejo publicar un binario que moria en el
# arranque sin que PyInstaller diera un solo error.
$raiz = "C:\Users\D\magi-port\Venim"
Get-Process Venim -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3
$err = Join-Path $raiz "build\arranque.err"
Remove-Item $err -ErrorAction SilentlyContinue
$exe = Join-Path $raiz "dist\Venim.exe"
Write-Host ("exe: {0} MB, del {1}" -f `
  [math]::Round((Get-Item $exe).Length / 1MB, 1), (Get-Item $exe).LastWriteTime)
$p = Start-Process $exe -PassThru -RedirectStandardError $err
$vivo = $false
for ($i = 0; $i -lt 30; $i++) {
  Start-Sleep -Seconds 3
  try {
    $r = Invoke-WebRequest "http://127.0.0.1:1420" -UseBasicParsing -TimeoutSec 3
    if ($r.StatusCode -eq 200) { $vivo = $true; break }
  } catch { }
  if ($p.HasExited) { Write-Host "el proceso murio a los $($i * 3)s"; break }
}
if ($vivo) {
  Write-Host "ARRANCA: la interfaz responde en http://127.0.0.1:1420"
} else {
  Write-Host "NO ARRANCA."
  if ((Test-Path $err) -and (Get-Item $err).Length -gt 0) {
    Write-Host "--- lo que dijo ---"; Get-Content $err -Tail 20
  } else { Write-Host "(no dijo nada)" }
}
