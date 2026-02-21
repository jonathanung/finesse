You are iterating on the Finesse plugin at `/workspace/plugins/finesse/` to add a new `/finesse-retro` command for post-execution retrospective analysis of ralph-loop runs. Before doing anything, check the current state by reading the key files and determining what has been completed vs what remains.

On cold start, determine your resume point by running these checks in reverse phase order — the first check that FAILS is where you resume:

1. Final check: Run ALL of the following — they must ALL succeed:
   - `grep "finesse-retro" plugins/finesse/commands/finesse-help.md` matches
   - `test -f plugins/finesse/commands/finesse-retro.md` file exists
   - `grep "## Step 8" plugins/finesse/commands/finesse-retro.md` matches (confirms file is complete)
   - `grep "baseline_commit" plugins/finesse/commands/finesse.md` matches
   - `grep "baseline_commit" plugins/finesse/commands/finesse-resume.md` matches
   - `grep "baseline_commit" plugins/finesse/skills/meta-prompting/SKILL.md` matches
   If ALL true: all work is done. Output the completion promise.
2. Check Phase 3: `grep "finesse-retro" plugins/finesse/commands/finesse-help.md` — if no match, resume at Phase 3.
3. Check Phase 2: `test -f plugins/finesse/commands/finesse-retro.md` — if file doesn't exist, resume at Phase 2. If it exists but `grep "## Step 8" plugins/finesse/commands/finesse-retro.md` finds no match, the file is incomplete — resume at Phase 2 and complete it.
4. Check Phase 1: `grep "baseline_commit" plugins/finesse/commands/finesse.md` — if no match, start at Phase 1.

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

Phase 1: Add plan metadata fields to Finesse's plan output

  Read all three target files first before making any edits.

  1a. In `plugins/finesse/commands/finesse.md`, find the "If ACCEPTED" section under "### User Decision". Make two changes:
    - In the numbered step that describes writing the plan metadata file (`ralph-plans/<name>-plan.md — metadata for human reference: task type, summary, ...`), append to the end of the metadata description list: `, baseline_commit (git rev-parse HEAD captured before writing plan files), git_config (user's git configuration: checkpointing yes/no, granularity, push yes/no), subagent_enabled (whether subagent instructions were included)`
    - Before the step that writes the three files (step 2 in the "If ACCEPTED" list), add a new sub-step: `1.5. Capture baseline commit by running git rev-parse HEAD. Include this as the baseline_commit field in the plan metadata file.`

  Also update the "If ACCEPTED (Multi-Workflow)" section: find the line describing `plan.md` as "sub-workflow metadata" and expand it to "sub-workflow metadata (includes baseline_commit, git_config, subagent_enabled in addition to task type, approach, and iteration reasoning)". Add the same baseline commit capture sub-step before the file-writing step.

  1b. In `plugins/finesse/commands/finesse-resume.md`, make the IDENTICAL changes to its "### User Decision" section. This file has its own copy of the User Decision content. Find and edit the same patterns.

  IMPORTANT: finesse.md and finesse-resume.md have very similar content. Use enough surrounding context in Edit tool calls to ensure uniqueness within each file. Read the file first, identify the exact line content, and include distinctive surrounding text.

  1c. In `plugins/finesse/skills/meta-prompting/SKILL.md`, find the "## File Output Format" section (around line 96). After the existing bullet points describing the three files, add a new subsection:

  ```markdown
  ### Plan Metadata Fields

  The `<name>-plan.md` file contains these fields for human reference and downstream tooling (e.g., `/finesse-retro`):

  | Field | Source | Description |
  |---|---|---|
  | Task Type | Task classification | feature, bugfix, refactor, testing, performance, or research |
  | Summary | User task description | 1-2 sentence description of the task |
  | Codebase Context | Exploration phase | Key files, patterns, and conventions discovered |
  | Chosen Approach | Architecture phase | Selected approach with rationale |
  | Recommended --max-iterations | Plan construction | Iteration count with reasoning |
  | Context Budget Estimate | Budget estimation | Pressure rating, file breakdown, cost range, disclaimer |
  | Validation Results | Validation phase | Per-agent verdict and notes |
  | Unresolved Warnings | Validation phase | Issues not resolved within refinement budget |
  | baseline_commit | `git rev-parse HEAD` before file write | Git commit hash at plan creation time, used by `/finesse-retro` for PR review |
  | git_config | Git Configuration Prompt | User's git choices: checkpointing (yes/no), granularity (phase/change/custom), push (yes/no) |
  | subagent_enabled | Subagent Configuration Prompt | Whether subagent instructions were included in the prompt (yes/no) |
  ```

  Verify: Run these commands — ALL must produce matches:
  - `grep "baseline_commit" plugins/finesse/commands/finesse.md`
  - `grep "baseline_commit" plugins/finesse/commands/finesse-resume.md`
  - `grep "baseline_commit" plugins/finesse/skills/meta-prompting/SKILL.md`
  - `grep "git_config" plugins/finesse/commands/finesse.md`
  - `grep "git_config" plugins/finesse/commands/finesse-resume.md`
  - `grep "git_config" plugins/finesse/skills/meta-prompting/SKILL.md`
  - `grep "subagent_enabled" plugins/finesse/commands/finesse.md`
  - `grep "subagent_enabled" plugins/finesse/commands/finesse-resume.md`
  - `grep "subagent_enabled" plugins/finesse/skills/meta-prompting/SKILL.md`
  [Subagent opportunity]: Spawn a Bash subagent to run all 9 verification grep commands while beginning Phase 2. Phase 2 creates a new file (finesse-retro.md) that does not overlap with Phase 1's modified files.

