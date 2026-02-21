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
5. ALL 6 validation agents launched in parallel (Step 5)
6. All CRITICAL and HIGH validation issues resolved (Step 5)
7. Pre-flight validation run (Step 6)

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

## Step 5: Validation

Launch ALL 6 validation agents in parallel via the Task tool. Pass the full edited prompt text to each agent:

1. **clarity-checker** — requirements unambiguous for autonomous agent
2. **completion-validator** — binary criteria, explicit promise
3. **scope-safety-reviewer** — scope, guardrails, safety
4. **phase-structure-analyzer** — cold start, phases, verification commands
5. **failure-mode-auditor** — stuck-state recovery, anti-thrashing
6. **goal-achievement-auditor** — goal achievement, truth coverage, dependency flow

All agents use the same verdict vocabulary: `PASS`, `FAIL`, or `NEEDS_REWORK`.

### Severity Tiers

| Tier | Condition | Behavior |
|------|-----------|----------|
| **CRITICAL** | scope-safety-reviewer returns `FAIL` | Blocks presentation unconditionally. Must fix before presenting. |
| **HIGH** | clarity-checker, phase-structure-analyzer, or completion-validator returns `FAIL` | Blocks presentation. Must fix before presenting. |
| **MEDIUM** | goal-achievement-auditor or failure-mode-auditor returns `FAIL` | Should fix within refinement budget. Can present with explicit warnings if budget exhausted. |
| **LOW** | Any agent returns `NEEDS_REWORK` | Fix if budget allows after higher tiers resolved. |

### Handling Verdicts

- **All PASS**: Proceed to pre-flight validation.
- **Any CRITICAL or HIGH issues**: Must fix before presenting. Issues requiring user input → ask the user. Issues fixable by you → fix directly.
- **Any MEDIUM issues**: Fix within refinement budget. If budget exhausted, present with explicit warnings listing each issue, its tier, and which agent flagged it.
- **Any LOW issues**: Fix if budget allows after all higher-tier issues are resolved.

When refinement budget drops below 50% remaining, prioritize CRITICAL and HIGH issues exclusively.

Each fix-and-revalidate cycle costs one refinement iteration against the `--max-refinements` budget. When revalidating after fixes, re-run ALL 6 agents to catch regressions.

If budget exhausted with only MEDIUM/LOW unresolved: present with explicit warnings.

## Step 6: Pre-flight Validation

Run 4 pre-flight checks (advisory, not blocking except execution layer health):

**1. Execution layer health**: Run `/finesse-validate-execute` using the Skill tool.
- Exit code 0: Set `execution_layer_healthy = true`.
- Exit code 1: Set `execution_layer_healthy = false`. Record the failure details as a pre-flight warning.

**2. Git tracking**: Run `git rev-parse --git-dir` via Bash.
- Success: Git tracking confirmed.
- Failure: Record warning: "Workspace is not git-tracked. The execution layer captures a pre-execution git hash for retro — this will fail without git."

**3. Scoped file existence**: Extract file paths from the edited prompt's scope constraints section. For each path, verify it exists using Glob.
- Missing files: Record warning for each: "Scoped file not found: [path]."

**4. Verification command runnability**: Extract verification commands from phase `Verify:` lines. Check plausibility:
- `npm/npx/yarn/pnpm`: check `package.json` exists
- `make`: check `Makefile` exists with target
- `pytest/python`: check `pyproject.toml` or `setup.py`/`setup.cfg` exists
- `cargo`: check `Cargo.toml` exists
- `go`: check `go.mod` exists
- Others: skip
- Record warning for unverifiable commands.

Collect all warnings into a `pre_flight_warnings` list.

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
1. Reset refinement counter to 0.
2. Snapshot the current prompt text as the **pre-edit version**.
3. Make **targeted edits** to the prompt based on the feedback — do NOT rebuild from scratch.
4. Generate a **new diff summary** comparing the pre-edit and post-edit prompt text.
5. Re-validate ALL 6 agents on the revised prompt.
6. Re-present via ExitPlanMode with the new diff summary included. Repeat until accepted.

**If REJECTED without feedback:**
1. Ask the user what specifically needs to change.
2. Do NOT re-present the same plan unchanged.

---

## Diff Summary Format

When generating a diff summary, compare the pre-edit and post-edit text and produce a concise bulleted list of semantic changes. This is NOT a unified diff — it is a human-readable summary.

**Rules:**
- Start each bullet with a prescribed action verb: **Added**, **Removed**, **Changed**, **Moved**, **Replaced**, **Tightened**, **Relaxed**, **Merged**, **Split**
- Use natural phrasing after the verb — no rigid template
- Include before/after values when relevant (e.g., "Changed Phase 2 verification command from `npm test` to `npm run test:integration`")
- Group bullets by section when there are many changes (e.g., "Cold start", "Phase 2", "Rules", "Completion criteria")
- Omit sections with no changes
- Keep each bullet to one line
- Maximum 15 bullets — if more changes exist, summarize the remainder as "... and N additional minor edits"

**Examples:**
- Added guardrail: Do NOT modify config files
- Changed Phase 2 verification command from `npm test` to `npm run test:integration`
- Increased max-iterations recommendation from 12 to 15 with reasoning
- Added new Phase 3 for database migration
- Removed scope constraint on `src/legacy/` directory
- Tightened completion criteria to require all linter warnings resolved, not just errors
