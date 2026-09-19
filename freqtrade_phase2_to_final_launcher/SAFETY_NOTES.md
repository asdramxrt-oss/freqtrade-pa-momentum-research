# Safety Notes

1. `.mece/PHASE_GATE.json` is authoritative.
2. Closed experiment gates are never bypassed.
3. `--force` is never used by this package.
4. Experiment execution flags are not automatically injected.
5. Phase names are detected from MECE state rather than hard-coded.
6. A later phase is not considered approved merely because an earlier phase
   finished.
7. The package relies on the repository bridge for production-tree and
   artifact validation.
8. Repeated bridge failures cause a stop rather than an uncontrolled loop.
9. Continuous mode only repeats the same safe bridge invocation.
10. A human/governance transition is still required where the repository
    requires one.

For unattended research, keep credentials, API keys, and exchange settings
outside this package.
