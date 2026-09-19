<#
.SYNOPSIS
    One-click Phase-2 automation bridge.

.DESCRIPTION
    Resolves the research interpreter (PA_BRIDGE_PYTHON, then py -3.12, then
    python), makes freqtrade importable via FREQTRADE_SRC, and runs
    `python -m automation.bridge`.

    The bridge is research-only. By default it validates the repository, writes a
    derived REPORT.md and a next-task PROPOSAL. The CrewAI stage, real analysis
    and OpenCode are opt-in via -WithCrew / -RunAnalysis / -WithOpenCode. It
    never commits, merges or pushes, and it never executes a new experiment
    while the phase gate forbids it.

.PARAMETER RunId
    Stable run identifier (used for the report filename and transcripts). Must
    match [A-Za-z0-9._-] and must not be a dot path segment.

.PARAMETER WithCrew
    Run the CrewAI orchestration stage. Requires the optional 'bridge' extra;
    without it the stage is skipped and the deterministic pipeline still runs.

.PARAMETER RunAnalysis
    Execute the local diagnostic scripts. These may rewrite tracked JSON, so the
    bridge aborts if tracked results change.

.PARAMETER IncludeExperiments
    Also run experiment-class runners. Requires an open phase gate.

.PARAMETER WithOpenCode
    Invoke the OpenCode CLI non-interactively (read-only advisory prompt).

.PARAMETER Force
    Overwrite an existing .mece/NEXT_TASK.md proposal.

.PARAMETER DryRun
    Print the plan and write nothing.

.PARAMETER Json
    Emit the summary as JSON.

.EXAMPLE
    ./run_bridge.ps1

.EXAMPLE
    ./run_bridge.ps1 -WithCrew

.EXAMPLE
    ./run_bridge.ps1 -RunAnalysis -WithOpenCode -Json

.EXAMPLE
    ./run_bridge.ps1 -DryRun
#>
[CmdletBinding()]
param(
    [string]$RunId = "phase2_bridge",
    [switch]$WithCrew,
    [switch]$RunAnalysis,
    [switch]$IncludeExperiments,
    [switch]$WithOpenCode,
    [switch]$Force,
    [switch]$DryRun,
    [switch]$Json
)

$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot ".")).Path

if (-not $env:FREQTRADE_SRC) {
    $env:FREQTRADE_SRC = "C:\Users\rahul\Downloads\freqtrade-develop\freqtrade-develop"
}
if ($env:FREQTRADE_SRC -and -not $env:PYTHONPATH) {
    $env:PYTHONPATH = $env:FREQTRADE_SRC
}

$interpreter = $null
if ($env:PA_BRIDGE_PYTHON) {
    $interpreter = $env:PA_BRIDGE_PYTHON
}
elseif (Get-Command "py" -ErrorAction SilentlyContinue) {
    $probe = & py -3.12 -c "import sys; print(sys.executable)" 2>$null
    if ($LASTEXITCODE -eq 0 -and $probe) {
        $interpreter = $probe.Trim()
    }
}
if (-not $interpreter) {
    $interpreter = "python"
}

$bridgeArgs = @("-m", "automation.bridge", "--root", $ProjectRoot, "--run-id", $RunId)
if ($WithCrew) { $bridgeArgs += "--with-crew" }
if ($RunAnalysis) { $bridgeArgs += "--run-analysis" }
if ($IncludeExperiments) { $bridgeArgs += "--include-experiments" }
if ($WithOpenCode) { $bridgeArgs += "--with-opencode" }
if ($Force) { $bridgeArgs += "--force" }
if ($DryRun) { $bridgeArgs += "--dry-run" }
if ($Json) { $bridgeArgs += "--json" }

Write-Host "Bridge interpreter: $interpreter" -ForegroundColor DarkGray
Write-Host "Project root      : $ProjectRoot" -ForegroundColor DarkGray

Push-Location $ProjectRoot
try {
    & $interpreter @bridgeArgs
    $exitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}

exit $exitCode
