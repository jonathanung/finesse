You are iterating on the Finesse plugin at /workspace/plugins/finesse/. Before doing anything, check the current state: read these 4 target files — commands/finesse.md, commands/finesse-help.md, skills/meta-prompting/SKILL.md, skills/task-workflows/SKILL.md. Search for any remaining `/ralph-loop:ralph-loop` command strings and `$(cat` patterns (including generic `$(cat ...)` references) to identify what has already been changed vs what remains.

Also read these 3 reference files for interface context — commands/finesse-execute.md, commands/cancel-finesse-execute.md, commands/finesse-validate.execute.md.

## Subagent Instructions

You may use the Task tool to spawn subagents for parallel work. Follow these guidelines:

### Available Subagent Types

- **Bash**: Run test suites, linting, and verification commands in parallel with continued work.
- **Explore**: Investigate unfamiliar code, research patterns, and trace execution flows.
- **general-purpose**: Perform file modifications on independent, non-overlapping file sets.

### Guardrails

- Run at most 2 concurrent subagents at a time.
- Subagents must NOT make git commits or push to remote repositories.
- Subagents must NOT modify files outside their assigned scope.
- Wait for all subagent results before marking a phase complete.
- If a subagent fails, retry once. If it fails again, do the work yourself.
- Provide clear, scoped instructions when spawning a subagent — include specific file paths and expected outcomes.

## Requirements (in order)

Phase 1: Update commands/finesse.md — all changes

This phase has multiple sub-tasks, all within commands/finesse.md. Apply ALL of the following:

### 1a. YAML frontmatter — add Skill to allowed-tools

In the YAML frontmatter (line 4), add "Skill" to the allowed-tools array. Insert it before "AskUserQuestion". The Skill tool is needed for the "Execute now" acceptance option (invokes /finesse-execute) and for the pre-flight validation check (invokes /finesse-validate-execute).

### 1b. Command format strings — single-workflow

In the "User Decision" → "If ACCEPTED:" section, find step 3 with the code block containing the /ralph-loop:ralph-loop command. Replace the entire code block content:

Old:
/ralph-loop:ralph-loop $(cat ralph-plans/<name>.md) --completion-promise "$(cat ralph-plans/<name>-promise.txt)" --max-iterations=<N>

New:
/finesse-execute --prompt-file ralph-plans/<name>.md --completion-promise-file ralph-plans/<name>-promise.txt --max-iterations <N>

### 1c. Command format strings — multi-workflow

In the "If ACCEPTED (Multi-Workflow):" section, find step 4 with the wave example code block. Replace ALL /ralph-loop:ralph-loop commands:

Old per-wave format:
/ralph-loop:ralph-loop $(cat ralph-plans/<session>/wave-1/<task-1>/prompt.md) --completion-promise "$(cat ralph-plans/<session>/wave-1/<task-1>/promise.txt)" --max-iterations=<N>

New per-wave format:
/finesse-execute --prompt-file ralph-plans/<session>/wave-1/<task-1>/prompt.md --completion-promise-file ralph-plans/<session>/wave-1/<task-1>/promise.txt --max-iterations <N>

Apply to ALL wave entries in the code block (Wave 1 and Wave 2).

### 1d. Update $(cat ...) references

1. The "IMPORTANT" note after the ACCEPTED single-workflow section says the file "must be valid as a direct `$(cat ...)` argument". Change this paragraph to:

"**IMPORTANT**: The `<name>.md` file must contain ONLY the prompt text. This means: no markdown metadata headers, no YAML frontmatter, starts directly with the prompt content (e.g., "You are iterating on..."). The file IS the prompt, nothing more."

2. In Critical Rules, find the rule about "three-file structure" that ends with "The `$(cat ...)` command references the first two." Change the last sentence to: "The `/finesse-execute` command references the first two via `--prompt-file` and `--completion-promise-file`."

3. In Critical Rules, find the rule about sub-workflow prompts that says "Sub-workflow prompts are read via `$(cat ...)` and have no access to sibling files." Change to: "Sub-workflow prompts are read by `/finesse-execute` from file and have no access to sibling files."

### 1e. Add execution layer pre-flight check

Add a new subsection between "### Validation" and "### Presentation" (between the validation table and the Presentation section). Title it "### Execution Layer Pre-flight Check" with this content:

Before presenting the plan, run `/finesse-validate-execute` using the Skill tool to confirm the Finesse execution layer is healthy. Parse the output:

