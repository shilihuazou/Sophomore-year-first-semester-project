$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$runtimeDirectory = Join-Path $PSScriptRoot '.runtime'
$runStamp = Get-Date -Format 'yyyyMMdd-HHmmss'
New-Item -ItemType Directory -Path $runtimeDirectory -Force | Out-Null

function ConvertTo-StringList {
    param([object]$Value)
    if ($null -eq $Value) { return @() }
    $items = if ($Value -is [string]) { $Value -split '[,;]' } else { @($Value) }
    return @($items | ForEach-Object { ([string]$_).Trim() } | Where-Object { $_ })
}

function Get-UniqueStrings {
    param([object[]]$Values)
    return @($Values | Where-Object { $_ } | ForEach-Object { ([string]$_).Trim() } |
        Where-Object { $_ } | Sort-Object -Unique)
}

$networkConfigPath = Join-Path $PSScriptRoot 'network-config.ps1'
$NetworkAccessConfig = @{ BindAddress = '0.0.0.0'; PublicOrigins = @() }
if (Test-Path -LiteralPath $networkConfigPath -PathType Leaf) {
    . $networkConfigPath
}

$bindAddress = if ($env:APP_BIND_ADDRESS) {
    $env:APP_BIND_ADDRESS.Trim()
} elseif ($NetworkAccessConfig.BindAddress) {
    ([string]$NetworkAccessConfig.BindAddress).Trim()
} else {
    '0.0.0.0'
}
$env:APP_BIND_ADDRESS = $bindAddress

$localIpv4Addresses = @(Get-NetIPAddress -AddressFamily IPv4 -AddressState Preferred -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -ne '127.0.0.1' -and $_.IPAddress -notlike '169.254.*' } |
    Select-Object -ExpandProperty IPAddress -Unique)
$computerHost = $env:COMPUTERNAME.Trim().ToLowerInvariant()
$localHosts = Get-UniqueStrings (@('127.0.0.1', 'localhost', $computerHost) + $localIpv4Addresses)

$configuredOrigins = @(
    @(ConvertTo-StringList $NetworkAccessConfig.PublicOrigins)
    @(ConvertTo-StringList $env:APP_PUBLIC_ORIGINS)
)
$publicOrigins = @()
$publicHosts = @()
foreach ($origin in (Get-UniqueStrings $configuredOrigins)) {
    $originUri = $null
    if (-not [Uri]::TryCreate($origin, [UriKind]::Absolute, [ref]$originUri) -or
        $originUri.Scheme -notin @('http', 'https') -or
        $originUri.AbsolutePath -ne '/' -or $originUri.Query -or $originUri.Fragment) {
        throw "Invalid public origin '$origin'. Use scheme + host + optional port, for example https://demo.example.com"
    }
    $publicOrigins += $originUri.GetLeftPart([UriPartial]::Authority)
    $publicHosts += $originUri.DnsSafeHost
}
$publicOrigins = Get-UniqueStrings $publicOrigins
$publicHosts = Get-UniqueStrings $publicHosts

$allowedHosts = Get-UniqueStrings @(
    $localHosts
    $publicHosts
    @(ConvertTo-StringList $env:DJANGO_ALLOWED_HOSTS)
)
$trustedOrigins = @(
    'http://127.0.0.1:5173', 'http://127.0.0.1:5174',
    'http://localhost:5173', 'http://localhost:5174'
)
foreach ($hostName in (Get-UniqueStrings (@($computerHost) + $localIpv4Addresses))) {
    $trustedOrigins += "http://${hostName}:5173", "http://${hostName}:5174"
}
$trustedOrigins = Get-UniqueStrings @(
    $trustedOrigins
    $publicOrigins
    @(ConvertTo-StringList $env:DJANGO_CSRF_TRUSTED_ORIGINS)
)
$viteAllowedHosts = Get-UniqueStrings @(
    $computerHost
    $publicHosts
    @(ConvertTo-StringList $env:VITE_ALLOWED_HOSTS)
)

