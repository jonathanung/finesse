# Finesse

A Claude Code plugin that turns vague task descriptions into validated, ready-to-run [ralph-loop](https://github.com/anthropics/claude-code-plugins) prompts — the kind that converge instead of thrashing. Describe what you want in plain English; Finesse plans it, validates it with 5 parallel agents, and hands you the command.

> **What is ralph-loop?** Ralph-loop is a Claude Code plugin that repeatedly invokes Claude to work on a task across multiple iterations until a completion condition is met. Each iteration is stateless — the agent starts fresh with only the prompt and the current state of the codebase. This makes prompt quality critical: a vague requirement becomes an infinite loop, a missing guardrail lets the agent delete your tests, and an ambiguous "done" condition means it either exits too early or never stops. Good prompts need [10 specific attributes](#the-10-mandatory-prompt-attributes) that Finesse encodes automatically.

## How It Works

```
/finesse Build a REST API for managing todos with authentication
```

Finesse detects your task type, explores your codebase, asks you clarifying questions, designs implementation approaches, constructs a ralph-loop prompt, validates it with 5 specialized agents, and presents the result for your approval.

```
You → /finesse "vague idea"
       ↓
  Task Classification (feature / bugfix / refactor / testing / performance)
       ↓
  Type-Specific Workflow  ←  you answer clarifying questions
       ↓
  Prompt Construction (cold start, ordered phases, verification commands, guardrails)
       ↓
  Parallel Validation (5 agents in parallel)
       ↓
  Refinement (auto-fix or ask you)
       ↓
  Presentation  ←  you approve or reject
       ↓
  On Accept → ralph-plans/todo-api-with-auth.md + copy-paste command
```

## Installation

```bash
/plugin marketplace add jonathanung/finesse
```

**Prerequisite:** The ralph-loop plugin must also be installed to run the generated prompts:

```bash
/plugin marketplace add anthropics/claude-code-plugins
```

## Commands

### `/finesse <TASK> [--max-refinements N]`

Plan a ralph-loop prompt for any development task.

- `TASK` — What you want to do. Can be vague — Finesse will clarify.
- `--max-refinements N` — Max planning refinement cycles (default: 5). This is Finesse's internal planning budget, **not** the ralph-loop iteration count. Finesse determines the ralph-loop iteration count automatically based on task scope.

```bash
# Features
/finesse Build a REST API for managing todos with auth
/finesse Add a dark mode toggle to the settings page

# Bug fixes
/finesse Fix the token refresh bug in auth.ts
/finesse The search endpoint returns duplicates when filters overlap

# Refactoring
/finesse Refactor the database layer to use repository pattern
/finesse Clean up the payment service — it's 800 lines

# Testing
/finesse Add integration tests for the payments module
/finesse Write unit tests for the email validation logic

# Performance
/finesse Optimize the search endpoint — it's taking 3+ seconds
/finesse The dashboard page takes 5s to load
```

#### Example Output

For `/finesse Fix the token refresh bug in auth.ts`, Finesse produces something like:

```bash
/ralph-loop <PROMPT> --completion-promise 'Token refresh succeeds for expired tokens and test_token_refresh passes' --max-iterations 8
```

The saved plan in `ralph-plans/fix-token-refresh-auth.md` includes a cold start paragraph, ordered fix-then-test phases, specific verification commands, and guardrails like "Do NOT modify the token generation logic."

### `/cancel-finesse`

Cancel the current planning session without saving.

### `/finesse-help`

Show a summary of what Finesse does, its agents, and how to use it.

## Task-Specific Workflows

Finesse detects your task type and runs a tailored multi-phase workflow. Every workflow ends with prompt construction, parallel validation, and presentation.

- **Feature Development** (7 phases) — Discovery, codebase exploration with 2-3 agents, clarifying questions, architecture design with 3 competing approaches (minimal, clean, pragmatic), construction, validation, presentation. Finesse always presents **3 architecture options** with trade-offs and asks you to choose.
- **Bug Fix** (6 phases) — Bug understanding, codebase investigation tracing the failing execution path, root cause analysis with hypothesis and evidence, fix strategy with regression tests, construction, validation.
- **Refactor/Chore** (6 phases) — Scope definition, current state analysis mapping all dependencies and callers, target state design, incremental migration strategy (never leaves codebase broken between phases), construction, validation.
- **Testing** (5 phases) — Coverage analysis mapping test framework and gaps, test strategy ranked by risk, clarifying questions on mocking/fixtures, construction, validation.
- **Performance** (5 phases) — Problem definition with target metrics, profiling tracing slow paths and flagging O(n^2) patterns, optimization strategy ranked by impact with measurable before/after, construction, validation.

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

> **What are `<promise>` tags?** They are ralph-loop's mechanism for detecting completion. When the agent outputs a `<promise>` tag matching the `--completion-promise` text, ralph-loop stops iterating.

## Agents

### Validation Agents

After constructing a prompt, Finesse launches 5 validation agents **in parallel**. All must pass before the plan is presented to you.

| Agent | Focus | Checks For |
|---|---|---|
| **clarity-checker** | Requirement specificity | Ambiguous text, missing context, implicit assumptions, scope completeness, success criteria clarity |
| **completion-validator** | Completion criteria | Binary criteria, explicit promise tag, anti-premature-exit language |
| **scope-safety-reviewer** | Scope & safety | File boundaries, destructive action guardrails, "Do NOT" rules, iteration limits |
| **phase-structure-analyzer** | Structural clarity | Cold start paragraph, ordered phases, verification commands, phase independence |
| **failure-mode-auditor** | Failure handling | Stuck-state instructions, blocked signal, anti-thrashing rules, task-specific risks |

Each agent returns `PASS`, `FAIL`, or `NEEDS_REWORK`:

- **All PASS** — Plan is ready to present.
- **Any FAIL** — Critical gaps. Finesse fixes what it can and asks you about the rest.
- **Any NEEDS_REWORK** — Fixable issues. Finesse auto-fixes within its refinement budget.

If the scope-safety-reviewer flags `HIGH_RISK`, Finesse will ask you to explicitly acknowledge the risk before proceeding.

### Planning Agents

| Agent | Used In | Role |
|---|---|---|
| **code-explorer** | All workflows | Traces execution paths, maps architecture, identifies patterns and essential files |
| **code-architect** | Feature workflow only | Designs implementation approaches — 3 competing designs with trade-offs |

## Output

When you accept a plan, Finesse:

1. Creates `ralph-plans/` in your workspace root (if it doesn't exist)
2. Saves the plan to `ralph-plans/<descriptive-name>.md`
3. Outputs the exact command to run (prompt text, `--completion-promise`, and `--max-iterations` with reasoning)

The saved plan file includes the task type, codebase context from exploration, chosen approach with rationale, the full ralph-loop prompt, and any unresolved warnings from validation.

## Plan Rejection & Iteration

If you reject a plan:

- **With feedback:** Finesse's refinement counter resets to zero, giving you a fresh refinement budget. It makes targeted edits (doesn't rebuild from scratch), re-validates with all 5 agents, and re-presents.
- **Without feedback:** Finesse asks what specifically needs to change.

You can reject and refine as many times as needed.

## Iteration Count Guidance

Finesse automatically sizes the ralph-loop `--max-iterations` based on task type and scope:

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

If a task needs more than 25 iterations, Finesse recommends decomposing it into separate sequential ralph runs.

## When to Use Finesse

**Use Finesse when:**
- You want to run a task autonomously via ralph-loop
- The task requires architectural decisions
- The bug's root cause isn't obvious
- The refactor touches many files
- You need comprehensive test coverage

**Skip Finesse when:**
- You already have a well-structured ralph-loop prompt
- The task is trivial (one file, obvious change)

## Limitations

- Finesse plans but does not execute — you need ralph-loop installed to run the output.
- Planning uses multiple sub-agents, which consumes more tokens than a simple prompt. Budget accordingly for complex tasks.
- Finesse works best with codebases it can explore. For greenfield projects with no existing code, provide more detail in your task description.

## Quick Start

```bash
/plugin marketplace add jonathanung/finesse
/plugin marketplace add anthropics/claude-code-plugins
/finesse <describe any task>
```

Finesse handles the rest. Plans are saved to `ralph-plans/` and the ralph-loop command is ready to copy-paste.

## License

MIT