- If all checks pass (exit code 0): Set `execution_layer_healthy = true`. Proceed to presentation with all three acceptance options (Execute now, Copy command, Save plan only).
- If any check fails (exit code 1): Set `execution_layer_healthy = false`. Warn the user that the execution layer has issues and include the failure details in the presentation. Fall back to two acceptance options only (Copy command, Save plan only) — omit "Execute now".

This check is NOT affected by UAT fast-forward — it always runs.

### 1f. Add three acceptance options to User Decision

Restructure the ACCEPTED single-workflow section. Keep steps 1, 2, and 1.5 as-is (create directory, write files, capture baseline). Replace step 3 (output command) and step 4 (keep working file) with:

3. Present acceptance options via `AskUserQuestion`:
   - If `execution_layer_healthy` is true, offer 3 options:
     1. **Execute now** — Launch the plan immediately via the Finesse execution layer
     2. **Copy command** — Output the /finesse-execute command string for manual use
     3. **Save plan only** — Files are saved; no command output
   - If `execution_layer_healthy` is false, offer 2 options (with a warning about execution layer issues):
     1. **Copy command** — Output the /finesse-execute command string for manual use
     2. **Save plan only** — Files are saved; no command output
4. Handle the selected option:
   - **Execute now**: Invoke `/finesse-execute` using the Skill tool with args `--prompt-file ralph-plans/<name>.md --completion-promise-file ralph-plans/<name>-promise.txt --max-iterations <N>`. The Finesse planning session ends here — execution continues under /finesse-execute.
   - **Copy command**: Output the exact command:
     `/finesse-execute --prompt-file ralph-plans/<name>.md --completion-promise-file ralph-plans/<name>-promise.txt --max-iterations <N>`
   - **Save plan only**: Report "Plan files saved to ralph-plans/. Use `/finesse-execute --prompt-file ralph-plans/<name>.md --completion-promise-file ralph-plans/<name>-promise.txt --max-iterations <N>` when ready to execute."
5. Keep any working file (`ralph-plans/<name>-working.md`) from this planning session for reference.

Apply the same three-option acceptance pattern to the Multi-Workflow ACCEPTED path, using the per-wave /finesse-execute commands.

### 1g. Update Presentation section

In the Presentation item list, change item 9:
Old: "9. **The exact ralph-loop command to run** (using file references — see User Decision below)"
New: "9. **The exact /finesse-execute command to run** (using file references — see User Decision below)"

### 1h. Update philosophy and rules text

Apply these targeted text changes for consistency:

1. Near the top (line 12 area), find: "Your ONLY output is a ralph-loop command that the user will copy-paste and run themselves. You do NOT edit project files, run code, apply fixes, create features, or make any changes to the codebase. You plan, validate, write to `ralph-plans/`, and output the command. Then you STOP."
   Change to: "Your ONLY output is a validated ralph-loop prompt saved to `ralph-plans/`. On acceptance, you offer the user options to execute immediately, copy the command, or save the plan only. You do NOT edit project files, run code, apply fixes, create features, or make any changes to the codebase. You plan, validate, write to `ralph-plans/`, present acceptance options, and STOP."

2. In Core Philosophy item 1, find: "Your deliverable is ALWAYS a ralph-loop command — NEVER direct code changes. After the user accepts your plan, you write files to `ralph-plans/`, output the command, and STOP."
   Change to: "Your deliverable is ALWAYS ralph-loop prompt files in `ralph-plans/` — NEVER direct code changes. After the user accepts your plan, you write files to `ralph-plans/`, offer acceptance options (execute, copy command, or save only), and STOP."

3. In Critical Rules, find the rule containing "Your sole output is the ralph-loop command."
   Change that phrase to: "Your sole deliverable is the ralph-loop prompt files."

4. In Critical Rules, find: "You are a PLANNER. You NEVER start a ralph loop, run setup scripts, or create loop state files."
   Change to: "You are a PLANNER. You NEVER directly implement changes. When the user chooses 'Execute now', you delegate to `/finesse-execute` via the Skill tool — you do NOT run setup scripts or create loop state files directly."

5. In Critical Rules, find: "After acceptance, plan goes in `ralph-plans/` and user gets a copy-paste command."
   Change to: "After acceptance, plan goes in `ralph-plans/` and the user chooses to execute, copy the command, or save only."

