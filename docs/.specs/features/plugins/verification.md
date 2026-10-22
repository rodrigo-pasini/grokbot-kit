# plugins verification

**Verdict**: FAIL
**Profile**: standard
**Diff range**: d9efceb..7a6d41b (fix under re-verification: 2dd3e68..7a6d41b)
**Round**: 2 - scoped
**Verifier**: independent sub-agent (author != verifier); did not write the code or round 1

57 of 59 checks PASS with located evidence at `7a6d41b`. The fix closed C36, C37 and C49: their proofs now select
real tests, and those tests ran and passed. C50 and C53 still fail. Their tests now exist, but this round did not run
them. On instruction: they post reviews to a real GitHub PR, push a commit, and need test repositories that only the
user's bot can reach. Two Coverage rows still have unproven members: one refusal branch the fix did not reach
(`_table`, `src/grokbot_kit/plugin.py:110`) and the real behaviour of the two built-in plugins (C50, C53). The
integration `Test policy` row is still unmet. All 5 faults injected in this round were killed.

Where the evidence came from. Every proof re-ran at `HEAD` = `7a6d41b`. The CI proofs ran on the development host.
`-m integration tests/integration/test_plugin_caps.py` and `-k code_review_loads_in_claude` also ran on the
**development host, not the box**, with real `claude` 2.1.308 (`sonnet`; C49 calls `haiku` itself) and `opencode` 2.1.3
(`opencode/deepseek-v4.1-flash-free`). AD-041 accepts the development host for the matrix and leaves the box run to the
bot. Nothing that posts to GitHub ran.

Scope of this round: the fix diff `2dd3e68..7a6d41b` changes only tests and `checks.md`, not `src/`. It adds
`tests/integration/test_builtin_plugins.py` and `tests/integration/__init__.py`, renames the C36 and C37 tests, adds
`test_manifest_rules_more` (11 cases) and `test_add_refuses_ref_for_directory`, and switches two integration imports to
`integration.test_real_cli`. It also edits the S5/S6 status lines in `checks.md`. No check text or `Proof:` line
changed.

## Binding sources

Carried from 2dd3e68. Step 1 only runs under `ui`, and the fix did not touch the interface. `design.md` was opened in
round 1. This round re-read `plan.md`, `checks.md`, `spike.md` and AD-037..AD-041 as context.

| Source | Opened | Contradiction | Uncovered |
| --- | --- | --- | --- |
| `docs/.specs/features/plugins/design.md` (binding) | yes - local file (round 1) | none | - |

## Checks

Verified at 7a6d41b: every proof re-ran at this commit. The citations in the files the fix touched were refreshed:
`tests/test_plugin.py` moved +8 lines from C20 on, plus `tests/test_plugin_manifest.py`, `tests/test_launch_plugin.py`
and `tests/integration/*`. The other citations are unchanged, because their files are not in the fix diff.

