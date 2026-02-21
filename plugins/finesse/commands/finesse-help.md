---
description: "Explain Finesse plugin and available commands"
---

# Finesse Plugin Help

Please explain the following to the user:

## What is Finesse?

Finesse is a planning and validation tool that transforms vague task descriptions into battle-tested ralph-loop prompts. It does NOT run loops — it plans, validates, and hands off a ready-to-run command.

Finesse automatically detects your task type and runs a tailored workflow:

| Task Type | Workflow |
|---|---|
| **Feature** | Discovery (deep) → Codebase Exploration [UAT] → Scope Analysis [UAT] → Clarifying Questions → Architecture Design [UAT] → Plan Construction [UAT] → Validate → Present |
| **Bug Fix** | Bug Understanding (deep) → Codebase Investigation [UAT] → Scope Analysis [UAT] → Root Cause Analysis [UAT] → Fix Strategy [UAT] → Plan → Validate → Present |
| **Refactor** | Scope Definition (deep) → Current State Analysis [UAT] → Scope Analysis [UAT] → Target State Design [UAT] → Migration Strategy [UAT] → Plan → Validate → Present |
| **Testing** | Coverage Analysis [UAT] → Scope Analysis [UAT] → Test Strategy [UAT] → Clarifying Questions → Plan → Validate → Present |
| **Performance** | Problem Definition (deep) → Profiling & Analysis [UAT] → Scope Analysis [UAT] → Optimization Strategy [UAT] → Plan → Validate → Present |
| **Research** | Goal Definition (deep) → Source Identification [UAT] → Scope Analysis [UAT] → Research Plan [UAT] → Investigation Strategy [UAT] → Plan → Validate → Present |

`(deep)` = thorough probing phase with iterative back-and-forth. `[UAT]` = User Acceptance Testing checkpoint (see below).

## Available Commands

### /finesse <TASK> [--max-refinements N]

Plan a ralph-loop prompt for any development task.

**Arguments:**
- `TASK` — What you want to do (can be vague — Finesse will clarify)
- `--max-refinements N` — Max planning refinement cycles (default: 5). This is Finesse's planning budget, NOT the ralph-loop iteration count.

**Usage:**
```
/finesse Build a REST API for managing todos with auth
/finesse Fix the token refresh bug in auth.ts
/finesse Refactor the database layer to use repository pattern
/finesse Add integration tests for the payments module
/finesse Optimize the search endpoint — it's taking 3+ seconds
/finesse Research whether we should use Redis or Memcached for caching
/finesse Investigate the trade-offs between REST and GraphQL for our API
```

### /finesse-mini <TASK>

Lightweight micro-task prompt planning — a single-pass alternative to `/finesse`.

Designed for small, obvious changes where the full multi-phase workflow is overkill. Finesse Mini runs a streamlined 3-phase pipeline: Quick Exploration (1–5 files, no parallel agents) → Prompt Construction (all 10 mandatory attributes, compact format) → Lightweight Validation (3 validators instead of 6). No UAT checkpoints, no architecture design, no subagent configuration, no exploration cache.

If the task turns out to be bigger than expected (>5 files, >8 estimated iterations, or requires architectural decisions), Finesse Mini will suggest switching to `/finesse`.

**Arguments:**
- `TASK` — What you want to do (should be specific and small-scoped)

**Usage:**
```
/finesse-mini Fix the typo in src/utils/format.ts line 42
/finesse-mini Add missing null check in handleSubmit
/finesse-mini Rename userId to user_id across the auth module
/finesse-mini Add a test case for the empty-input edge case in parseConfig
/finesse-mini Fix the ESLint error in src/api/client.ts
/finesse-mini Update the timeout config value from 30s to 60s
```

