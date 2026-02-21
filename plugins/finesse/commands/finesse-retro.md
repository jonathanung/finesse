---
description: "Perform post-execution retrospective analysis on a completed ralph-loop run"
argument-hint: "PLAN_NAME"
allowed-tools: ["Task", "Read", "Glob", "Grep", "Bash", "Write(ralph-plans/*)", "AskUserQuestion"]
---

# Finesse Retro — Post-Execution Retrospective

Perform retrospective analysis on a completed ralph-loop run. This command reads plan metadata, gathers execution data from the user, and produces a timestamped retro document. Optionally performs PR review against the original plan scope and generates validated fix-loop prompts for identified gaps.

This command only writes to `ralph-plans/`. It is read-only against all other project files except when running verification commands from the original plan (which require user confirmation).

## Step 1: Resolve Plan Name

Parse `$ARGUMENTS` as the plan name.

- **If empty**: Use Glob to scan `ralph-plans/*-plan.md`, list available plans, and ask the user to pick one via AskUserQuestion.
- **If provided**: Check for an exact match at `ralph-plans/<name>-plan.md`.
  - **If no exact match**: Use Glob for `ralph-plans/*-plan.md`, filter for entries containing the argument as a substring (partial match / fuzzy resolution), and list matching candidates via AskUserQuestion.
  - **If no matches at all**: Say "No plan found matching '<name>' in ralph-plans/. Available plans:" and list all `-plan.md` files. Stop.

## Step 2: Load Plan Data

Read the plan metadata file (`ralph-plans/<name>-plan.md`). Extract:
- Task type (from `## Task Type` section)
- Summary (from `## Summary` section)
- Recommended --max-iterations (from `## Recommended --max-iterations` heading — parse the number)
- baseline_commit (from `## baseline_commit` or from inline mention — may not exist in older plans)
- git_config (from `## git_config` or inline mention — may not exist in older plans)
- subagent_enabled (from `## subagent_enabled` or inline mention — may not exist in older plans)

Read the prompt file (`ralph-plans/<name>.md`). Extract:
- Scoped files: look for patterns like "Only modify files in", "Do NOT modify anything in", or file path lists
- Phase structure: look for "Phase N:" or "### Phase N" headings
- Completion criteria: look for "## Completion" section content
- Verification commands: look for "Verify:" lines within phases
- Guardrails: look for "## Rules" section, especially "Do NOT" lines

Read the promise file (`ralph-plans/<name>-promise.txt`) if it exists.

If any file is missing, report which files were found and which are missing. Continue with available data — do not stop.

## Step 3: Gather Execution Data

Use AskUserQuestion to ask two questions in a single call:

- **Question 1**: "What was the actual outcome of the ralph-loop run?"
  - Options: "Completed successfully" / "Blocked (could not finish)" / "Manually stopped"
- **Question 2**: "How many iterations did the ralph-loop actually use?"
  - Options: generate ranges based on the plan's estimated max-iterations (e.g., if estimated 15: "1-5", "6-10", "11-15", "15+"). User can also enter an exact number via Other.

## Step 4: Check for Existing Retro

Use Glob to check if `ralph-plans/<name>-retro*.md` files already exist.

- **If found**: Use AskUserQuestion: "A retro document already exists for this plan (<filename>). What should we do?" with options:
  - "Overwrite" — replace the existing retro with a new one
  - "Create timestamped version" — save as `<name>-retro-<YYYYMMDD-HHMMSS>.md` alongside the existing one
  - "Cancel" — stop the retro process
- **If not found**: Proceed with default name `<name>-retro.md`.

## Step 5: Mode 1 — Retrospective Analysis (Always Runs)

Compare estimated iterations (from plan metadata `Recommended --max-iterations`) vs actual iterations (from user in Step 3). Calculate efficiency ratio: `actual / estimated`.

Use AskUserQuestion with multiSelect to ask: "What challenges did the ralph-loop encounter? Select all that apply:" with options:
- "Got stuck on a specific error"
- "Missing guardrails led to unwanted behavior"
- "Scope was too broad or too narrow"
- "Completion criteria were ambiguous"
- "Phases were in wrong order or had missing dependencies"

(User can add free text via Other.)

For each selected challenge, use a follow-up AskUserQuestion asking for specific details about that challenge (what error? what guardrail? what was ambiguous?).

Generate the retro document using the Retro Document Format (below). Synthesize:

