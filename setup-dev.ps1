param([switch]$Docker)
$ErrorActionPreference = 'Stop'
function New-LocalSecret {
    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    return ([BitConverter]::ToString($bytes)).Replace('-', '').ToLowerInvariant()
}
$mongoEnv = Join-Path $PSScriptRoot 'infra\mongo.env'
$backendEnv = Join-Path $PSScriptRoot 'backend\.env'
if ((Test-Path -LiteralPath $mongoEnv) -or (Test-Path -LiteralPath $backendEnv)) {
    throw 'Environment files already exist. Refusing to overwrite credentials.'
}
$appPassword = New-LocalSecret
$mongo = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'infra\mongo.env.example') -Raw
$mongo = $mongo.Replace('replace-with-a-unique-random-password', (New-LocalSecret))
$mongo = $mongo.Replace('replace-with-a-different-random-password', $appPassword)
Set-Content -LiteralPath $mongoEnv -Value $mongo -Encoding ascii
$backend = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'backend\.env.example') -Raw
$backend = $backend.Replace('CHANGE_ME', $appPassword)
$backend = $backend.Replace('change-me-generate-with-openssl-rand-hex-32', (New-LocalSecret))
if ($Docker) {
    $backend = $backend.Replace('@localhost:', '@mongo:').Replace('HOST=127.0.0.1', 'HOST=0.0.0.0')
}
Set-Content -LiteralPath $backendEnv -Value $backend -Encoding ascii
Write-Host 'Private environment files created. No secret values are displayed.'
Write-Host 'For Docker: docker compose up --build -d'
Write-Host 'For local startup: install dependencies, then run start_path.bat'
