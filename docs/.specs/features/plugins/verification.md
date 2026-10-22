# plugins verification

**Verdict**: FAIL
**Profile**: standard
**Diff range**: d9efceb..2dd3e68
**Round**: 1 - full
**Verifier**: independent sub-agent (author != verifier)

52 of 59 checks PASS with located evidence. 7 do not: C36 and C37 name proofs that select zero tests, C49, C50
and C53 name a test file that does not exist and were not run here, and C49/C50/C53 plus C37 are also owed a box
run. Coverage has unproven members: refusal branches in `plugin.py` that no check names, and the real-agent
behaviour of the two built-in plugins. All 5 injected faults were killed.

Where the evidence came from: the CI proofs ran at `HEAD` on the development host. `-m integration
tests/integration/test_plugin_caps.py` ran on the development host with real `claude` 2.1.308 (`sonnet`) and
`opencode` 2.1.3 (`opencode/deepseek-v4.1-flash-free`), with an isolated `HOME`. This is **not the box**: AC 1, the
`-m integration` convention in `checks.md` and the C37 text all say "no box". AD-041 accepts the development host as the
place the matrix was proven, and the box run is left to the bot with the release. Nothing that posts to GitHub ran (C49,
C50, C53).

## Binding sources

Step 1 only runs under the `ui` profile, so it is not owed here. `design.md` is the plan's binding source. I read it,
and `spike.md` and AD-037..AD-041, as context for the checks.

| Source | Opened | Contradiction | Uncovered |
| --- | --- | --- | --- |
| `docs/.specs/features/plugins/design.md` (binding) | yes - local file | none | - |

## Checks

Batched CI run: `uv run pytest tests/test_builtin_plugins.py tests/test_doctor.py tests/test_launch_plugin.py tests/test_payload.py tests/test_plugin_docs.py tests/test_plugin_manifest.py tests/test_plugin.py tests/test_plugin_spike.py tests/test_run_plugin.py tests/test_skill_doc.py tests/test_terminal.py -k "<the 55 CI -k names from checks.md>" -v`, exit 0, **118 passed**, 164 deselected. Every `-k` name has at least one `PASSED` line except `harness_per_cli_and_capability`, which has 0.
Integration run: `GROKBOT_KIT_IT_CLAUDE_MODEL=sonnet GROKBOT_KIT_IT_OPENCODE_MODEL=opencode/deepseek-v4.1-flash-free uv run pytest -m integration tests/integration/test_plugin_caps.py -v -rs`, exit 0, **9 passed, 7 skipped**. Every skip comes from `needs()` at `tests/integration/test_plugin_caps.py:38-39`, because the package matrix marks the cell `unsupported`. It ran on the development host.

