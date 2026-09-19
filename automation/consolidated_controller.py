import json, hashlib, os, sys, subprocess
from pathlib import Path
from datetime import datetime

def find_root():
    here=Path(__file__).resolve()
    for base in [here.parent]+list(here.parents):
        if (base/".mece/PHASE_GATE.json").is_file() and (base/"docs/EXPERIMENT_REGISTRY.md").is_file():
            return base
        try:
            for child in base.iterdir():
                if child.is_dir() and (child/".mece/PHASE_GATE.json").is_file() and (child/"docs/EXPERIMENT_REGISTRY.md").is_file():
                    return child
        except OSError:
            pass
    raise RuntimeError("Research project root not found.")

def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        while True:
            b=f.read(1024*1024)
            if not b: break
            h.update(b)
    return h.hexdigest()

def main():
    root=find_root()
    os.chdir(root)
    gate=json.loads((root/".mece/PHASE_GATE.json").read_text(encoding="utf-8"))
    reg=(root/"docs/EXPERIMENT_REGISTRY.md").read_text(encoding="utf-8",errors="replace")
    frozen=root/"docs/FROZEN_IMPLEMENTATION_SPEC.md"

    # Correct detection: exact filename, recursive, independent of 004A filename matching.
    strategy_matches=sorted(str(p.relative_to(root)).replace("\\","/")
        for p in root.rglob("CrossSectionalMomentumResearch.py") if p.is_file())
    config_matches=sorted(str(p.relative_to(root)).replace("\\","/")
        for p in root.rglob("P3-EXP-004A.json") if p.is_file())
    runner_matches=sorted(str(p.relative_to(root)).replace("\\","/")
        for p in root.rglob("*004a*.py") if p.is_file())
    spec_matches=sorted(str(p.relative_to(root)).replace("\\","/")
        for p in root.rglob("*EXP-004A*.md") if p.is_file())

    py=root/".venv/Scripts/python.exe"
    if not py.exists(): py=Path(sys.executable)
    def ver(mod):
        try:
            m=__import__(mod)
            return getattr(m,"__version__","imported")
        except Exception as e:
            return "ERROR: "+type(e).__name__+": "+str(e)
    pyver=subprocess.run([str(py),"--version"],capture_output=True,text=True).stdout.strip()

    state={
      "timestamp":datetime.now().isoformat(timespec="seconds"),
      "project_root":str(root),
      "phase":gate.get("phase"),
      "allow_new_experiments":bool(gate.get("allow_new_experiments",False)),
      "stop_after_phase_completion":bool(gate.get("stop_after_phase_completion",True)),
      "frozen_spec_sha256":sha256(frozen) if frozen.exists() else None,
      "p3_exp004a_registered":"P3-EXP-004A" in reg,
      "strategy_matches":strategy_matches,
      "config_matches":config_matches,
      "runner_matches":runner_matches,
      "spec_matches":spec_matches,
      "python":pyver,
      "freqtrade":ver("freqtrade"),
      "pydantic":ver("pydantic"),
      "codex":False,"chatgpt_data_analysis":False,"work":False,
      "live_trading":False,"promotion":False,
      "experiment_executed":False,"gate_modified":False,"action":"WAIT"
    }
    blockers=[]
    if not state["allow_new_experiments"] or state["stop_after_phase_completion"]:
        blockers.append("Governance gate is closed for new experiments.")
    if not state["p3_exp004a_registered"]: blockers.append("P3-EXP-004A is not registered.")
    if not strategy_matches: blockers.append("CrossSectionalMomentumResearch.py not found.")
    if not config_matches: blockers.append("P3-EXP-004A.json not found.")
    if not runner_matches: blockers.append("No P3-EXP-004A Python runner found.")
    if str(state["freqtrade"]).startswith("ERROR:"): blockers.append("Freqtrade import/version error.")
    if str(state["pydantic"]).startswith("ERROR:"): blockers.append("Pydantic import/version error.")
    state["blockers"]=blockers
    state["reason"]="; ".join(blockers) if blockers else "No readiness blocker detected."
    out=root/"phase_runs/p3_exp004a_readiness"; out.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
    (out/f"FIXED_READINESS_{stamp}.json").write_text(json.dumps(state,indent=2),encoding="utf-8")
    print("="*64)
    print("FREQTRADE FIXED CONSOLIDATED CONTROLLER")
    print("Codex=OFF Data Analysis=OFF Work=OFF Live Trading=OFF")
    print("="*64)
    print("[ROOT]",root)
    print("[PHASE]",state["phase"])
    print("[GATE] allow_new_experiments:",state["allow_new_experiments"])
    print("[GATE] stop_after_phase_completion:",state["stop_after_phase_completion"])
    print("[STRATEGY]",", ".join(strategy_matches) if strategy_matches else "NOT FOUND")
    print("[CONFIG]",", ".join(config_matches) if config_matches else "NOT FOUND")
    print("[RUNNER]",", ".join(runner_matches) if runner_matches else "NOT FOUND")
    print("[SPEC]",", ".join(spec_matches) if spec_matches else "NOT FOUND")
    print("[PYTHON]",pyver)
    print("[FREQTRADE]",state["freqtrade"])
    print("[PYDANTIC]",state["pydantic"])
    print("[ACTION]",state["action"])
    for b in blockers: print("[BLOCKER]",b)
    print("[OK] No gate, research logic, dependency, or experiment execution was changed.")
    return 0

if __name__=="__main__":
    try: raise SystemExit(main())
    except Exception as e:
        print("[ERROR]",type(e).__name__+":",e)
        raise SystemExit(1)
