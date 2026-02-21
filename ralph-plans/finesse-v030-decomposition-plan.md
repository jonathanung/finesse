# Finesse v0.3.0 — Scope Analysis & Decomposition Plan

## Task Type
Feature

## Summary
Add automated task decomposition to the Finesse plugin. A new "Scope Analysis & Decomposition" phase detects large tasks, proposes sub-workflows organized into parallel/sequential waves, and generates independent ralph-loop instruction files for each. Upgrades plugin to v0.3.0.

## Codebase Context
- All plugin files are markdown (prompt engineering, no executable code)
- Plugin root: `plugins/finesse/`
- Authoritative workflow definitions: `skills/task-workflows/SKILL.md` (543 lines)
- Main orchestrator: `commands/finesse.md` (229 lines)
- Prompt template: `skills/meta-prompting/SKILL.md` (103 lines)
- Validation orchestration: `skills/prompt-validation/SKILL.md` (74 lines)
- Architect agent: `agents/code-architect.md` (71 lines)
- 5 validator agents follow PASS/FAIL/NEEDS_REWORK pattern
- Version tracked in: `plugin.json`, `marketplace.json`, `finesse-version.md`
- Current output format: flat `ralph-plans/<name>.md`, `<name>-promise.txt`, `<name>-plan.md`

## Chosen Approach — Pragmatic Balance
Decomposition logic embedded in task-workflows (co-located with task-type knowledge), code-architect extended with decomposition mode, new task-decomposer validation agent.

**Rationale**: Decomposition criteria are inherently task-type-specific. Embedding them in task-workflows keeps this knowledge co-located. A separate skill would constantly cross-reference task-workflows, adding indirection without real separation.

**Key decisions from user**:
- New phase between exploration and next phase for ALL 6 workflow types
- Collaborative splitting: Finesse proposes via code-architect, task-decomposer validates, user approves/modifies/overrides
- Shared exploration + architecture, separate plan construction + validation per sub-workflow
- Multi-workflow output: `ralph-plans/<session>/wave-N/<task>/prompt.md|promise.txt|plan.md` + `execution-graph.md`
- Single-workflow: keep old flat format
- User override: warn but respect
- Dependency analysis: file-based + logical

## Files Modified (10 total)
1. `plugins/finesse/skills/task-workflows/SKILL.md` (MODIFY)
2. `plugins/finesse/agents/code-architect.md` (MODIFY)
3. `plugins/finesse/agents/task-decomposer.md` (CREATE)
4. `plugins/finesse/skills/meta-prompting/SKILL.md` (MODIFY)
5. `plugins/finesse/skills/prompt-validation/SKILL.md` (MODIFY)
6. `plugins/finesse/commands/finesse.md` (MODIFY)
7. `plugins/finesse/commands/finesse-help.md` (MODIFY)
8. `plugins/finesse/commands/finesse-version.md` (MODIFY)
9. `plugins/finesse/.claude-plugin/plugin.json` (MODIFY)
10. `.claude-plugin/marketplace.json` (MODIFY)

## Recommended --max-iterations: 20
Complex feature touching 10 files (1 new, 9 modified) with cross-file consistency requirements (phase numbering must align across 3 files). All files are markdown with no compilation step, but edits are substantial (~500+ lines added). The interdependencies between files and the phase renumbering across 6 workflow types require careful coordination. 20 iterations provides comfortable margin for 8 phases plus cross-file verification and corrections.

## Completion Promise
`FINESSE_V030_COMPLETE`

## Validation Results
- clarity-checker: PASS (after refinement)
- completion-validator: PASS (after refinement)
- scope-safety-reviewer: PASS, LOW_RISK
- phase-structure-analyzer: PASS
- failure-mode-auditor: PASS (after refinement)

## Unresolved Warnings
None — all validation issues addressed in refinement.
