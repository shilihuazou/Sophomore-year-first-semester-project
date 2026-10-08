$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $projectRoot 'app\backend'
$frontend = Join-Path $projectRoot 'app\frontend'
$teamFrontend = Join-Path $projectRoot 'app\team-frontend'

$pythonExecutable = (& py -c 'import sys; print(sys.executable)').Trim()
if ($LASTEXITCODE -ne 0) {
    throw 'Python is unavailable.'
}

Write-Host 'Running Django tests...'
Push-Location $backend
try {
    & $pythonExecutable manage.py test
    if ($LASTEXITCODE -ne 0) { throw 'Django tests failed.' }
} finally {
    Pop-Location
}

Write-Host 'Checking frontend formatting...'
Push-Location $frontend
try {
    & npm.cmd run format:check
    if ($LASTEXITCODE -ne 0) { throw 'Frontend formatting check failed.' }

    Write-Host 'Building frontend...'
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
} finally {
    Pop-Location
}

Write-Host 'Checking team portal formatting...'
Push-Location $teamFrontend
try {
    & npm.cmd run format:check
    if ($LASTEXITCODE -ne 0) { throw 'Team portal formatting check failed.' }

    Write-Host 'Building team portal...'
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'Team portal build failed.' }
} finally {
    Pop-Location
}

Write-Host 'Project verification passed.'
