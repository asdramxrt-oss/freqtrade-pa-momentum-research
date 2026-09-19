$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
Write-Host "============================================================"
Write-Host "FREQTRADE GOVERNED READINESS CHECK"
Write-Host "Codex=OFF Data Analysis=OFF Work=OFF Live Trading=OFF"
Write-Host "============================================================"
$gate = Join-Path $root ".mece\PHASE_GATE.json"
if (!(Test-Path $gate)) { Write-Host "[ERROR] Gate file not found:" $gate; exit 2 }
try { $g = Get-Content -Raw -LiteralPath $gate | ConvertFrom-Json } catch { Write-Host "[ERROR] Cannot read gate:" $_; exit 3 }
Write-Host "[ROOT]" $root
Write-Host "[PHASE]" $g.phase
Write-Host "[GATE] allow_new_experiments:" $g.allow_new_experiments
Write-Host "[GATE] stop_after_phase_completion:" $g.stop_after_phase_completion

$strategy = Get-ChildItem -LiteralPath $root -Filter "CrossSectionalMomentumResearch.py" -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch "\\(\.git|\.venv|phase_runs)\\" }
$config = Get-ChildItem -LiteralPath $root -Filter "P3-EXP-004A.json" -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch "\\(\.git|\.venv|phase_runs)\\" }
$runner = Get-ChildItem -LiteralPath $root -Filter "p3_exp004a_run.py" -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch "\\(\.git|\.venv|phase_runs)\\" }
$registry = Join-Path $root "docs\EXPERIMENT_REGISTRY.md"
$registryHit = $false
if (Test-Path $registry) { $registryHit = (Get-Content -Raw $registry -ErrorAction SilentlyContinue) -match "P3-EXP-004A" }

Write-Host "[STRATEGY]" ($(if($strategy){$strategy.FullName.Substring($root.Length+1)}else{"NOT FOUND"}))
Write-Host "[CONFIG]" ($(if($config){$config.FullName.Substring($root.Length+1)}else{"NOT FOUND"}))
Write-Host "[EXPERIMENT RUNNER]" ($(if($runner){$runner.FullName.Substring($root.Length+1)}else{"NOT FOUND"}))
Write-Host "[REGISTRY] P3-EXP-004A:" $registryHit

$blockers = @()
if (!$g.allow_new_experiments -or $g.stop_after_phase_completion) { $blockers += "Governance gate is closed for new experiments." }
if (!$strategy) { $blockers += "CrossSectionalMomentumResearch.py not found." }
if (!$config) { $blockers += "P3-EXP-004A.json not found." }
if (!$runner) { $blockers += "No P3-EXP-004A experiment runner is present." }

Write-Host ""
Write-Host "[ACTION] WAIT"
foreach($b in $blockers){ Write-Host "[BLOCKER]" $b }
Write-Host "[OK] No gate, strategy, configuration, dependency, or experiment execution was changed."
Write-Host ""
Write-Host "READINESS CHECK FINISHED."
exit 0
