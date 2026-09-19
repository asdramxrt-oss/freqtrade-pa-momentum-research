$ErrorActionPreference="Stop"
$root=Split-Path -Parent $PSScriptRoot
$gate=Join-Path $root ".mece\PHASE_GATE.json"
$outdir=Join-Path $root "phase_runs\p3_exp004a_readiness"
New-Item -ItemType Directory -Force -Path $outdir | Out-Null
$stamp=Get-Date -Format "yyyyMMdd_HHmmss"

function Rel($p){ if($p){$p.FullName.Substring($root.Length+1).Replace("\","/")} }

$g=Get-Content -Raw -LiteralPath $gate | ConvertFrom-Json
$strategy=Get-ChildItem $root -Recurse -File -Filter "CrossSectionalMomentumResearch.py" -ErrorAction SilentlyContinue | ? {$_.FullName -notmatch "\\(\.git|\.venv|phase_runs)\\"}
$config=Get-ChildItem $root -Recurse -File -Filter "P3-EXP-004A.json" -ErrorAction SilentlyContinue | ? {$_.FullName -notmatch "\\(\.git|\.venv|phase_runs)\\"}
$registry=Join-Path $root "docs\EXPERIMENT_REGISTRY.md"
$spec=Get-ChildItem $root -Recurse -File -Filter "*.md" -ErrorAction SilentlyContinue | ? {$_.FullName -notmatch "\\(\.git|\.venv|phase_runs)\\"} | ? { (Get-Content -Raw $_.FullName -ErrorAction SilentlyContinue) -match "P3-EXP-004A" }
$runner=Join-Path $root "automation\p3_exp004a_runner.ps1"

$blockers=@()
if(-not $g.allow_new_experiments -or $g.stop_after_phase_completion){$blockers+="Governance gate is closed; execution is prohibited."}
if(-not $strategy){$blockers+="CrossSectionalMomentumResearch.py is missing."}
if(-not $config){$blockers+="P3-EXP-004A.json is missing."}
if(-not (Test-Path $registry)){$blockers+="Experiment registry is missing."}

$result=[ordered]@{
 timestamp=(Get-Date).ToString("o")
 phase=$g.phase
 allow_new_experiments=[bool]$g.allow_new_experiments
 stop_after_phase_completion=[bool]$g.stop_after_phase_completion
 strategy=if($strategy){Rel $strategy}else{$null}
 config=if($config){Rel $config}else{$null}
 documentation=if($spec){@($spec|%{Rel $_})}else{@()}
 runner_scaffold=Rel (Get-Item $runner -ErrorAction SilentlyContinue)
 execution="NOT_RUN"
 live_trading=$false
 promotion=$false
 gate_modified=$false
 blockers=$blockers
}
$j=Join-Path $outdir "RUNNER_SCAFFOLD_$stamp.json"
$m=Join-Path $outdir "RUNNER_SCAFFOLD_$stamp.md"
$result|ConvertTo-Json -Depth 6|Set-Content -Encoding UTF8 $j
@("# P3-EXP-004A Gate-Aware Runner Scaffold","","Status: READY-TO-WAIT","",
"Execution is deliberately blocked until the governance gate authorizes new experiments.","",
"## Detected","",
"- Phase: $($g.phase)",
"- allow_new_experiments: $($g.allow_new_experiments)",
"- stop_after_phase_completion: $($g.stop_after_phase_completion)",
"- Strategy: $(if($strategy){Rel $strategy}else{'MISSING'})",
"- Config: $(if($config){Rel $config}else{'MISSING'})",
"- Documentation matches: $($spec.Count)",
"- Execution: NOT RUN",
"- Live trading: FALSE",
"- Promotion: FALSE",
"- Gate modified: FALSE","",
"## Blockers","")+(@($blockers|%{"- $_"}))|Set-Content -Encoding UTF8 $m

Write-Host "============================================================"
Write-Host "P3-EXP-004A GATE-AWARE RUNNER SCAFFOLD"
Write-Host "Codex=OFF Data Analysis=OFF Work=OFF Live Trading=OFF"
Write-Host "============================================================"
Write-Host "[ROOT]" $root
Write-Host "[PHASE]" $g.phase
Write-Host "[STRATEGY]" (if($strategy){Rel $strategy}else{"NOT FOUND"})
Write-Host "[CONFIG]" (if($config){Rel $config}else{"NOT FOUND"})
Write-Host "[DOCS]" $spec.Count "matching document(s)"
Write-Host "[EXECUTION] NOT RUN"
foreach($b in $blockers){Write-Host "[BLOCKER]" $b}
Write-Host "[REPORT]" $j
Write-Host "[REPORT]" $m
Write-Host "[OK] Scaffold created; no experiment, gate, strategy, or live-trading state was changed."
exit 0
