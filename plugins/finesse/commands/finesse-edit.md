---
description: "Edit an existing accepted plan, re-validate, and re-save"
argument-hint: "PLAN_NAME [--max-refinements N]"
allowed-tools: ["Task", "Read", "Glob", "Grep", "Write(finesse-plans/*)", "Write(finesse-plans/**/*)", "Bash(git rev-parse HEAD)", "Bash(git rev-parse --git-dir)", "Skill", "AskUserQuestion", "EnterPlanMode", "ExitPlanMode"]
hide-from-slash-command-tool: "true"
---

# Finesse Edit — Plan Editor & Re-Validator

Edit an existing accepted plan by applying targeted changes, re-validating with all 6 agents, and re-saving on acceptance. This command skips exploration, discovery, architecture, and scope analysis — those outputs are already baked into the loaded plan.

## Critical Rules — READ BEFORE ANYTHING ELSE

All identity rules (planning-only, never implement, plan mode, explore first, ask clarifications, file structure, scope-safety, baseline commit, allowed agents, write permissions, core philosophy) are defined in the **planner-identity** skill and injected by `identity_hook.py` before this command runs. Those rules are non-negotiable and not repeated here.

The following rules are specific to the `/finesse-edit` workflow:

- NEVER re-run exploration, discovery, architecture design, or scope analysis. Those outputs are baked into the existing plan.
- Make TARGETED edits to the existing prompt — do NOT rebuild from scratch.
- All 6 validation agents MUST run on the edited plan. No shortcuts.
- Maximum refinement cycles default to 5 (overridable via `--max-refinements N`).
- Edit sessions do NOT create working files. They complete within a single context window.
- The Task tool may ONLY launch these agent types: clarity-checker, completion-validator, scope-safety-reviewer, phase-structure-analyzer, failure-mode-auditor, goal-achievement-auditor.
- This command reads from and writes to `finesse-plans/`.
- The final deliverable is ALWAYS the `/finesse:finesse-execute` command using file references. After handling the user's acceptance option (execute, copy, or save), STOP.

## Mandatory Workflow Checklist

Before calling ExitPlanMode, verify:

1. Plan resolved and loaded (Step 2)
2. Current plan presented to user (Step 3)
3. Edit instructions collected (Step 3)
4. Edits applied with diff summary generated (Step 4)
5. Validation + pre-flight via plan-validator agent (Step 5)
6. All CRITICAL and HIGH validation issues resolved (Step 5)

If ANY step was skipped, STOP and return to the first skipped step.

---

## Step 0: Enter Plan Mode

Enter plan mode immediately. All editing work happens in plan mode until the plan is presented.

## Step 1: Argument Parsing

Parse `$ARGUMENTS`:

- Extract `--max-refinements N` if present (default: 5). This is the validation refinement budget.
- Everything remaining after flag extraction is the **plan name**.
- If the plan name is empty or blank after extraction, proceed to auto-detection (see Step 2, No Argument Mode).

## Step 2: Plan Resolution

### No Argument Mode

If no plan name was provided:

1. Use Glob to scan for available plans:
   - Single-workflow: `finesse-plans/*-plan.md`
   - Multi-workflow: `finesse-plans/*/execution-graph.md`
2. If no plans found: say "No plans found in finesse-plans/. Run /finesse first to create a plan." and stop.
3. If exactly one single-workflow plan found: extract the plan name from the filename (strip `-plan.md` suffix) and proceed to loading.
4. If multiple plans found: list each plan with its name, then use `AskUserQuestion` to let the user pick one. Proceed with the selected plan.

### Named Plan Mode

If a plan name was provided:

#### Single-Workflow Resolution

Check for the three-file structure:
- `finesse-plans/<name>.md` (prompt)
- `finesse-plans/<name>-promise.txt` (promise)
- `finesse-plans/<name>-plan.md` (metadata)

Use Glob to verify existence. If the prompt file (`<name>.md`) exists, load as single-workflow.

If the prompt file exists but promise or metadata files are missing, warn: "Found prompt file but missing [list missing files]. Proceeding with available files." Continue with what exists.

#### Multi-Workflow Resolution