**Compared to `/finesse`:**
| | `/finesse` | `/finesse-mini` |
|---|---|---|
| Workflow phases | 6–8 with UAT checkpoints | 3, no UAT |
| Exploration | 2–3 parallel agents, cache | 1–5 file reads, no agents |
| Validators | 6 in parallel | 3 in parallel |
| Refinement cycles | Up to `--max-refinements` (default 5) | 1 max |
| Subagent config | Optional | Skipped |
| Context budget | Estimated | Skipped |
| Architecture design | Multiple approaches | Skipped |
| Acceptance options | Execute / Copy / Save | Execute / Copy |

### /finesse-linear <LINEAR_ISSUE> [--max-refinements N] [--mini]

Fetch a Linear issue and plan it with `/finesse` or `/finesse-mini`.

Accepts a Linear issue URL or raw issue ID (e.g., `PF-254`). Fetches all issue data (title, description, labels, priority, assignees, comments, state, git branch, parent/sub-issues, relations) via the Linear MCP server and formats it into a structured task description. Then delegates to `/finesse` (or `/finesse-mini` with `--mini`).

Requires the `linear-server` MCP server to be configured. Run the command without setup to see configuration instructions.

**Arguments:**
- `LINEAR_ISSUE` — A Linear issue URL or raw issue ID (e.g., `PF-254`, `https://linear.app/team/issue/PF-254/fix-auth-bug`)
- `--max-refinements N` — Passed through to `/finesse` (ignored with `--mini`)
- `--mini` — Delegate to `/finesse-mini` instead of `/finesse`

**Usage:**
```
/finesse-linear PF-254
/finesse-linear https://linear.app/myteam/issue/PF-254/fix-the-auth-bug
/finesse-linear PF-254 --mini
/finesse-linear PF-254 --max-refinements 3
```

### /cancel-finesse

Cancel the current planning session without saving.

### /finesse-resume [PATH]

Resume an interrupted Finesse planning session from a working file.

**Arguments:**
- No arguments — scans `finesse-plans/` for working files, lists if multiple
- `PATH` — path to a specific working file to resume from

**Usage:**
```
/finesse-resume
/finesse-resume finesse-plans/build-rest-api-working.md
```

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

### /finesse-edit <PLAN_NAME> [--max-refinements N]

Edit an existing accepted plan — apply targeted changes, re-validate, and re-save.

Loads plan files from `finesse-plans/`, presents the current plan, collects your edit instructions, applies targeted changes to the prompt (does NOT rebuild from scratch), re-validates with all 6 validation agents, shows a diff summary of what changed, and re-saves on acceptance. Does NOT re-run exploration, discovery, architecture, or scope analysis — those are already baked into the plan.

**Arguments:**
- `PLAN_NAME` — Name of the plan to edit. If omitted, lists available plans.
- `--max-refinements N` — Max validation refinement cycles (default: 5).

**Usage:**
```
/finesse-edit fix-token-refresh
/finesse-edit fix-token-refresh --max-refinements 3
/finesse-edit
```

### /finesse:finesse-execute [ARGS]

Launch a Finesse-managed ralph loop from a plan or inline prompt.

**Arguments:**
- `--prompt-file PATH` — Path to prompt file (e.g., `finesse-plans/my-plan.md`)
- `--completion-promise-file PATH` — Path to completion promise file
- `--max-iterations N` — Maximum iterations before auto-stop
- No args — auto-detects the most recent plan from `finesse-plans/`
- Inline prompt text — for quick tasks without /finesse planning

**Usage:**
```
/finesse:finesse-execute --prompt-file finesse-plans/fix-token-refresh.md --completion-promise-file finesse-plans/fix-token-refresh-promise.txt --max-iterations 8
/finesse:finesse-execute
```

### /cancel-finesse-execute

Cancel an active Finesse execution loop. Saves telemetry to `.finesse/run-log.json` for retro analysis.

### /finesse-validate-execute

Validate the Finesse execution layer. Runs structural and functional checks against the setup script, stop hook, hook registration, and command definitions. Exit code 0 = all checks pass.

