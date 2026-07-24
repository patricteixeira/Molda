$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$templateDir = Join-Path $repoRoot "carrosseis\.molda-private\runtime-packages"
$fontDir = Join-Path $repoRoot "apps\web\public\fonts\synapsis"

if (-not (Test-Path -LiteralPath $templateDir -PathType Container)) {
    throw "O catálogo privado local não foi encontrado em $templateDir."
}

if (-not (Test-Path -LiteralPath $fontDir -PathType Container)) {
    throw "A pasta local de fontes não foi encontrada em $fontDir."
}

$env:BRANDRT_PRIVATE_TEMPLATE_HOST_DIR = (Resolve-Path $templateDir).Path
$env:BRANDRT_PRIVATE_FONT_HOST_DIR = (Resolve-Path $fontDir).Path
$env:VITE_SYNAPSIS_FONT_BASE_URL = "/fonts/synapsis"

Push-Location $repoRoot
try {
    docker compose `
        -f docker-compose.yml `
        -f infra/hosting/compose.hosted-assets.yml `
        up -d --build --wait
}
finally {
    Pop-Location
}
