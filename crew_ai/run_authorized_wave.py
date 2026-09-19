from __future__ import annotations
import argparse, json, os, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    args = ap.parse_args()
    root = Path(args.root)
    gate = root / ".mece" / "PHASE_GATE.json"
    if not gate.exists():
        print("[CREWAI] BLOCKED: gate missing")
        return 2

    g = json.loads(gate.read_text(encoding="utf-8"))
    if not (g.get("allow_new_experiments") is True and
            g.get("stop_after_phase_completion") is False):
        print("[CREWAI] WAIT: governance gate closed")
        return 0

    # CrewAI is an orchestration boundary. It does not itself decide whether
    # an experiment is authorized. It launches the OpenCode task only after
    # the same fail-closed gate check above.
    packet = root / "crew_ai" / "TASK_PACKET.json"
    packet.write_text(json.dumps({
        "phase": g.get("phase"),
        "task": "Execute only the explicitly authorized preregistered research work.",
        "constraints": {
            "no_live_trading": True,
            "no_auto_promotion": True,
            "no_gate_modification": True,
            "no_parameter_search_unless_explicitly_authorized": True
        },
        "created_utc": datetime.now(timezone.utc).isoformat()
    }, indent=2), encoding="utf-8")

    opencode = os.environ.get("OPENCODE_CMD", "opencode")
    prompt = (
        f"Work only inside {root}. Read .mece/PHASE_GATE.json and frozen methodology. "
        "Execute only the authorized preregistered task represented by crew_ai/TASK_PACKET.json. "
        "Do not modify the governance gate. Do not enable live trading or promotion. "
        "Run tests and record artifacts. Stop when the authorized task is complete."
    )
    print("[CREWAI] Dispatching authorized coding wave to OpenCode.")
    p = subprocess.run([opencode, prompt], cwd=root)
    return p.returncode

if __name__ == "__main__":
    raise SystemExit(main())
