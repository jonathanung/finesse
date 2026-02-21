# Exploration Caching System — Plan Metadata

## Task Type
Feature

## Summary
Add an exploration caching system to Finesse that persists key codebase findings across planning sessions. On subsequent runs, if the cache exists and the codebase hasn't changed significantly (configurable threshold, default 50 files), Finesse loads cached findings as baseline context and runs a single lighter explorer agent instead of full 2-3 agent exploration.

## Codebase Context
- Finesse is a Claude Code plugin at `/workspace/plugins/finesse/` (v0.5.0)
- All files are markdown prompt instructions — no executable code
- 8 agents, 5 commands, 3 skills
- Exploration phases exist in all 6 workflow types (F2, B2, R2, T1, P2, RE2) in `task-workflows/SKILL.md`
- Existing patterns to follow: Git Config (v0.3.1) and Subagent Config (v0.4.0) three-layer pattern (schema in skill, procedure in command, notes in workflows)
- No existing cross-session caching mechanism

## Chosen Approach
**Pragmatic Balance (Three-Layer)**
- Cache schema defined in `meta-prompting/SKILL.md` (after Subagent Configuration, before Multi-Workflow Output Format)
- Cache orchestration as top-level section in `finesse.md` (between Agent Launch Guidance and Critical Rules)
- Cache-aware notes in all 6 exploration phases in `task-workflows/SKILL.md`
- Cache data model: global baseline + task-indexed entries (dual directory + keyword indexing)
- Staleness: file-change detection via git diff against referenced files
- Config: separate `.finesse/config.json` with configurable threshold
- All `.finesse/` artifacts gitignored

## Rationale
- Follows the proven three-layer pattern established by git config and subagent config features
- No agent changes needed — orchestrator-level optimization
- Graceful degradation: cache miss falls back to full exploration seamlessly
- Detailed JSON schema and cache-hit explorer mission template ensure correct LLM implementation
- 9 files modified, 0 new plugin files, ~200-250 lines added

## Recommended --max-iterations
**12** — Medium feature with formulaic insertions across 9 markdown files. Verification is grep-based. Comparable to v0.4.0 subagent config (7 files, ~200 lines, 12 iterations).

## Validation Results
All 5 validators PASS:
- clarity-checker: PASS — No ambiguities, all line references verified against actual files
- completion-validator: PASS — Binary criteria, explicit completion signal, anti-premature-exit
- scope-safety-reviewer: PASS, LOW_RISK — Tight scope, comprehensive guardrails
- phase-structure-analyzer: PASS — Cold start, 7 ordered phases, verification per phase
- failure-mode-auditor: PASS — Stuck-state recovery, anti-thrashing, blocked signal

## Unresolved Warnings
None.