If single-workflow prompt file is NOT found, check for multi-workflow structure:

1. Glob for `finesse-plans/<name>/wave-*/*/prompt.md`
2. If matches found, this is a multi-workflow session.
3. List each sub-task with its wave number and task name.
4. Use `AskUserQuestion`: "Which sub-task do you want to edit?" with options listing each sub-task (up to 4 options). The user can specify a different sub-task via Other.
5. Load the selected sub-task's three files: `prompt.md`, `promise.txt`, `plan.md` from `finesse-plans/<name>/wave-<N>/<task>/`.

#### Not Found

If neither single-workflow nor multi-workflow files are found:

1. Error: "No plan found for '<name>'."
2. Show what was checked:
   - `finesse-plans/<name>.md` (single-workflow)
   - `finesse-plans/<name>/` (multi-workflow)
3. Glob for `finesse-plans/*-plan.md` and `finesse-plans/*/execution-graph.md` to list available plans.
4. Stop.

### Load Plan Files

After resolution, read all available plan files:

- **Prompt file**: Read the full prompt text. This is the primary file being edited.
- **Promise file**: Read the promise text (if exists).
- **Metadata file**: Read and extract task type, summary, recommended --max-iterations, baseline_commit, git_config, subagent_enabled (if exists). Handle missing fields gracefully — older plans may lack some metadata.

## Step 3: Present Current Plan & Collect Edit Instructions

Present the loaded plan summary:

**Editing Plan: <name>**

- **Task type**: <from metadata, or "Unknown" if missing>
- **Max iterations**: <from metadata, or "Not specified">
- **Promise**: <promise text, or "No promise file found">
- **Prompt size**: <line count> lines

Use `AskUserQuestion`: "What changes would you like to make to this plan?" with options:

1. **Show full prompt first** — Display the entire prompt text, then re-ask for changes
2. **Describe changes** — Provide a free-text description of what to change (via Other)

If the user selects "Show full prompt first":
1. Display the full prompt content.
2. Re-ask: "Now describe the changes you'd like to make:" with options:
   1. **Describe changes** — Free-text description (via Other)
   2. **Cancel edit** — Exit without changes

If the user selects "Cancel edit" at any point: say "Edit cancelled." and stop.

## Step 4: Apply Edits

1. **Snapshot** the current prompt text as the **pre-edit version** — hold it in context for diff generation.
2. **Apply targeted edits** to the prompt text based on the user's instructions. Make only the changes requested — do NOT rebuild the prompt from scratch.
   - If the user requested adding guardrails: add them to the `## Rules` section.
   - If the user requested adjusting iteration count: update the recommendation and reasoning.
   - If the user requested modifying scope: update the scope constraints section.
   - If the user requested adding phases: insert new phases in the `## Requirements` section with appropriate verification commands.
   - If the user requested changing verification commands: update the relevant `Verify:` lines.
   - If the user requested changing the promise: update the completion signal and snapshot the promise text for diff.
3. **Generate a diff summary** comparing the pre-edit and post-edit prompt text. See Diff Summary Format below.
4. If the promise text was also changed, note this in the diff summary.

## Step 5: Validation & Pre-flight

Delegate validation and pre-flight checks to the **plan-validator** agent via the Task tool. Pass the full edited prompt text, promise text, and `--max-refinements` budget. The agent:

1. Launches all 6 validation agents in parallel (clarity-checker, completion-validator, scope-safety-reviewer, phase-structure-analyzer, failure-mode-auditor, goal-achievement-auditor)
2. Classifies verdicts by severity tier (CRITICAL > HIGH > MEDIUM > LOW)
3. Fixes issues within the refinement budget (CRITICAL and HIGH must be resolved before presenting)
4. Runs 4 pre-flight checks (execution layer health, git tracking, scoped file existence, verification command runnability)
5. Returns consolidated results with per-agent verdicts, any revised prompt text, unresolved warnings, pre-flight warnings, and `execution_layer_healthy` status

If the plan-validator reports issues requiring user input, present those to the user and re-delegate.

If budget exhausted with only MEDIUM/LOW unresolved: present with explicit warnings. If unresolved CRITICAL/HIGH: present with BLOCKING warnings and ask the user whether to proceed.

