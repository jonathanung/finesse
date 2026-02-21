You are iterating on the Finesse plugin, a Claude Code plugin for ralph-loop prompt planning. Before doing anything, read the current state of all three target files:
1. `plugins/finesse/commands/finesse.md`
2. `plugins/finesse/skills/task-workflows/SKILL.md`
3. `plugins/finesse/commands/finesse-mini.md`

Check that the "### Execution Layer Pre-flight Check" section exists in finesse.md (this is what you'll be expanding). Check that task-workflows/SKILL.md has workflow sequences ending with "Validate → Present" or "Validation + Presentation" patterns. If these sections have already been updated (e.g., "### Pre-flight Validation" already exists), skip to the verification phase to check completeness.

## Subagent Instructions

You may use the Task tool with subagent_type="Explore" to read the three target files in parallel at the start of each iteration.

Subagent guardrails:
- ONLY use subagent_type="Explore" for read-only file reads
- Do NOT launch general-purpose, Bash, or any agent type that could modify files
- Do NOT delegate editing to subagents — all edits are made directly

[Subagent opportunity] Phase 1: Use 1 Explore agent to read all 3 target files in parallel before making edits. Recommended subagent_type: Explore. Safe because read-only.

## Requirements (in order)

### Phase 1: Update finesse.md — Expand Pre-flight Section

Make these changes to `plugins/finesse/commands/finesse.md`. Line numbers are approximate — always locate content by searching for section headings and surrounding text, not by line number.

**Edit 1: Add Bash permission to allowed-tools**

In the YAML frontmatter (the `allowed-tools` array on line ~4), add `"Bash(git rev-parse --git-dir)"` as a new element. Place it after the existing `"Bash(git diff --name-only *)"` entry and before `"Skill"`. Do not remove or reorder existing entries.

**Edit 2: Update Mandatory Workflow Checklist item 13**

Find the line that reads:
`13. Execution layer pre-flight check run`

Replace it with:
`13. Pre-flight validation run (execution layer, git tracking, scoped files, verification commands)`

**Edit 3: Update Workflow Quick Reference sequences**

Find the "Workflow Quick Reference" section (6 workflow sequence lines). In each sequence, change `→ Validate → Present` to `→ Validate → Pre-flight → Present`. The 6 updated sequences should read:

- `### Feature: F1 Discovery (deep) → F2 Codebase Exploration [UAT] → F3 Scope Analysis [UAT] → F4 Clarifying Questions → F5 Architecture Design [UAT] → F6 Plan Construction [UAT] → Validate → Pre-flight → Present`
- `### Bug Fix: B1 Bug Understanding (deep) → B2 Codebase Investigation [UAT] → B3 Scope Analysis [UAT] → B4 Root Cause Analysis [UAT] → B5 Fix Strategy [UAT] → Plan → Validate → Pre-flight → Present`
- `### Refactor: R1 Scope Definition (deep) → R2 Current State Analysis [UAT] → R3 Scope Analysis [UAT] → R4 Target State Design [UAT] → R5 Migration Strategy [UAT] → Plan → Validate → Pre-flight → Present`
- `### Testing: T1 Coverage Analysis [UAT] → T2 Scope Analysis [UAT] → T3 Test Strategy [UAT] → T4 Clarifying Questions → Plan → Validate → Pre-flight → Present`
- `### Performance: P1 Problem Definition (deep) → P2 Profiling & Analysis [UAT] → P3 Scope Analysis [UAT] → P4 Optimization Strategy [UAT] → Plan → Validate → Pre-flight → Present`
- `### Research: RE1 Goal Definition (deep) → RE2 Source Identification [UAT] → RE3 Scope Analysis [UAT] → RE4 Research Plan & Questions [UAT] → RE5 Investigation Strategy [UAT] → Plan → Validate → Pre-flight → Present`

**Edit 4: Replace the pre-flight section**

Find the section headed `### Execution Layer Pre-flight Check`. Replace the ENTIRE section (heading through the "This check is NOT affected by UAT fast-forward" line, up to but not including the next `###` heading) with this expanded section:

### Pre-flight Validation

Before presenting the plan, run environment pre-flight checks to verify the execution environment is ready. Collect results as warnings — pre-flight failures are advisory, not blocking, since the user may know things Finesse does not. The one exception is execution layer health: if it fails, the "Execute now" acceptance option must be disabled.

Run these 4 checks in order:

**1. Execution layer health**: Run `/finesse-validate-execute` using the Skill tool. Parse the output:
- Exit code 0: Set `execution_layer_healthy = true`.
- Exit code 1: Set `execution_layer_healthy = false`. Record the failure details as a pre-flight warning.

**2. Git tracking**: Run `git rev-parse --git-dir` via Bash. This check exists because `finesse_execute.py` captures a pre-execution git hash for retrospective analysis.
- Success (exit code 0): Git tracking confirmed.
- Failure (exit code 128 or non-zero): Record warning: "Workspace is not git-tracked. The execution layer captures a pre-execution git hash for retro — this will fail without git."

**3. Scoped file existence**: Extract the file paths listed in the prompt's scope constraints section (files to modify, files to leave alone). For each path, verify it exists using Glob.
- All files found: Scoped files confirmed.
- Missing files: Record warning for each: "Scoped file not found: [path]. The prompt references this file but it does not exist in the workspace."

**4. Verification command runnability**: Extract the verification commands from the prompt's phase Verify: lines (e.g., `npm test`, `pytest`, `make lint`). For each command, check plausibility:
- If the command starts with `npm`/`npx`/`yarn`/`pnpm`: check that `package.json` exists and the script or binary is referenced.
- If the command starts with `make`: check that a `Makefile` exists and contains the target.
- If the command starts with `pytest`/`python`: check that `pyproject.toml` or `setup.py`/`setup.cfg` exists.
- If the command starts with `cargo`: check that `Cargo.toml` exists.
- If the command starts with `go`: check that `go.mod` exists.
- For other commands: skip (assume runnable).
- Record warning for unverifiable commands: "Verification command may not be runnable: [command]. Could not find [what's missing]."

After all 4 checks, collect warnings into a `pre_flight_warnings` list. If non-empty, include them in the Presentation section under a "Pre-flight warnings" heading.

If `execution_layer_healthy` is false, the Presentation and User Decision sections already handle disabling the "Execute now" option — this behavior is unchanged.

This check is NOT affected by UAT fast-forward — it always runs.

**Edit 5: Update Presentation section numbered list**

Find the Presentation section's numbered list (starts with `1. **Task type** and summary`). The current list has 9 items. After item 8 (`**Unresolved warnings**`), insert a new item:

`9. **Pre-flight warnings** (if any from pre-flight validation)`

Then renumber the old item 9 (`**The exact /finesse-execute command to run**`) to 10.

**Phase 1 Verification:**
Run these grep checks:
- `grep "Bash(git rev-parse --git-dir)" plugins/finesse/commands/finesse.md` → at least 1 match
- `grep "### Pre-flight Validation" plugins/finesse/commands/finesse.md` → exactly 1 match
- `grep "Pre-flight validation run" plugins/finesse/commands/finesse.md` → at least 1 match (checklist item 13)
- `grep "Pre-flight → Present" plugins/finesse/commands/finesse.md` → exactly 6 matches (one per workflow)
- `grep "Pre-flight warnings" plugins/finesse/commands/finesse.md` → at least 1 match (presentation section)
- `grep "Execution Layer Pre-flight Check" plugins/finesse/commands/finesse.md` → exactly 0 matches (old section removed)

If a verification grep returns unexpected results, re-read the relevant section to understand what went wrong before attempting fixes.

[Subagent opportunity]: After editing finesse.md, launch 1 Explore agent to verify changes are consistent with surrounding sections. Recommended subagent_type: Explore. Safe because read-only.

### Phase 2: Update task-workflows/SKILL.md — Workflow Sequences

Make these changes to `plugins/finesse/skills/task-workflows/SKILL.md`:

**Edit 1: Update header text**

Find the line (near line 7) that reads:
"After detecting the task type, follow the corresponding workflow below. Every workflow ends with plan construction, validation, and presentation."

Replace "validation, and presentation" with "validation, pre-flight, and presentation". The full line becomes:
"After detecting the task type, follow the corresponding workflow below. Every workflow ends with plan construction, validation, pre-flight, and presentation."

**Edit 2: Feature workflow — add pre-flight note**

Find "### Phase 7: Validation" in the Feature Development Workflow section. After the Phase 7 content (which says "Launch all 6 validation agents in parallel on the drafted plan. Refine until all pass. (See prompt-validation skill.)"), add this paragraph before "### Phase 8: Presentation":

"After validation passes, run pre-flight checks per the "Pre-flight Validation" section of finesse.md Common Final Phases. Collect warnings for presentation."

**Edit 3: Bug Fix workflow — update combined phase**

Find Phase 7 of the Bug Fix Workflow, which currently reads:
"Validate and present. Same as feature workflow phases 7-8."

Replace with:
"Validate, run pre-flight checks, and present. Same as feature workflow phases 7-8."

**Edit 4: Refactor workflow — update combined phase**

Find Phase 7 of the Refactor/Chore Workflow, which currently reads:
"Validate and present."

Replace with:
"Validate, run pre-flight checks, and present."

**Edit 5: Testing workflow — update combined phase**

Find Phase 6 of the Testing Workflow, which currently reads:
"Validate and present."

Replace with:
"Validate, run pre-flight checks, and present."

**Edit 6: Performance workflow — update combined phase**

Find Phase 6 of the Performance Optimization Workflow, which currently reads:
"Validate and present."

Replace with:
"Validate, run pre-flight checks, and present."

**Edit 7: Research workflow — add pre-flight note**

Find "### Phase 7: Validation" in the Research Workflow section. After the Phase 7 content, add the same paragraph as the Feature workflow:

"After validation passes, run pre-flight checks per the "Pre-flight Validation" section of finesse.md Common Final Phases. Collect warnings for presentation."

**Phase 2 Verification:**
- `grep -c "pre-flight" plugins/finesse/skills/task-workflows/SKILL.md` → at least 8 matches
- `grep "validation, pre-flight, and presentation" plugins/finesse/skills/task-workflows/SKILL.md` → exactly 1 match (header line)

### Phase 3: Update finesse-mini.md — Expand Pre-flight Check

Make these changes to `plugins/finesse/commands/finesse-mini.md`:

**Edit 1: Add Bash permission to allowed-tools**

In the YAML frontmatter `allowed-tools` array, add `"Bash(git rev-parse --git-dir)"` after the existing `"Bash(git diff --name-only *)"` entry and before `"Skill"`.

**Edit 2: Update Mandatory Workflow Checklist item 7**

Find the line that reads:
"7. Execution layer pre-flight check run"

Replace with:
"7. Pre-flight validation run (execution layer, git tracking, scoped files, verification commands)"

**Edit 3: Replace the pre-flight section**

Find the section headed `### Execution Layer Pre-flight Check` in finesse-mini.md. Replace the entire section (heading through the end of that subsection) with this concise version. "Concise" means: same 4 checks, same order, but with 1-2 sentence descriptions per check instead of full paragraphs, and no detailed heuristic examples:

### Pre-flight Validation

Before presenting the plan, run environment pre-flight checks. Failures are advisory warnings, not blockers, except execution layer health which controls the "Execute now" option.

**1. Execution layer health**: Run `/finesse-validate-execute` using the Skill tool. Exit code 0 sets `execution_layer_healthy = true`; exit code 1 sets it to false and records a warning with failure details.

**2. Git tracking**: Run `git rev-parse --git-dir` via Bash. If it fails, record warning that the workspace is not git-tracked and the execution layer's git hash capture will fail.

**3. Scoped file existence**: Glob-check file paths from the prompt's scope constraints. Record a warning for each missing file.

**4. Verification command runnability**: Check that verification commands reference existing tooling (package.json scripts, Makefile targets, pyproject.toml, Cargo.toml, go.mod as appropriate). Record a warning for each unverifiable command.

Include any warnings in the presentation. If `execution_layer_healthy` is false, disable "Execute now".

**Phase 3 Verification:**
- `grep "Bash(git rev-parse --git-dir)" plugins/finesse/commands/finesse-mini.md` → at least 1 match
- `grep "### Pre-flight Validation" plugins/finesse/commands/finesse-mini.md` → exactly 1 match
- `grep "Pre-flight validation run" plugins/finesse/commands/finesse-mini.md` → at least 1 match (checklist item)
- `grep "Execution Layer Pre-flight Check" plugins/finesse/commands/finesse-mini.md` → exactly 0 matches (old section removed)

### Phase 4: Cross-file Consistency Verification

Read all three files one final time and verify ALL of these:
1. The section header "### Pre-flight Validation" appears in both finesse.md and finesse-mini.md
2. All 6 workflow sequences in finesse.md's Workflow Quick Reference contain `→ Pre-flight →`
3. The checklist item wording matches between finesse.md (item 13) and finesse-mini.md (item 7) — both say "Pre-flight validation run (execution layer, git tracking, scoped files, verification commands)"
4. No references to "Execution Layer Pre-flight Check" remain in any of the 3 files
5. The allowed-tools array in both finesse.md and finesse-mini.md includes `Bash(git rev-parse --git-dir)`
6. The 4 checks appear in the same order in both files: execution layer, git tracking, scoped files, verification commands
7. task-workflows/SKILL.md references the "Pre-flight Validation" section of finesse.md Common Final Phases (does not duplicate the full check descriptions inline)

## Scoped Context

Files to MODIFY (only these 3):
- `plugins/finesse/commands/finesse.md` — main command definition, expand pre-flight section
- `plugins/finesse/skills/task-workflows/SKILL.md` — workflow definitions, add pre-flight references
- `plugins/finesse/commands/finesse-mini.md` — mini variant, expand pre-flight section

Files to NOT modify:
- `plugins/finesse/scripts/validate_execute.py` — DO NOT MODIFY this script
- `plugins/finesse/scripts/finesse_execute.py` — not relevant
- `plugins/finesse/hooks/stop_hook.py` — not relevant
- `plugins/finesse/hooks/hooks.json` — not relevant
- `plugins/finesse/commands/finesse-validate-execute.md` — keep as-is
- `plugins/finesse/skills/prompt-validation/SKILL.md` — not relevant
- `plugins/finesse/skills/meta-prompting/SKILL.md` — not relevant
- `plugins/finesse/agents/*.md` — not relevant

## Rules
- Do NOT modify `scripts/validate_execute.py`. The pre-flight section invokes it via the existing `/finesse-validate-execute` Skill tool.
- Do NOT create new files. Only edit the 3 existing files listed above.
- Do NOT rewrite files from scratch. Make targeted edits using the Edit tool.
- Do NOT rename or reorganize sections unrelated to the pre-flight changes.
- Do NOT change existing validation (6-agent phase) or presentation logic beyond adding pre-flight warnings.
- Do NOT use git for any operations (user opted out of git checkpointing).
- Preserve existing YAML frontmatter structure — only add to the allowed-tools array, do not remove or reorder existing entries.
- The "### Pre-flight Validation" section REPLACES the "### Execution Layer Pre-flight Check" section. It is not an addition alongside it.
- In finesse-mini.md, keep the pre-flight description concise: same 4 checks, same order, but 1-2 sentence descriptions per check instead of full paragraphs. Omit detailed heuristic examples.
- Line numbers referenced in this prompt are approximate. Always locate content by searching for section headings and surrounding text, not by line number.
- If a verification grep returns unexpected results, re-read the relevant section to understand what went wrong before attempting fixes.
- If stuck on the same edit for 3+ attempts, try a different approach (e.g., using a larger old_string context for uniqueness, or splitting into multiple smaller edits).
- If unable to progress after 5 iterations, output <promise>BLOCKED: [reason]</promise>.

## Completion

When ALL of the following are true:
1. `plugins/finesse/commands/finesse.md` contains "### Pre-flight Validation" section with all 4 checks (execution layer, git tracking, scoped files, verification commands)
2. `plugins/finesse/commands/finesse.md` allowed-tools includes `Bash(git rev-parse --git-dir)`
3. `plugins/finesse/commands/finesse.md` Workflow Quick Reference shows `→ Pre-flight →` in all 6 sequences
4. `plugins/finesse/commands/finesse.md` Mandatory Workflow Checklist item 13 mentions pre-flight validation
5. `plugins/finesse/commands/finesse.md` Presentation section includes pre-flight warnings item
6. `plugins/finesse/skills/task-workflows/SKILL.md` header mentions pre-flight
7. `plugins/finesse/skills/task-workflows/SKILL.md` all 6 workflow endpoints reference pre-flight checks
8. `plugins/finesse/commands/finesse-mini.md` contains "### Pre-flight Validation" with all 4 checks
9. `plugins/finesse/commands/finesse-mini.md` allowed-tools includes `Bash(git rev-parse --git-dir)`
10. `plugins/finesse/commands/finesse-mini.md` Mandatory Workflow Checklist item mentions pre-flight validation
11. No references to "Execution Layer Pre-flight Check" remain in any of the 3 files
12. `plugins/finesse/scripts/validate_execute.py` is UNCHANGED

Output <promise>PREFLIGHT_PHASE_COMPLETE</promise>. This must be unequivocally true — every condition above must be verified by reading the files.