# Coloca la ventana de Venim en el TERCIO DERECHO, este donde este.
#
# Se separa de `abrir_en_un_tercio.ps1` porque son dos cosas distintas: aquella
# arranca el .exe y espera; esta solo recoloca lo que ya hay. Mezcladas, para
# mover una ventana habia que reiniciar el programa.
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class W {
  [DllImport("user32.dll")] public static extern bool MoveWindow(IntPtr h,int x,int y,int w,int t,bool r);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h,int c);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out R r);
  public struct R { public int L, T, Rr, B; }
}
"@
$p = Get-Process Venim -ErrorAction SilentlyContinue |
     Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
if (-not $p) { Write-Host "no hay ventana de Venim"; exit 1 }
$h = $p.MainWindowHandle
$r = New-Object W+R
[void][W]::GetWindowRect($h, [ref]$r)
Write-Host "estaba en $($r.L),$($r.T) - $($r.Rr),$($r.B)"
[void][W]::ShowWindow($h, 9)          # SW_RESTORE
Start-Sleep -Milliseconds 500
[void][W]::MoveWindow($h, 1707, 0, 853, 1400, $true)
[void][W]::SetForegroundWindow($h)
Start-Sleep -Milliseconds 400
[void][W]::GetWindowRect($h, [ref]$r)
Write-Host "ahora en $($r.L),$($r.T) - $($r.Rr),$($r.B)"
