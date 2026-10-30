# Version 2 execution notes — 30 October 2026 (Kuala Lumpur)

- All 18 cases were exported before independent replays from the frozen v2 corpus.
- Each replay requested a fresh gpt-6.1-sol Codex agent, fork_turns=none, with only
  its own instructions/input and a record output path. No expected answers were sent.
- Two early replay attempts (cases 02 and 03 in replay order) returned temporary
  capacity errors before a usable response. Retrying the same inputs succeeded.
  They are infrastructure failures, not additional scored model decisions.
- Actual per-case records were imported without changing report prose; only the
  neutral case ID was mapped back. No raw provider or full tool-call trace is claimed.
- First expanded control-test run failed to import `export` from prepare_replay;
  the function is named `prepare`. The test import was fixed; all 22 tests pass.
- First source recollection failed on attack-tool's diff final newline. Four v2 diff
  strings omit it. Collector comparison now normalizes trailing newline characters
  only, retaining frozen file bytes. Formula and guidance text remain exact.
- No Claude Code executable or provider credential was available. npm registry
  lookup failed with EPERM through the session proxy. Installation and inference
  were not performed. CLI command wiring uses a clearly identified subprocess stub.
- Current score: 18 valid reports, 17 category agreements, baseline 16, 18 human
  adjudications pending. tgenv-before remains the sole category disagreement.
