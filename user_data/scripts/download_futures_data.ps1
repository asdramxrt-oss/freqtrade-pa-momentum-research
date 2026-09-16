<#
.SYNOPSIS
    Download the GENUINE Binance USDT-M futures dataset for Phase 3 (P3-EXP-001+).

.DESCRIPTION
    Writes into a SEPARATE data directory (default `user_data/data_p3`) so the
    historical spot mirror at `user_data/data/binance/futures/` is NEVER touched.

    The spot mirror exists only so EXP-001...EXP-004 remain reproducible; it is
    NOT genuine futures OHLCV and must never be substituted silently.

    Downloads:
      - futures      (genuine USDT-M perpetual OHLCV, 4h)
      - funding_rate (1h container, one row per funding event)
      - mark / index / premiumIndex (4h)

    Open interest is intentionally omitted: Binance does not expose long history
    for it (verified 2026-09-16).

.PARAMETER Timerange
    freqtrade timerange. Defaults to the full Phase-3 span.

.PARAMETER Timeframe
    Candle timeframe. Defaults to 4h (the pre-registered timeframe).

.PARAMETER DataDir
    Destination datadir, relative to the project root. Defaults to
    `user_data/data_p3`.

.EXAMPLE
    ./user_data/scripts/download_futures_data.ps1
#>
[CmdletBinding()]
param(
    [string]$Timerange = "20190101-20260916",
    [string]$Timeframe = "4h",
    [string]$DataDir = "user_data/data_p3"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Config = Join-Path $ProjectRoot "user_data\configs\EXP-003.json"
$Dest = Join-Path $ProjectRoot $DataDir

if ($env:FREQTRADE_SRC -and -not $env:PYTHONPATH) {
    $env:PYTHONPATH = $env:FREQTRADE_SRC
}

if (-not (Test-Path -LiteralPath $Config)) {
    throw "Config not found: $Config"
}

Write-Host "Downloading GENUINE futures data -> $Dest" -ForegroundColor Cyan
Write-Host "Spot mirror (user_data\data) is NOT modified." -ForegroundColor DarkGray

$arguments = @(
    "-m", "freqtrade", "download-data",
    "--userdir", (Join-Path $ProjectRoot "user_data"),
    "-d", $Dest,
    "-c", $Config,
    "-t", $Timeframe,
    "--trading-mode", "futures",
    "--candle-types", "futures", "funding_rate", "mark", "index", "premiumIndex",
    "--timerange", $Timerange
)

Push-Location $ProjectRoot
try {
    & python @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "freqtrade download-data failed with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}

Write-Host "Genuine futures download complete." -ForegroundColor Green