6. In Critical Rules, find: "The final deliverable is ALWAYS the ralph-loop command using file references — NEVER output the raw prompt inline in the command. After outputting the command, STOP. Do not continue to implementation under any circumstances."
   Change to: "The final deliverable is ALWAYS the `/finesse-execute` command using file path arguments — NEVER output the raw prompt inline. After handling the user's acceptance option (execute, copy, or save), STOP. Do not continue to implementation under any circumstances."

7. Find the "STOP HERE" paragraph: "STOP HERE. After outputting the command(s), your job is done. Do NOT proceed to implement the plan. Do NOT edit any project files. Do NOT apply the changes described in the prompt. The user will run the ralph-loop command themselves. If the user asks you to implement the changes directly (without ralph-loop), they must do so outside of a `/finesse` session."
   Change to: "STOP HERE. After handling the user's acceptance option (execute, copy, or save), your job is done. Do NOT proceed to implement the plan. Do NOT edit any project files. Do NOT apply the changes described in the prompt. If the user asks you to implement the changes directly (without the execution layer), they must do so outside of a `/finesse` session."

Verify: Read commands/finesse.md in full. Confirm:
(a) No `/ralph-loop:ralph-loop` command strings remain
(b) No `$(cat` patterns remain (including generic `$(cat ...)` references)
(c) "Skill" is in allowed-tools
(d) AskUserQuestion acceptance flow with 3 options is present in both single and multi-workflow paths
(e) Pre-flight check section exists between Validation and Presentation
(f) All philosophy and rules text is updated consistently
(g) Presentation item 9 references /finesse-execute

[Subagent opportunity]: After verifying Phase 1, spawn a general-purpose subagent to handle Phase 2 (finesse-help.md) while you begin Phase 3 (meta-prompting/SKILL.md). These files are independent — no shared writes.

Phase 2: Update commands/finesse-help.md — all changes

### 2a. Add new commands to Available Commands section

