# LESSONS - auto-maintained by scripts/lessons.py

> Machine-owned. Do NOT hand-edit. Changes are overwritten on the next `lessons.py` write.
> Canonical state lives in `.specs/lessons.json`. Edit lessons only via the script.
> promote_threshold=2 distinct features · window_days=45 · quarantine_threshold=2

## Confirmed (load these at Plan/Checks)

Corroborated across multiple features. Safe to apply as guidance.

_none_

## Candidates (under observation - do NOT load as guidance yet)

Seen once or not yet corroborated. Tracked, not trusted.

### L-001 - Write repository-state proofs against refs and facts that stay true after the step, never against a local branch ref or a one-time precondition
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `repo-setup` · harmful: 0
- features: agent-run-notify
- evidence: C30 checks.md:109; C25 checks.md:94 (repo-setup)
- last seen: 2026-10-21T00:07:45Z

### L-002 - Give every usage refusal an entry point has its own boundary test, not only the refusals the acceptance criteria name
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `cli-guards` · harmful: 0
- features: agent-run-notify
- evidence: src/grokbot_kit/run.py:49,54,57,63 (cli-guards)
- last seen: 2026-10-21T00:07:45Z

### L-003 - When a check names an open flag such as O_EXCL, assert the flag or a behaviour only that flag produces
- signal: `spec_precision_gap` · recurrence: 1 feature(s) · scope: `locking` · harmful: 0
- features: agent-run-notify
- evidence: C86 tests/test_redeliver.py:133 (locking)
- last seen: 2026-10-21T00:07:45Z

### L-004 - Quando um valor pode vir de duas fontes (PyPI e o --version do executável novo), o teste deve fazer as duas responderem valores diferentes, senão a fonte errada passa
- signal: `surviving_mutant` · recurrence: 1 feature(s) · scope: `update` · harmful: 0
- features: kit-update
- evidence: F3 src/grokbot_kit/update.py:286 (C22) (update)
- last seen: 2026-10-21T19:37:04Z

### L-005 - Ao contar os caminhos de saída de um ponto de entrada, conte também o except OSError de um subprocesso (executável ausente no PATH) e dê a ele uma prova
- signal: `ac_gap` · recurrence: 1 feature(s) · scope: `update` · harmful: 0
- features: kit-update
- evidence: src/grokbot_kit/update.py:280-281 (Test policy: ponto de entrada) (update)
- last seen: 2026-10-21T19:37:08Z

## Quarantined (failed when applied - ignore)

A confirmed lesson that recurred alongside failure. Kept for the maintainer to review.

_none_
