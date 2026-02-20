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

### Multi-Workflow Validation

When the Scope Analysis phase resulted in a decomposition with multiple sub-workflows:

**Per-sub-workflow validation**: Launch all 6 validators on each sub-workflow's prompt independently. Process sub-workflows sequentially (to manage context), not all at once.

**Cross-sub-workflow checks**: After individual validation passes, verify:
1. No file scope overlaps between parallel (same-wave) sub-workflow prompts
2. Wave 2+ sub-workflows correctly assume wave 1 outputs as existing state (not as things to build)

**Verdict aggregation**: All sub-workflow prompts must pass all 6 validators. A FAIL on any single sub-workflow blocks the entire plan.

**Refinement budget**: Applies per sub-workflow independently. Each sub-workflow can use up to `--max-refinements` cycles.

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
4. Re-run ALL 6 validators on the revised plan (not a subset — this catches regressions)
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

### Step 6: Goal Achievement Escalation

When the goal-achievement-auditor identifies issues that require user input:
- If the cold start paragraph has no extractable goal: ask the user to clarify the intended end-state of the ralph-loop. What should be different when done?
- If derived truths have no covering phases: present the uncovered truths and ask whether they should be added as new phases or whether the truths are incorrect
- If completion criteria don't verify all truths: present the gaps and suggest specific additions to the promise section
- Do NOT invent phases or modify the goal yourself — surface the gaps for user decision

### Refinement Budget

- Default budget: 5 refinement cycles
- User can set via `--max-refinements N`
- If budget exhausted without full PASS: present the plan with explicit warnings listing every unresolved issue and which agent flagged it
- On user rejection with feedback: budget resets to 0, but make targeted edits (the skeleton is already built — don't rebuild from scratch)

### Post-Acceptance

Once the user accepts:

**Single-workflow acceptance:**
1. Create `ralph-plans/` directory in workspace root
2. Write THREE files:
   - `ralph-plans/<name>.md` — prompt text ONLY (no metadata, no headers — the raw prompt content)
   - `ralph-plans/<name>-promise.txt` — completion promise text ONLY (no quotes)
   - `ralph-plans/<name>-plan.md` — metadata: task type, summary, codebase context, approach with rationale, recommended iterations with reasoning, unresolved warnings
3. Output the exact ralph-loop command:
   ```
   /ralph-loop:ralph-loop $(cat ralph-plans/<name>.md) --completion-promise "$(cat ralph-plans/<name>-promise.txt)" --max-iterations=<N>
   ```
   The command uses `$(cat ...)` shell expansion to read the prompt and promise from their files at runtime. The `<name>.md` file MUST contain only the prompt text for this to work correctly.

**Multi-workflow acceptance:**
1. Create `ralph-plans/<session-name>/` directory in workspace root
2. For each wave N, create `ralph-plans/<session-name>/wave-<N>/`
3. For each sub-workflow, create its directory and write three files:
   - `ralph-plans/<session-name>/wave-<N>/<task-name>/prompt.md` — sub-workflow prompt text ONLY
   - `ralph-plans/<session-name>/wave-<N>/<task-name>/promise.txt` — sub-workflow completion promise ONLY
   - `ralph-plans/<session-name>/wave-<N>/<task-name>/plan.md` — sub-workflow metadata
4. Write `ralph-plans/<session-name>/execution-graph.md` with wave structure, dependency rationale, and per-task commands
5. Output ralph-loop commands organized by wave