Batched CI run: `uv run pytest tests/test_builtin_plugins.py tests/test_doctor.py tests/test_launch_plugin.py tests/test_payload.py tests/test_plugin_docs.py tests/test_plugin_manifest.py tests/test_plugin.py tests/test_plugin_spike.py tests/test_run_plugin.py tests/test_skill_doc.py tests/test_terminal.py -k "<the 55 CI -k names from checks.md>" -v` exited 0 with **134 passed** and 160 deselected. Each of the 55 `-k` names has at least one `PASSED` line. `harness_per_cli_and_capability` has 5 and `manifest_rules` has 28.
Integration run 1: `GROKBOT_KIT_IT_CLAUDE_MODEL=sonnet GROKBOT_KIT_IT_OPENCODE_MODEL=opencode/deepseek-v4.1-flash-free uv run pytest -m integration tests/integration/test_plugin_caps.py -v -rs` exited 0 with **9 passed and 7 skipped**. `test_run_plugin_claude_end_to_end` was among the passes. Every skip is `needs()` at `tests/integration/test_plugin_caps.py:39`, on a matrix cell marked `unsupported`.
Integration run 2: `uv run pytest -m integration tests/integration/test_builtin_plugins.py -k code_review_loads_in_claude -v` exited 0 with **2 passed** and 2 deselected.
Not run: `-k code_review_posts_comment_review` (C50) and `-k bug_verify_reproduces` (C53), by instruction.

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
| C19 | the 15 manifest rules give exit 2, name the error, write nothing | CI `-k add_refuses_invalid_manifest` 15/15, `-k manifest_rules` 28 PASSED | `tests/test_plugin.py:278-280` - `returncode == 2`, `message in result.stderr`, `entries == []`; `tests/test_plugin_manifest.py:158-159` - `raised.value.code == 2`, `message in str(raised.value)`; `:82` `len(INVALID) == 15`. `-k manifest_rules` now also selects the 11 `test_manifest_rules_more` cases (`:140-141`), 28 passed in all | PASS |
| C20 | `add` of a plugin named `code-review` gives exit 2 | CI `-k add_refuses_builtin_name` PASSED | `tests/test_plugin.py:294` - `returncode == 2` | PASS |
| C21 | an installed name needs `--replace`; with it the copy and `origin.json` are swapped | CI `-k add_existing_needs_replace` PASSED | `tests/test_plugin.py:307-309` - `returncode == 2`, version stays `1.2.3`; `:312-314` - exit 0, version `9.0.0`, `origin == str(newer)` | PASS |
| C22 | an unreadable dir or a failed git clone gives exit 1 with nothing left behind | CI `-k add_io_failure_leaves_nothing` PASSED | `tests/test_plugin.py:326-327` - `returncode == 1`, `entries == []`; `:330-332` - the same for the clone, `"git clone" in stderr` | PASS |
| C23 | `rm` prints `removed <name>`, exit 0 | CI `-k rm_installed` PASSED | `tests/test_plugin.py:339-341` - `returncode == 0`, `stdout == "removed teste\n"`, `entries == []` | PASS |
| C24 | `rm code-review` and `rm nao-existe` give exit 2 | CI `-k rm_refuses_builtin_and_unknown` 2/2 PASSED | `tests/test_plugin.py:349` - `returncode == 2` | PASS |
| C25 | running-task predicate across its 7 cases | CI `-k running_task_predicate` PASSED | `tests/test_plugin.py:370` - `plugin.running_tasks("teste", now) == ["a-rodando"]` over all 7 fixtures; `:375` window boundary | PASS |
| C26 | `rm` and `add --replace` give exit 2 with the `task_id` while a task runs | CI `-k rm_and_replace_refuse_running_task` PASSED | `tests/test_plugin.py:390-392` - `returncode == 2`, `task in stderr`, copy kept; `:397-399` the same for `--replace` | PASS |
| C27 | plugin copied, PR clone checked out, cwd in `work`, prompt variables substituted | CI `-k launches_in_clone_with_prompt` PASSED | `tests/test_run_plugin.py:127` - `tree(task_dir/"plugin") == tree(source)`; `:133` - `calls[1] == {"argv": ["pr","checkout","7"], ...}`; `:135` `cwd == str(work)`; `:136-138` prompt fully substituted | PASS |
| C28 | a branch URL clones `feat/x` | CI `-k branch_url_checkout` PASSED | `tests/test_run_plugin.py:159` - `rev-parse --abbrev-ref HEAD == "feat/x"`; `:161` gh argv `--branch feat/x` | PASS |
| C29 | 6 bad inputs give exit 2 with no task dir | CI `-k refuses_bad_inputs_before_task_dir` 6/6 PASSED | `tests/test_run_plugin.py:179-182` - `returncode == 2`, `kit.tasks() == []`, `not kit.record.exists()` | PASS |
| C30 | size bounds: 3 refused (exit 2, no task dir), exact 1 MiB and 64 KiB accepted | CI `-k input_size_bounds` 5/5 PASSED | `tests/test_run_plugin.py:216-217` accepted gives exit 0 and 1 task; `:219-220` refused gives exit 2 and `tasks() == []` | PASS |
| C31 | a `file` input is copied to `inputs/<name>` and substituted | CI `-k file_input_copied` PASSED | `tests/test_run_plugin.py:231-232` - copied content equal; `argv[-1] == f"Doc {copied} ..."` | PASS |
| C32 | `--plugin nao-existe` gives exit 2 with no task dir | CI `-k unknown_plugin` PASSED | `tests/test_run_plugin.py:238-240` | PASS |
| C33 | `--prompt-file`, `--` extras and `--cwd` with a repo input give exit 2 with no task dir | CI `-k plugin_flag_conflicts` 3/3 PASSED | `tests/test_run_plugin.py:254-255` - `returncode == 2`, `kit.tasks() == []` | PASS |
| C34 | an unenforceable capability gives exit 2 with the exact message; a supporting CLI runs | CI `-k refuses_unenforceable_capability` PASSED | `tests/test_run_plugin.py:264-266` - `returncode == 2`, `"plugin offline needs network=off, which opencode cannot enforce" in stderr`, no task; `:268-269` claude gives exit 0 | PASS |
| C35 | a clone failure means no launch and an `error/failed/agent_error` event with the gh output | CI `-k clone_failure_event` PASSED | `tests/test_run_plugin.py:276` - `not kit.record.exists()`; `:278` outcome; `:279` - `"Could not resolve to a Repository" in event["summary"]` | PASS |
| C36 | per-CLI harness table (3 CLIs × 5 capabilities) | CI batch `-k harness_per_cli_and_capability` **5 PASSED** (claude 1, opencode 3 params, codex 1); round 1 selected 0 | `tests/test_launch_plugin.py:62` - `h.args == ["--restricted", ...]` and `:74` `h.permissions == {...}` for claude (`test_harness_per_cli_and_capability_claude`, `:60`); `:101-102` - `h.args == args`, `h.permissions == {}` for opencode (`:99`); `:126` - `pytest.raises(ValueError, match="codex has no plugin harness")` (`:125`). The fix only renamed the tests; the bodies are the ones round 1 M1 killed | PASS |
| C37 | real `claude`: no write to `~`, no `touch`, no workspace hook, the skill loads | integration `-k run_plugin_claude_end_to_end` PASSED (`test_run_plugin_claude_end_to_end`, `tests/integration/test_plugin_caps.py:204`), 1 selected. **Development host, not the box**: the check text says "No box"; the S3 header in `checks.md` and AD-041 move the proof to the development host and leave the box run to the bot | `tests/integration/test_plugin_caps.py:220` - `not outside.exists() and not home_outside.exists()`; `:221` - `not (task_dir / "spike-cmd").exists()`; `:222` - `not marker.exists()`; `:223` - `event["result"]["word"] == "spike-skill-ok"`; `:224` `skill_invoked(...)` | PASS |
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
| C49 | `claude --plugin-dir <code-review>` loads without a validation error | integration `-k code_review_loads_in_claude` **2 PASSED** (`[code-review]`, `[bug-verify]`), real `claude` 2.1.308 on the development host (the check needs no box) | `tests/integration/test_builtin_plugins.py:82-83` - `validated.returncode == 0`, `"Validation passed" in validated.stdout` (`claude plugin validate`); `:94-96` - `loaded.returncode == 0`, `json.loads(loaded.stdout)["is_error"] is False`, `"plugin" not in loaded.stderr.lower()` (`claude -p --plugin-dir`). Fault F5 killed it at `:82` | PASS |
| C50 | on the box, posts a `COMMENT` review and a re-review returns only new findings | **not run in this round, by instruction**: it posts reviews to a real GitHub PR and pushes a commit, and needs `GROKBOT_KIT_IT_REVIEW_PR` set to a test PR reachable only by the user's bot. The test now exists: `test_code_review_posts_comment_review`, `tests/integration/test_builtin_plugins.py:100` | written, never run: `:112` - `review["state"] == "COMMENTED"`; `:128` - `{f["file"] for f in findings} == {novo}`. No run, so no evidence | FAIL |
| C51 | `bug-verify` manifest, with network following the matrix | CI `-k bug_verify_manifest` PASSED | `tests/test_builtin_plugins.py:72-75` - `network == expected_network` (`on` while opencode network is unsupported), `commands == [*GIT_READ, *TEST_RUNNERS]`, required fields | PASS |
| C52 | `bug-verify` instructions (AC 56-59) | CI `-k bug_verify_instructions` PASSED | `tests/test_builtin_plugins.py:81-87` | PASS |
| C53 | on the box, reproduces the known `ZeroDivisionError` | **not run in this round, by instruction**: it needs a test repository with the known bug (`GROKBOT_KIT_IT_BUG_REPO`, `_ALERT`, `_FILE`) that only the user's bot can reach. The test now exists: `test_bug_verify_reproduces`, `tests/integration/test_builtin_plugins.py:132` | written, never run: `:139` - `event["result"]["reproduced"] == "yes"`; `:140` - `bug_file in [s["file"] for s in suspects]`. No run, so no evidence | FAIL |
| C54 | SKILL.md: `plugin list --json`, show name, description and capabilities, `run --plugin` | CI `-k plugin_list_and_run` PASSED | `tests/test_skill_doc.py:407` - the ```` ```sh grokbot-kit plugin list --json ``` ```` block; `:415` - `` `grokbot-kit run --plugin <nome>` `` | PASS |
| C55 | install order: show, show the capabilities, ask, add `--yes` | CI `-k plugin_install_confirms` PASSED | `tests/test_skill_doc.py:435` - `positions == sorted(positions)` | PASS |
| C56 | no `curl`; every cited plugin command and flag is in `--help` | CI `-k commands_exist_in_help` PASSED (`test_plugin_commands_exist_in_help`) | `tests/test_skill_doc.py:442` - `not command.startswith("curl")`; `:452` - `flag in result.stdout` | PASS |
| C57 | the en and pt-BR guides: sections, matrix, warning, links to each other | CI `-k guide_sections` [en], [pt-BR] PASSED | `tests/test_plugin_docs.py:71-72` warning and the other-language link; `:96` the matrix table equals `plugin.matrix()`; `:104-105` example equals the built-in files | PASS |
| C58 | `doctor --json` `plugins`; an unreadable manifest adds a problem; gh not logged in is a warning only | CI `-k plugins_listed_and_problems` PASSED | `tests/test_doctor.py:334`; `:344-347` - code 1, problem names `plugin teste` and `grokbot-kit.toml`; `:353` - `(0, [], {"logged_in": False})`; `:356` the exact line | PASS |
| C59 | plugin event delivery: 200 receipt, 401 no retry, 500 3 attempts | CI `-k plugin_event_delivery_statuses` [200], [401], [500] PASSED | `tests/test_run_plugin.py:491-493` (200: 1 body, receipt, no undelivered); `:495` - `len(bodies) == (1 if 401 else 3)`; `:497` `http_status == status` | PASS |
## Coverage

