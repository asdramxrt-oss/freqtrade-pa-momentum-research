param(
    [switch]$Continuous,
    [switch]$InstallTask
)

$ErrorActionPreference = "Stop"
$LauncherRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Repo = 'C:\Users\rahul\Downloads\freqtrade-develop\freqtrade-pa-momentum-research'

# If package is extracted directly into the research repo, use it.
if (Test-Path (Join-Path $LauncherRoot "automation\bridge.py")) {
$Repo = 'C:\Users\rahul\Downloads\freqtrade-develop\freqtrade-pa-momentum-research'
}

$Python = (Get-Command python -ErrorAction Stop).Source
$MaxRetries = 2
$RetryDelay = 15
$LoopDelay = 60
$TaskName = "Freqtrade All Phases Research Controller"

function Test-Repo {
    if (-not (Test-Path $Repo)) {
        throw "Research repository not found: $Repo"
    }
    if (-not (Test-Path (Join-Path $Repo ".mece\PHASE_GATE.json"))) {
        throw "MECE gate not found: $Repo\.mece\PHASE_GATE.json"
    }
    if (-not (Test-Path (Join-Path $Repo "automation\bridge.py"))) {
        throw "automation.bridge not found under: $Repo"
    }
}

function Get-Gate {
    $gatePath = Join-Path $Repo ".mece\PHASE_GATE.json"
    return Get-Content $gatePath -Raw | ConvertFrom-Json
}

function Invoke-SafePass {
    Push-Location $Repo
    try {
        & $Python -m automation.bridge --json
        return $LASTEXITCODE
    }
    finally {
        Pop-Location
    }
}

function Install-ScheduledTask {
    $launcher = Join-Path $LauncherRoot "RUN_CONTINUOUS_ALL_PHASES.bat"
    schtasks /Create /TN $TaskName /TR "`"$launcher`"" /SC ONLOGON /RL LIMITED /F | Out-Host
    Write-Host "Installed: $TaskName"
}

if ($InstallTask) {
    Test-Repo
    Install-ScheduledTask
    exit 0
}

Test-Repo

do {
    $gate = Get-Gate
    Write-Host ""
    Write-Host "============================================================"
    Write-Host " ALL-PHASE RESEARCH CONTROLLER"
    Write-Host " Repository: $Repo"
    Write-Host " Phase:      $($gate.phase)"
    Write-Host " Gate open:  $($gate.allow_new_experiments)"
    Write-Host " Stop flag:  $($gate.stop_after_phase_completion)"
    Write-Host "============================================================"

    # Governance is authoritative. Never bypass a closed gate.
    if ($gate.allow_new_experiments -ne $true) {
        Write-Host "Gate is closed. Running only the bridge's safe read/validation/report path."
    }

    $rc = 1
    for ($attempt = 1; $attempt -le ($MaxRetries + 1); $attempt++) {
        Write-Host ""
        Write-Host "Safe controller pass $attempt/$($MaxRetries + 1)..."
        $rc = Invoke-SafePass

        if ($rc -eq 0) { break }

        # 10 is reserved for governance/closed-gate stop in the bridge.
        if ($rc -eq 10) {
            Write-Host "Governance stop received. No bypass attempted."
            exit 10
        }

        if ($attempt -le $MaxRetries) {
            Write-Host "Pass failed. Retrying in $RetryDelay seconds..."
            Start-Sleep -Seconds $RetryDelay
        }
    }

    if ($rc -ne 0) {
        Write-Host "Controller stopped after repeated failure: $rc"
        exit $rc
    }

    # Re-read state after the pass so phase transitions are detected.
    $after = Get-Gate
    Write-Host ""
    Write-Host "Post-pass phase: $($after.phase)"
    Write-Host "Post-pass gate open: $($after.allow_new_experiments)"

    if (-not $Continuous) {
        exit 0
    }

    Write-Host "Continuous mode: next safe pass in $LoopDelay seconds..."
    Start-Sleep -Seconds $LoopDelay

} while ($true)



