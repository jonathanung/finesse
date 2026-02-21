# Finesse

A Claude Code plugin that turns vague task descriptions into validated, ready-to-run prompts for iterative autonomous development — the kind that converge instead of thrashing. Describe what you want in plain English; Finesse plans it, validates it with parallel agents, and executes it.

> **How does iterative execution work?** Finesse ships its own execution layer (based on the [ralph-loop](https://github.com/anthropics/claude-code-plugins) plugin) that repeatedly invokes Claude to work on a task across multiple iterations until a completion condition is met. Each iteration is stateless — the agent starts fresh with only the prompt and the current state of the codebase. This makes prompt quality critical: a vague requirement becomes an infinite loop, a missing guardrail lets the agent delete your tests, and an ambiguous "done" condition means it either exits too early or never stops. Good prompts need [10 specific attributes](#the-10-mandatory-prompt-attributes) that Finesse encodes automatically.

## How It Works

```
/finesse:finesse Build a REST API for managing todos with authentication
```

Finesse detects your task type, explores your codebase, asks you clarifying questions, designs implementation approaches, constructs the prompt, validates it with specialized agents, and presents the result for your approval — then executes it.

```
You → /finesse:finesse "vague idea"
       ↓
  Task Classification (feature / bugfix / refactor / testing / performance / research)
       ↓
  Codebase Exploration (2-3 agents in parallel)
       ↓
  Scope Analysis & Decomposition (split large tasks into parallel sub-workflows?)
       ↓
  Type-Specific Workflow  ←  you answer clarifying questions
       ↓
  Prompt Construction (cold start, ordered phases, verification commands, guardrails)
       ↓
  Parallel Validation (6 agents in parallel)
       ↓
  Refinement (auto-fix or ask you)
       ↓
  Presentation  ←  you approve or reject
       ↓
  On Accept → finesse-plans/ output + execute or copy command(s)
```

## Installation

```bash
# Add the marketplace
/plugin marketplace add jonathanung/finesse

# Install the plugin
/plugin install finesse @ jonathanung-finesse
```

Finesse ships its own execution layer — no additional plugins are required.

## Commands

### `/finesse:finesse <TASK> [--max-refinements N]`

Plan and validate a prompt for any development task.

- `TASK` — What you want to do. Can be vague — Finesse will clarify.
- `--max-refinements N` — Max planning refinement cycles (default: 5). This is Finesse's internal planning budget, **not** the execution iteration count. Finesse determines the iteration count automatically based on task scope.

```bash
# Features
/finesse:finesse Build a REST API for managing todos with auth
/finesse:finesse Add a dark mode toggle to the settings page

# Bug fixes
/finesse:finesse Fix the token refresh bug in auth.ts
/finesse:finesse The search endpoint returns duplicates when filters overlap

# Refactoring
/finesse:finesse Refactor the database layer to use repository pattern
/finesse:finesse Clean up the payment service — it's 800 lines

# Testing
/finesse:finesse Add integration tests for the payments module
/finesse:finesse Write unit tests for the email validation logic

# Performance
/finesse:finesse Optimize the search endpoint — it's taking 3+ seconds
/finesse:finesse The dashboard page takes 5s to load

# Research
/finesse:finesse Research whether we should use Redis or Memcached for caching
/finesse:finesse Investigate the trade-offs between REST and GraphQL for our API
/finesse:finesse Evaluate feasibility of migrating from Postgres to CockroachDB
```

#### Example Output

For `/finesse:finesse Fix the token refresh bug in auth.ts`, Finesse produces something like:

```bash
/finesse:finesse-execute --prompt-file finesse-plans/fix-token-refresh-auth.md --completion-promise-file finesse-plans/fix-token-refresh-auth-promise.txt --max-iterations 8
```

Finesse saves three files:
- `finesse-plans/fix-token-refresh-auth.md` — the prompt only: cold start paragraph, ordered fix-then-test phases, verification commands, and guardrails
- `finesse-plans/fix-token-refresh-auth-promise.txt` — the completion promise text
- `finesse-plans/fix-token-refresh-auth-plan.md` — metadata: task type, codebase context, chosen approach with rationale, iteration reasoning

### `/finesse:finesse-execute [--prompt-file PATH] [--completion-promise-file PATH] [--max-iterations N] [PROMPT...]`

Execute a plan using Finesse's built-in execution layer. Can auto-detect plans from `finesse-plans/`, take explicit file arguments, or accept an inline prompt.

### `/finesse:finesse-mini <TASK>`

Lightweight single-pass alternative to `/finesse` for micro-tasks (fix a typo, add a missing import, rename a variable across a few files). Skips the full multi-phase workflow — explores 1-5 files, constructs a prompt, validates with 3 agents, and presents.

### `/finesse:cancel-finesse`

Cancel the current planning session without saving.

### `/finesse:cancel-finesse-execute`

Cancel an active execution loop.

### `/finesse:finesse-help`

Show a summary of what Finesse does, its agents, and how to use it.

## Task-Specific Workflows

Finesse detects your task type and runs a tailored multi-phase workflow. Every workflow ends with prompt construction, parallel validation, and presentation.

- **Feature Development** (8 phases) — Discovery, codebase exploration with 2-3 agents, scope analysis & decomposition, clarifying questions, architecture design with 3 competing approaches (minimal, clean, pragmatic), construction, validation, presentation. Finesse always presents **3 architecture options** with trade-offs and asks you to choose.
- **Bug Fix** (7 phases) — Bug understanding, codebase investigation tracing the failing execution path, scope analysis & decomposition, root cause analysis with hypothesis and evidence, fix strategy with regression tests, construction, validation.
- **Refactor/Chore** (7 phases) — Scope definition, current state analysis mapping all dependencies and callers, scope analysis & decomposition, target state design, incremental migration strategy (never leaves codebase broken between phases), construction, validation.
- **Testing** (6 phases) — Coverage analysis mapping test framework and gaps, scope analysis & decomposition, test strategy ranked by risk, clarifying questions on mocking/fixtures, construction, validation.
- **Performance** (6 phases) — Problem definition with target metrics, profiling tracing slow paths and flagging O(n^2) patterns, scope analysis & decomposition, optimization strategy ranked by impact with measurable before/after, construction, validation.
- **Research** (8 phases) — Goal definition clarifying the research question and deliverable format, source identification mapping codebase references and prior decisions, scope analysis & decomposition, research plan with outline and clarifying questions, investigation strategy with per-section evidence requirements and anti-rabbit-hole constraints, construction, validation, presentation. Output is a document, not code changes — source code is strictly read-only.

## The 10 Mandatory Prompt Attributes

You don't need to know these to use Finesse — it handles them automatically. This section explains what Finesse encodes into every prompt it produces, so you can audit the output.

| # | Attribute | Why It Matters |
|---|---|---|
| 1 | **Binary completion criteria** | Every requirement checkable by running a command — no subjective "code is clean" |
| 2 | **Explicit completion signal** | `<promise>COMPLETE</promise>` with exact conditions listed |
| 3 | **Self-diagnosing failure instructions** | What to do when stuck — try alternatives, document blockers, output `<promise>BLOCKED</promise>` |
| 4 | **Ordered phases** | "Build auth, then products, then cart" — not a flat list of 20 requirements |
| 5 | **Verification commands** | Specific commands per phase — `npm test`, `curl localhost:3000/health` |
| 6 | **Guardrails against failure modes** | "Do NOT rewrite files from scratch", "Do NOT delete tests to pass the suite" |
| 7 | **Scoped context** | Which files to modify, which to leave alone |
| 8 | **Cold start paragraph** | Orientation for stateless re-entry: check state, identify what's done vs remaining |
| 9 | **Conservative iteration limit** | Right-sized by task type and scope, with reasoning |
| 10 | **Zero ambiguity about "done"** | Anti-premature-exit language, no room to rationalize partial completion |

> **What are `<promise>` tags?** They are the execution layer's mechanism for detecting completion. When the agent outputs a `<promise>` tag matching the completion promise text, the loop stops iterating.

## Agents

### Validation Agents

After constructing a prompt, Finesse launches 6 validation agents **in parallel**. All must pass before the plan is presented to you.

| Agent | Focus | Checks For |
|---|---|---|
| **clarity-checker** | Requirement specificity | Ambiguous text, missing context, implicit assumptions, scope completeness, success criteria clarity |
| **completion-validator** | Completion criteria | Binary criteria, explicit promise tag, anti-premature-exit language |
| **scope-safety-reviewer** | Scope & safety | File boundaries, destructive action guardrails, "Do NOT" rules, iteration limits |
| **phase-structure-analyzer** | Structural clarity | Cold start paragraph, ordered phases, verification commands, phase independence |
| **failure-mode-auditor** | Failure handling | Stuck-state instructions, blocked signal, anti-thrashing rules, task-specific risks |
| **goal-achievement-auditor** | Goal achievement | Truth coverage, dependency flow, phase-to-goal mapping, observable verification |

Each agent returns `PASS`, `FAIL`, or `NEEDS_REWORK`:

- **All PASS** — Plan is ready to present.
- **Any FAIL** — Critical gaps. Finesse fixes what it can and asks you about the rest.
- **Any NEEDS_REWORK** — Fixable issues. Finesse auto-fixes within its refinement budget.

If the scope-safety-reviewer flags `HIGH_RISK`, Finesse will ask you to explicitly acknowledge the risk before proceeding.

### Planning Agents

| Agent | Used In | Role |
|---|---|---|
| **code-explorer** | All workflows | Traces execution paths, maps architecture, identifies patterns and essential files |
| **code-architect** | Feature workflow + scope analysis | Designs implementation approaches with trade-offs; proposes task decomposition |
| **task-decomposer** | Scope analysis (all workflows) | Validates decomposition proposals: sub-workflow scoping, dependencies, wave grouping, coverage |

## Output

When you accept a plan, Finesse:

**Single-workflow tasks:**
1. Creates `finesse-plans/` in your workspace root (if it doesn't exist)
2. Saves three files:
   - `finesse-plans/<name>.md` — the prompt text only
   - `finesse-plans/<name>-promise.txt` — the completion promise text only
   - `finesse-plans/<name>-plan.md` — human-readable metadata: task type, codebase context, chosen approach, rationale, iteration reasoning, unresolved warnings
3. Outputs the exact command:
   ```
   /finesse:finesse-execute --prompt-file finesse-plans/<name>.md --completion-promise-file finesse-plans/<name>-promise.txt --max-iterations <N>
   ```

**Multi-workflow tasks (decomposed):**
1. Creates `finesse-plans/<session-name>/` with wave/task subdirectories
2. Each sub-workflow gets its own `prompt.md`, `promise.txt`, and `plan.md`
3. An `execution-graph.md` documents the dependency structure and all commands
4. Outputs commands grouped by wave:
   ```
   ## Wave 1 (run in parallel)
   /finesse:finesse-execute --prompt-file finesse-plans/<session>/wave-1/<task>/prompt.md --completion-promise-file finesse-plans/<session>/wave-1/<task>/promise.txt --max-iterations <N>

   ## Wave 2 (run after Wave 1 completes)
   /finesse:finesse-execute --prompt-file finesse-plans/<session>/wave-2/<task>/prompt.md --completion-promise-file finesse-plans/<session>/wave-2/<task>/promise.txt --max-iterations <N>
   ```

Metadata and rationale live in the separate `-plan.md` (or `plan.md`) file.

For automated wave execution with parallel worktrees, tmux session management, and merge reconciliation, use the `/finesse-waves` command instead of manually running each sub-workflow.

## Plan Rejection & Iteration

If you reject a plan:

- **With feedback:** Finesse's refinement counter resets to zero, giving you a fresh refinement budget. It makes targeted edits (doesn't rebuild from scratch), re-validates with all 6 agents, and re-presents.
- **Without feedback:** Finesse asks what specifically needs to change.

You can reject and refine as many times as needed.

## Iteration Count Guidance

Finesse automatically sizes `--max-iterations` based on task type and scope:

| Task Type | Scope | Iterations |
|---|---|---|
| Feature | 1-2 files | 8-12 |
| Feature | 3-5 files | 12-18 |
| Feature | 6+ files | 18-25 |
| Bug Fix | One file, clear cause | 5-8 |
| Bug Fix | Multi-file, clear cause | 8-12 |
| Bug Fix | Unclear cause, multiple files | 12-18 |
| Refactor | 1-3 files | 5-8 |
| Refactor | 4-8 files | 10-15 |
| Refactor | 9+ files | 15-22 |
| Testing | 5-10 tests | 5-8 |
| Testing | 10-25 tests | 10-15 |
| Testing | 25+ tests | 15-20 |
| Performance | Single bottleneck | 5-10 |
| Performance | Multiple bottlenecks | 10-18 |
| Performance | System-wide | 15-22 |
| Research | Narrow (1-2 sections) | 5-8 |
| Research | Medium (3-5 sections) | 8-14 |
| Research | Broad (6+ sections) | 14-20 |

If a task needs more than 25 iterations, Finesse automatically proposes decomposing it into multiple independent sub-workflows during the Scope Analysis phase. Each sub-workflow runs with its own right-sized iteration count.

## When to Use Finesse

**Use Finesse when:**
- You want to run a task autonomously with iterative execution
- The task requires architectural decisions
- The bug's root cause isn't obvious
- The refactor touches many files
- You need comprehensive test coverage
- You want a structured research spike, feasibility study, or architecture comparison

**Skip Finesse when:**
- You already have a well-structured prompt
- The task is trivial (one file, obvious change) - use `/finesse:finesse-mini` instead

## Limitations

- Planning uses multiple sub-agents, which consumes more tokens than a simple prompt. Budget accordingly for complex tasks.
- Finesse works best with codebases it can explore. For greenfield projects with no existing code, provide more detail in your task description.

## Quick Start

```bash
/plugin marketplace add jonathanung/finesse
/plugin install finesse @ jonathanung-finesse
/finesse:finesse <describe any task> # or
/finesse:finesse-mini <describe a small task>
```

Finesse handles the rest. Plans are saved to `finesse-plans/` and ready to execute.

## License

MIT