After the `/finesse-retro` command entry (after the closing ``` of the /finesse-retro usage block, around line 81), add these three command entries:

### /finesse-execute [ARGS]

Launch a Finesse-managed ralph loop from a plan or inline prompt.

**Arguments:**
- `--prompt-file PATH` — Path to prompt file (e.g., `ralph-plans/my-plan.md`)
- `--completion-promise-file PATH` — Path to completion promise file
- `--max-iterations N` — Maximum iterations before auto-stop
- No args — auto-detects the most recent plan from `ralph-plans/`
- Inline prompt text — for quick tasks without /finesse planning

**Usage:**
```
/finesse-execute --prompt-file ralph-plans/fix-token-refresh.md --completion-promise-file ralph-plans/fix-token-refresh-promise.txt --max-iterations 8
/finesse-execute
```

### /cancel-finesse-execute

Cancel an active Finesse execution loop. Saves telemetry to `.finesse/run-log.json` for retro analysis.

### /finesse-validate-execute

Validate the Finesse execution layer. Runs 63 structural and functional checks against the setup script, stop hook, hook registration, and command definitions. Exit code 0 = all checks pass.

### 2b. Update Output section command format

Find the code block in the Output section (around line 140-142) containing the /ralph-loop:ralph-loop command. Replace it:

Old:
/ralph-loop:ralph-loop $(cat ralph-plans/<name>.md) --completion-promise "$(cat ralph-plans/<name>-promise.txt)" --max-iterations=<N>

New:
/finesse-execute --prompt-file ralph-plans/<name>.md --completion-promise-file ralph-plans/<name>-promise.txt --max-iterations <N>

### 2c. Update "You get a ready-to-run command:" text

Change the text just before the output command code block from:
"You get a ready-to-run command:"
to:
"You get a ready-to-run command (or can execute directly):"

### 2d. Update "What Happens" step 10

In the "What Happens" section, step 10, change:
Old: "Three files saved to `ralph-plans/` (prompt, promise, metadata), you get the ralph-loop command"
New: "Three files saved to `ralph-plans/` (prompt, promise, metadata), you choose to execute immediately, copy the command, or save only"

### 2e. Update Output section description text

In the Output section, find the bullet point:
"`<name>.md` — prompt text only (referenced by the command via `$(cat ...)`)"

Change to:
"`<name>.md` — prompt text only (referenced by `/finesse-execute` via `--prompt-file`)"

### 2f. Add Execution Layer section

After the "Exploration Cache" section and before "When to Use Finesse", add:

## Execution Layer

Finesse ships its own execution layer and no longer requires the ralph-wiggum plugin as a separate install. The execution layer includes a setup script, stop hook, and per-iteration telemetry for post-execution retrospectives via `/finesse-retro`.

Use `/finesse-validate-execute` to verify the execution layer is healthy on your machine.

Verify: Read commands/finesse-help.md. Confirm:
(a) /finesse-execute, /cancel-finesse-execute, /finesse-validate-execute are documented
(b) No `/ralph-loop:ralph-loop` command strings remain
(c) No `$(cat` patterns remain (including generic `$(cat ...)` references)
(d) Execution layer section exists
(e) Output format uses /finesse-execute

[Subagent opportunity]: Spawn a general-purpose subagent to handle Phase 4 (task-workflows/SKILL.md) while continuing with Phase 3 (meta-prompting/SKILL.md). These files are independent — no shared writes.

Phase 3: Update skills/meta-prompting/SKILL.md — all changes

### 3a. Update File Output Format section

Find the bullet point that says:
"- The file is referenced via `$(cat ralph-plans/<name>.md)` in the ralph-loop command"

Change to:
"- The file is referenced via `--prompt-file ralph-plans/<name>.md` in the `/finesse-execute` command"

### 3b. Update Execution Graph Format per-wave commands

Find the per-wave commands code block in the Execution Graph Format section. Replace the entire code block content. The block contains Wave 1 and Wave 2 entries using /ralph-loop:ralph-loop format.

Replace each /ralph-loop:ralph-loop command:

Old wave entry:
/ralph-loop:ralph-loop $(cat ralph-plans/<session>/wave-1/<task>/prompt.md) --completion-promise "$(cat ralph-plans/<session>/wave-1/<task>/promise.txt)" --max-iterations=<N>

New wave entry:
/finesse-execute --prompt-file ralph-plans/<session>/wave-1/<task>/prompt.md --completion-promise-file ralph-plans/<session>/wave-1/<task>/promise.txt --max-iterations <N>

Do this for BOTH the Wave 1 and Wave 2 entries in the code block.

### 3c. Update Per-Sub-Workflow Prompt Rules

Find the bullet point in the Per-Sub-Workflow Prompt Rules section that says:
"Each `prompt.md` must be fully self-contained (valid as a `$(cat ...)` argument)"

Change to:
"Each `prompt.md` must be fully self-contained (read by `/finesse-execute` via `--prompt-file`)"

Verify: Read skills/meta-prompting/SKILL.md. Confirm:
(a) No `/ralph-loop:ralph-loop` command strings remain
(b) No `$(cat` patterns remain (including generic `$(cat ...)` references)
(c) `/finesse-execute` format is used in all command examples

Phase 4: Update skills/task-workflows/SKILL.md — add per-wave command examples

In the "Multi-Workflow Execution (Decomposed Tasks)" section, find the last paragraph that ends with "The user accepts or rejects the entire decomposition as a unit." (around line 574).

After that paragraph, add:

**Per-wave execution commands** — The `execution-graph.md` file includes ready-to-run commands for each sub-workflow:

```
## Wave 1 (run in parallel)
/finesse-execute --prompt-file ralph-plans/<session>/wave-1/<task>/prompt.md --completion-promise-file ralph-plans/<session>/wave-1/<task>/promise.txt --max-iterations <N>

## Wave 2 (run after Wave 1 completes)
/finesse-execute --prompt-file ralph-plans/<session>/wave-2/<task>/prompt.md --completion-promise-file ralph-plans/<session>/wave-2/<task>/promise.txt --max-iterations <N>
```

Verify: Read skills/task-workflows/SKILL.md. Confirm the per-wave command format is present using `/finesse-execute` format.

Phase 5: Final cross-file verification

Search ALL 4 target files for remaining old-format references:

1. Search for `/ralph-loop:ralph-loop` across all 4 files — expect 0 matches
2. Search for `$(cat` across all 4 files — expect 0 matches (covers both `$(cat ralph-plans/...` and generic `$(cat ...)` references)
3. Search for `finesse-execute` across all 4 files — expect matches confirming changes
4. Search for `finesse-validate` in commands/finesse.md — confirm pre-flight check exists
5. Read the acceptance options section in commands/finesse.md — verify 3 options
6. Read the execution layer section in commands/finesse-help.md — verify it exists

Fix any remaining old-format references or missing content.

Verify: All grep checks pass with expected results.

## Rules
- Do NOT make git commits. Do NOT push to remote repositories.
- ONLY modify these 4 files: commands/finesse.md, commands/finesse-help.md, skills/meta-prompting/SKILL.md, skills/task-workflows/SKILL.md.
- Do NOT modify: scripts/finesse_execute.py, hooks/stop_hook.py, hooks/hooks.json, scripts/validate_execute.py (or finesse_validate_execute.py), commands/finesse-execute.md, commands/cancel-finesse-execute.md, commands/finesse-validate.execute.md, or any other file.
- Make targeted edits using the Edit tool. Do NOT rewrite files from scratch.
- Read actual file content before editing. Verify line content matches expectations.
- Preserve all existing content that is not being changed. These are large, complex files — surgical edits only.
- When updating command format strings, use consistent formatting: `/finesse-execute --prompt-file <path> --completion-promise-file <path> --max-iterations <N>` (space before N, not equals sign).
- Read actual error messages before attempting fixes.
- If stuck on the same error for 3+ attempts, try an alternative approach.
- If unable to make progress after 3 iterations on a single edit, document what is blocking and move on.
- If unable to make progress overall after 8 iterations, document blockers and output <promise>BLOCKED</promise>.
- **Edit tool non-unique strings**: If the Edit tool fails because `old_string` is not unique in the file, do NOT guess or truncate. Instead, include more surrounding context (3-5 additional lines before/after) to make the match unique. If the string appears multiple times intentionally, use `replace_all: true` only when ALL occurrences should change.
- **Copy old_string from the file, not from this prompt**: Before every Edit call, Read the file and copy the exact text to use as `old_string` from the Read output. Do NOT copy old_string from this prompt's instructions — whitespace, quoting, and escaping may differ from the actual file content.
- **Anti-oscillation**: If an edit fails twice with the same approach, do NOT retry the same approach a third time. Switch to an alternative strategy (e.g., use Write to replace a larger section, or split the edit into smaller pieces).
- **Anchor verification for insertions**: Before inserting a new section (e.g., Phase 1e pre-flight check), Read the file and confirm the exact anchor text (the line before and after the insertion point) exists as expected. If the anchor text differs from what this prompt describes, use the actual file content as the anchor.
- **Code blocks inside markdown files**: When editing command strings that appear inside triple-backtick code fences in the target files, include the surrounding backtick lines (opening and closing ```) as part of the old_string to ensure uniqueness and correct placement. Do NOT attempt to match only the inner command line if it appears similar to other command lines in the file.
- **Wave command blocks**: When replacing Wave 1 and Wave 2 command entries in code blocks (Phases 1c, 3b), replace the ENTIRE code block content at once (from opening ``` to closing ```), not individual wave command lines. The per-line content between Wave 1 and Wave 2 is near-identical and will cause non-unique match errors if targeted individually.
- **Phase 1f large restructuring**: The acceptance flow restructuring (Phase 1f) replaces steps 3-5 with a new multi-option flow. Use a single Edit call with old_string spanning from "3. Output the exact command:" through "4. Keep any working file" (inclusive). If this edit fails twice, fall back to using Write to replace the entire "If ACCEPTED:" subsection while preserving the surrounding content.
- **Phase 1h progress tracking**: Phase 1h has 7 independent text replacements. Before starting (or resuming) Phase 1h, grep the file for each old-text pattern to determine which replacements remain. Do NOT re-apply a replacement that has already been made — this will cause an old_string-not-found error.

## Completion
When ALL of the following are true:
1. commands/finesse.md: (a) "Skill" in allowed-tools, (b) /finesse-execute format in single + multi-workflow sections, (c) no remaining `$(cat` references, (d) three acceptance options via AskUserQuestion, (e) pre-flight validation check section, (f) updated philosophy and rules text, (g) Presentation item 9 references /finesse-execute
2. commands/finesse-help.md: (a) /finesse-execute + /cancel-finesse-execute + /finesse-validate-execute documented, (b) execution layer section present, (c) /finesse-execute format in output section, (d) "What Happens" step 10 updated
3. skills/meta-prompting/SKILL.md: (a) /finesse-execute in file output format section, (b) /finesse-execute in execution graph per-wave commands
4. skills/task-workflows/SKILL.md: per-wave /finesse-execute command examples in Multi-Workflow section
5. Zero `/ralph-loop:ralph-loop` command strings across all 4 files
6. Zero `$(cat` patterns across all 4 files (includes both `$(cat ralph-plans/...` and generic `$(cat ...)` references)

Output <promise>FINESSE_EXECUTION_LAYER_INTEGRATION_COMPLETE</promise>. Do not output the promise unless every criterion is met.
