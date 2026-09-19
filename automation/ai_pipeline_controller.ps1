$ErrorActionPreference = "Stop"

$Root = "C:\Users\rahul\Downloads\freqtrade-develop\freqtrade-pa-momentum-research"
$Gate = Join-Path $Root ".mece\PHASE_GATE.json"
$StateDir = Join-Path $Root "phase_runs\ai_orchestrator"
$State = Join-Path $StateDir "AI_PIPELINE_STATE.json"

New-Item -ItemType Directory -Force -Path $StateDir | Out-Null

function Save-State($obj) {
    $obj | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $State -Encoding UTF8
}

if (!(Test-Path $Gate)) {
    Save-State @{ status="BLOCKED"; reason="governance_gate_missing"; utc=(Get-Date).ToUniversalTime().ToString("o") }
    Write-Host "[BLOCKED] Governance gate missing. FAIL CLOSED."
    exit 2
}

$g = Get-Content -Raw -LiteralPath $Gate | ConvertFrom-Json

if (-not ($g.allow_new_experiments -eq $true -and $g.stop_after_phase_completion -eq $false)) {
    Save-State @{
        status="WAIT"
        phase=$g.phase
        allow_new_experiments=$g.allow_new_experiments
        stop_after_phase_completion=$g.stop_after_phase_completion
        codex=$false
        chatgpt_data_analysis=$false
        live_trading=$false
        promotion=$false
        utc=(Get-Date).ToUniversalTime().ToString("o")
    }
    Write-Host "[WAIT] Governance has not authorized new experiments."
    Write-Host "[WAIT] ChatGPT/CrewAI/OpenCode pipeline will not execute experiment work."
    exit 0
}

Write-Host "[AUTHORIZED] Governance gate is open."
Write-Host "[1/4] Checking CrewAI..."
$crew = Get-Command crewai -ErrorAction SilentlyContinue
if (-not $crew) {
    Save-State @{ status="BLOCKED"; reason="crewai_not_found"; phase=$g.phase; utc=(Get-Date).ToUniversalTime().ToString("o") }
    Write-Host "[BLOCKED] CrewAI executable not found."
    exit 3
}

Write-Host "[2/4] Checking OpenCode..."
$oc = Get-Command opencode -ErrorAction SilentlyContinue
if (-not $oc) {
    Save-State @{ status="BLOCKED"; reason="opencode_not_found"; phase=$g.phase; utc=(Get-Date).ToUniversalTime().ToString("o") }
    Write-Host "[BLOCKED] OpenCode executable not found."
    exit 4
}

Write-Host "[3/4] Starting CrewAI coordinator..."
$crewProject = Join-Path $Root "crew_ai"
if (!(Test-Path $crewProject)) {
    Save-State @{ status="BLOCKED"; reason="crew_ai_project_missing"; phase=$g.phase; utc=(Get-Date).ToUniversalTime().ToString("o") }
    Write-Host "[BLOCKED] crew_ai project is not installed."
    exit 5
}

# The coordinator must itself enforce the same gate before dispatching coding tasks.
$coord = Join-Path $crewProject "run_authorized_wave.py"
$python = Join-Path $Root ".venv\Scripts\python.exe"
if (!(Test-Path $python)) { $python = "python" }

& $python $coord --root $Root
$rc = $LASTEXITCODE

Save-State @{
    status= if($rc -eq 0){"COMPLETE"}else{"FAILED"}
    phase=$g.phase
    crewai=$true
    opencode=$true
    runner_exit_code=$rc
    utc=(Get-Date).ToUniversalTime().ToString("o")
}

if ($rc -ne 0) { exit $rc }

Write-Host "[4/4] AI pipeline finished. No automatic promotion."
exit 0