$env:DJANGO_ALLOWED_HOSTS = $allowedHosts -join ','
$env:DJANGO_CSRF_TRUSTED_ORIGINS = $trustedOrigins -join ','
$env:VITE_ALLOWED_HOSTS = $viteAllowedHosts -join ','

function Start-LocalService {
    param(
        [string]$Name,
        [int]$Port,
        [string]$Executable,
        [string[]]$Arguments,
        [string]$Directory,
        [bool]$RestartExisting = $false,
        [string]$ExpectedCommandPattern = ''
    )
    $listener = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    if ($listener) {
        if (-not $RestartExisting) {
            Write-Host "$Name already listening on port $Port."
            return
        }

        $processes = @($listener | Select-Object -ExpandProperty OwningProcess -Unique |
            ForEach-Object { Get-CimInstance Win32_Process -Filter "ProcessId = $_" })
        $unexpectedProcess = @($processes | Where-Object {
                -not $ExpectedCommandPattern -or $_.CommandLine -notmatch $ExpectedCommandPattern
            })
        if ($unexpectedProcess.Count -gt 0 -or $processes.Count -eq 0) {
            throw "$Name port $Port is occupied by an unknown process. Stop it manually and retry."
        }

        Write-Host "Restarting managed $Name listener on port $Port to apply current configuration..."
        $processes | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
        $stopDeadline = (Get-Date).AddSeconds(10)
        while ((Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue) -and
            (Get-Date) -lt $stopDeadline) {
            Start-Sleep -Milliseconds 200
        }
        if (Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue) {
            throw "$Name port $Port did not become available after stopping the old listener."
        }
    }
    $process = Start-Process -FilePath $Executable -ArgumentList $Arguments -WorkingDirectory $Directory `
        -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $runtimeDirectory "$Name-$runStamp.out.log") `
        -RedirectStandardError (Join-Path $runtimeDirectory "$Name-$runStamp.err.log")
    Write-Host "$Name launched (PID $($process.Id), port $Port)."
}

$pythonExecutable = (& py -c 'import sys; print(sys.executable)').Trim()
if ($LASTEXITCODE -ne 0) { throw 'Python is unavailable.' }
$nodeExecutable = (Get-Command node.exe).Source
$npmExecutable = (Get-Command npm.cmd).Source
$backendDirectory = Join-Path $PSScriptRoot 'backend'
$frontendDirectory = Join-Path $PSScriptRoot 'frontend'
$teamFrontendDirectory = Join-Path $PSScriptRoot 'team-frontend'

function Ensure-NodeDependencies {
    param([string]$Name, [string]$Directory)
    $viteEntry = Join-Path $Directory 'node_modules\vite\bin\vite.js'
    if (Test-Path -LiteralPath $viteEntry) { return }
    Write-Host "Installing $Name dependencies..."
    Push-Location $Directory
    try {
        & $npmExecutable install
        if ($LASTEXITCODE -ne 0) { throw "$Name dependency installation failed." }
    } finally {
        Pop-Location
    }
}

& $pythonExecutable -c 'import django' 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Installing backend dependencies...'
    & $pythonExecutable -m pip install -r (Join-Path $backendDirectory 'requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Backend dependency installation failed.' }
}

Ensure-NodeDependencies -Name 'administrator frontend' -Directory $frontendDirectory
Ensure-NodeDependencies -Name 'team frontend' -Directory $teamFrontendDirectory

Write-Host 'Applying database migrations...'
Push-Location $backendDirectory
try {
    & $pythonExecutable manage.py migrate --noinput
    if ($LASTEXITCODE -ne 0) { throw 'Database migration failed.' }
} finally {
    Pop-Location
}