Phase 2: Create the finesse-retro.md command file

  Create `plugins/finesse/commands/finesse-retro.md`. Before writing, read `plugins/finesse/commands/finesse-resume.md` and `plugins/finesse/commands/cancel-finesse.md` to understand the command file pattern (YAML frontmatter structure, section organization, tool usage patterns).

  The file must contain:

  **YAML Frontmatter:**
  ```yaml
  ---
  description: "Perform post-execution retrospective analysis on a completed ralph-loop run"
  argument-hint: "PLAN_NAME"
  allowed-tools: ["Task", "Read", "Glob", "Grep", "Bash", "Write(ralph-plans/*)", "AskUserQuestion"]
  ---
  ```

  NOTE: Do NOT include EnterPlanMode or ExitPlanMode in allowed-tools. The retro command is interactive, not a plan-mode command.

  **Markdown body** with these sections in order:

  ```markdown
  # Finesse Retro — Post-Execution Retrospective

  Perform retrospective analysis on a completed ralph-loop run. This command reads plan metadata, gathers execution data from the user, and produces a timestamped retro document. Optionally performs PR review against the original plan scope and generates validated fix-loop prompts for identified gaps.

  This command only writes to `ralph-plans/`. It is read-only against all other project files except when running verification commands from the original plan (which require user confirmation).
  ```

  **## Step 1: Resolve Plan Name**
  - Parse `$ARGUMENTS` as the plan name
  - If empty: use Glob to scan `ralph-plans/*-plan.md`, list available plans, ask user to pick one via AskUserQuestion
  - If provided: check for exact match at `ralph-plans/<name>-plan.md`
  - If no exact match: use Glob for `ralph-plans/*-plan.md`, filter for entries containing the argument as a substring, list matching candidates via AskUserQuestion
  - If no matches at all: say "No plan found matching '<name>' in ralph-plans/. Available plans:" and list all `-plan.md` files. Stop.

  **## Step 2: Load Plan Data**
  - Read the plan metadata file (`ralph-plans/<name>-plan.md`). Extract:
    - Task type (from `## Task Type` section)
    - Summary (from `## Summary` section)
    - Recommended --max-iterations (from `## Recommended --max-iterations` heading — parse the number)
    - baseline_commit (from `## baseline_commit` or from inline mention — may not exist in older plans)
    - git_config (from `## git_config` or inline mention — may not exist in older plans)
    - subagent_enabled (from `## subagent_enabled` or inline mention — may not exist in older plans)
  - Read the prompt file (`ralph-plans/<name>.md`). Extract:
    - Scoped files: look for patterns like "Only modify files in", "Do NOT modify anything in", or file path lists
    - Phase structure: look for "Phase N:" or "### Phase N" headings
    - Completion criteria: look for "## Completion" section content
    - Verification commands: look for "Verify:" lines within phases
    - Guardrails: look for "## Rules" section, especially "Do NOT" lines
  - Read the promise file (`ralph-plans/<name>-promise.txt`) if it exists
  - If any file is missing, report which files were found and which are missing. Continue with available data — do not stop.

  **## Step 3: Gather Execution Data**
  Use AskUserQuestion to ask two questions in a single call:
  - Question 1: "What was the actual outcome of the ralph-loop run?" — Options: "Completed successfully" / "Blocked (could not finish)" / "Manually stopped"
  - Question 2: "How many iterations did the ralph-loop actually use?" — Options: generate ranges based on plan's estimated max-iterations (e.g., if estimated 15: "1-5", "6-10", "11-15", "15+"). User can also enter an exact number via Other.

  **## Step 4: Check for Existing Retro**
  Use Glob to check if `ralph-plans/<name>-retro*.md` files already exist.
  - If found: use AskUserQuestion: "A retro document already exists for this plan (<filename>). What should we do?" with options:
    - "Overwrite" — replace the existing retro with a new one
    - "Create timestamped version" — save as `<name>-retro-<YYYYMMDD-HHMMSS>.md` alongside the existing one
    - "Cancel" — stop the retro process
  - If not found: proceed with default name `<name>-retro.md`

  **## Step 5: Mode 1 — Retrospective Analysis (Always Runs)**

  Compare estimated iterations (from plan metadata `Recommended --max-iterations`) vs actual iterations (from user in Step 3). Calculate efficiency ratio: `actual / estimated`.

  Use AskUserQuestion with multiSelect to ask: "What challenges did the ralph-loop encounter? Select all that apply:" with options:
  - "Got stuck on a specific error"
  - "Missing guardrails led to unwanted behavior"
  - "Scope was too broad or too narrow"
  - "Completion criteria were ambiguous"
  - "Phases were in wrong order or had missing dependencies"
  (User can add free text via Other)

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

  **## Step 6: Mode Selection Checkpoint**

  Use AskUserQuestion: "Retro complete and saved. Would you like to also:" with options:
  - "[A] Run PR review on the changes" — proceed to Step 7 only, then stop
  - "[B] Generate fix loop prompts for gaps found" — proceed to Steps 7 AND 8 (PR review is required for fix loops)
  - "[C] Both A and B" — proceed to Steps 7 AND 8
  - "[D] Done — just keep the retro" — output retro file path and stop

  If user selects [B], inform them: "Fix loop generation requires PR review data to identify gaps. Running PR review first, then generating fix loops." Then proceed to Steps 7 and 8.

  If user selects [D], output: "Retro saved to `ralph-plans/<retro-filename>`. Done." and stop.

  **## Step 7: Mode 2 — PR Review**

  **Get baseline commit:**
  - If `baseline_commit` was found in plan metadata (Step 2), use it
  - Otherwise, use AskUserQuestion: "No baseline commit found in plan metadata (older plan format). What was the git commit hash before the ralph-loop started? You can find this with `git log --oneline`." (User enters hash via Other)

  **Analyze the diff:**
  - Run `git diff --name-only <baseline_commit>..HEAD` to get list of changed files
  - Run `git diff --stat <baseline_commit>..HEAD` for change statistics

  **Scope compliance check:**
  - Compare each changed file against the scoped files extracted from the original prompt (Step 2)
  - Files IN the original scope: PASS
  - Files NOT in the original scope: WARN if they are test files or config related to scoped code, FAIL if they are unrelated
  - Files in scope that were NOT changed: note as potential gaps

  **Phase completion check:**
  - For each phase extracted from the original prompt (Step 2), check if the diff contains changes to the files expected by that phase
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

  **## Step 8: Mode 3 — Generate Fix Loops**

  Based on findings from the retro (Step 5) and PR review (Step 7), identify specific gaps that warrant fix loops. Each gap becomes one fix-loop prompt.

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
  /ralph-loop:ralph-loop $(cat ralph-plans/<name>-retro-fix-<N>.md) --completion-promise "$(cat ralph-plans/<name>-retro-fix-<N>-promise.txt)" --max-iterations=<M>
  ```

  **## Retro Document Format**

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

  **## PR Review Output Format**

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

  Verify Phase 2: Run ALL of the following — they must ALL match:
  - `test -f plugins/finesse/commands/finesse-retro.md`
  - `grep "^---" plugins/finesse/commands/finesse-retro.md | head -1` (YAML frontmatter exists)
  - `grep "allowed-tools" plugins/finesse/commands/finesse-retro.md` (frontmatter has tool permissions)
  - `grep "## Step 1" plugins/finesse/commands/finesse-retro.md`
  - `grep "## Step 2" plugins/finesse/commands/finesse-retro.md`
  - `grep "## Step 3" plugins/finesse/commands/finesse-retro.md`
  - `grep "## Step 4" plugins/finesse/commands/finesse-retro.md`
  - `grep "## Step 5" plugins/finesse/commands/finesse-retro.md`
  - `grep "## Step 6" plugins/finesse/commands/finesse-retro.md`
  - `grep "## Step 7" plugins/finesse/commands/finesse-retro.md`
  - `grep "## Step 8" plugins/finesse/commands/finesse-retro.md`
  - `grep "## Retro Document Format" plugins/finesse/commands/finesse-retro.md`
  - `grep "## PR Review Output Format" plugins/finesse/commands/finesse-retro.md`
  - `grep -i "fuzzy\|partial match\|substring" plugins/finesse/commands/finesse-retro.md` (fuzzy plan name resolution present)
  - `grep "Mode 2.*required\|PR review.*required\|requires.*PR review\|requires Mode 2" plugins/finesse/commands/finesse-retro.md` (Mode 3 gating on Mode 2)
  - `grep "6 validation agents\|ALL 6 validation\|all 6 validator" plugins/finesse/commands/finesse-retro.md` (fix-loop validation pipeline)
  - `grep "ralph-plans/" plugins/finesse/commands/finesse-retro.md` (output to ralph-plans/)

Phase 3: Update finesse-help.md

  Read `plugins/finesse/commands/finesse-help.md`. In the "## Available Commands" section, after the `/finesse-resume` entry (which ends before "## What Happens"), add:

  ```markdown
  ### /finesse-retro <PLAN_NAME>

  Perform post-execution retrospective on a completed ralph-loop run.

  **Arguments:**
  - `PLAN_NAME` — Name of the plan to analyze (fuzzy matching supported). If omitted, lists available plans.

  **Modes:**
  - **Retro (always)** — Compare estimated vs actual iterations, capture what worked and lessons learned
  - **PR Review (optional)** — Analyze git diff against original plan's scope, phases, and completion criteria
  - **Fix Loops (optional)** — Generate validated follow-up ralph-loop prompts for identified gaps

  **Usage:**
  ```
  /finesse-retro fix-token-refresh
  /finesse-retro
  ```
  ```

  Verify Phase 3: Run BOTH of the following:
  - `grep -c "finesse-retro" plugins/finesse/commands/finesse-help.md` must return 3 or more (section title, description lines, usage examples)
  - `grep "### /finesse-retro" plugins/finesse/commands/finesse-help.md` must match (confirms section heading exists, not just scattered mentions)

## Rules
- Run verification commands after every phase. Fix failures before moving on.
- Do NOT rewrite files from scratch. Make targeted edits using the Edit tool.
- Do NOT delete existing content in modified files unless replacing it with updated content.
- Do NOT make git commits. Do NOT push to remote repositories.
- Do NOT add unnecessary abstractions or extra files beyond the 5 specified.
- Only modify files in `plugins/finesse/commands/` and `plugins/finesse/skills/meta-prompting/`.
- Read the actual file content before making edits — understand the surrounding context.
- If stuck on the same error for 3+ attempts (e.g., Edit tool uniqueness failures), try an alternative approach: expand the old_string context, use a different anchor point, or read the file again to verify current state.
- When editing `finesse.md` and `finesse-resume.md`, be careful — these files share similar content. Always include enough surrounding context in Edit tool old_string to ensure uniqueness within the target file.
- Do NOT modify any files outside the 5 specified files. Do NOT create any new skill or agent files.
- If unable to make progress after 5 iterations on the same issue, document blockers and output <promise>BLOCKED</promise>.

## Completion
When ALL phases are complete and ALL verification commands pass cleanly:
- Phase 1: `baseline_commit`, `git_config`, and `subagent_enabled` each appear in all three target files (finesse.md, finesse-resume.md, meta-prompting/SKILL.md) — 9 grep checks total
- Phase 2: `finesse-retro.md` exists AND all of the following are true:
  - All 8 steps present (Step 1 through Step 8)
  - Both output format sections present (Retro Document Format, PR Review Output Format)
  - YAML frontmatter with allowed-tools present
  - Fuzzy plan name resolution logic present (grep for fuzzy/partial/substring)
  - Mode 3 gating on Mode 2 documented (grep for PR review required)
  - Fix-loop validation pipeline referenced (grep for 6 validation agents)
  - Output directed to ralph-plans/ (grep for ralph-plans/)
- Phase 3: `finesse-help.md` has a `### /finesse-retro` section heading AND mentions `finesse-retro` at least 3 times

Output <promise>FINESSE_RETRO_COMPLETE</promise>. This must be unequivocally true.
Do not output the completion promise unless every criterion is met.
Do not lie even if you think you should exit.
