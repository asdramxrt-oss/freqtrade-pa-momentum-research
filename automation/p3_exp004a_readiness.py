import json, hashlib, sys, os, re
from datetime import datetime
from pathlib import Path

def find_root():
    p = Path(__file__).resolve()
    candidates = [p.parent] + list(p.parents)
    for base in candidates:
        if (base / ".mece" / "PHASE_GATE.json").is_file() and (base / "docs" / "EXPERIMENT_REGISTRY.md").is_file():
            return base
        try:
            for child in base.iterdir():
                if child.is_dir() and (child / ".mece" / "PHASE_GATE.json").is_file() and (child / "docs" / "EXPERIMENT_REGISTRY.md").is_file():
                    return child
        except OSError:
            pass
    raise RuntimeError("Project root not found.")

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b:
                return h.hexdigest()
            h.update(b)

def main():
    root = find_root()
    os.chdir(root)
    gate_path = root / ".mece" / "PHASE_GATE.json"
    registry_path = root / "docs" / "EXPERIMENT_REGISTRY.md"
    frozen_path = root / "docs" / "FROZEN_IMPLEMENTATION_SPEC.md"
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    registry = registry_path.read_text(encoding="utf-8", errors="replace")
    scripts = root / "user_data" / "scripts"
    runners = sorted(p.name for p in scripts.glob("p3_exp*.py")) if scripts.exists() else []
    exp004a = sorted(str(x.relative_to(root)) for x in root.rglob("*004a*") if x.is_file())
    frozen_sha = digest(frozen_path) if frozen_path.exists() else None

    state = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(root),
        "phase": gate.get("phase"),
        "allow_new_experiments": bool(gate.get("allow_new_experiments", False)),
        "stop_after_phase_completion": bool(gate.get("stop_after_phase_completion", True)),
        "p3_exp004a_registered": "P3-EXP-004A" in registry,
        "p3_runners": runners,
        "p3_exp004a_files": exp004a,
        "frozen_spec_sha256": frozen_sha,
        "codex": False,
        "chatgpt_data_analysis": False,
        "work": False,
        "live_trading": False,
        "promotion": False,
        "experiment_executed": False,
        "gate_modified": False,
        "action": "WAIT",
    }

    if state["allow_new_experiments"] and not state["stop_after_phase_completion"]:
        state["reason"] = "Gate is open, but no runner is automatically invented."
    else:
        state["reason"] = "Governance gate is closed; no experiment or later phase is executed."

    out = root / "phase_runs" / "p3_exp004a_readiness"
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    jp = out / f"READINESS_{stamp}.json"
    mp = out / f"READINESS_{stamp}.md"
    jp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    mp.write_text(
        "# P3-EXP-004A Readiness\n\n"
        f"- Phase: `{state['phase']}`\n"
        f"- allow_new_experiments: `{state['allow_new_experiments']}`\n"
        f"- stop_after_phase_completion: `{state['stop_after_phase_completion']}`\n"
        f"- P3-EXP-004A registered: `{state['p3_exp004a_registered']}`\n"
        f"- Runner files: `{', '.join(state['p3_runners']) or 'none'}`\n"
        f"- 004A-related files: `{', '.join(state['p3_exp004a_files']) or 'none'}`\n"
        f"- Frozen SHA256: `{state['frozen_spec_sha256']}`\n\n"
        "## Safety\n"
        "- No experiment executed.\n"
        "- No gate modified.\n"
        "- No strategy/config modified.\n"
        "- No package installed or upgraded.\n"
        "- Codex/Data Analysis/Work/live trading are not required.\n\n"
        f"## Action\n{state['action']} — {state['reason']}\n",
        encoding="utf-8"
    )
    print("="*62)
    print("P3-EXP-004A PERMANENT READINESS CHECK")
    print("Codex=OFF Data Analysis=OFF Work=OFF Live Trading=OFF")
    print("="*62)
    print("[ROOT]", root)
    print("[PHASE]", state["phase"])
    print("[GATE] allow_new_experiments:", state["allow_new_experiments"])
    print("[GATE] stop_after_phase_completion:", state["stop_after_phase_completion"])
    print("[004A] registered:", state["p3_exp004a_registered"])
    print("[004A] related files:", ", ".join(state["p3_exp004a_files"]) or "none")
    print("[ACTION]", state["action"])
    print("[REPORT]", mp)
    print("[OK] No gate or research logic was modified.")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print("[ERROR]", type(e).__name__ + ":", e)
        raise SystemExit(1)
