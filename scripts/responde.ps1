$lock = "C:\Users\D\magi-port\VeniceMAGI\.git\index.lock"
if (Test-Path $lock) {
  Remove-Item $lock -Force
  Write-Host "index.lock eliminado"
} else { Write-Host "no habia index.lock" }
Set-Location "C:\Users\D\magi-port\VeniceMAGI"
git status --porcelain | Measure-Object | ForEach-Object { Write-Host "$($_.Count) ficheros con cambios" }