$gisDirectory = Join-Path $projectRoot 'Gis\kqgisserver-lite-20260211_150534_release\kqwebservice'
$gisDataRoot = [IO.Path]::GetFullPath((Join-Path $projectRoot 'Gis'))
$gisPidDirectory = Join-Path $gisDataRoot 'kqmsdata\pids'
# The vendor launcher clears its own stale PID directory during startup.
foreach ($directory in @($gisDataRoot, (Join-Path $gisDataRoot 'kqmsdata'), $gisPidDirectory)) {
    if (Test-Path -LiteralPath $directory) {
        $item = Get-Item -LiteralPath $directory
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw "Refusing to start with a redirected GIS data directory: $directory"
        }
    }
}
if (-not (Test-Path -LiteralPath (Join-Path $gisDirectory 'bin\start.bat'))) {
    throw "KQGIS launcher not found: $gisDirectory"
}

Start-LocalService -Name 'backend' -Port 8000 -Executable $pythonExecutable `
    -Arguments @('-u', 'manage.py', 'runserver', '127.0.0.1:8000', '--noreload') `
    -Directory $backendDirectory -RestartExisting $true `
    -ExpectedCommandPattern 'manage\.py.+runserver.+127\.0\.0\.1:8000'
Start-LocalService -Name 'frontend' -Port 5173 -Executable $nodeExecutable `
    -Arguments @('node_modules/vite/bin/vite.js', '--host', $bindAddress, '--port', '5173', '--strictPort') `
    -Directory $frontendDirectory -RestartExisting $true `
    -ExpectedCommandPattern 'node_modules[\\/]vite[\\/]bin[\\/]vite\.js.+--port\s+5173(\s|$)'
Start-LocalService -Name 'team-frontend' -Port 5174 -Executable $nodeExecutable `
    -Arguments @('node_modules/vite/bin/vite.js', '--host', $bindAddress, '--port', '5174', '--strictPort') `
    -Directory $teamFrontendDirectory -RestartExisting $true `
    -ExpectedCommandPattern 'node_modules[\\/]vite[\\/]bin[\\/]vite\.js.+--port\s+5174(\s|$)'

$previousGisDataPath = $env:KQMS_DATA_PATH
try {
    $env:KQMS_DATA_PATH = $gisDataRoot
    Start-LocalService -Name 'kqgis' -Port 9600 -Executable $env:ComSpec `
        -Arguments @('/d', '/c', 'bin\start.bat') -Directory $gisDirectory
} finally {
    $env:KQMS_DATA_PATH = $previousGisDataPath
}

$pending = @{
    frontend = 'http://127.0.0.1:5173/'
    teamFrontend = 'http://127.0.0.1:5174/'
    backend = 'http://127.0.0.1:8000/api/csrf/'
    kqgis = 'http://127.0.0.1:9600/kqgis/rest/services/jilong_port_multitemporal/map/getmetadata'
}
$deadline = (Get-Date).AddSeconds(180)
while ($pending.Count -gt 0 -and (Get-Date) -lt $deadline) {
    foreach ($name in @($pending.Keys)) {
        try {
            $response = Invoke-WebRequest -Uri $pending[$name] -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -eq 200) {
                if ($name -eq 'kqgis') {
                    # KQGIS returns an HTML starting page before the map API is ready.
                    $metadata = $response.Content | ConvertFrom-Json -ErrorAction Stop
                    if (-not $metadata -or $metadata.error -or $metadata.success -eq $false) { continue }
                }
                Write-Host "$name ready: $($pending[$name])"
                $pending.Remove($name)
            }
        } catch { }
    }
    if ($pending.Count -gt 0) { Start-Sleep -Seconds 2 }
}
if ($pending.Count -gt 0) {
    throw "Not ready yet: $($pending.Keys -join ', '). Inspect logs in $runtimeDirectory"
}
Write-Host 'Open http://127.0.0.1:5173/#/login'
Write-Host 'Team portal: http://127.0.0.1:5174/'
foreach ($address in $localIpv4Addresses) {
    Write-Host "LAN administrator: http://${address}:5173/#/login"
    Write-Host "LAN team portal:  http://${address}:5174/"
}
foreach ($origin in $publicOrigins) {
    Write-Host "Configured public origin: $origin"
}
