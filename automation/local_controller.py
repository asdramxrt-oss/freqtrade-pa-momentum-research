import json, hashlib, subprocess, sys
from datetime import datetime
from pathlib import Path

GATE_REL = Path(".mece/PHASE_GATE.json")
REG_REL = Path("docs/EXPERIMENT_REGISTRY.md")
FROZEN_REL = Path("docs/FROZEN_IMPLEMENTATION_SPEC.md")

def find_root():
    starts = [Path(__file__).resolve().parent]
    starts += list(Path(__file__).resolve().parents)
    for start in starts:
        if (start / GATE_REL).is_file() and (start / REG_REL).is_file():
            return start
        try:
            for child in start.iterdir():
                if child.is_dir() and (child / GATE_REL).is_file() and (child / REG_REL).is_file():
                    return child
        except OSError:
            pass
    raise RuntimeError("Research project not found.")

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def main():
    root = find_root()
    gate_path = root / GATE_REL
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    phase = gate.get("phase")
    allow = bool(gate.get("allow_new_experiments", False))
    stop = bool(gate.get("stop_after_phase_completion", True))
    frozen = root / FROZEN_REL
    frozen_sha = sha256(frozen) if frozen.exists() else None
    scripts_dir = root / "user_data" / "scripts"
    runners = sorted(p.name for p in scripts_dir.glob("p3_exp*.py")) if scripts_dir.exists() else []
    registry = (root / REG_REL).read_text(encoding="utf-8", errors="replace")
    registered_004a = "P3-EXP-004A" in registry
    runner_004a = any("004a" in x.lower() for x in runners)

    state = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(root),
        "codex": False,
        "chatgpt_data_analysis": False,
        "work": False,
        "live_trading": False,
        "promotion": False,
        "phase": phase,
        "allow_new_experiments": allow,
        "stop_after_phase_completion": stop,
        "frozen_spec_sha256": frozen_sha,
        "p3_runners": runners,
        "p3_exp004a_registered": registered_004a,
        "p3_exp004a_runner_present": runner_004a,
        "action": "WAIT",
        "executed": [],
        "reason": "Governance gate is closed. No experiment or later phase was executed."
    }

    print("=" * 62)
    print("FREQTRADE PERMANENT LOCAL CONTROLLER")
    print("Codex=OFF Data Analysis=OFF Work=OFF Live Trading=OFF")
    print("=" * 62)
    print("[ROOT]", root)
    print("[PHASE]", phase)
    print("[GATE] allow_new_experiments:", allow)
    print("[GATE] stop_after_phase_completion:", stop)
    print("[FROZEN SHA256]", frozen_sha)
    print("[P3 RUNNERS]", ", ".join(runners) if runners else "none")
    print("[P3-EXP-004A] registered:", registered_004a)
    print("[P3-EXP-004A] runner:", "present" if runner_004a else "missing")

    # Fail closed. This controller is intentionally not an experiment runner.
    if phase == "PHASE2":
        bridge = root / "automation" / "bridge.py"
        if bridge.exists():
            print("[ACTION] Phase 2 governance remains active.")
            print("[ACTION] Existing governed bridge can be used by the project.")
            state["action"] = "WAIT"
        else:
            print("[ACTION] WAIT - no bridge found.")
    elif phase == "PHASE3" and allow and not stop:
        print("[ACTION] Gate is open, but this controller will not invent a runner.")
        state["action"] = "WAIT"
        state["reason"] = "No newly invented experiment execution is permitted."
    else:
        print("[ACTION] WAIT - governance gate forbids new experiments.")

    out = root / "phase_runs" / "autonomous_controller"
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = out / f"PERMANENT_CONTROLLER_{stamp}.json"
    report.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print("[STATE]", report)
    print("[OK] No gate or research logic was modified.")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print("[ERROR]", type(e).__name__ + ":", e)
        raise SystemExit(1)