### /finesse-waves <subcommand> [session-name]

Wave execution orchestration for multi-workflow plans. Launches parallel sub-workflows in isolated git worktrees via tmux, monitors completion, and handles merge reconciliation.

This command outputs terminal commands for you to run directly — the orchestrator runs outside Claude Code.

**Subcommands:**
- `start <session-name>` — Parse execution-graph.md, show dry-run confirmation, launch wave 1
- `status` — Show status of all active wave sessions
- `attach <session-name>` — Attach to the tmux session for observation
- `stop <session-name>` — Gracefully stop, wait for current iterations, save telemetry
- `cleanup <session-name>` — Remove worktrees and tmux sessions for a completed session
- `merge <session-name>` — Manually trigger merge reconciliation after conflict resolution

**Usage:**
```
/finesse-waves start my-api-project
/finesse-waves status
/finesse-waves attach my-api-project
/finesse-waves stop my-api-project
/finesse-waves cleanup my-api-project
/finesse-waves merge my-api-project
```

## What Happens

1. **Task type detection** — Finesse classifies your task (feature, bugfix, refactor, testing, performance, research)
2. **Scope analysis** — For large tasks, Finesse may propose splitting into multiple sub-workflows that can run in parallel
3. **Type-specific workflow** — Runs the appropriate multi-phase workflow:
   - Features get codebase exploration (with cache for faster repeat sessions) + 3 architecture approaches
   - Bug fixes get root cause analysis + fix strategy
   - Refactors get dependency mapping + migration strategy
   - etc.
4. **Clarifying questions** — Finesse asks you to resolve ambiguities (never guesses)
5. **UAT checkpoints** — At strategic phases, Finesse presents its work and asks you to accept, provide feedback, make specific changes, or skip remaining checkpoints
6. **Plan construction** — Builds a structured ralph-loop prompt with cold start, phases, verification commands, guardrails. Optionally includes subagent spawning instructions for parallel execution.
7. **Parallel validation** — 6 agents review the plan simultaneously
8. **Refinement** — Issues fixed automatically or flagged for your input
9. **Presentation** — Plan shown for your approval
10. **On acceptance** — Three files saved to `finesse-plans/` (prompt, promise, metadata), you choose to execute immediately, copy the command, or save only

## UAT Checkpoints

At strategic phases in each workflow (marked `[UAT]` in the table above), Finesse presents the phase output and asks for your input before proceeding. You can:

- **Accept** — continue to the next phase
- **Provide feedback** — the phase re-runs incorporating your feedback
- **Make specific changes** — targeted edits to the phase output without re-running
- **Accept and skip remaining UAT** — auto-approve all future checkpoints in this session (for experienced users)

Discovery phases (marked `(deep)`) always require full confirmation, even if UAT is fast-forwarded. Finesse will never infer answers to questions it can ask you directly.

## Agents

### Planning Agents
| Agent | Role |
|---|---|
| code-explorer | Traces execution paths, maps architecture, identifies patterns |
| code-architect | Designs implementation approaches with trade-offs; proposes task decomposition |
| task-decomposer | Validates decomposition proposals: sub-workflow scoping, dependencies, wave grouping, coverage |

### Validation Agents
| Agent | Focus |
|---|---|
| clarity-checker | Are requirements specific enough for an autonomous agent? |
| completion-validator | Are completion criteria binary, explicit, and unambiguous? |
| scope-safety-reviewer | Are scope constraints and safety guardrails in place? |
| phase-structure-analyzer | Are phases ordered with verification commands and cold start? |
| failure-mode-auditor | Are stuck-state recovery and anti-thrashing rules present? |
| goal-achievement-auditor | Does the prompt achieve the stated goal? Truth coverage + dependency flow |

## Output

Accepted plans are saved as three files in `finesse-plans/`:
- `<name>.md` — prompt text only (referenced by `/finesse:finesse-execute` via `--prompt-file`)
- `<name>-promise.txt` — completion promise text only
- `<name>-plan.md` — metadata: task type, approach, rationale, iteration reasoning

