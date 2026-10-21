$ErrorActionPreference = 'Stop'

function New-LocalSecret {
    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    return ([BitConverter]::ToString($bytes)).Replace('-', '').ToLowerInvariant()
}

$rootEnv = Join-Path $PSScriptRoot '.env'
$backendEnv = Join-Path $PSScriptRoot 'backend\.env'
if ((Test-Path -LiteralPath $rootEnv) -or (Test-Path -LiteralPath $backendEnv)) {
    throw 'An .env file already exists. Setup stopped to preserve existing credentials. Follow README.md to configure it manually.'
}

$rootPassword = New-LocalSecret
$appPassword = New-LocalSecret
$jwtSecret = New-LocalSecret
$template = Get-Content -LiteralPath (Join-Path $PSScriptRoot '.env.example') -Raw
$template = $template.Replace('MONGO_ROOT_PASSWORD=replace-with-strong-random-value', "MONGO_ROOT_PASSWORD=$rootPassword")
$template = $template.Replace('PATH_APP_PASSWORD=replace-with-strong-random-value', "PATH_APP_PASSWORD=$appPassword")
$template = $template.Replace('path_app:replace-with-strong-random-value@mongo', "path_app:${appPassword}@mongo")
$template = $template.Replace('change-me-generate-with-openssl-rand-hex-32', $jwtSecret)
Set-Content -LiteralPath $rootEnv -Value $template -Encoding ascii

$backendTemplate = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'backend\.env.example') -Raw
$backendTemplate = $backendTemplate.Replace('path_app:CHANGE_ME@localhost', "path_app:${appPassword}@localhost")
$backendTemplate = $backendTemplate.Replace('change-me-generate-with-openssl-rand-hex-32', $jwtSecret)
Set-Content -LiteralPath $backendEnv -Value $backendTemplate -Encoding ascii

Write-Host 'Created local environment files with unique credentials. Keep these files private.'
Write-Host 'Start Docker Desktop and wait until its engine is running, then run:'
Write-Host '  docker compose up --build -d'
Write-Host '  docker compose exec backend python scripts/create_user.py --email you@example.com --role admin'
Write-Host 'Open http://localhost:5173 and log in using the account you created.'