## Step 7: Presentation

Present the edited plan via ExitPlanMode. The plan file must contain:

1. **Plan name** and task type
2. **Edit summary** — what the user asked to change
3. **What changed** — the diff summary from Step 4
4. **The full edited ralph-loop prompt**
5. **Recommended `--max-iterations`** with reasoning (original or updated)
6. **`--completion-promise`** text
7. **Unresolved warnings** (if any from validation)
8. **Pre-flight warnings** (if any from pre-flight validation)
9. **The exact `/finesse:finesse-execute` command to run**

For single-workflow plans:
```
/finesse:finesse-execute --prompt-file finesse-plans/<name>.md --completion-promise-file finesse-plans/<name>-promise.txt --max-iterations <N>
```

For multi-workflow sub-tasks:
```
/finesse:finesse-execute --prompt-file finesse-plans/<session>/wave-<W>/<task>/prompt.md --completion-promise-file finesse-plans/<session>/wave-<W>/<task>/promise.txt --max-iterations <N>
```

## Step 8: User Decision

**If ACCEPTED:**

1. Capture baseline commit by running `git rev-parse HEAD`.
2. Write updated files:
   - **Single-workflow**:
     - `finesse-plans/<name>.md` — the edited prompt text ONLY (no metadata, no YAML frontmatter — just the raw prompt)
     - `finesse-plans/<name>-promise.txt` — the promise text ONLY (no quotes, no extra content)
     - `finesse-plans/<name>-plan.md` — updated metadata: preserve existing content, append an Edit History section with timestamp, change description, diff summary, and updated baseline_commit
   - **Multi-workflow sub-task**:
     - `finesse-plans/<session>/wave-<W>/<task>/prompt.md` — edited prompt text ONLY
     - `finesse-plans/<session>/wave-<W>/<task>/promise.txt` — promise text ONLY
     - `finesse-plans/<session>/wave-<W>/<task>/plan.md` — updated metadata with Edit History appended
3. Present acceptance options via `AskUserQuestion`:
   - If `execution_layer_healthy` is true, offer 3 options:
     1. **Execute now** — Launch the plan immediately via the Finesse execution layer
     2. **Copy command** — Output the /finesse:finesse-execute command string for manual use
     3. **Save plan only** — Files are saved; no command output
   - If `execution_layer_healthy` is false, offer 2 options (with a warning about execution layer issues):
     1. **Copy command** — Output the /finesse:finesse-execute command string for manual use
     2. **Save plan only** — Files are saved; no command output
4. Handle the selected option:
   - **Execute now**: Invoke `/finesse:finesse-execute` using the Skill tool with args `--prompt-file finesse-plans/<path>.md --completion-promise-file finesse-plans/<path>-promise.txt --max-iterations <N>`. The edit session ends here.
   - **Copy command**: Output the exact command:
     `/finesse:finesse-execute --prompt-file finesse-plans/<path>.md --completion-promise-file finesse-plans/<path>-promise.txt --max-iterations <N>`
   - **Save plan only**: Report "Plan files updated in finesse-plans/. Use `/finesse:finesse-execute --prompt-file finesse-plans/<path>.md --completion-promise-file finesse-plans/<path>-promise.txt --max-iterations <N>` when ready to execute."

**STOP HERE.** After handling the user's acceptance option, your job is done. Do NOT proceed to implement the plan.

**If REJECTED with feedback:**
1. Reset refinement counter, snapshot current prompt, make targeted edits (do NOT rebuild).
2. Generate a new diff summary, re-validate via **plan-validator** agent.
3. Re-present via ExitPlanMode with the diff summary. Repeat until accepted.

**If REJECTED without feedback:**
1. Ask the user what specifically needs to change.
2. Do NOT re-present the same plan unchanged.

---

## Diff Summary Format

For diff summary rules and format, follow the **uat-procedure** skill's Diff Summary Format section. In brief: bulleted list of semantic changes using prescribed action verbs (Added, Removed, Changed, Moved, Replaced, Tightened, Relaxed, Merged, Split), max 15 bullets.
