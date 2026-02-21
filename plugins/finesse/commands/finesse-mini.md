---
description: "Lightweight micro-task prompt planning — single-pass alternative to /finesse"
argument-hint: "TASK_DESCRIPTION"
allowed-tools: ["Task", "Read", "Glob", "Grep", "Bash(mkdir -p finesse-plans/*)", "Bash(mkdir -p finesse-plans/**/*)", "Write(finesse-plans/*)", "Write(finesse-plans/**/*)", "Bash(mkdir -p .finesse)", "Write(.finesse/*)", "Bash(git rev-parse HEAD)", "Bash(git diff --name-only *)", "Bash(git rev-parse --git-dir)", "Skill", "AskUserQuestion", "EnterPlanMode", "ExitPlanMode"]
hide-from-slash-command-tool: "true"
---

# Finesse Mini — Micro-Task Prompt Planner

## Critical Rules — READ BEFORE ANYTHING ELSE

All identity rules (planning-only, never implement, plan mode, explore first, ask clarifications, file structure, scope-safety, baseline commit, allowed agents, write permissions, core philosophy) are defined in the **planner-identity** skill and injected by `identity_hook.py` before this command runs. Those rules are non-negotiable and not repeated here.

The following rules are specific to the `/finesse-mini` micro-task workflow:

- The ralph-loop iteration count is YOUR recommendation (3-8 based on file count).
- Every prompt must follow the meta-prompting skill template with all 10 mandatory attributes.
- Maximum 1 refinement cycle for validation failures. If still failing, present with warnings.
- The Task tool may ONLY launch these agent types: scope-safety-reviewer, completion-validator, goal-achievement-auditor. Do NOT launch code-explorer, code-architect, general-purpose, Bash, or any other agent type. (This overrides the broader list in planner-identity rule 10.)
- Do NOT create working files. Micro-tasks complete within a single context window.
- Do NOT use the exploration cache. Read files directly.
- File naming: derive `<name>` from the first 3-4 words of the task description in kebab-case (e.g., `fix-typo-format-ts`).

## Mandatory Workflow Checklist

You MUST complete ALL 3 phases IN ORDER. Do NOT call ExitPlanMode until all steps are done:

1. Phase 1: Quick Exploration completed (1-5 files read)
2. Task size gate evaluated (>5 files or >8 iterations = suggest /finesse)
3. Phase 2: Prompt constructed with all 10 mandatory attributes
4. Git Configuration prompted (mandatory)
5. Phase 3: All 3 validators launched in parallel
6. All CRITICAL validation issues resolved
7. Pre-flight validation run (execution layer, git tracking, scoped files, verification commands)

If ANY step was skipped, STOP and return to the first skipped step.

---

Finesse Mini is a lightweight single-pass alternative to `/finesse`, designed for tasks that are small enough that the full multi-phase workflow with UAT checkpoints and 6 parallel validators is overkill. Examples: fix a specific typo, add a missing import, rename a variable across a few files, add a single test case, fix a linter error, update a config value, add a missing null check.

## Argument Parsing

Parse `$ARGUMENTS`:
- Everything is the **task description**. There are no flags.
- If `$ARGUMENTS` is empty or blank, ask the user what they want to do. Do NOT proceed with an empty task.

## Step 0: Enter Plan Mode

Enter plan mode immediately. All work happens in plan mode until the plan is presented.

---

## Phase 1: Quick Exploration

Read only the files the user explicitly mentions or that are obviously relevant from the task description. This is a targeted, minimal exploration — NOT a codebase-wide architecture mapping.

### Rules

- Read **1–5 files** maximum using Read and Grep directly.
- Do NOT launch parallel agents. Do NOT use Task tool for exploration.
- Focus on: the file(s) to change, their immediate imports/dependencies, and any test files that cover them.
- Identify the verification command (e.g., `npm test`, `pytest`, `cargo test`, `go test ./...`) by checking for test configuration files or existing test scripts.

### Task Size Gate

During exploration, evaluate whether this task is truly a micro-task. If ANY of the following are true:

1. The task touches **more than 5 files**, OR
2. The estimated iteration count would exceed **8**, OR
3. The task requires **architectural decisions** (choosing between patterns, designing new abstractions, multi-component coordination)

Then present this warning:

> This task looks bigger than a micro-task. Consider using `/finesse` instead for the full planning pipeline.

