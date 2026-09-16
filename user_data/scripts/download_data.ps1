<#
.SYNOPSIS
    Download the pre-registered market data for this research project.

.DESCRIPTION
    Wraps `freqtrade download-data` so that the data universe, timestamp range
    and destination are identical for every experiment. Raw candles are
    git-ignored and are expected to be regenerated, never committed.

    freqtrade must be importable. If it is not installed, set FREQTRADE_SRC to a
    freqtrade source checkout; that directory is prepended to PYTHONPATH.

.PARAMETER Pairs
    Comma-separated pair list, or "all" to use the config whitelist.

.PARAMETER Timerange
    freqtrade timerange, e.g. 20190101-20260101.

.PARAMETER Timeframe
    Candle timeframe. Defaults to 4h, the pre-registered timeframe.

.PARAMETER Prepend
    Download data before the existing range instead of after it. Use this after
    a partial download has already created a truncated file.

.EXAMPLE
    ./user_data/scripts/download_data.ps1

.EXAMPLE
    ./user_data/scripts/download_data.ps1 -Pairs BTC/USDT,ETH/USDT -Prepend
#>
[CmdletBinding()]
param(
    [string]$Pairs = "all",
    [string]$Timerange = "20190101-20260101",
    [string]$Timeframe = "4h",
    [switch]$Prepend
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Config = Join-Path $ProjectRoot "user_data\configs\EXP-001.json"

if ($env:FREQTRADE_SRC -and -not $env:PYTHONPATH) {
    $env:PYTHONPATH = $env:FREQTRADE_SRC
}

$arguments = @(
    "-m", "freqtrade", "download-data",
    "--userdir", (Join-Path $ProjectRoot "user_data"),
    "-c", $Config,
    "-t", $Timeframe,
    "--timerange", $Timerange
)

if ($Pairs -ne "all") {
    $arguments += "--pairs"
    $arguments += ($Pairs -split "," | ForEach-Object { $_.Trim() })
}

if ($Prepend) {
    $arguments += "--prepend"
}

Write-Host "Downloading $Timeframe data for '$Pairs' over $Timerange" -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot" -ForegroundColor DarkGray

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

Write-Host "Data download complete." -ForegroundColor Green
