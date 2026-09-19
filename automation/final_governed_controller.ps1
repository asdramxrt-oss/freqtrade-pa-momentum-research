$ErrorActionPreference="Stop"
$root=Split-Path -Parent $PSScriptRoot
$gate=Join-Path $root ".mece\PHASE_GATE.json"
if(!(Test-Path $gate)){ throw "Gate file not found: $gate" }
$g=Get-Content -Raw $gate|ConvertFrom-Json
function Find($n){Get-ChildItem $root -Recurse -File -Filter $n -ErrorAction SilentlyContinue|?{$_.FullName -notmatch "\\(\.git|\.venv|phase_runs)\\"}}
function Rel($p){if($p){$p.FullName.Substring($root.Length+1).Replace("\","/")}else{"NOT FOUND"}}
$strategy=Find "CrossSectionalMomentumResearch.py"
$config=Find "P3-EXP-004A.json"
$runner=Find "p3_exp004a_run.py"
$registry=Join-Path $root "docs\EXPERIMENT_REGISTRY.md"
$registered=Test-Path $registry
if($registered){$registered=(Get-Content -Raw $registry)-match "P3-EXP-004A"}
$blockers=@()
if(!$g.allow_new_experiments -or $g.stop_after_phase_completion){$blockers+="Governance gate is closed for new experiments."}
if(!$registered){$blockers+="P3-EXP-004A is not registered."}
if(!$strategy){$blockers+="CrossSectionalMomentumResearch.py not found."}
if(!$config){$blockers+="P3-EXP-004A.json not found."}
if(!$runner){$blockers+="No P3-EXP-004A experiment execution runner is present."}
$out=Join-Path $root "phase_runs\final_governed_controller";New-Item -ItemType Directory -Force $out|Out-Null
$stamp=Get-Date -Format "yyyyMMdd_HHmmss"
@{timestamp=(Get-Date).ToString("o");project_root=$root;phase=$g.phase;allow_new_experiments=$g.allow_new_experiments;stop_after_phase_completion=$g.stop_after_phase_completion;strategy=Rel $strategy;config=Rel $config;experiment_runner=Rel $runner;registered=$registered;execution="NOT_RUN";live_trading=$false;promotion=$false;gate_modified=$false;blockers=$blockers}|ConvertTo-Json -Depth 5|Set-Content (Join-Path $out "FINAL_$stamp.json") -Encoding UTF8
Write-Host "============================================================"
Write-Host "FREQTRADE FINAL GOVERNED CONTROLLER"
Write-Host "Codex=OFF Data Analysis=OFF Work=OFF Live Trading=OFF"
Write-Host "============================================================"
Write-Host "[ROOT]" $root
Write-Host "[PHASE]" $g.phase
Write-Host "[GATE] allow_new_experiments:" $g.allow_new_experiments
Write-Host "[GATE] stop_after_phase_completion:" $g.stop_after_phase_completion
Write-Host "[STRATEGY]" (Rel $strategy)
Write-Host "[CONFIG]" (Rel $config)
Write-Host "[EXPERIMENT RUNNER]" (Rel $runner)
Write-Host "[REGISTRY] P3-EXP-004A:" $registered
Write-Host "[ACTION] WAIT"
foreach($b in $blockers){Write-Host "[BLOCKER]" $b}
Write-Host "[OK] No gate, strategy, configuration, or experiment execution was changed."
exit 0