Use `AskUserQuestion` with two options:
1. **Proceed with mini** — continue with the lightweight workflow anyway
2. **Switch to /finesse** — abort and recommend the user run `/finesse` with the same task description

If the user chooses to switch, output: "Run `/finesse <original task description>` for the full planning pipeline." and STOP.

---

## Phase 2: Prompt Construction

Build a complete ralph-loop prompt using all 10 mandatory attributes from the **meta-prompting** skill. The prompt should be compact since the task is small, but every mandatory attribute MUST be present.

### Git Configuration Prompt

Before assembling the prompt, ask the user about git usage. This is mandatory.

Use `AskUserQuestion`:

**Question 1**: "Should the ralph-loop agent use git to checkpoint progress?"
- Options: "Yes" / "No"

**If Yes**, ask Questions 2 and 3 together in a single `AskUserQuestion` call:

**Question 2**: "What commit granularity should the agent use?"
- Options: "After each phase" / "After each change" / "Custom"

**Question 3**: "Should the agent push commits to the remote?"
- Options: "Yes" / "No"

Include the appropriate git rules in the prompt's `## Rules` section per the meta-prompting skill's Git Configuration Rules section.

### Prompt Assembly

The prompt MUST include all 10 mandatory attributes:

1. **Cold start paragraph** — task-specific orientation. Example: "You are iterating on [project]. Your task is [micro-task]. Check current file state before making changes."
2. **Ordered phases** — typically 1–3 phases for a micro-task (e.g., Phase 1: Make the change, Phase 2: Verify)
3. **Verification commands** — specific commands discovered during exploration (e.g., `npm test`, `npx tsc --noEmit`)
4. **Scope constraints** — which files to modify (explicit list), which files to leave alone
5. **Guardrails** — "Do NOT" rules (e.g., "Do NOT modify files outside the listed scope", "Do NOT refactor surrounding code", "Do NOT add unrelated changes")
6. **Stuck-state handling** — what to do when blocked (e.g., "If the test framework is missing, output BLOCKED: [reason]")
7. **Completion signal** — explicit `<promise>` with ALL conditions
8. **Binary completion criteria** — every requirement checkable by running a command
9. **Conservative iteration limit** — 3–8 depending on file count (1 file = 3, 2–3 files = 5, 4–5 files = 8)
10. **Zero ambiguity about done** — "Do not output promise unless every criterion is met"

### Iteration Count

Determine `--max-iterations` based on file count:
- **1 file**: 3 iterations
- **2–3 files**: 5 iterations
- **4–5 files**: 8 iterations

### Skip Entirely

- Subagent configuration — micro-tasks do not benefit from parallel agents
- Context budget estimation — micro-tasks will never hit pressure thresholds
- Exploration cache — not worth the overhead for targeted reads

---

## Phase 3: Lightweight Validation

Launch exactly **3 validators in parallel** using the Task tool:

1. **scope-safety-reviewer** — Are scope constraints and safety guardrails in place? (Always, non-negotiable)
2. **completion-validator** — Are completion criteria binary, explicit, and unambiguous? (Ensures the agent knows when to stop)
3. **goal-achievement-auditor** — Does the prompt actually solve the stated problem? (Ensures correctness)

Skip: clarity-checker, phase-structure-analyzer, failure-mode-auditor (micro-task prompts are simple enough that these rarely catch issues).

### Handling Verdicts

- If **all 3 pass**: proceed to presentation.
- If **scope-safety-reviewer returns FAIL**: this is CRITICAL. Fix the prompt and re-validate all 3 agents. This counts as the 1 allowed refinement cycle.
- If **completion-validator or goal-achievement-auditor returns FAIL**: fix the prompt and re-validate all 3 agents. This counts as the 1 allowed refinement cycle.
- If **any validator returns NEEDS_REWORK**: fix if this is the first cycle; otherwise present with a note.
- **Maximum 1 refinement cycle.** If any validator still fails after 1 fix-and-revalidate cycle, present the plan with warnings attached. Do NOT loop further.
- If scope-safety-reviewer returns FAIL with HIGH_RISK, ask the user to acknowledge the risk before presenting.

