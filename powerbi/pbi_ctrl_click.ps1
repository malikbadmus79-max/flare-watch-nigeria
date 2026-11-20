# Ctrl+click at screen coordinates (X, Y) in the Power BI Desktop window, then optionally screenshot.
param([Parameter(Mandatory = $true)][int]$X, [Parameter(Mandatory = $true)][int]$Y, [string]$Out, [switch]$NoCtrl)
Add-Type -AssemblyName System.Drawing, System.Windows.Forms
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class In {
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")] public static extern void mouse_event(uint f, uint dx, uint dy, uint d, IntPtr e);
    [DllImport("user32.dll")] public static extern void keybd_event(byte k, byte s, uint f, IntPtr e);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
}
"@
[void][In]::SetProcessDPIAware()
$p = Get-Process PBIDesktop | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
[In]::keybd_event(0x12, 0, 0, [IntPtr]::Zero); [In]::keybd_event(0x12, 0, 2, [IntPtr]::Zero)   # Alt tap
[void][In]::ShowWindow($p.MainWindowHandle, 3)
[void][In]::SetForegroundWindow($p.MainWindowHandle); Start-Sleep -Milliseconds 1200
[void][In]::SetCursorPos($X, $Y); Start-Sleep -Milliseconds 300
[In]::keybd_event(0x1B, 0, 0, [IntPtr]::Zero); [In]::keybd_event(0x1B, 0, 2, [IntPtr]::Zero)  # Esc: leave any edit mode
Start-Sleep -Milliseconds 300
if (-not $NoCtrl) { [In]::keybd_event(0x11, 0, 0, [IntPtr]::Zero) }   # Ctrl down
[In]::mouse_event(0x0002, 0, 0, 0, [IntPtr]::Zero)     # left down
[In]::mouse_event(0x0004, 0, 0, 0, [IntPtr]::Zero)     # left up
if (-not $NoCtrl) { [In]::keybd_event(0x11, 0, 2, [IntPtr]::Zero) }  # Ctrl up
Start-Sleep -Seconds 4
[void][In]::SetCursorPos(1400, 950)                     # move pointer off the canvas
if ($Out) {
    $b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    $bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size)
    $bmp.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose()
    "saved $Out"
}
