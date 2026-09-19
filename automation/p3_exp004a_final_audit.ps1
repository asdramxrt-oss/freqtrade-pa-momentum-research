$ErrorActionPreference="Stop"
# This file is installed at <project>\automation\.
$root=Split-Path -Parent $PSScriptRoot
$gate=Join-Path $root ".mece\PHASE_GATE.json"
if(!(Test-Path -LiteralPath $gate)){throw "Project root not found from: $root"}
$g=Get-Content -Raw -LiteralPath $gate|ConvertFrom-Json
function FindFile($name){
 Get-ChildItem -LiteralPath $root -Recurse -File -Filter $name -ErrorAction SilentlyContinue |
 ?{$_.FullName -notmatch "\\(\.git|\.venv|phase_runs)\\"}
}
function Rel($p){if($p){return $p.FullName.Substring($root.Length+1).Replace("\","/")}return "NOT FOUND"}
$strategy=FindFile "CrossSectionalMomentumResearch.py"
$config=FindFile "P3-EXP-004A.json"
$runner=FindFile "p3_exp004a_run.py"
$registry=Join-Path $root "docs\EXPERIMENT_REGISTRY.md"
$registered=$false
if(Test-Path $registry){$registered=(Get-Content -Raw -LiteralPath $registry)-match "P3-EXP-004A"}
$dataRoot=Join-Path $root "user_data\data"
$data=@()
if(Test-Path $dataRoot){
 $data=Get-ChildItem -LiteralPath $dataRoot -Recurse -File -ErrorAction SilentlyContinue |
  ?{$_.FullName -match "\\futures\\" -and $_.Extension -match "\.(feather|parquet|csv)$"}
}
$symbols=@($data|%{if($_.Name -match "^([^_]+)_USDT_USDT-"){$Matches[1]}}|Sort-Object -Unique)
$blockers=@()
if(!$g.allow_new_experiments -or $g.stop_after_phase_completion){$blockers+="Governance gate is closed; execution is prohibited."}
if(!$registered){$blockers+="P3-EXP-004A is not registered."}
if(!$strategy){$blockers+="004A strategy missing."}
if(!$config){$blockers+="004A config missing."}
if(!$runner){$blockers+="No P3-EXP-004A experiment execution runner is present."}
if($data.Count -eq 0){$blockers+="No futures data found."}
$out=Join-Path $root "phase_runs\p3_exp004a_readiness"
New-Item -ItemType Directory -Force -Path $out|Out-Null
$stamp=Get-Date -Format "yyyyMMdd_HHmmss"
$status=if($blockers.Count -eq 0){"READY"}else{"NOT_READY"}
$report=[ordered]@{timestamp=(Get-Date).ToString("o");status=$status;project_root=$root;phase=$g.phase;allow_new_experiments=[bool]$g.allow_new_experiments;stop_after_phase_completion=[bool]$g.stop_after_phase_completion;registered=$registered;strategy=Rel $strategy;config=Rel $config;experiment_runner=Rel $runner;futures_data_files=$data.Count;futures_symbols=$symbols;blockers=$blockers;execution="NOT_RUN";live_trading=$false;promotion=$false;gate_modified=$false}
$report|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $out "FINAL_AUDIT_$stamp.json") -Encoding UTF8
Write-Host "============================================================"
Write-Host "P3-EXP-004A FINAL PRE-EXECUTION AUDIT"
Write-Host "Codex=OFF Data Analysis=OFF Work=OFF Live Trading=OFF"
Write-Host "============================================================"
Write-Host "[ROOT]" $root
Write-Host "[STATUS]" $status
Write-Host "[PHASE]" $g.phase
Write-Host "[GATE] allow_new_experiments:" $g.allow_new_experiments
Write-Host "[GATE] stop_after_phase_completion:" $g.stop_after_phase_completion
Write-Host "[STRATEGY]" (Rel $strategy)
Write-Host "[CONFIG]" (Rel $config)
Write-Host "[FUTURES DATA FILES]" $data.Count
Write-Host "[FUTURES SYMBOLS]" ($symbols -join ", ")
Write-Host "[EXPERIMENT RUNNER]" (Rel $runner)
foreach($b in $blockers){Write-Host "[BLOCKER]" $b}
Write-Host "[EXECUTION] NOT RUN"
Write-Host "[LIVE TRADING] FALSE"
Write-Host "[PROMOTION] FALSE"
Write-Host "[GATE MODIFIED] FALSE"
Write-Host "AUDIT FINISHED."
exit 0