- **What Worked**: Infer from outcome and efficiency. If completed in fewer iterations than estimated, the prompt was well-structured. Note specific phases or guardrails that worked well based on user feedback.
- **What the Prompt Should Have Said Differently**: Based on user's challenge descriptions. Map each challenge to a specific prompt section that could have prevented it.
- **Suggested Guardrail Additions**: Convert each "missing guardrail" challenge into a specific "Do NOT" or "ALWAYS" rule.
- **Lessons Learned**: Assign severity based on impact:
  - Critical: Challenge caused the loop to fail or block completely
  - High: Challenge wasted 3+ iterations or caused significant rework
  - Medium: Challenge caused 1-2 wasted iterations
  - Low: Minor inconvenience, optimization opportunity

Write the retro document to `ralph-plans/<name>-retro.md` (or timestamped name from Step 4).

## Step 6: Mode Selection Checkpoint

Use AskUserQuestion: "Retro complete and saved. Would you like to also:" with options:
- "[A] Run PR review on the changes" — proceed to Step 7 only, then stop
- "[B] Generate fix loop prompts for gaps found" — proceed to Steps 7 AND 8 (PR review is required for fix loops)
- "[C] Both A and B" — proceed to Steps 7 AND 8
- "[D] Done — just keep the retro" — output retro file path and stop

If user selects [B], inform them: "Fix loop generation requires PR review data to identify gaps. Running PR review first, then generating fix loops." Then proceed to Steps 7 and 8.

If user selects [D], output: "Retro saved to `ralph-plans/<retro-filename>`. Done." and stop.

## Step 7: Mode 2 — PR Review

**Get baseline commit:**
- If `baseline_commit` was found in plan metadata (Step 2), use it.
- Otherwise, use AskUserQuestion: "No baseline commit found in plan metadata (older plan format). What was the git commit hash before the ralph-loop started? You can find this with `git log --oneline`." (User enters hash via Other.)

**Analyze the diff:**
- Run `git diff --name-only <baseline_commit>..HEAD` to get list of changed files.
- Run `git diff --stat <baseline_commit>..HEAD` for change statistics.

**Scope compliance check:**
- Compare each changed file against the scoped files extracted from the original prompt (Step 2).
- Files IN the original scope: PASS
- Files NOT in the original scope: WARN if they are test files or config related to scoped code, FAIL if they are unrelated
- Files in scope that were NOT changed: note as potential gaps

**Phase completion check:**
- For each phase extracted from the original prompt (Step 2), check if the diff contains changes to the files expected by that phase.
- PASS: expected file changes are present in the diff
- WARN: some expected changes are present but the phase appears partially done
- FAIL: no evidence of the phase's expected changes in the diff

**Completion criteria check:**
- For each criterion from the original prompt's Completion section, assess satisfaction:
  - If verification commands exist: present ALL commands to the user via AskUserQuestion: "The following verification commands from the original plan can check completion criteria. Run them all?" with options "Yes, run all" / "Skip verification commands"
  - If user confirms: run each command, record output, classify as PASS (clean output) / FAIL (errors or failures)
  - If no verification commands: assess based on diff evidence, classify as PASS/WARN/FAIL

**Guardrail compliance check:**
- For each "Do NOT" rule from the original prompt's Rules section, check the diff for evidence of violation:
  - "Do NOT rewrite files from scratch" — check if any file has >80% of lines changed
  - "Do NOT delete existing tests" — check if any test files had deletions
  - Other guardrails: assess based on diff patterns
- PASS: no evidence of violation. WARN: ambiguous. FAIL: clear violation.

**Append PR Review section** to the retro document using the PR Review Output Format (below).

## Step 8: Mode 3 — Generate Fix Loops

Based on findings from the retro (Step 5) and PR review (Step 7), identify specific gaps that warrant fix loops. Each gap becomes one fix-loop prompt. Note: Mode 3 requires PR review data from Mode 2 — it cannot run independently.

**Gap identification:**
- Completion criteria with FAIL verdict → fix loop to satisfy that criterion
- Phases with FAIL verdict → fix loop to complete that phase
- Files outside scope with FAIL verdict → cleanup fix loop to revert or properly integrate those changes
- Guardrails with FAIL verdict → fix loop to correct the violation
- Skip WARN verdicts unless the user specifically flagged the issue as a challenge in Step 5

**For each identified gap**, generate a fix-loop prompt set:

File naming: `ralph-plans/<original-name>-retro-fix-<N>.md`, `ralph-plans/<original-name>-retro-fix-<N>-promise.txt`, `ralph-plans/<original-name>-retro-fix-<N>-plan.md` where N starts at 1 and increments.

