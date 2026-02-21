# Validator Severity Tiers — Plan Metadata

## Task Type
**Feature** — Add a 4-tier severity system to the Finesse validation orchestration.

## Summary
Currently all 6 Finesse validation agents are treated equally: any FAIL blocks presentation, any NEEDS_REWORK is conditional on budget. This change adds a CRITICAL/HIGH/MEDIUM/LOW tier system that differentiates how validator verdicts are handled, enabling budget-constrained sessions to fix the most important issues first.

## Codebase Context
- **Primary file**: `/workspace/plugins/finesse/skills/prompt-validation/SKILL.md` (109 lines) — full validation workflow
- **Summary files**: `/workspace/plugins/finesse/commands/finesse.md` (validation at lines 273-294) and `/workspace/plugins/finesse/commands/finesse-resume.md` (validation at lines 324-345) — identical summaries
- Safety Escalation (Step 4) already has HIGH_RISK handling — compatible with CRITICAL tier
- Goal Achievement Escalation (Step 6) and User Clarification (Step 5) apply regardless of tier

## Approach
Single direct approach: implement exact tier assignments across 3 files. SKILL.md gets full specification; command files get consistent summary. No decomposition needed (3 small markdown files, low context pressure).

### Tier Assignments
| Tier | Agents (on FAIL) | Behavior |
|------|-------------------|----------|
| CRITICAL | scope-safety-reviewer | Blocks unconditionally |
| HIGH | clarity-checker, phase-structure-analyzer, completion-validator | Blocks, must fix |
| MEDIUM | goal-achievement-auditor, failure-mode-auditor | Fix within budget, present with warnings if exhausted |
| LOW | Any agent (on NEEDS_REWORK) | Fix if budget allows |

### Budget Threshold
When refinement budget drops below 50% remaining, prioritize CRITICAL and HIGH exclusively.

## Recommended --max-iterations: 5
Text-only modification to 3 markdown files. Phase 1 (SKILL.md) is most complex. Phases 2-3 are summary updates. Phase 4 is read-only consistency check. Cold start paragraph and idempotency guards ensure safe re-entry.

## Context Budget Estimate
| Metric | Value |
|--------|-------|
| Files | 3 (all small, < 1,100 lines) |
| Peak iteration tokens | ~49,000 |
| Context window | 200,000 |
| Pressure | 25% (low) |
| Estimated cost | $0.50-$2.00 |

*Cost estimates are approximate.*

## Validation Results
### Round 1
- clarity-checker: **PASS**
- scope-safety-reviewer: **PASS** (LOW_RISK)
- phase-structure-analyzer: **FAIL** — missing cold start, narrative verification, fragile line refs, implicit dependencies
- completion-validator: **NEEDS_REWORK** — promise not grep-verifiable, no anti-premature-exit
- failure-mode-auditor: **NEEDS_REWORK** — no blocked signal, no anti-thrashing, no idempotency

### Refinement
All round 1 issues addressed: added cold start paragraph, executable grep/diff verification commands, content-based anchors, explicit phase dependencies, grep-verifiable promise (8 conditions), anti-premature-exit section, anti-thrashing guardrails, error-reading discipline, blocked signal, idempotency guards, exact multi-workflow aggregation text.

## Unresolved Warnings
None.