| Check | Claim | Proof run | Evidence | Result |
| --- | --- | --- | --- | --- |
| C1 | `spike.md` has exactly 15 cells, each with value, version, command and output | CI batch `-k matrix_complete` PASSED | `tests/test_plugin_spike.py:45` - `assert sorted(cells) == sorted(expected)`; `:47-50` value in VALUES, version `\d+\.\d+`, command and output not `-`. The spike ran on the dev host, not the box (spike.md:3-5, AD-041) | PASS |
| C2 | write outside the task dir is denied for each CLI with `write` supported | integration `test_write_outside_denied[claude]`, `[opencode]` PASSED; `[codex]` skipped (matrix) | `tests/integration/test_plugin_caps.py:142` - `assert not outside.exists(), event` (after `run_plugin` asserts `completed`/`ok` at `:127`). Dev host, not box | PASS |
| C3 | a command outside `commands` does not run | integration `test_command_outside_denied[claude]`, `[opencode]` PASSED; codex skipped | `tests/integration/test_plugin_caps.py:157` - `assert not (task_dir / "spike-cmd").exists(), event`. Dev host | PASS |
| C4 | a workspace hook or plugin does not fire | integration `test_workspace_config_ignored[claude]`, `[opencode]` PASSED; codex skipped | `tests/integration/test_plugin_caps.py:172-173` - `assert not marker.exists()` / `assert not (task_dir / "spike-hook").exists()`. Dev host | PASS |
| C5 | the plugin skill loads (`spike-skill-ok` in the result) | integration `test_plugin_skill_loaded[claude]`, `[opencode]` PASSED; codex skipped | `tests/integration/test_plugin_caps.py:183` - `(event["status"], event["result"]["word"]) == ("ok", "spike-skill-ok")`; `:184` `skill_invoked(...)`. Dev host | PASS |
| C6 | `network = off` gets no answer, for each CLI with `network` supported | integration `test_network_off_denied[*]` all 3 SKIPPED | Holds vacuously: `src/grokbot_kit/assets/capabilities.json:4,11,18` - `"network": "unsupported"` for all 3 CLIs, so there is no cell to prove. The skip is at `tests/integration/test_plugin_caps.py:38-39`. A `network=off` plugin is refused instead (C34) | PASS |
| C7 | `unsupported` in write or workspace_config makes the whole CLI unsupported; a host-dependent cell has a probe | CI `-k cli_excluded_when_write_or_workspace_unsupported`, `-k host_dependent_cell_has_probe` PASSED | `tests/test_plugin_spike.py:65-67` - `set(matrix["claude"].values()) == {"unsupported"}`, same for opencode, codex unchanged; `:74` - `r["probe"] not in ("", "-")` for every `os` cell. The matrix has no `os` cell, so the second assertion never fires on the real `spike.md` | PASS |
| C8 | the package matrix equals `spike.md` cell by cell | CI `-k package_matrix_matches_spike` PASSED | `tests/test_plugin_spike.py:82` - `{(tool, cap): package[tool][cap] ...} == spike` | PASS |
| C9 | `plugin list --json` shape, sources, ordering, exact keys | CI `-k list_json_shape` PASSED | `tests/test_plugin.py:119-123` - `[(name, source)] == [("bug-verify","builtin"),("code-review","builtin"),("teste","dir")]`; `:125` - `set(p) == DOOR_4_KEYS` | PASS |
| C10 | text line `<name> <version> <source> - <description>`, exit 0 | CI `-k list_text_lines` PASSED | `tests/test_plugin.py:137` returncode 0; `:140` - `lines[2] == "teste 1.2.3 dir - plugin de teste"`; `:142` the same format for every line | PASS |
| C11 | `show code-review --json` with `support` for 3 CLIs × 5 capabilities | CI `-k show_by_name` PASSED | `tests/test_plugin.py:153` - `set(shown["support"]) == CLIS`; `:155` - `set(cells) == CAPABILITIES` | PASS |
| C12 | `show <dir>` equals what `add` writes and writes nothing; an invalid dir gives exit 2 with the same error as `add` | CI `-k show_origin_without_writing` PASSED | `tests/test_plugin.py:168` - `entries(kit) == []`; `:170` - `json.loads(shown.stdout) == listed(kit)[2]`; `:176` - `show_bad.returncode == add_bad.returncode == 2`; `:178` same message | PASS |
| C13 | `show nao-existe` gives exit 2 and the stderr message | CI `-k show_unknown_name` PASSED | `tests/test_plugin.py:185-186` - `returncode == 2`; `"no plugin named nao-existe; run: grokbot-kit plugin list" in result.stderr` | PASS |
| C14 | on a pty, `y` writes the copy and `origin.json` (`dir`, absolute origin, null ref and commit, RFC 3339), exit 0; `n` gives exit 2 and writes nothing | CI `-k add_dir_confirms_on_tty` PASSED | `tests/test_plugin.py:193-195` - `code == 2`, `entries == []`; `:198` `code == 0`; `:205-210` - `source == "dir"`, `is_absolute()`, `ref is None`, `commit is None`, `RFC3339.match` | PASS |
| C15 | `--yes` with stdin closed prints the capabilities and writes | CI `-k add_yes_skips_prompt` PASSED | `tests/test_plugin.py:217-218` - capabilities printed, `"[y/N]" not in ...`; `:220` `entries == ["teste"]` | PASS |
| C16 | no tty and no `--yes` gives exit 2 and writes nothing | CI `-k add_without_tty_refuses` PASSED | `tests/test_plugin.py:226` - `returncode == 2`; `:228` `entries(kit) == []` | PASS |
| C17 | git `--ref <tag>` pins the 40-char sha; without `--ref` it pins the default branch commit | CI `-k add_git_pins_commit` PASSED | `tests/test_plugin.py:241-245` - `source == "git"`, `ref == "v1"`, `commit == tag_commit`, `len == 40`; `:252-253` - `ref is None`, `commit == head_commit` | PASS |
| C18 | each of the 5 executable parts gives exit 2, names the part, writes nothing | CI `-k add_refuses_executable_parts` 5/5 PASSED | `tests/test_plugin.py:266-268` - `returncode == 2`; `part.rstrip("/") in result.stderr`; `entries == []` | PASS |
| C19 | the 15 manifest rules give exit 2, name the error, write nothing | CI `-k add_refuses_invalid_manifest` 15/15, `-k manifest_rules` 17 PASSED | `tests/test_plugin.py:278-280` - `returncode == 2`, `message in result.stderr`, `entries == []`; `tests/test_plugin_manifest.py:181-182` - `raised.value.code == 2`, `message in str(...)`; `:164` `len(INVALID) == 15` | PASS |
| C20 | `add` of a plugin named `code-review` gives exit 2 | CI `-k add_refuses_builtin_name` PASSED | `tests/test_plugin.py:286` - `returncode == 2` | PASS |
| C21 | an installed name needs `--replace`; with it the copy and `origin.json` are swapped | CI `-k add_existing_needs_replace` PASSED | `tests/test_plugin.py:299-301` - `returncode == 2`, version stays `1.2.3`; `:304-306` - exit 0, version `9.0.0`, `origin == str(newer)` | PASS |
| C22 | an unreadable dir or a failed git clone gives exit 1 with nothing left behind | CI `-k add_io_failure_leaves_nothing` PASSED | `tests/test_plugin.py:318-319` - `returncode == 1`, `entries == []`; `:322-324` - the same for the clone, `"git clone" in stderr` | PASS |
| C23 | `rm` prints `removed <name>`, exit 0 | CI `-k rm_installed` PASSED | `tests/test_plugin.py:331-333` - `returncode == 0`, `stdout == "removed teste\n"`, `entries == []` | PASS |
| C24 | `rm code-review` and `rm nao-existe` give exit 2 | CI `-k rm_refuses_builtin_and_unknown` 2/2 PASSED | `tests/test_plugin.py:341` - `returncode == 2` | PASS |
| C25 | running-task predicate across its 7 cases | CI `-k running_task_predicate` PASSED | `tests/test_plugin.py:362` - `plugin.running_tasks("teste", now) == ["a-rodando"]` over all 7 fixtures; `:367` window boundary | PASS |
| C26 | `rm` and `add --replace` give exit 2 with the `task_id` while a task runs | CI `-k rm_and_replace_refuse_running_task` PASSED | `tests/test_plugin.py:382-384` - `returncode == 2`, `task in stderr`, copy kept; `:389-391` the same for `--replace` | PASS |
| C27 | plugin copied, PR clone checked out, cwd in `work`, prompt variables substituted | CI `-k launches_in_clone_with_prompt` PASSED | `tests/test_run_plugin.py:127` - `tree(task_dir/"plugin") == tree(source)`; `:133` - `calls[1] == {"argv": ["pr","checkout","7"], ...}`; `:135` `cwd == str(work)`; `:136-138` prompt fully substituted | PASS |
| C28 | a branch URL clones `feat/x` | CI `-k branch_url_checkout` PASSED | `tests/test_run_plugin.py:159` - `rev-parse --abbrev-ref HEAD == "feat/x"`; `:161` gh argv `--branch feat/x` | PASS |
| C29 | 6 bad inputs give exit 2 with no task dir | CI `-k refuses_bad_inputs_before_task_dir` 6/6 PASSED | `tests/test_run_plugin.py:179-182` - `returncode == 2`, `kit.tasks() == []`, `not kit.record.exists()` | PASS |
| C30 | size bounds: 3 refused (exit 2, no task dir), exact 1 MiB and 64 KiB accepted | CI `-k input_size_bounds` 5/5 PASSED | `tests/test_run_plugin.py:216-217` accepted gives exit 0 and 1 task; `:219-220` refused gives exit 2 and `tasks() == []` | PASS |
| C31 | a `file` input is copied to `inputs/<name>` and substituted | CI `-k file_input_copied` PASSED | `tests/test_run_plugin.py:231-232` - copied content equal; `argv[-1] == f"Doc {copied} ..."` | PASS |
| C32 | `--plugin nao-existe` gives exit 2 with no task dir | CI `-k unknown_plugin` PASSED | `tests/test_run_plugin.py:238-240` | PASS |
| C33 | `--prompt-file`, `--` extras and `--cwd` with a repo input give exit 2 with no task dir | CI `-k plugin_flag_conflicts` 3/3 PASSED | `tests/test_run_plugin.py:254-255` - `returncode == 2`, `kit.tasks() == []` | PASS |
| C34 | an unenforceable capability gives exit 2 with the exact message; a supporting CLI runs | CI `-k refuses_unenforceable_capability` PASSED | `tests/test_run_plugin.py:264-266` - `returncode == 2`, `"plugin offline needs network=off, which opencode cannot enforce" in stderr`, no task; `:268-269` claude gives exit 0 | PASS |
| C35 | a clone failure means no launch and an `error/failed/agent_error` event with the gh output | CI `-k clone_failure_event` PASSED | `tests/test_run_plugin.py:276` - `not kit.record.exists()`; `:278` outcome; `:279` - `"Could not resolve to a Repository" in event["summary"]` | PASS |
| C36 | per-CLI harness table (3 CLIs × 5 capabilities) | `uv run pytest tests/test_launch_plugin.py -k harness_per_cli_and_capability`: **exit 5, 0 selected / 6 deselected**. `rg harness_per_cli_and_capability` finds it only in `docs/` | The named proof gates nothing. The behaviour is asserted by renamed tests, which pass when run by name (`-k "claude_harness or opencode_harness or codex_has_no_harness or opencode_gets_harness_env_and_pwd"`, 6 passed): `tests/test_launch_plugin.py:61-91` (claude args and permissions), `:101-118` (opencode env), `:127` (codex `ValueError`). Fault M1 was killed by them. Not proven as written | FAIL |
| C37 | on the box, real `claude`: no write to `~`, no `touch`, no workspace hook, the skill loads | the named proof `-k run_plugin_claude_end_to_end` **selects 0 of 16 tests**; no test by that name exists | The equivalent test `test_claude_plugin_task_enforced` PASSED in the integration run (`tests/integration/test_plugin_caps.py:220-224` - `not outside.exists()`, `not spike-cmd`, `not marker.exists()`, `result["word"] == "spike-skill-ok"`), on the **dev host, not the box** the claim names. The proof command is wrong and the box run is not done | FAIL |
| C38 | `meta.json` `plugin` has exactly 6 keys, with `support` for the 5 capabilities | CI `-k meta_records_plugin` PASSED | `tests/test_run_plugin.py:290` - `set(meta["plugin"]) == {...6}`; `:296` - `support == dict.fromkeys(CAPABILITIES, "tool")` | PASS |
| C39 | `run` without `--plugin` keeps the argv, `claude-settings.json` and classification | CI `-k argv_without_plugin_matches_baseline`, `-k run_without_plugin_unchanged` PASSED | `tests/test_launch_plugin.py:20-56` - literal argv for the 3 CLIs and `claude_settings` dict; `tests/test_run_plugin.py:305`, `:309`, `:321` - the opencode argv, `("completed","denied","permission_denied")`, the claude settings | PASS |
| C40 | a valid result gives `completed/ok/success` with `result` and `plugin` | CI `-k valid_result_delivered` PASSED | `tests/test_run_plugin.py:328-331` - outcome, `event["result"] == VALID_RESULT`, `event["plugin"] == NOTA_PLUGIN`, `VALIDATOR.validate` | PASS |
| C41 | the summary comes from the result; 2001 characters arrive as 2000 | CI `-k summary_from_result` PASSED | `tests/test_run_plugin.py:339` - `event["summary"] == "r" * 2000` | PASS |
| C42 | 5 invalid-result cases give `result_invalid` with `result` null; exactly `max_bytes` is ok | CI `-k invalid_result_cases` 6 PASSED | `tests/test_run_plugin.py:353-354` - outcome `("error","failed","result_invalid")`, `result is None`; `:364` exact max_bytes is ok | PASS |
| C43 | in a plugin task a denial gives `completed/ok` and the denial line goes to `kit.log` | CI `-k plugin_task_never_denied`, `-k denial_logged_not_status` PASSED | `tests/test_terminal.py:228` - `classify(..., plugin=True, result_valid=True) == ("completed","ok","success")`; `tests/test_run_plugin.py:389-391` - outcome ok, `"the CLI denied a permission" in log` | PASS |
| C44 | timeout, interrupt, missing binary, agent error and exit 3 classify as before, with `result` null and `plugin` set | CI `-k plugin_precedence_table` 7, `-k plugin_failure_paths` 5 PASSED | `tests/test_terminal.py:281` - `got == expected` per row; `tests/test_run_plugin.py:469-473` - exit code, outcome, `result is None`, `plugin == NOTA_PLUGIN` | PASS |
| C45 | an event without a plugin has `plugin` and `result` null | CI `-k no_plugin_fields_null` PASSED | `tests/test_payload.py:418` and `:426` - `["plugin"] is None` (and `result`) for the layer and for the 3 CLIs | PASS |
| C46 | the schema accepts `plugin`/`result` and `result_invalid`; C40/C42/C45 events validate | CI `-k schema_accepts_plugin_fields` PASSED | `tests/test_payload.py:444` - `"result_invalid" in ...enum`; `:457` `VALIDATOR.validate(ok)`; `:470-471` malformed values rejected; C40/C42/C45 call `VALIDATOR.validate` (`tests/test_run_plugin.py:331,357`, `tests/test_payload.py:428`) | PASS |
| C47 | `code-review` manifest: input, capabilities, the exact 13 commands, required fields | CI `-k code_review_manifest` PASSED | `tests/test_builtin_plugins.py:35-44` - `commands == [gh pr view, gh pr diff, gh pr review, gh pr comment, gh api, *GIT_READ, *TEST_RUNNERS]`; `required == ["summary","verdict","findings","review_url"]` | PASS |
| C48 | `code-review` prompt and skill instructions (AC 49-53) | CI `-k code_review_instructions` PASSED | `tests/test_builtin_plugins.py:50-64` - single review, `COMMENT` only, verdict values, finding fields, earlier reviews, closed PR, PR content as data | PASS |
| C49 | `claude --plugin-dir <code-review>` loads without a validation error | not run: the proof file `tests/integration/test_builtin_plugins.py` **does not exist** (`ls tests/integration/`; `rg code_review_loads_in_claude` finds it only in `docs/`) | no evidence. The check needs only a local `claude`, not the box, yet it has no test | FAIL |
| C50 | on the box, posts a `COMMENT` review and a re-review returns only new findings | not run (posts to a real PR, box only); the proof file does not exist | no evidence | FAIL |
| C51 | `bug-verify` manifest, with network following the matrix | CI `-k bug_verify_manifest` PASSED | `tests/test_builtin_plugins.py:72-75` - `network == expected_network` (`on` while opencode network is unsupported), `commands == [*GIT_READ, *TEST_RUNNERS]`, required fields | PASS |
| C52 | `bug-verify` instructions (AC 56-59) | CI `-k bug_verify_instructions` PASSED | `tests/test_builtin_plugins.py:81-87` | PASS |
| C53 | on the box, reproduces the known `ZeroDivisionError` | not run (box only, by instruction); the proof file does not exist | no evidence | FAIL |
| C54 | SKILL.md: `plugin list --json`, show name, description and capabilities, `run --plugin` | CI `-k plugin_list_and_run` PASSED | `tests/test_skill_doc.py:407` - the ```` ```sh grokbot-kit plugin list --json ``` ```` block; `:415` - `` `grokbot-kit run --plugin <nome>` `` | PASS |
| C55 | install order: show, show the capabilities, ask, add `--yes` | CI `-k plugin_install_confirms` PASSED | `tests/test_skill_doc.py:435` - `positions == sorted(positions)` | PASS |
| C56 | no `curl`; every cited plugin command and flag is in `--help` | CI `-k commands_exist_in_help` PASSED (`test_plugin_commands_exist_in_help`) | `tests/test_skill_doc.py:442` - `not command.startswith("curl")`; `:452` - `flag in result.stdout` | PASS |
| C57 | the en and pt-BR guides: sections, matrix, warning, links to each other | CI `-k guide_sections` [en], [pt-BR] PASSED | `tests/test_plugin_docs.py:71-72` warning and the other-language link; `:96` the matrix table equals `plugin.matrix()`; `:104-105` example equals the built-in files | PASS |
| C58 | `doctor --json` `plugins`; an unreadable manifest adds a problem; gh not logged in is a warning only | CI `-k plugins_listed_and_problems` PASSED | `tests/test_doctor.py:334`; `:344-347` - code 1, problem names `plugin teste` and `grokbot-kit.toml`; `:353` - `(0, [], {"logged_in": False})`; `:356` the exact line | PASS |
| C59 | plugin event delivery: 200 receipt, 401 no retry, 500 3 attempts | CI `-k plugin_event_delivery_statuses` [200], [401], [500] PASSED | `tests/test_run_plugin.py:491-493` (200: 1 body, receipt, no undelivered); `:495` - `len(bodies) == (1 if 401 else 3)`; `:497` `http_status == status` | PASS |