Each fix-loop prompt (`-retro-fix-<N>.md`) must include:
- **Cold start paragraph**: "You are fixing gaps identified in the retrospective of the '<original-plan-name>' ralph-loop run. Before doing anything, check the current state of the relevant files and determine what needs to be fixed."
- **Narrowly scoped requirements**: Only the specific gap. Single phase if possible.
- **Verification commands**: Specific to the fix (e.g., the failing verification command from PR review, or the specific test that needs to pass)
- **Guardrails**: Original plan's guardrails PLUS any new guardrails from the retro's "Suggested Guardrail Additions"
- **Scope constraints**: Only the files relevant to the specific gap
- **Completion signal**: `<promise><ORIGINAL-NAME>_RETRO_FIX_<N>_COMPLETE</promise>`

Each fix-loop plan metadata (`-retro-fix-<N>-plan.md`) must include:
- Task type (inherit from original or classify as bugfix if it's a correction)
- Summary referencing the original plan
- The specific gap being addressed
- Recommended --max-iterations: 5-8 for simple fixes, 8-12 for complex fixes
- git_config and subagent_enabled inherited from the original plan metadata

**Validation**: For EACH fix-loop prompt, launch ALL 6 validation agents in parallel via the Task tool:
1. clarity-checker
2. completion-validator
3. scope-safety-reviewer
4. phase-structure-analyzer
5. failure-mode-auditor
6. goal-achievement-auditor

Handle validation verdicts using severity tiers:
- CRITICAL (scope-safety-reviewer FAIL): Must fix before presenting
- HIGH (clarity-checker, phase-structure-analyzer, completion-validator FAIL): Must fix before presenting
- MEDIUM (goal-achievement-auditor, failure-mode-auditor FAIL): Fix if within budget, warn if exhausted
- LOW (any NEEDS_REWORK): Fix if budget allows
Maximum 3 refinement cycles per fix-loop prompt.

**Present all fix-loop prompts** to the user. For each, output:
```
### Fix <N>: <gap description>
/ralph-loop:ralph-loop $(cat ralph-plans/<name>-retro-fix-<N>.md) --completion-promise "$(cat ralph-plans/<name>-retro-fix-<N>-promise.txt)" --max-iterations <M>
```

Write all fix-loop files to `ralph-plans/`.

## Retro Document Format

The retro document saved to `ralph-plans/` must follow this template:

```markdown
# Retrospective: <plan-name>

**Date**: <YYYY-MM-DD HH:MM>
**Plan**: <name>-plan.md
**Task Type**: <from plan metadata>

## Execution Summary

| Metric | Estimated | Actual |
|---|---|---|
| Iterations | <from plan metadata> | <from user> |
| Outcome | — | <completed/blocked/manually stopped> |
| Efficiency | — | <actual/estimated as percentage>% |

## What Worked
- <bullet points based on successful aspects — infer from outcome, efficiency, and user feedback>

## What the Prompt Should Have Said Differently
- <bullet points mapping each challenge to a specific prompt section that could have prevented it>

## Suggested Guardrail Additions
- <specific "Do NOT" or "ALWAYS" rules that would have helped, based on challenges encountered>

## Lessons Learned

| Severity | Lesson | Context |
|---|---|---|
| Critical | <lesson> | <what happened and why this severity> |
| High | <lesson> | <what happened> |
| Medium | <lesson> | <what happened> |
| Low | <lesson> | <what happened> |
```

NOTE: The ## PR Review section is appended by Step 7 (Mode 2) if the user selects it. Do NOT include a placeholder PR Review section in Mode 1 output.

## PR Review Output Format

The PR Review section appended to the retro document by Step 7:

```markdown
## PR Review

**Baseline Commit**: <hash>
**Current HEAD**: <hash>
**Files Changed**: <count>

### Scope Compliance

| File | In Original Scope? | Verdict |
|---|---|---|
| <file path> | Yes / No | PASS / WARN / FAIL |

### Phase Completion

| Phase | Expected Changes | Evidence in Diff | Verdict |
|---|---|---|---|
| Phase N: <name> | <expected files/changes> | <found / partial / not found> | PASS / WARN / FAIL |

### Completion Criteria

| Criterion | Verification Command | Result | Verdict |
|---|---|---|---|
| <criterion text> | <command or "manual check"> | <output summary or "N/A"> | PASS / WARN / FAIL |

### Guardrail Compliance

| Guardrail | Evidence | Verdict |
|---|---|---|
| <"Do NOT" rule from original prompt> | <compliant / violation description> | PASS / WARN / FAIL |

### Summary
- **Total checks**: <N>
- **PASS**: <count>
- **WARN**: <count>
- **FAIL**: <count>
```
