param(
    [int]$Port = 8765
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Url = "http://127.0.0.1:$Port/mora/"

$Python = Get-Command py -ErrorAction SilentlyContinue
if ($Python) {
    $FilePath = $Python.Source
    $Arguments = @("-3", "-m", "http.server", "$Port", "--bind", "127.0.0.1", "--directory", $Root)
} else {
    $Python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $Python) { throw "Python 3 is required only as a local static-file server." }
    $FilePath = $Python.Source
    $Arguments = @("-m", "http.server", "$Port", "--bind", "127.0.0.1", "--directory", $Root)
}

$Server = Start-Process -FilePath $FilePath -ArgumentList $Arguments -PassThru -WindowStyle Hidden
try {
    $Ready = $false
    for ($Attempt = 0; $Attempt -lt 40; $Attempt++) {
        try {
            Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 1 | Out-Null
            $Ready = $true
            break
        } catch {
            Start-Sleep -Milliseconds 250
        }
    }
    if (-not $Ready) { throw "Mora did not become available at $Url" }
    Start-Process $Url
    Write-Host "Mora is ready at $Url. Keep this PowerShell window open; press Ctrl+C to stop the server."
    Wait-Process -Id $Server.Id
} finally {
    if (-not $Server.HasExited) { Stop-Process -Id $Server.Id -Force }
}
