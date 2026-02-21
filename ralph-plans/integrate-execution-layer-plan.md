# Plan Metadata: integrate-execution-layer

## Task Type
Feature

## Summary
Integrate the Finesse execution layer into the existing command pipeline by updating 4 files to wire in `/finesse-execute` commands, add three acceptance options (Execute now / Copy command / Save plan only), add a pre-flight validation check, and document the new commands.

## Codebase Context

**Target files** (4, all in `/workspace/plugins/finesse/`):
- `commands/finesse.md` (425 lines) — Main command definition. Contains command format strings, acceptance flow, philosophy, rules.
- `commands/finesse-help.md` (197 lines) — Help documentation. Lists commands, output format, workflow descriptions.
- `skills/meta-prompting/SKILL.md` (408 lines) — Prompt construction guide. Contains file output format and execution-graph per-wave command examples.
- `skills/task-workflows/SKILL.md` (575 lines) — Workflow definitions. Multi-Workflow Execution section needs per-wave command examples added.

**Reference files** (3, read-only):
- `commands/finesse-execute.md` — New execute command definition
- `commands/cancel-finesse-execute.md` — Cancel command definition
- `commands/finesse-validate.execute.md` — Validation suite definition

**Key format change**:
- Old: `/ralph-loop:ralph-loop $(cat ralph-plans/<name>.md) --completion-promise "$(cat ralph-plans/<name>-promise.txt)" --max-iterations=<N>`
- New: `/finesse-execute --prompt-file ralph-plans/<name>.md --completion-promise-file ralph-plans/<name>-promise.txt --max-iterations <N>`

## Chosen Approach
Single-pass targeted edits across 4 files with subagent parallelization for the 3 independent files (finesse-help.md, meta-prompting/SKILL.md, task-workflows/SKILL.md) while the main agent handles finesse.md.

**Rationale**: All changes are well-specified, the files are small (<600 lines each), and the edits are surgical. No architectural decisions needed — the integration points are fully defined by the user.

## Recommended --max-iterations
10

**Reasoning**: 4 small files (425 + 197 + 408 + 575 = 1,605 total lines), 16+ distinct edits across the files. With subagents handling 3 independent files in parallel, the main agent focuses on finesse.md (8 sub-edits, most complex). Cold start + 5 main phases + verification = ~7-8 productive iterations. Adding buffer for Edit tool retries (non-unique string matches) and the final cross-file verification: 10 iterations.

## Context Budget Estimate

| Metric | Value |
|---|---|
| Context window | 200,000 tokens |
| Files | 7 (4 target + 3 reference), all small category |
| Total lines | ~1,810 |
| Estimated file tokens | ~18,100 |
| Heaviest phase (finesse.md) | ~13,500 tokens |
| Peak usage | ~37,500 tokens |
| Pressure | 18.75% — **LOW** |
| Estimated cost | Under $5 |

> Cost estimates are order-of-magnitude approximations based on a 200k token context window. Actual costs vary with model choice, caching behavior, and agent reasoning patterns. Treat these as directional, not precise.

## Unresolved Warnings
None.

## baseline_commit
47e89f0b49bf0c30c3e3fa49e32caa4dde66dab0

## git_config
- Checkpointing: No
- Push: No

## subagent_enabled
true

## Validation Results (6/6 PASS)

| Agent | Verdict | Notes |
|---|---|---|
| clarity-checker | PASS | Exceptionally well-specified |
| completion-validator | PASS | All criteria binary and verifiable |
| scope-safety-reviewer | PASS (LOW_RISK) | All guardrails present |
| phase-structure-analyzer | PASS | Cold start pattern broadened to match criteria |
| failure-mode-auditor | PASS | 4 task-specific rules added per suggestions |
| goal-achievement-auditor | PASS | All $(cat patterns addressed |
