# Plan Metadata: goal-achievement-auditor

## Task Type
Feature

## Summary
Add a goal-backward validation agent (`goal-achievement-auditor`) as the 6th validator in the Finesse plugin's validation pipeline. This agent checks whether a drafted ralph-loop prompt will actually achieve its stated goal by deriving observable truths and verifying phase coverage, dependency flow, and completion criteria.

## Codebase Context
- **Plugin location**: `/workspace/plugins/finesse/`
- **Existing validators** (5): clarity-checker, completion-validator, scope-safety-reviewer, phase-structure-analyzer, failure-mode-auditor
- **All validators** follow identical pattern: YAML frontmatter → H1 title → intro paragraph → "## What to Check" with numbered ### subsections → "## Output Format" → verdict rules
- **Validators spawned** via Task tool with agent name as subagent_type, auto-discovered from `agents/` directory
- **6 files reference "5 validators"**: prompt-validation/SKILL.md, task-workflows/SKILL.md, finesse.md, finesse-resume.md, finesse-help.md (+ the clarity-checker used as a reference template)

## Chosen Approach
**Consistent validator pattern (Approach 1)**: Structure the new agent identically to existing validators with 5 numbered "What to Check" sections mapping to the goal-backward validation process:
1. Goal Extraction
2. Truth Derivation (3-7 post-execution observable truths)
3. Phase Coverage (coverage matrix with rationale)
4. Dependency Flow (logical ordering verification)
5. Completion Criteria Verification

**Rationale**: Maximally consistent with the 5 existing validators, easy for the orchestrator to parse, explicit enough for LLM execution.

## Recommended --max-iterations: 10
**Reasoning**: 6 files (1 create, 5 edit). Phase 1 (agent creation) requires ~90 lines of careful prompt authoring. Phases 2-6 are targeted edits requiring care with Edit tool uniqueness (multiple "ALL 5" patterns in same files). Phase 7 is verification. 10 provides margin for Edit uniqueness retries and verification-fix cycles.

## Context Budget Estimate
- **Pressure**: LOW (22.3%)
- **Peak iteration context**: ~44,500 / 200,000 tokens
- **File count**: 7 (all small, <2,000 lines each)
- **File categories**: 7 small, 0 medium, 0 large
- **Estimated cost**: Low
- *Disclaimer: estimates are heuristic-based approximations and may not reflect actual costs*

## Validation Results

| Validator | Verdict | Notes |
|---|---|---|
| clarity-checker | PASS | All requirements specific enough for autonomous agent |
| completion-validator | NEEDS_REWORK → Fixed | Added specific instance counts per file, file count check, non-validator regression check |
| scope-safety-reviewer | PASS (LOW_RISK) | All markdown files in single plugin directory, minimal blast radius |
| phase-structure-analyzer | NEEDS_REWORK → Fixed | Expanded cold start to reverse-order detection for all 7 phases, made Phase 5 self-contained, added "5 standard" to grep pattern, corrected file count to 5 |
| failure-mode-auditor | NEEDS_REWORK → Fixed | Added false-positive "5" protection rules, Edit tool uniqueness guidance, post-edit verification, non-validator regression check |

## Unresolved Warnings
None — all validator issues were resolved in refinement.