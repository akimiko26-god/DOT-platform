# dot local dev (no Docker) - LAN access on port 5173

$root = $PSScriptRoot

function Get-LanIp {
    $ip = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object {
            $_.IPAddress -notlike '127.*' -and
            $_.PrefixOrigin -ne 'WellKnown' -and
            $_.InterfaceAlias -notmatch 'vEthernet|WSL|Virtual|Loopback'
        } |
        Select-Object -First 1 -ExpandProperty IPAddress)
    if (-not $ip) { $ip = '127.0.0.1' }
    return $ip
}

function Stop-PortListeners {
    param([int[]]$Ports)
    foreach ($port in $Ports) {
        Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
            ForEach-Object {
                Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
            }
    }
}

Write-Host 'Stopping old listeners on 8000 and 5173...'
Stop-PortListeners -Ports @(8000, 5173)
Start-Sleep -Seconds 1

$lanIp = Get-LanIp

Start-Process powershell -ArgumentList @(
    '-NoExit', '-Command',
    "Set-Location '$root\backend'; if (-not (Test-Path .venv)) { python -m venv .venv }; .\.venv\Scripts\pip install -q -r requirements.txt; .\.venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000"
)

Start-Sleep -Seconds 2

Start-Process powershell -ArgumentList @(
    '-NoExit', '-Command',
    "Set-Location '$root\frontend'; if (-not (Test-Path node_modules)) { npm install }; npm run dev"
)

Start-Sleep -Seconds 3

Write-Host ''
Write-Host 'Started.' -ForegroundColor Green
Write-Host "  This PC:  http://localhost:5173"
Write-Host "  LAN:      http://${lanIp}:5173"
Write-Host ''
Write-Host 'Open LAN URL on phone/tablet in same Wi-Fi (free, no tunnel).'
Write-Host 'If blocked: allow Node.js and Python in Windows Firewall (Private network).'