Rows whose authority the fix touched were recomputed at 7a6d41b: the manifest/layout refusals, the plan doors, the
built-in plugins, and the matrix enforcement through C37. The other rows are carried from 2dd3e68. The fix touched
no `src/`, so their members did not change.

| Set (size) | Recomputed from | Member -> proof | Unproven |
| --- | --- | --- | --- |
| webhook statuses for a plugin event (3 in the row; Surface names 4 classes) - carried from 2dd3e68 | plan Surface + `sinks.py` | 200, 401 and 500 by C59. Network failure is existing behaviour on the same sink path (`tests/test_sink_routine.py:223`) | - |
| matrix CLIs × capabilities (15) - verified at 7a6d41b | `assets/capabilities.json`, `spike.md` | C1/C8 table over all 15. Enforcement on claude and opencode (development host): write C2, commands C3, workspace_config C4, skills C5, and C37 end to end on claude. Network has no supported cell (C6 vacuous). Codex has none supported | - |
| `plugin list` / `show` / `add` / `rm` exits - carried from 2dd3e68 | plan Surface | list 0 (C9, C10); show 0 and 2 (C11-C13); add 0, 1, 2 (C14-C22, C26); rm 0 and 2 (C23, C24, C26) | - |
| manifest and layout refusals - verified at 7a6d41b (recomputed from the 45 `PluginError(` raises in `src/grokbot_kit/plugin.py`, `_check_layout` and `_manifest_rules` at `:79-205`, plus `:371`) | code | the 15 AC 19 rules by C19 (`tests/test_plugin_manifest.py:154-159`) and the 5 forbidden parts by C18. The round 1 gaps are closed by `test_manifest_rules_more`, selected by C19's `-k manifest_rules` (`tests/test_plugin_manifest.py:136-141`). Symbolic link `:94` is `link_simbolico`. Prompt outside the plugin `:187` is `prompt_fora_do_plugin` (the outside file exists, so only `is_relative_to` refuses it). Empty `version` `:136` is `version_vazia`. Invalid JSON in `plugin.json` `:142` is `plugin_json_invalido`. Non-UTF-8 `:103` is `prompt_nao_utf8`. An input shadowing a variable `:150` is `entrada_com_nome_de_variavel`. `required` not bool `:159` is `required_nao_booleano`. Two `repo` inputs `:162` is `duas_entradas_repo`. Missing `capabilities` `:165` is `capabilities_ausente`, and missing `result` `:176` is `result_ausente`. `max_bytes` 0 `:184` is `max_bytes_zero`. `--ref` on a directory `:371` is covered by `test_add_refuses_ref_for_directory` (`tests/test_plugin.py:286-287`), which no check's `Proof:` selects: it ran on its own, passed, and killed F4 | `_table` "must be a table" (`src/grokbot_kit/plugin.py:110`; `inputs`, `inputs.<x>`, `capabilities` or `result` that is not a table): `rg "must be a table" tests/` finds nothing. Round 1 missed this member too |
| `run --plugin` refusals (exit 2) - carried from 2dd3e68 | AC 27-32 | C29 (6), C30 (3 refused, 2 accepted), C32, C33 (3), C34 | - |
| `kind` (3), door 7 URLs (6), prompt variables (4), `source` (3) - carried from 2dd3e68 | door 2, door 7, door 3 | kind: C27/C28, C30, C31. URLs: C27, C28, C29 ×4. Variables: C27, C31. Source: C9, C14, C17 | - |
| running-task predicate (7) - carried from 2dd3e68 | AC 25 | C25 over all 7 plus the boundary | - |
| invalid result (5) + precedence in a plugin task (7) - carried from 2dd3e68 | AC 43-45 | C42 ×5 (plus exact max_bytes). C44 ×7 in its own layer and ×5 at the boundary. C43 | - |
| plan doors (8) - verified at 7a6d41b | plan Landing | 1: C18, C49 (now run). 2: C19. 3: C14, C17, C22, C27. 4: C9, C11. 5: C40, C46, C59. 6: C42. 7: C27-C29. 8: C1, C8, C34, C36 (proof now selects 5 tests), C37 | - |
| built-in plugins (2) - verified at 7a6d41b | plan S5/S6 | `code-review`: manifest and instructions C47, C48, loads in claude C49. `bug-verify`: C51, C52, also loads in claude (`test_code_review_loads_in_claude[bug-verify]`) | `code-review` posting a COMMENT review and re-reviewing (C50), and `bug-verify` reproducing the bug (C53): the tests exist but were not run (GitHub and box only) |

