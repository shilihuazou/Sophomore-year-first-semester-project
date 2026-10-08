$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$launcher = Join-Path $projectRoot 'app\start-services.ps1'

if (-not (Test-Path -LiteralPath $launcher -PathType Leaf)) {
    throw "Application launcher not found: $launcher"
}

& $launcher
