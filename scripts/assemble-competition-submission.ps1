$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$submissionRoot = Join-Path $projectRoot '参赛作品提交材料_20260929'
$sections = @(
    '01_开发源代码',
    '02_安装及配置文件',
    '03_部署说明及访问地址',
    '04_相关数据',
    '05_作品介绍文档',
    '06_系统概述',
    '07_作品过程及成果截图',
    '08_演示视频',
    '09_人员信息'
)

foreach ($section in $sections) {
    New-Item -ItemType Directory -Path (Join-Path $submissionRoot $section) -Force | Out-Null
}

function Copy-ProjectFile {
    param(
        [Parameter(Mandatory)][string]$RelativeSource,
        [Parameter(Mandatory)][string]$RelativeDestination,
        [switch]$SkipHash
    )
    $source = Join-Path $projectRoot $RelativeSource
    $destination = Join-Path $submissionRoot $RelativeDestination
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "Missing submission source file: $source"
    }
    New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
    Copy-Item -LiteralPath $source -Destination $destination -Force
    if ((Get-Item -LiteralPath $source).Length -ne (Get-Item -LiteralPath $destination).Length) {
        throw "Copy length verification failed: $source"
    }
    if ($SkipHash) { return }
    try {
        if ((Get-FileHash -LiteralPath $source -Algorithm SHA256 -ErrorAction Stop).Hash -ne
            (Get-FileHash -LiteralPath $destination -Algorithm SHA256 -ErrorAction Stop).Hash) {
            throw "Copy hash verification failed: $source"
        }
    } catch [System.IO.IOException] {
        # Word can hold an exclusive handle on an open DOCX; byte-length was checked above.
    }
}

function Copy-ProjectTree {
    param(
        [Parameter(Mandatory)][string]$RelativeSource,
        [Parameter(Mandatory)][string]$RelativeDestination,
        [string[]]$Extensions = @(),
        [string[]]$ExcludeNames = @(),
        [switch]$SkipHash
    )
    $sourceRoot = Join-Path $projectRoot $RelativeSource
    if (-not (Test-Path -LiteralPath $sourceRoot -PathType Container)) {
        throw "Missing submission source directory: $sourceRoot"
    }
    Get-ChildItem -LiteralPath $sourceRoot -File -Recurse | ForEach-Object {
        if ($Extensions.Count -gt 0 -and $_.Extension -notin $Extensions) { return }
        if ($_.Name -in $ExcludeNames) { return }
        $suffix = $_.FullName.Substring($sourceRoot.Length).TrimStart('\')
        Copy-ProjectFile -RelativeSource (Join-Path $RelativeSource $suffix) `
            -RelativeDestination (Join-Path $RelativeDestination $suffix) -SkipHash:$SkipHash
    }
}

# 01: runnable application source tree, excluding local DB, uploads, build output and dependencies.
Copy-ProjectTree 'app\backend' '01_开发源代码\app\backend' @('.py')
Copy-ProjectTree 'app\frontend\src' '01_开发源代码\app\frontend\src'
Copy-ProjectTree 'app\team-frontend\src' '01_开发源代码\app\team-frontend\src'
foreach ($relative in @(
    'app\backend\manage.py',
    'app\frontend\index.html',
    'app\frontend\vite.config.js',
    'app\team-frontend\index.html',
    'app\team-frontend\vite.config.js',
    'app\backend\requirements.txt',
    'app\frontend\package.json',
    'app\frontend\package-lock.json',
    'app\team-frontend\package.json',
    'app\team-frontend\package-lock.json',
    'app\start-services.ps1',
    'app\network-config.ps1',
    '一键启动全部环境.cmd',
    'scripts\start.ps1',
    'scripts\verify-project.ps1',
    '.editorconfig',
    '.gitattributes',
    '.gitignore',
    'app\.gitignore',
    'app\README.md',
    'README.md',
    'docs\PROJECT_STRUCTURE.md'
)) {
    Copy-ProjectFile $relative (Join-Path '01_开发源代码' $relative)
}

# 02: dependency manifests and launch/configuration files. Duplicates here are intentional.
foreach ($relative in @(
    '一键启动全部环境.cmd',
    'app\start-services.ps1',
    'app\network-config.ps1',
    'app\backend\requirements.txt',
    'app\frontend\package.json',
    'app\frontend\package-lock.json',
    'app\team-frontend\package.json',
    'app\team-frontend\package-lock.json',
    'scripts\start.ps1',
    'scripts\verify-project.ps1',
    'docs\NETWORK_ACCESS.md',
    'docs\KQGIS_基础地图服务说明.md'
)) {
    Copy-ProjectFile $relative (Join-Path '02_安装及配置文件' $relative)
}

# 03, 05 and 06: final Word deliverables only; exclude render/QA intermediates.
Copy-ProjectFile `
    'artifacts\部署说明文档_20260929\基于KQGIS的地质灾害监测救援部署系统—以吉隆口岸泥石流灾害为例，系统部署说明文档.docx' `
    '03_部署说明及访问地址\系统部署说明文档.docx'
Copy-ProjectFile `
    'artifacts\作品介绍文档_20260929\基于KQGIS的地质灾害监测救援部署系统—以吉隆口岸泥石流灾害为例,作品介绍文档.docx' `
    '05_作品介绍文档\作品介绍文档.docx'
Copy-ProjectFile `
    'artifacts\作品介绍文档_20260929\基于KQGIS的地质灾害监测救援部署系统—以吉隆口岸泥石流灾害为例，系统概述.docx' `
    '06_系统概述\系统概述.docx'

# 04: project-created KQGIS maps and all supplied geographic source data.
# The desktop installer ZIP is not geographic data and is expressly excluded.
Copy-ProjectTree 'kqgis_publish' '04_相关数据\KQGIS地图工程'
foreach ($name in @('jilong_base', 'jilong_county_atlas', 'jilong_port_multitemporal')) {
    Copy-ProjectFile "Gis\kqmsdata\gis\srvs\services\$name.kqmdx" `
        "04_相关数据\KQGIS地图工程\当前已发布工程\$name.kqmdx"
}
Write-Host 'Copying original geographic data (this is approximately 11 GiB)...'
Copy-ProjectTree '尼泊尔泥石流巨灾' '04_相关数据\原始地图数据\尼泊尔泥石流巨灾' `
    -ExcludeNames @('kqgis desktop.zip') -SkipHash
& py (Join-Path $PSScriptRoot 'prepare-submission-database.py')
if ($LASTEXITCODE -ne 0) { throw 'Failed to prepare the offline demo database.' }

# 07: numbered result screenshots, at least three required.
Copy-ProjectTree 'artifacts\作品过程及成果截图_20260929' '07_作品过程及成果截图' @('.png')

# 09: use the member list supplied next to the overview, with no edits to names.
Copy-ProjectFile 'artifacts\作品介绍文档_20260929\人员信息名录.txt' `
    '09_人员信息\人员信息名录.txt'

Write-Host "Submission materials assembled at: $submissionRoot"
$sections | ForEach-Object {
    $path = Join-Path $submissionRoot $_
    $count = @(Get-ChildItem -LiteralPath $path -File -Recurse).Count
    Write-Host ("{0}: {1} files" -f $_, $count)
}