## Test policy rows

The rows come from `docs/.specs/features/agent-run-notify/checks.md`, binding without change. This round re-judged the
two unmet rows and the row for `launch.py` (its test file was touched). The others are carried from 2dd3e68.

| Row | Files it classifies | Required proof | Expectation met |
| --- | --- | --- | --- |
| Decides, reached across a boundary (re-judged at 7a6d41b) | `plugin.py` manifest rules | boundary C19 `add_refuses_invalid_manifest` · own layer `manifest_rules` | partly: the 12 round 1 refusal rows now have a case each, but the `_table` row (`plugin.py:110`) has none (see Coverage) |
| Decides, reached across a boundary (carried from 2dd3e68) | `plugin.py` running predicate | own layer C25 · boundary C26 | yes |
| Decides, reached across a boundary (re-judged at 7a6d41b) | `launch.py` `plugin_harness` | own layer `test_harness_per_cli_and_capability_{claude,opencode,codex}` (selected by C36's proof) · boundary `test_opencode_gets_harness_env_and_pwd` + C37 integration | yes |
| Decides, reached across a boundary (carried from 2dd3e68) | `terminal.py` plugin classification | own layer: first proofs of C43/C44 · boundary: C42 and the second proof of C44 | yes |
| Entry point that does not decide (carried from 2dd3e68) | `run.py` input validation | boundary C29-C34 | yes |
| Instrumentation, pass-through (carried from 2dd3e68) | `doctor.py` plugins | covered by C58 | yes |
| Integration with a real CLI or GitHub (re-judged at 7a6d41b) | `-m integration`: `test_plugin_caps.py`, `test_builtin_plugins.py` | `-m integration` on the box, once per CLI | not met: `test_builtin_plugins.py` now exists and C49 ran, but only on the development host (AD-041). C50 and C53 never ran. No `-m integration` proof of this feature has run on the box |

Swept `existing` row (data lifecycle), carried from 2dd3e68: `gc` deletes the whole task dir, including the clone, at
`src/grokbot_kit/gc.py:35` (`shutil.rmtree(task_dir)`). The fix did not touch it.

## Faults injected

Round 2 faults (verified at 7a6d41b) target the assertion surfaces the fix created. Each ran in a scratch copy
(`git archive HEAD | tar -x` into the scratchpad, with its own `uv` venv). Each fault was restored with
`git checkout -- .` inside the scratch, which showed an empty porcelain after every run. The worktree was never mutated.
Its `git status --porcelain` was empty before the round, and at the end it lists only this report.

| Mutation | Location | Killed |
| --- | --- | --- |
| F1 - symbolic link check disabled (`if False and os.path.islink(...)`) | `src/grokbot_kit/plugin.py:92` | yes - `test_manifest_rules_more[link_simbolico]` failed |
| F2 - prompt path no longer has to stay inside the plugin (`is_relative_to` removed) | `src/grokbot_kit/plugin.py:187` | yes - `test_manifest_rules_more[prompt_fora_do_plugin]` failed |
| F3 - "at most one `repo` input" bound `> 1` becomes `> 2` | `src/grokbot_kit/plugin.py:161` | yes - `test_manifest_rules_more[duas_entradas_repo]` failed |
| F4 - `--ref` on a directory accepted (`if ref is not None` becomes `if False`) | `src/grokbot_kit/plugin.py:370` | yes - `test_add_refuses_ref_for_directory` failed (`tests/test_plugin.py:286`) |
| F5 - `code-review` `.claude-plugin/plugin.json` `"version": 1` (a number) | `src/grokbot_kit/assets/plugins/code-review/.claude-plugin/plugin.json:3` | yes - `test_code_review_loads_in_claude[code-review]` failed at `tests/integration/test_builtin_plugins.py:82` (real `claude plugin validate`: "Validation failed") |
| M1 - claude denies `WebFetch`/`WebSearch` when `network == "on"` (carried from 2dd3e68) | `src/grokbot_kit/launch.py:68` | yes - the claude harness test failed (now `test_harness_per_cli_and_capability_claude`, same body) |
| M2 - running predicate ignores the plugin name (carried from 2dd3e68) | `src/grokbot_kit/plugin.py:395` | yes - `test_running_task_predicate` (C25) failed |
| M3 - plugin classification ignores `result_valid` (carried from 2dd3e68) | `src/grokbot_kit/terminal.py:92` | yes - `test_invalid_result_cases` 5/5 (C42) failed |
| M4 - `text` bound `>` becomes `>=` (carried from 2dd3e68) | `src/grokbot_kit/run.py:90` | yes - `test_input_size_bounds[text_64kib]` (C30) failed |
| M5 - AC 7 exclusion removed from `matrix()` (carried from 2dd3e68) | `src/grokbot_kit/plugin.py:70` | yes - `test_cli_excluded_when_write_or_workspace_unsupported` (C7) failed |

Round 1's M1-M5 were not re-injected: the fix changed no `src/` file and no assertion they hit (the C36 tests were only
renamed).

