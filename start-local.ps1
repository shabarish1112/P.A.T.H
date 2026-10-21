$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$runtimeDir = Join-Path $PSScriptRoot '.local'
$python = Join-Path $PSScriptRoot 'backend\.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $python) -or !(Test-Path -LiteralPath 'backend\.env')) {
    throw 'Backend environment is missing. Follow the setup steps in README.md.'
}
New-Item -ItemType Directory -Force -Path "$runtimeDir\mongo" | Out-Null

function Test-LocalPort([int]$Port) {
    $client = New-Object System.Net.Sockets.TcpClient
    try { $client.Connect('127.0.0.1', $Port); return $true }
    catch { return $false }
    finally { $client.Dispose() }
}

if (!(Test-LocalPort 27017)) {
    $mongod = (Get-Command mongod.exe -ErrorAction Stop).Source
    Start-Process -FilePath $mongod -ArgumentList @('--dbpath', "`"$runtimeDir\mongo`"", '--bind_ip', '127.0.0.1', '--port', '27017', '--auth', '--logpath', "`"$runtimeDir\mongo.log`"", '--logappend') -WindowStyle Hidden
    $deadline = (Get-Date).AddSeconds(30)
    while (!(Test-LocalPort 27017)) {
        if ((Get-Date) -gt $deadline) { throw "MongoDB did not start. Check $runtimeDir\mongo.log" }
        Start-Sleep -Milliseconds 500
    }
    & $python backend/scripts/bootstrap_local_mongo.py
    if ($LASTEXITCODE -ne 0) { throw 'MongoDB initialization failed.' }
}

if (!(Test-LocalPort 8000)) {
    Start-Process -FilePath $python -ArgumentList @('-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000') -WorkingDirectory "$PSScriptRoot\backend" -WindowStyle Hidden -RedirectStandardOutput "$runtimeDir\backend.log" -RedirectStandardError "$runtimeDir\backend-error.log"
}
if (!(Test-LocalPort 5173)) {
    $node = (Get-Command node.exe -ErrorAction Stop).Source
    Start-Process -FilePath $node -ArgumentList @('node_modules/vite/bin/vite.js', '--host', '127.0.0.1') -WorkingDirectory "$PSScriptRoot\frontend" -WindowStyle Hidden -RedirectStandardOutput "$runtimeDir\frontend.log" -RedirectStandardError "$runtimeDir\frontend-error.log"
}
$deadline = (Get-Date).AddSeconds(60)
do {
    try {
        $null = Invoke-WebRequest 'http://127.0.0.1:8000/health/ready' -UseBasicParsing -TimeoutSec 3
        Write-Host 'P.A.T.H. is ready: http://localhost:5173'
        Write-Host "Logs: $runtimeDir"
        exit 0
    } catch {
        Start-Sleep -Seconds 1
    }
} while ((Get-Date) -lt $deadline)
throw "Backend did not become ready. Check $runtimeDir\backend-error.log"