> **Note**: The full `/finesse` command uses a 4-tier severity system (CRITICAL/HIGH/MEDIUM/LOW) with budget-aware prioritization. `/finesse-mini` simplifies this to a single-pass approach: scope-safety-reviewer FAIL blocks unconditionally (equivalent to CRITICAL); completion-validator or goal-achievement-auditor FAIL gets one fix attempt then present-with-warnings (collapses HIGH and MEDIUM); any NEEDS_REWORK presents with a note (equivalent to LOW).

---

## Presentation

### Pre-flight Validation

Before presenting the plan, run environment pre-flight checks. Failures are advisory warnings, not blockers, except execution layer health which controls the "Execute now" option.

**1. Execution layer health**: Run `/finesse-validate-execute` using the Skill tool. Exit code 0 sets `execution_layer_healthy = true`; exit code 1 sets it to false and records a warning with failure details.

**2. Git tracking**: Run `git rev-parse --git-dir` via Bash. If it fails, record warning that the workspace is not git-tracked and the execution layer's git hash capture will fail.

**3. Scoped file existence**: Glob-check file paths from the prompt's scope constraints. Record a warning for each missing file.

**4. Verification command runnability**: Check that verification commands reference existing tooling (package.json scripts, Makefile targets, pyproject.toml, Cargo.toml, go.mod as appropriate). Record a warning for each unverifiable command.

Include any warnings in the presentation. If `execution_layer_healthy` is false, disable "Execute now".

### Present via ExitPlanMode

The plan file must contain:
1. **Task summary**
2. **Files identified** — from exploration
3. **The full ralph-loop prompt**
4. **Recommended `--max-iterations`** with reasoning
5. **What changed** (re-presentations only — omit on first presentation). Display the prompt diff summary generated during the rejection handling procedure, under the heading "What changed since last review:". This appears above validation warnings so the user sees what was revised before reviewing validation results. See diff summary rules in the rejection handling section below.
6. **Unresolved warnings** (if any from validation)
7. **Pre-flight warnings** (if any from pre-flight validation)
8. **The exact `/finesse:finesse-execute` command to run**

---

## User Decision

**If ACCEPTED:**

1. Create `finesse-plans/` in workspace root if needed.
2. Write THREE files:
   - `finesse-plans/<name>.md` — the prompt text ONLY (no metadata, no YAML frontmatter, no markdown headers — just the raw prompt)
   - `finesse-plans/<name>-promise.txt` — the completion promise text ONLY
   - `finesse-plans/<name>-plan.md` — metadata: task summary, files identified, recommended iterations with reasoning, git config, unresolved warnings, baseline_commit
3. Capture baseline commit by running `git rev-parse HEAD`. Include as `baseline_commit` in the plan metadata file.
4. Present acceptance options via `AskUserQuestion`:
   - If `execution_layer_healthy` is true, offer 2 options:
     1. **Execute now** — Launch the plan immediately via `/finesse:finesse-execute`
     2. **Copy command** — Output the `/finesse:finesse-execute` command string
   - If `execution_layer_healthy` is false, offer 1 option (with a warning):
     1. **Copy command** — Output the `/finesse:finesse-execute` command string
5. Handle the selected option:
   - **Execute now**: Invoke `/finesse:finesse-execute` using the Skill tool with args `--prompt-file finesse-plans/<name>.md --completion-promise-file finesse-plans/<name>-promise.txt --max-iterations <N>`. The session ends here.
   - **Copy command**: Output the exact command:
     `/finesse:finesse-execute --prompt-file finesse-plans/<name>.md --completion-promise-file finesse-plans/<name>-promise.txt --max-iterations <N>`

**STOP HERE.** After handling the user's acceptance option, your job is done. Do NOT proceed to implement the plan.

**If REJECTED with feedback:**
1. Snapshot the current prompt text as the **pre-edit version** — hold it in context for diff generation.
2. Make targeted edits to the prompt — do NOT rebuild from scratch.
3. Generate a **prompt diff summary** comparing the pre-edit and post-edit prompt text. Rules: start each bullet with a prescribed action verb (Added, Removed, Changed, Moved, Replaced, Tightened, Relaxed, Merged, Split), use natural phrasing, include before/after values when relevant, max 15 bullets. The planning agent generates this inline — no separate agent needed.
4. Re-validate all 3 agents on the revised plan.
5. Re-present via ExitPlanMode with the diff summary included as item 5 in the presentation format. This counts as a refinement cycle.

**If REJECTED without feedback:**
1. Ask the user what specifically needs to change.
2. Do NOT re-present the same plan unchanged.

