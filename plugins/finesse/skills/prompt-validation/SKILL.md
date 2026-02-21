---
description: "Orchestrates parallel prompt validation for Finesse planning sessions"
---

# Prompt Validation Orchestration

During a Finesse planning session, you MUST validate every drafted plan before presenting it to the user. This is a non-negotiable gate.

## Validation Workflow

### Step 1: Launch All Validators in Parallel

Use the Task tool to launch ALL SIX agents simultaneously in a single message. Pass the full drafted plan text to each agent in their prompt:

1. **clarity-checker** — Are requirements specific enough for an autonomous agent with no ability to ask questions?
2. **completion-validator** — Are completion criteria binary, explicit, and unambiguous?
3. **scope-safety-reviewer** — Are scope constraints, guardrails, and safety measures in place?
4. **phase-structure-analyzer** — Are phases ordered with verification commands and a cold start paragraph?
5. **failure-mode-auditor** — Are stuck-state recovery, anti-thrashing rules, and failure handling present?
6. **goal-achievement-auditor** — Does the prompt actually achieve the stated goal? Are all observable truths covered by phases and verified by completion criteria?

Each agent returns a verdict: `PASS`, `FAIL`, or `NEEDS_REWORK`.

### Severity Tiers

Each verdict is classified into a severity tier based on the agent and verdict type:

| Tier | Condition | Behavior |
|------|-----------|----------|
| **CRITICAL** | scope-safety-reviewer returns `FAIL` | Blocks presentation unconditionally. Must fix before presenting. |
| **HIGH** | clarity-checker, phase-structure-analyzer, or completion-validator returns `FAIL` | Blocks presentation. Must fix before presenting. |
| **MEDIUM** | goal-achievement-auditor or failure-mode-auditor returns `FAIL` | Should fix within refinement budget. Can present with explicit warnings if budget exhausted. |
| **LOW** | Any agent returns `NEEDS_REWORK` | Fix if budget allows after higher tiers resolved. |

### Multi-Workflow Validation

When the Scope Analysis phase resulted in a decomposition with multiple sub-workflows:

**Per-sub-workflow validation**: Launch all 6 validators on each sub-workflow's prompt independently. Process sub-workflows sequentially (to manage context), not all at once.

**Cross-sub-workflow checks**: After individual validation passes, verify:
1. No file scope overlaps between parallel (same-wave) sub-workflow prompts
2. Wave 2+ sub-workflows correctly assume wave 1 outputs as existing state (not as things to build)

**Verdict aggregation**: All sub-workflow prompts must pass all 6 validators. A CRITICAL or HIGH tier verdict on any sub-workflow blocks the entire plan. MEDIUM tier verdicts on a sub-workflow generate warnings but do not block if that sub-workflow's refinement budget is exhausted.

**Refinement budget**: Applies per sub-workflow independently. Each sub-workflow can use up to `--max-refinements` cycles.

### Step 2: Evaluate the Gate

- **All PASS**: The plan is ready to present to the user.
- **Any CRITICAL issues**: You MUST fix these before presenting. They take absolute priority.
- **Any HIGH issues**: You MUST fix these before presenting. Second priority after CRITICAL.
- **Any MEDIUM issues**: Fix within refinement budget. If budget exhausted, present with explicit warnings listing each unresolved issue, its tier, and which agent flagged it.
- **Any LOW issues**: Fix if budget allows after all higher-tier issues are resolved.

### Step 3: Handle Failures

For FAIL or NEEDS_REWORK verdicts:

1. Collect all issues from all agents and classify each by severity tier (using the tier table above)
2. Separate issues into two categories:
   - **Fixable by you**: Missing guardrails, missing verification commands, structural issues → fix them directly
   - **Requires user input**: Ambiguous requirements, missing context, unclear scope → ask the user
3. Fix in priority order: CRITICAL → HIGH → MEDIUM → LOW
4. **Budget-aware prioritization**: When the refinement budget drops below 50% remaining, focus exclusively on CRITICAL and HIGH issues. Skip MEDIUM and LOW unless all CRITICAL and HIGH issues are resolved and budget remains.
5. Re-run ALL 6 validators on the revised plan (not a subset — this catches regressions)
6. Each cycle costs one refinement iteration against your budget

### Step 4: Safety Escalation

If the scope-safety-reviewer returns FAIL with `SAFETY LEVEL: HIGH_RISK`, you MUST ask the user to explicitly acknowledge the risk before presenting the plan. Do not silently proceed.

### Step 5: User Clarification

When the clarity-checker (or any agent) identifies ambiguities that require user input:
- Present the specific questions to the user
- Do NOT guess or fill in blanks with assumptions
- Wait for answers before revising the plan
- Incorporate answers and re-validate
- This is consistent with the core philosophy: never infer when you can ask. Validation ambiguities are just as important as planning ambiguities.

### Step 6: Goal Achievement Escalation

When the goal-achievement-auditor identifies issues that require user input:
- If the cold start paragraph has no extractable goal: ask the user to clarify the intended end-state of the ralph-loop. What should be different when done?
- If derived truths have no covering phases: present the uncovered truths and ask whether they should be added as new phases or whether the truths are incorrect
- If completion criteria don't verify all truths: present the gaps and suggest specific additions to the promise section
- Do NOT invent phases or modify the goal yourself — surface the gaps for user decision

### Refinement Budget

- Default budget: 5 refinement cycles
- User can set via `--max-refinements N`
- When budget is at or above 50% remaining: fix all tiers in priority order (CRITICAL → HIGH → MEDIUM → LOW)
- When budget drops below 50% remaining: prioritize CRITICAL and HIGH exclusively
- Budget exhausted with unresolved MEDIUM/LOW only: present with explicit warnings listing each unresolved issue, its severity tier, and which agent flagged it
- CRITICAL or HIGH issues should never remain unresolved (they are mandatory), but if budget is exhausted with unresolved CRITICAL/HIGH: present with BLOCKING warnings and explicitly ask the user whether to proceed
- On user rejection with feedback: budget resets to 0, but make targeted edits (the skeleton is already built — don't rebuild from scratch). Before re-validation, generate a prompt diff summary comparing pre-edit and post-edit prompt text — see the rejection handling procedure in finesse.md / finesse-mini.md for format and rules.

