# Plan: Add /finesse-retro Command

## Task Type
Feature

## Summary
Add a `/finesse-retro` command that performs post-execution retrospective analysis on completed ralph-loop runs, optionally runs PR review against the original plan, and generates validated fix-loop prompts for identified gaps. Also adds `baseline_commit`, `git_config`, and `subagent_enabled` fields to plan metadata for retro consumption.

## Codebase Context
- **Plugin location**: `/workspace/plugins/finesse/`
- **Command pattern**: YAML frontmatter (description, argument-hint, allowed-tools) + markdown body. Complex commands are 400+ lines (finesse.md: 423, finesse-resume.md: 461).
- **Plan metadata**: Markdown with sections (Task Type, Summary, Codebase Context, Chosen Approach, Recommended --max-iterations, Context Budget Estimate, Validation Results, Unresolved Warnings). Currently does NOT include baseline_commit, git_config, or subagent_enabled.
- **Three-file output**: `<name>.md` (prompt only), `<name>-promise.txt` (promise only), `<name>-plan.md` (metadata)
- **Validation pipeline**: 6 agents (clarity-checker, completion-validator, scope-safety-reviewer, phase-structure-analyzer, failure-mode-auditor, goal-achievement-auditor) launched in parallel via Task tool
- **finesse.md User Decision section** (line ~213-226): Describes what goes in each output file
- **finesse-resume.md User Decision section** (line ~376-407): Identical copy of User Decision
- **meta-prompting/SKILL.md File Output Format** (line ~96-106): Documents three-file structure

## Chosen Approach
**Approach 3: Pragmatic Balance** — Self-contained command file (~300 lines), no new skills or agents, follows existing patterns. Plan metadata fields formalized in meta-prompting/SKILL.md. Internal organization uses clear section headers (8 steps + 2 format sections).

**Rationale**: Matches existing codebase patterns (compare with finesse-resume.md). No new file types or abstractions. Comprehensive Mode 2/3 handling. If retro analysis later needs reuse, extracting to a skill is straightforward.

## Files Modified
1. **NEW**: `plugins/finesse/commands/finesse-retro.md` (~300 lines) — the retro command
2. **MODIFY**: `plugins/finesse/commands/finesse.md` — add baseline_commit, git_config, subagent_enabled to plan metadata
3. **MODIFY**: `plugins/finesse/commands/finesse-resume.md` — same metadata additions
4. **MODIFY**: `plugins/finesse/skills/meta-prompting/SKILL.md` — document new metadata fields
5. **MODIFY**: `plugins/finesse/commands/finesse-help.md` — add retro command documentation

## Recommended --max-iterations: 15

**Reasoning**: 5 files (1 create, 4 modify). Phase 1 requires 3 carefully targeted edits across files with similar content (Edit tool uniqueness risk). Phase 2 is a substantial ~300-line file creation requiring careful section authoring. Phase 3 is a simple edit. 15 iterations provides margin for Edit tool retries and verification-fix cycles. Within the medium feature range (12-18).

## Context Budget Estimate
- **Pressure**: MODERATE (35%)
- **Peak iteration context**: ~70,000 / 200,000 tokens
- **File count**: 5 (all small, <2,000 lines)
- **File categories**: 5 small, 0 medium, 0 large
- **Estimated cost**: $5-20
- *Cost estimates are order-of-magnitude approximations based on a 200k token context window. Actual costs vary with model choice, caching behavior, codebase growth during execution, and agent reasoning patterns. Treat these as directional, not precise.*

## Validation Results

| Validator | Verdict | Notes |
|---|---|---|
| scope-safety-reviewer | PASS (LOW_RISK) | All markdown files in plugin directory, minimal blast radius |
| phase-structure-analyzer | PASS | Cold start, ordered phases, verification commands all adequate |
| completion-validator | PASS | Promise defined, binary criteria, explicit signal |
| clarity-checker | NEEDS_REWORK → Fixed | Phase 2 completion criteria made more granular (added grep checks for fuzzy matching, mode gating, validation pipeline, ralph-plans output) |
| goal-achievement-auditor | NEEDS_REWORK → Fixed | Completion criteria now verify all 7 observable truths with specific grep commands |
| failure-mode-auditor | PASS | Stuck-state, blocked signal, Edit tool guidance, anti-thrashing all present |

## Unresolved Warnings
None — all validator issues resolved in refinement cycle 1.
