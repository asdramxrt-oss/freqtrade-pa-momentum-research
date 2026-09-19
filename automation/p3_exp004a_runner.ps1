$ErrorActionPreference="Stop"
$root=Split-Path -Parent $PSScriptRoot
$gate=Join-Path $root ".mece\PHASE_GATE.json"
$g=Get-Content -Raw $gate|ConvertFrom-Json
Write-Host "P3-EXP-004A EXECUTION GUARD"
if(-not $g.allow_new_experiments -or $g.stop_after_phase_completion){
  Write-Host "[BLOCKED] Governance gate is closed. No experiment will be executed."
  exit 0
}
Write-Host "[BLOCKED] Execution implementation is intentionally not enabled by this scaffold."
Write-Host "[ACTION] Obtain an explicitly authorized experiment runner before execution."
exit 0