For multi-workflow tasks, files are organized under `finesse-plans/<session-name>/` with wave/task subdirectories. See Multi-Workflow Output below.

You get a ready-to-run command (or can execute directly):
```
/finesse:finesse-execute --prompt-file finesse-plans/<name>.md --completion-promise-file finesse-plans/<name>-promise.txt --max-iterations <N>
```

## Multi-Workflow Output

For large tasks, Finesse may decompose the work into multiple ralph-loop runs organized into execution waves:

- **Wave 1**: Independent sub-tasks that can run in parallel
- **Wave 2+**: Sub-tasks that depend on earlier waves completing

Output goes to `finesse-plans/<session>/wave-N/<task>/` instead of the flat format. An `execution-graph.md` shows the dependency structure and all commands.

Single-workflow tasks still use the flat `finesse-plans/<name>.md` format.

## Plan Rejection

If you reject a plan with feedback:
- Finesse's refinement counter resets
- Subsequent passes make targeted edits (the skeleton is already built)
- A "What changed since last review:" diff summary shows exactly what was revised (bulleted list of semantic changes)
- All 6 validators re-run on the revised plan
- You see the revised plan with the diff summary above validation results for another round of approval

## Resuming Sessions

Finesse saves progress to working files during long planning sessions. If a session is interrupted (context compaction, crash, new session), use `/finesse-resume` to continue:

- The resume command recovers task type, completed phases, user decisions, and prompt drafts
- Discovery phases are restarted from scratch (they require live interaction)
- Later phases resume from where they left off
- All UAT checkpoint decisions are preserved
- Works with both single-workflow and multi-workflow (decomposed) sessions

## Exploration Cache

Finesse caches codebase exploration findings in `.finesse/exploration-cache.json` to speed up repeat planning sessions:

- **Cache hit**: If fewer than 50 files changed since last cache, Finesse loads cached findings and runs a lighter, task-specific exploration
- **Cache miss**: If many files changed or no cache exists, full exploration runs as normal
- **Staleness**: Cache entries referencing files that changed since last session are automatically pruned
- **Configuration**: Override the threshold in `.finesse/config.json` (default: 50 files)
- **Location**: `.finesse/` is gitignored — cache is local to your machine
- **Reset**: Delete `.finesse/exploration-cache.json` to force full re-exploration

## Execution Layer

Finesse ships its own execution layer and no longer requires the ralph-wiggum plugin as a separate install. The execution layer includes a setup script, stop hook, and per-iteration telemetry for post-execution retrospectives via `/finesse-retro`.

Use `/finesse-validate-execute` to verify the execution layer is healthy on your machine.

For multi-workflow plans, use `/finesse-waves` to launch parallel wave execution instead of manually running each sub-workflow.

## When to Use Finesse

### Use `/finesse-linear` when:
- You have a Linear issue you want to plan
- You want all issue context (description, comments, sub-issues) pulled automatically
- Saves manual copy-pasting of issue details into the task description

### Use `/finesse-mini` for:
- Micro-tasks touching 1–5 files with obvious changes
- Fixing typos, linter errors, or compiler warnings
- Adding missing imports, null checks, or type annotations
- Renaming a variable or function across a few files
- Adding a single test case
- Updating a config value
- Any task where you already know exactly what needs to change

### Use `/finesse` for:
- Any task you want to run autonomously via ralph-loop
- Features requiring architectural decisions
- Complex bugs where root cause isn't obvious
- Large refactors touching many files
- Test suites covering significant surface area
- Research spikes, feasibility studies, or architecture comparisons
- Tasks touching more than 5 files
- Tasks where the approach isn't immediately obvious

### Skip both when:
- You already have a well-structured ralph-loop prompt
- The task doesn't need autonomous execution at all
