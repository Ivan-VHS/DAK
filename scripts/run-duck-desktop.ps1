param(
    [switch]$Fullscreen
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$App = Join-Path $Root "release\bin\duckos-desktop.exe"

if (-not (Test-Path -LiteralPath $App -PathType Leaf)) {
    throw "Native DuckOS desktop is not built. Install the Windows native desktop bundle first."
}

$Arguments = @("--root", $Root)
if ($Fullscreen) { $Arguments += "--fullscreen" }
Start-Process -FilePath $App -ArgumentList $Arguments -WorkingDirectory $Root
