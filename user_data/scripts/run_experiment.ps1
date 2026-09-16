<#
.SYNOPSIS
    Run a pre-registered research experiment and print its headline metrics.

.DESCRIPTION
    Executes `freqtrade backtesting` with the frozen configuration for a given
    experiment ID and extracts the metrics that the research charter requires to
    be reported.

    The script does not choose parameters. It runs the configuration that was
    committed for the experiment, so that the numbers it prints are attributable
    to a specific commit.

.PARAMETER Experiment
    Experiment ID whose config is user_data/configs/<Experiment>.json.

.PARAMETER Timerange
    freqtrade timerange. Defaults to the full pre-registered sample.

.PARAMETER Fee
    Optional fee override per side, e.g. 0.001 or 0.002. Used for the cost
    sensitivity sweep.

.PARAMETER Pairs
    Optional comma-separated pair override, for diagnostics only. Results
    produced with a pair override are not comparable to the pre-registered runs
    and must be labelled as such.

.EXAMPLE
    ./user_data/scripts/run_experiment.ps1 -Experiment EXP-001

.EXAMPLE
    ./user_data/scripts/run_experiment.ps1 -Experiment EXP-001 -Fee 0.002

.EXAMPLE
    ./user_data/scripts/run_experiment.ps1 -Experiment EXP-001 -Timerange 20250101-20260101
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Experiment,

    [string]$Timerange = "20190101-20260101",
    [string]$Fee = "",
    [string]$Pairs = ""
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Config = Join-Path $ProjectRoot "user_data\configs\$Experiment.json"

if (-not (Test-Path -LiteralPath $Config)) {
    throw "No configuration found for '$Experiment' at $Config. Author the spec and config first."
}

if ($env:FREQTRADE_SRC -and -not $env:PYTHONPATH) {
    $env:PYTHONPATH = $env:FREQTRADE_SRC
}

$arguments = @(
    "-m", "freqtrade", "backtesting",
    "--userdir", (Join-Path $ProjectRoot "user_data"),
    "-c", $Config,
    "--timerange", $Timerange,
    "--cache", "none",
    "--export", "trades"
)

if ($Fee -ne "") {
    $arguments += "--fee"
    $arguments += $Fee
}

if ($Pairs -ne "") {
    $arguments += "--pairs"
    $arguments += ($Pairs -split "," | ForEach-Object { $_.Trim() })
}

$logDirectory = Join-Path $env:TEMP "pa-momentum-research"
New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logFile = Join-Path $logDirectory "$Experiment-$Timerange-$stamp.log"

Write-Host "Experiment : $Experiment" -ForegroundColor Cyan
Write-Host "Config     : $Config" -ForegroundColor DarkGray
Write-Host "Timerange  : $Timerange" -ForegroundColor DarkGray
if ($Fee -ne "") { Write-Host "Fee        : $Fee" -ForegroundColor DarkGray }
Write-Host "Log        : $logFile" -ForegroundColor DarkGray

Push-Location $ProjectRoot
try {
    & python @arguments 2>&1 | Tee-Object -FilePath $logFile | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "freqtrade backtesting failed with exit code $LASTEXITCODE. See $logFile"
    }
}
finally {
    Pop-Location
}

$patterns = @(
    "Backtesting from",
    "Backtesting to",
    "Max open trades",
    "Total/Daily Avg Trades",
    "Starting balance",
    "Final balance",
    "Total profit %",
    "CAGR %",
    "Profit factor",
    "Expectancy",
    "SQN",
    "Mean profit p-value",
    "Sharpe \(closed trades\)",
    "Sharpe \(daily wallet balance\)",
    "Max % of account underwater ",
    "Absolute drawdown ",
    "Market change",
    "Total trade volume"
)

Write-Host ""
Write-Host "=== Headline metrics ($Experiment, $Timerange) ===" -ForegroundColor Cyan
Select-String -Path $logFile -Pattern $patterns |
    ForEach-Object { $_.Line.Trim() } |
    Where-Object { $_ -notmatch "wallet balance\)$" }
Write-Host ""
Write-Host "Full log: $logFile" -ForegroundColor DarkGray
Write-Host "Record the results in research/experiment_results/$Experiment.md" -ForegroundColor Yellow
