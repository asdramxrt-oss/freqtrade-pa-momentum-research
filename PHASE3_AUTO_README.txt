PHASE 3 / P3-EXP-004A COMPLETE AUTOMATION

Installed components:
- automation\phase3_auto_controller.ps1
- user_data\scripts\p3_exp004a_run.py
- RUN_PHASE3_AUTO.bat
- INSTALL_PHASE3_AUTO_SCHEDULED.bat

Safety:
- Codex OFF
- ChatGPT Data Analysis OFF
- Work OFF
- Live trading OFF
- Promotion OFF
- The controller never opens or modifies the governance gate.
- The runner executes only when allow_new_experiments=true AND
  stop_after_phase_completion=false.
- While the current PHASE2 gate is closed, the controller returns WAIT.
- The 004A runner performs one preregistered cross-sectional momentum
  backtest using the fixed 10-pair universe, 4h timeframe and 30-day
  ranking definition in the frozen implementation spec.
- No parameter search is performed.
- Results are written under phase_runs\p3_exp004a and are not promoted.

IMPORTANT:
The repository currently records P3-EXP-004A as not yet backtested and
the governance gate is currently closed. Therefore installation does not
execute the experiment.

Optional:
Run INSTALL_PHASE3_AUTO_SCHEDULED.bat once if you want Windows Task Scheduler
to invoke the controller hourly. It will continue to WAIT until governance
explicitly authorizes new experiments.
