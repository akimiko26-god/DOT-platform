# Public internet URL (free) via Cloudflare Quick Tunnel
# Requires: Node.js, Python, internet. PC must stay on while tunnel runs.

$root = $PSScriptRoot
$cf = Join-Path $root '.tools\cloudflared.exe'
$cfUrl = 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe'

function Stop-PortListeners {
    param([int[]]$Ports)
    foreach ($port in $Ports) {
        Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
            ForEach-Object {
                Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
            }
    }
}

Write-Host 'Building frontend...'
Push-Location (Join-Path $root 'frontend')
if (-not (Test-Path node_modules)) { npm install }
npm run build
if ($LASTEXITCODE -ne 0) { Pop-Location; exit 1 }
Pop-Location

if (-not (Test-Path $cf)) {
    Write-Host 'Downloading cloudflared...'
    New-Item -ItemType Directory -Force -Path (Split-Path $cf) | Out-Null
    Invoke-WebRequest -Uri $cfUrl -OutFile $cf -UseBasicParsing
}

Write-Host 'Stopping old listeners on 8000 and 5173...'
Stop-PortListeners -Ports @(8000, 5173)
Start-Sleep -Seconds 1

$backendCmd = @"
Set-Location '$root\backend'
if (-not (Test-Path .venv)) { python -m venv .venv }
.\.venv\Scripts\pip install -q -r requirements.txt
.\.venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000
"@

Start-Process powershell -ArgumentList @('-NoExit', '-Command', $backendCmd)
Start-Sleep -Seconds 4

$health = $null
try {
    $health = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/api/health' -UseBasicParsing -TimeoutSec 10
} catch {}

if (-not $health -or $health.StatusCode -ne 200) {
    Write-Host 'Backend did not start. Check the backend window.' -ForegroundColor Red
    exit 1
}

Write-Host ''
Write-Host 'Starting public tunnel (Cloudflare, free)...' -ForegroundColor Cyan
Write-Host 'Copy the https://....trycloudflare.com URL from the output below.'
Write-Host 'Share that link anywhere on the internet. Keep this window open.'
Write-Host ''

& $cf tunnel --url http://127.0.0.1:8000
