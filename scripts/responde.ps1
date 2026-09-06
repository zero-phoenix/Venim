$raiz = "C:\Users\D\magi-port\VeniceMAGI"
$log = Join-Path $raiz "build\compilacion.log"
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
Remove-Item $log -ErrorAction SilentlyContinue
Start-Process powershell.exe -WindowStyle Hidden -RedirectStandardOutput $log `
  -RedirectStandardError (Join-Path $raiz "build\compilacion.err") `
  -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                  (Join-Path $raiz "scripts\compilar_local.ps1"))
Write-Host "compilacion de Venim lanzada; registro en build\compilacion.log"
