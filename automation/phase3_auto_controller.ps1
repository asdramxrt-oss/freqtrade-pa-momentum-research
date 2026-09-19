$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$gatePath = Join-Path $root ".mece\PHASE_GATE.json"
$runner = Join-Path $root "user_data\scripts\p3_exp004a_run.py"
$logDir = Join-Path $root "phase_runs\phase3_auto_controller"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Get-Sha256($p) {
    if (Test-Path $p) { return (Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash }
    return ""
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$log = Join-Path $logDir "AUTO_$stamp.log"

"PHASE 3 AUTO CONTROLLER" | Tee-Object -FilePath $log
"Codex=OFF Data Analysis=OFF Work=OFF Live Trading=OFF" | Tee-Object -FilePath $log -Append
"ROOT=$root" | Tee-Object -FilePath $log -Append

if (!(Test-Path $gatePath)) {
    "BLOCKER: gate missing. FAIL CLOSED." | Tee-Object -FilePath $log -Append
    exit 2
}
if (!(Test-Path $runner)) {
    "BLOCKER: P3-EXP-004A runner missing." | Tee-Object -FilePath $log -Append
    exit 2
}

$gate = Get-Content -Raw -LiteralPath $gatePath | ConvertFrom-Json
"PHASE=$($gate.phase)" | Tee-Object -FilePath $log -Append
"allow_new_experiments=$($gate.allow_new_experiments)" | Tee-Object -FilePath $log -Append
"stop_after_phase_completion=$($gate.stop_after_phase_completion)" | Tee-Object -FilePath $log -Append

$spec = Join-Path $root "docs\FROZEN_IMPLEMENTATION_SPEC.md"
$specSha = Get-Sha256 $spec
$specExpected = "E9B3145A51AC6BD587844F26AD1675720AB531556992027DE78097FE06543DF2"
if ($specSha.ToUpper() -ne $specExpected) {
    "BLOCKER: frozen specification hash changed. FAIL CLOSED." | Tee-Object -FilePath $log -Append
    exit 2
}
"FrozenSpecSHA256=$specSha" | Tee-Object -FilePath $log -Append

if (!($gate.allow_new_experiments -eq $true -and $gate.stop_after_phase_completion -eq $false)) {
    "ACTION=WAIT" | Tee-Object -FilePath $log -Append
    "No experiment executed. Governance remains authoritative." | Tee-Object -FilePath $log -Append
    exit 0
}

"AUTHORIZATION DETECTED. Starting the single preregistered 004A runner." | Tee-Object -FilePath $log -Append
$python = Join-Path $root ".venv\Scripts\python.exe"
if (!(Test-Path $python)) { $python = "python" }

& $python $runner 2>&1 | Tee-Object -FilePath $log -Append
$rc = $LASTEXITCODE
"RunnerExitCode=$rc" | Tee-Object -FilePath $log -Append

if ($rc -ne 0) { exit $rc }
exit 0
