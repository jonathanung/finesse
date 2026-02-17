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
| **Feature** | Discovery → Codebase Exploration → Clarifying Questions → Architecture Design (3 approaches) → Plan → Validate → Present |
| **Bug Fix** | Bug Understanding → Codebase Investigation → Root Cause Analysis → Fix Strategy → Plan → Validate → Present |
| **Refactor** | Scope Definition → Current State Analysis → Target State Design → Migration Strategy → Plan → Validate → Present |
| **Testing** | Coverage Analysis → Test Strategy → Clarifying Questions → Plan → Validate → Present |
| **Performance** | Problem Definition → Profiling & Analysis → Optimization Strategy → Plan → Validate → Present |
| **Research** | Goal Definition → Source Identification → Research Plan & Questions → Investigation Strategy → Plan → Validate → Present |

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

### /cancel-finesse

Cancel the current planning session without saving.

## What Happens

1. **Task type detection** — Finesse classifies your task (feature, bugfix, refactor, testing, performance, research)
2. **Type-specific workflow** — Runs the appropriate multi-phase workflow:
   - Features get codebase exploration + 3 architecture approaches
   - Bug fixes get root cause analysis + fix strategy
   - Refactors get dependency mapping + migration strategy
   - etc.
3. **Clarifying questions** — Finesse asks you to resolve ambiguities (never guesses)
4. **Plan construction** — Builds a structured ralph-loop prompt with cold start, phases, verification commands, guardrails
5. **Parallel validation** — 5 agents review the plan simultaneously
6. **Refinement** — Issues fixed automatically or flagged for your input
7. **Presentation** — Plan shown for your approval
8. **On acceptance** — Saved to `ralph-plans/`, you get the ralph-loop command

## Agents

### Planning Agents
| Agent | Role |
|---|---|
| code-explorer | Traces execution paths, maps architecture, identifies patterns |
| code-architect | Designs implementation approaches with trade-offs (feature workflow only) |

### Validation Agents
| Agent | Focus |
|---|---|
| clarity-checker | Are requirements specific enough for an autonomous agent? |
| completion-validator | Are completion criteria binary, explicit, and unambiguous? |
| scope-safety-reviewer | Are scope constraints and safety guardrails in place? |
| phase-structure-analyzer | Are phases ordered with verification commands and cold start? |
| failure-mode-auditor | Are stuck-state recovery and anti-thrashing rules present? |

## Output

Accepted plans are saved to `ralph-plans/<descriptive-name>.md` in your workspace root. You get a ready-to-run ralph-loop command with:
- The validated prompt
- A recommended `--max-iterations` (determined by Finesse with reasoning based on task scope)
- A `--completion-promise` phrase

## Plan Rejection

If you reject a plan with feedback:
- Finesse's refinement counter resets
- Subsequent passes make targeted edits (the skeleton is already built)
- All 5 validators re-run on the revised plan
- You see the revised plan for another round of approval

## When to Use Finesse

**Use for:**
- Any task you want to run autonomously via ralph-loop
- Features requiring architectural decisions
- Complex bugs where root cause isn't obvious
- Large refactors touching many files
- Test suites covering significant surface area
- Research spikes, feasibility studies, or architecture comparisons

**Skip when:**
- You already have a well-structured ralph-loop prompt
- The task is trivial (one file, obvious change)
