---
description: "Orchestrates parallel prompt validation for Finesse planning sessions"
---

# Prompt Validation Orchestration

During a Finesse planning session, you MUST validate every drafted plan before presenting it to the user. This is a non-negotiable gate.

## Validation Workflow

### Step 1: Launch All Validators in Parallel

Use the Task tool to launch ALL FIVE agents simultaneously in a single message. Pass the full drafted plan text to each agent in their prompt:

1. **clarity-checker** — Are requirements specific enough for an autonomous agent with no ability to ask questions?
2. **completion-validator** — Are completion criteria binary, explicit, and unambiguous?
3. **scope-safety-reviewer** — Are scope constraints, guardrails, and safety measures in place?
4. **phase-structure-analyzer** — Are phases ordered with verification commands and a cold start paragraph?
5. **failure-mode-auditor** — Are stuck-state recovery, anti-thrashing rules, and failure handling present?

Each agent returns a verdict: `PASS`, `FAIL`, or `NEEDS_REWORK`.

### Step 2: Evaluate the Gate

- **All PASS**: The plan is ready to present to the user.
- **Any FAIL**: The plan has critical gaps. You MUST fix them before presenting.
- **Any NEEDS_REWORK**: The plan has issues that should be fixed. Fix them if within your refinement budget.

### Step 3: Handle Failures

For FAIL or NEEDS_REWORK verdicts:

1. Collect all issues from all agents
2. Separate issues into two categories:
   - **Fixable by you**: Missing guardrails, missing verification commands, structural issues → fix them directly
   - **Requires user input**: Ambiguous requirements, missing context, unclear scope → ask the user
3. Fix everything you can, ask the user about the rest
4. Re-run ALL 5 validators on the revised plan (not a subset — this catches regressions)
5. Each cycle costs one refinement iteration against your budget

### Step 4: Safety Escalation

If the scope-safety-reviewer returns FAIL with `SAFETY LEVEL: HIGH_RISK`, you MUST ask the user to explicitly acknowledge the risk before presenting the plan. Do not silently proceed.

### Step 5: User Clarification

When the clarity-checker (or any agent) identifies ambiguities that require user input:
- Present the specific questions to the user
- Do NOT guess or fill in blanks with assumptions
- Wait for answers before revising the plan
- Incorporate answers and re-validate
- This is consistent with the core philosophy: never infer when you can ask. Validation ambiguities are just as important as planning ambiguities.

### Refinement Budget

- Default budget: 5 refinement cycles
- User can set via `--max-refinements N`
- If budget exhausted without full PASS: present the plan with explicit warnings listing every unresolved issue and which agent flagged it
- On user rejection with feedback: budget resets to 0, but make targeted edits (the skeleton is already built — don't rebuild from scratch)

### Post-Acceptance

Once the user accepts:
1. Create `ralph-plans/` directory in workspace root
2. Write the plan to `ralph-plans/<descriptive-kebab-case-name>.md`
3. Output the exact ralph-loop command with:
   - The full prompt text
   - `--completion-promise` with the chosen phrase
   - `--max-iterations` with the agent-recommended count and reasoning