## Coverage

| Set (size) | Recomputed from | Member -> proof | Unproven |
| --- | --- | --- | --- |
| webhook statuses for a plugin event (3 in the row; Surface names 4 classes) | plan Surface + `sinks.py` | 200, 401, 500 by C59. Network failure: existing, same sink path (`tests/test_sink_routine.py:223`) | - |
| matrix CLIs × capabilities (15) | `assets/capabilities.json`, `spike.md` | C1/C8 table over all 15. Enforcement: write C2, commands C3, workspace_config C4, skills C5 on claude and opencode (dev host). Network: no supported cell (C6 vacuous). Codex: none supported | - |
| `plugin list` / `show` / `add` / `rm` exits | plan Surface | list 0 (C9, C10); show 0 and 2 (C11-C13); add 0, 1, 2 (C14-C22, C26); rm 0 and 2 (C23, C24, C26) | - |
| manifest and layout refusals (`_check_layout` + `_manifest_rules`, recomputed from `src/grokbot_kit/plugin.py:79-205`; AC 19 "value outside door 2") | code | the 15 AC 19 rules by C19 (`tests/test_plugin_manifest.py:124-164`); the 5 forbidden parts by C18 | symbolic link in the plugin (`plugin.py:94`); prompt path outside the plugin dir (`plugin.py:187`); `version`/`description`/`prompt` empty or not a string (`:136`); `.claude-plugin/plugin.json` not valid JSON (`:142`); non-UTF-8 text (`:103`); input name invalid or shadowing a variable (`:150`); `inputs.<x>.required` not bool (`:159`); more than one `repo` input (`:162`); `capabilities` or `result` missing (`:165`, `:176`); `result.max_bytes` not a positive int (`:184`); `--ref` on a directory origin (`:371`). `rg` finds none of these messages in `tests/` |
| `run --plugin` refusals (exit 2) | AC 27-32 | C29 (6), C30 (3 refused, 2 accepted), C32, C33 (3), C34 | - |
| `kind` (3), door 7 URLs (6), prompt variables (4), `source` (3) | door 2, door 7, door 3 | kind: C27/C28, C30, C31; URLs: C27, C28, C29 ×4; variables: C27, C31; source: C9, C14, C17 | - |
| running-task predicate (7) | AC 25 | C25 over all 7 plus the boundary | - |
| invalid result (5) + precedence in a plugin task (7) | AC 43-45 | C42 ×5 (+ exact max_bytes); C44 ×7 own layer, ×5 at the boundary; C43 | - |
| plan doors (8) | plan Landing | 1: C18 · 2: C19 · 3: C14, C17, C22, C27 · 4: C9, C11 · 5: C40, C46, C59 · 6: C42 · 7: C27-C29 · 8: C1, C8, C34, and the harness only through renamed tests (C36's proof selects nothing) | door 1 "loads in Claude Code" (C49, no test) |
| built-in plugins (2) | plan S5/S6 | `code-review`: manifest and instructions C47, C48 · `bug-verify`: C51, C52 | `code-review` real behaviour (C49 load in claude, C50 COMMENT review and re-review) and `bug-verify` reproduction (C53): no test file exists |

## Test policy rows

The rows come from `docs/.specs/features/agent-run-notify/checks.md`, which `checks.md` declares binding without change.

| Row | Files it classifies | Required proof | Expectation met |
| --- | --- | --- | --- |
| Decides, reached across a boundary | `plugin.py` manifest rules | boundary C19 `add_refuses_invalid_manifest` · own layer `manifest_rules` | no - one case per decision row is owed, and 13 refusal rows in `_check_layout`/`_manifest_rules` have no case (see Coverage) |
| Decides, reached across a boundary | `plugin.py` running predicate | own layer C25 · boundary C26 | yes |
| Decides, reached across a boundary | `launch.py` `plugin_harness` | own layer `test_claude_harness`/`test_opencode_harness`/`test_codex_has_no_harness` · boundary `test_opencode_gets_harness_env_and_pwd` + integration | yes (the tests exist and pass; the C36 proof name does not select them, recorded on C36) |
| Decides, reached across a boundary | `terminal.py` plugin classification | own layer C43/C44 first proofs · boundary C42, C44 second proof | yes |
| Entry point that does not decide | `run.py` input validation | boundary C29-C34 | yes |
| Instrumentation, pass-through | `doctor.py` plugins | covered by C58 | yes |
| Integration with a real CLI or GitHub | `-m integration`: `test_plugin_caps.py`, the missing `test_builtin_plugins.py` | `-m integration` on the box, once per CLI | no - it ran on the dev host, not the box. The integration test for C49/C50/C53 does not exist |

Swept `existing` row (data lifecycle): `gc` deletes the whole task dir, including the clone, at `src/grokbot_kit/gc.py:35`
(`shutil.rmtree(task_dir)`). The cited constraint is there.

## Faults injected

All faults ran in a scratch copy (`git archive HEAD` into the scratchpad, its own `uv` venv); the real tree was never
mutated. `git status --porcelain` of the worktree was empty before and is empty after, apart from this report.

| Mutation | Location | Killed |
| --- | --- | --- |
| claude denies `WebFetch`/`WebSearch` when `network == "on"` instead of `"off"` | `src/grokbot_kit/launch.py:68` | yes - `test_claude_harness` failed |
| running predicate ignores the plugin name | `src/grokbot_kit/plugin.py:395` | yes - `test_running_task_predicate` (C25) failed |
| plugin classification ignores `result_valid` | `src/grokbot_kit/terminal.py:92` | yes - `test_invalid_result_cases` 5/5 (C42) failed |
| `text` bound `>` becomes `>=` (off by one) | `src/grokbot_kit/run.py:90` | yes - `test_input_size_bounds[text_64kib]` (C30) failed |
| AC 7 exclusion removed from `matrix()` | `src/grokbot_kit/plugin.py:70` | yes - `test_cli_excluded_when_write_or_workspace_unsupported` (C7) failed |

## Gate

`uv run pytest <11 files> -k "<55 names>"` - 118 passed, 0 failed (exit 0).
`uv run pytest -m integration tests/integration/test_plugin_caps.py` (dev host) - 9 passed, 7 skipped by the matrix, 0 failed.
`uv run ruff check .` - all checks passed. `uv run mypy` - no issues in 22 source files.

## Ranked gaps

1. C49, C50, C53 - `tests/integration/test_builtin_plugins.py` does not exist, so the three proofs point at nothing.
   C49 needs only a local `claude` and could have run here. C50 and C53 also need the box and a real PR or test repo.
2. C37 - the proof `-k run_plugin_claude_end_to_end` selects 0 tests. The equivalent test is
   `test_claude_plugin_task_enforced` (`tests/integration/test_plugin_caps.py:204`); it passed on the dev host, not the box.
3. C36 - the proof `-k harness_per_cli_and_capability` selects 0 tests (exit 5). The real tests are
   `test_claude_harness`, `test_opencode_harness` and `test_codex_has_no_harness` (`tests/test_launch_plugin.py:60,99,125`).
4. Coverage - 13 refusal branches in `src/grokbot_kit/plugin.py` have no test, among them two that matter for safety:
   the symlink refusal (`:94`) and the prompt path staying inside the plugin (`:187`).
5. Test policy, integration row - the capability enforcement (C2-C5, C37) is proven on the dev host only. AD-041 accepts
   this, but the checks' own text still says "no box".