## Gate

At 7a6d41b:
`uv run pytest <11 files> -k "<55 names>"` - 134 passed, 0 failed (exit 0).
`uv run pytest tests/test_plugin.py -k add_refuses_ref_for_directory` - 1 passed.
`uv run pytest` (full suite, default markers) - 753 passed, 38 deselected, 0 failed.
`GROKBOT_KIT_IT_CLAUDE_MODEL=sonnet GROKBOT_KIT_IT_OPENCODE_MODEL=opencode/deepseek-v4.1-flash-free uv run pytest -m integration tests/integration/test_plugin_caps.py` (development host) - 9 passed, 7 skipped by the matrix, 0 failed.
`uv run pytest -m integration tests/integration/test_builtin_plugins.py -k code_review_loads_in_claude` (development host) - 2 passed.
`uv run ruff check .` - All checks passed. `uv run mypy` - no issues found in 22 source files.

## Ranked gaps

1. C50, C53 - not proven. `test_code_review_posts_comment_review` (`tests/integration/test_builtin_plugins.py:100`) and
   `test_bug_verify_reproduces` (`:132`) exist but were not run. They post to a real GitHub PR, push a commit, and need
   test repositories that only the user's bot can reach. To close them, the bot runs them on the box with
   `GROKBOT_KIT_IT_REVIEW_PR` / `GROKBOT_KIT_IT_BUG_*` set.
2. Test policy, integration row - every `-m integration` proof of this feature ran on the development host only.
   AD-041 accepts this for the matrix, but the row's bar is the box.
3. Coverage - the `_table` refusal (`src/grokbot_kit/plugin.py:110`, a non-table `inputs`/`inputs.<x>`/`capabilities`/
   `result`) has no test. Round 1 missed it as well.
4. Precision (not counted in the verdict) - `test_add_refuses_ref_for_directory` (`tests/test_plugin.py:284`) proves a
   door 4 refusal that no check names. It runs in the full suite but not through any `Proof:` line. The C37 text still
   says "No box", while its slice header and AD-041 record the proof on the development host.
