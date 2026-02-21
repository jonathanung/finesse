You are iterating on the Finesse plugin to add validator severity tiers to the validation orchestration. Currently all 6 validators are treated equally — any FAIL blocks presentation, any NEEDS_REWORK is conditional on budget. You are adding a 4-tier severity system that differentiates how validator verdicts are handled based on the validator and verdict type.

Before doing anything, assess current state. Read all three target files in full:
- `/workspace/plugins/finesse/skills/prompt-validation/SKILL.md`
- `/workspace/plugins/finesse/commands/finesse.md`
- `/workspace/plugins/finesse/commands/finesse-resume.md`

Check whether each file already contains a severity tier table (search for "CRITICAL" and "MEDIUM" appearing in a markdown table). Check whether Step 2 in SKILL.md already uses tier-based gate logic instead of flat "Any FAIL" logic. Check whether the 50% budget threshold is already present. Use these observations to determine which phases are already complete, then resume from the first incomplete phase.

## Requirements

### Severity Tier Definitions

| Tier | Condition | Behavior |
|------|-----------|----------|
| **CRITICAL** | scope-safety-reviewer returns `FAIL` | Blocks presentation unconditionally. Must fix before presenting. |
| **HIGH** | clarity-checker, phase-structure-analyzer, or completion-validator returns `FAIL` | Blocks presentation. Must fix before presenting. |
| **MEDIUM** | goal-achievement-auditor or failure-mode-auditor returns `FAIL` | Should fix within refinement budget. Can present with explicit warnings if budget exhausted. |
| **LOW** | Any agent returns `NEEDS_REWORK` | Fix if budget allows after higher tiers resolved. |

### Budget-Aware Prioritization

When refinement budget drops below 50% remaining:
- CRITICAL and HIGH issues take absolute priority
- MEDIUM issues: only attempt if all CRITICAL/HIGH are resolved and budget remains
- LOW issues: only attempt if all higher tiers are resolved and budget remains

When budget is at or above 50%:
- Fix all tiers in priority order (CRITICAL → HIGH → MEDIUM → LOW)

### Presentation Rules

- If ANY CRITICAL or HIGH issues remain unresolved: plan CANNOT be presented regardless of budget state
- If only MEDIUM and/or LOW issues remain unresolved AND budget is exhausted: present the plan with explicit warnings listing each unresolved issue, its severity tier, and which agent flagged it
- All PASS from all agents: present without warnings (unchanged)

## Scope Constraints

- Do NOT modify any agent files in `/workspace/plugins/finesse/agents/`
- Do NOT modify `/workspace/plugins/finesse/skills/meta-prompting/SKILL.md`
- Do NOT modify `/workspace/plugins/finesse/skills/task-workflows/SKILL.md`
- Do NOT modify `/workspace/plugins/finesse/.claude-plugin/plugin.json`
- Do NOT change the agent verdict vocabulary (PASS/FAIL/NEEDS_REWORK) — only change how verdicts are interpreted
- Do NOT change the number of validators launched or their individual agent descriptions
- Do NOT remove or restructure existing steps (Steps 1-6, Refinement Budget, Post-Acceptance) in SKILL.md — modify their content in place
- Preserve ALL content not related to verdict handling (Post-Acceptance, agent launch instructions, safety escalation flow, user clarification flow, goal achievement escalation flow)
- Never rewrite an entire file from scratch. Always use targeted edits (Edit tool with old_string/new_string). If you find yourself replacing more than 40 contiguous lines, pause and verify you are making a targeted change, not a full rewrite.

## Phase 1: Update prompt-validation SKILL.md

**No dependencies. Can start immediately.**

Read `/workspace/plugins/finesse/skills/prompt-validation/SKILL.md` in full.

### 1a: Add Severity Tier Definitions

Find the line that reads `Each agent returns a verdict: \`PASS\`, \`FAIL\`, or \`NEEDS_REWORK\`.` and insert a new subsection immediately after it. The subsection should be titled `### Severity Tiers` and contain the exact tier table from the Requirements section above. Frame it as: "Each verdict is classified into a severity tier based on the agent and verdict type."

Before inserting, check whether the tier table already exists (search for "CRITICAL" in SKILL.md in a table context). If it already exists from a prior iteration, skip this sub-step.

### 1b: Rewrite Step 2 (Evaluate the Gate)

Find the section headed `### Step 2: Evaluate the Gate`. Replace the content between that heading and `### Step 3` with tier-based gate logic:

- **All PASS**: The plan is ready to present to the user.
- **Any CRITICAL issues**: You MUST fix these before presenting. They take absolute priority.
- **Any HIGH issues**: You MUST fix these before presenting. Second priority after CRITICAL.
- **Any MEDIUM issues**: Fix within refinement budget. If budget exhausted, present with explicit warnings listing each unresolved issue, its tier, and which agent flagged it.
- **Any LOW issues**: Fix if budget allows after all higher-tier issues are resolved.

### 1c: Rewrite Step 3 (Handle Failures)

Find the section headed `### Step 3: Handle Failures`. Replace its content (up to `### Step 4`) with priority-ordered failure handling:

1. Collect all issues from all agents and classify each by severity tier (using the tier table)
2. Separate into fixable-by-you vs requires-user-input (unchanged)
3. Fix in priority order: CRITICAL → HIGH → MEDIUM → LOW
4. **Budget-aware prioritization**: When the refinement budget drops below 50% remaining, focus exclusively on CRITICAL and HIGH issues. Skip MEDIUM and LOW unless all CRITICAL and HIGH issues are resolved and budget remains.
5. After each fix cycle, re-run ALL 6 validators on the revised plan (unchanged — catches regressions)
6. Each cycle costs one refinement iteration (unchanged)

### 1d: Update Refinement Budget Section

Find the section headed `### Refinement Budget`. Update it to include the 50% threshold rule:
- Default budget: 5 refinement cycles (unchanged)
- User can set via `--max-refinements N` (unchanged)
- When budget is at or above 50% remaining: fix all tiers in priority order (CRITICAL → HIGH → MEDIUM → LOW)
- When budget drops below 50% remaining: prioritize CRITICAL and HIGH exclusively
- Budget exhausted with unresolved MEDIUM/LOW only: present with explicit warnings listing each unresolved issue, its severity tier, and which agent flagged it
- CRITICAL or HIGH issues should never remain unresolved (they are mandatory), but if budget is exhausted with unresolved CRITICAL/HIGH: present with BLOCKING warnings and explicitly ask the user whether to proceed
- On user rejection with feedback: budget resets to 0 (unchanged)

### 1e: Update Multi-Workflow Validation

Find the `### Multi-Workflow Validation` subsection. Replace the verdict aggregation line that currently reads `A FAIL on any single sub-workflow blocks the entire plan.` with: `A CRITICAL or HIGH tier verdict on any sub-workflow blocks the entire plan. MEDIUM tier verdicts on a sub-workflow generate warnings but do not block if that sub-workflow's refinement budget is exhausted.`

Keep the rest of the multi-workflow section (per-sub-workflow validation, cross-sub-workflow checks) unchanged. Keep per-sub-workflow refinement budgets applying independently.

### 1f: Preserve Step 4 (Safety Escalation)

Do NOT modify Step 4 (Safety Escalation). The CRITICAL tier governs the gate decision (must fix before presenting). Safety Escalation is an additional user-acknowledgment requirement that applies on top when `SAFETY LEVEL: HIGH_RISK` is returned. Both mechanisms coexist.

### Phase 1 Verification

Read the modified SKILL.md in full. Then run these checks:

```
Verify: grep -c "CRITICAL" /workspace/plugins/finesse/skills/prompt-validation/SKILL.md
Expected: >= 2 (tier table + gate logic)

Verify: grep -c "50%" /workspace/plugins/finesse/skills/prompt-validation/SKILL.md
Expected: >= 1

Verify: grep "Any FAIL" /workspace/plugins/finesse/skills/prompt-validation/SKILL.md
Expected: no output (flat gate logic removed)

Verify: grep "Any NEEDS_REWORK" /workspace/plugins/finesse/skills/prompt-validation/SKILL.md
Expected: no output (flat gate logic removed)

Verify: grep -c "### Step 4: Safety Escalation" /workspace/plugins/finesse/skills/prompt-validation/SKILL.md
Expected: 1 (preserved)

Verify: grep -c "### Post-Acceptance" /workspace/plugins/finesse/skills/prompt-validation/SKILL.md
Expected: 1 (preserved)

Verify: grep "SAFETY LEVEL: HIGH_RISK" /workspace/plugins/finesse/skills/prompt-validation/SKILL.md
Expected: match found (safety escalation preserved)

Verify: grep "Do NOT guess or fill in blanks" /workspace/plugins/finesse/skills/prompt-validation/SKILL.md
Expected: match found (user clarification preserved)
```

If any check fails, re-read the file, identify what went wrong, and fix with a targeted edit. Do NOT re-apply the entire phase.

## Phase 2: Update finesse.md Validation Section

**No dependencies on Phase 1 (different file). Can start immediately if Phase 1 is complete or in parallel.**

Read `/workspace/plugins/finesse/commands/finesse.md`. Search for `### Validation` to find the section.

Replace the verdict handling block (from `**Handling verdicts:**` through the multi-workflow line) with a tier-aware version:

1. Keep the agent list and `All agents use the same verdict vocabulary: \`PASS\`, \`FAIL\`, or \`NEEDS_REWORK\`.` line unchanged
2. After the verdict vocabulary line, add the severity tier table (same table as in SKILL.md Requirements)
3. Replace the flat handling verdicts with:
   - **All PASS**: Plan is ready to present.
   - **Any CRITICAL or HIGH issues**: Must fix before presenting. Issues requiring user input → ask the user. Issues fixable by you → fix directly.
   - **Any MEDIUM issues**: Fix within refinement budget. If budget exhausted, present with explicit warnings listing each issue, its tier, and which agent flagged it.
   - **Any LOW issues (NEEDS_REWORK)**: Fix if budget allows after higher tiers resolved.
4. Add: `When refinement budget drops below 50% remaining, prioritize CRITICAL and HIGH issues exclusively.`
5. Update the budget-exhausted line: `If budget exhausted with only MEDIUM/LOW unresolved: present with explicit warnings listing each issue, its severity tier, and which agent flagged it.`
6. Update the multi-workflow line: `In Multi-Workflow mode, validate EACH sub-workflow's plan independently with all 6 validators. A CRITICAL or HIGH verdict on any sub-workflow blocks the entire plan.`
7. Keep the revalidation note (re-run ALL 6 agents to catch regressions)

### Phase 2 Verification

```
Verify: grep -c "CRITICAL" /workspace/plugins/finesse/commands/finesse.md
Expected: >= 2

Verify: grep -c "50%" /workspace/plugins/finesse/commands/finesse.md
Expected: >= 1

Verify: grep "Any FAIL" /workspace/plugins/finesse/commands/finesse.md
Expected: no output

Verify: grep "Any NEEDS_REWORK" /workspace/plugins/finesse/commands/finesse.md
Expected: no output
```

## Phase 3: Update finesse-resume.md Validation Section

**Requires Phase 2 complete.** Phase 3 copies Phase 2's changes. If Phase 2 is not complete, complete Phase 2 first.

Read `/workspace/plugins/finesse/commands/finesse.md` and capture the full validation section (between `### Validation` and `### Presentation`). Then read `/workspace/plugins/finesse/commands/finesse-resume.md`, search for `### Validation`, and replace the content between `### Validation` and `### Presentation` with the captured text from finesse.md. Do NOT attempt to reproduce the Phase 2 edits from memory — read the actual finesse.md output and copy it.

### Phase 3 Verification

```
Verify: diff <(sed -n '/^### Validation$/,/^### Presentation$/p' /workspace/plugins/finesse/commands/finesse.md) <(sed -n '/^### Validation$/,/^### Presentation$/p' /workspace/plugins/finesse/commands/finesse-resume.md)
Expected: no output (sections are identical)
```

If the diff shows differences, re-read both sections and fix finesse-resume.md to match finesse.md exactly.

## Phase 4: Cross-File Consistency Check

**Requires Phases 1, 2, and 3 complete.**

Read all three files' validation sections. Then run the final verification:

```
Verify: grep -rn "Any FAIL\|Any NEEDS_REWORK" /workspace/plugins/finesse/skills/prompt-validation/SKILL.md /workspace/plugins/finesse/commands/finesse.md /workspace/plugins/finesse/commands/finesse-resume.md
Expected: no output (all flat gate logic removed from all three files)

Verify: grep -c "CRITICAL" /workspace/plugins/finesse/skills/prompt-validation/SKILL.md
Expected: >= 2

Verify: grep -c "CRITICAL" /workspace/plugins/finesse/commands/finesse.md
Expected: >= 2

Verify: grep "goal-achievement-auditor" /workspace/plugins/finesse/skills/prompt-validation/SKILL.md
Expected: match found (Step 6 preserved)

Verify: grep "ralph-plans/" /workspace/plugins/finesse/skills/prompt-validation/SKILL.md
Expected: match found (Post-Acceptance preserved)
```

Also confirm by reading:
- Safety Escalation (Step 4 in SKILL.md) still contains `SAFETY LEVEL: HIGH_RISK` handling — coherent with CRITICAL tier as an additional check
- SKILL.md has the full detailed procedure; command files have a consistent summary
- The tier table content is the same across all three files

## Rules

- Preserve existing markdown formatting (ATX headers, pipe tables, code blocks)
- SKILL.md is authoritative; command files are summaries that reference SKILL.md's detail level
- Do NOT change agent output formats or verdict vocabulary
- Do NOT reorder, rename, or renumber steps in SKILL.md
- The tier system changes how Finesse interprets verdicts, not how agents produce them
- Do NOT add git operations (user opted out of git checkpointing)
- If an Edit tool call fails (old_string not found), STOP and re-read the target file before retrying. Never retry the same edit without first confirming the file's current content.
- Before inserting new content (tier tables, new logic), check whether it already exists in the file. If the content is already present from a prior iteration, do not insert it again.
- Never rewrite an entire file from scratch. Always use targeted edits (Edit tool with old_string/new_string). If you find yourself replacing more than 40 contiguous lines, pause and verify you are making a targeted change, not a full rewrite.
- If you have attempted the same fix 3 times without success, step back and try a fundamentally different approach (e.g., different old_string boundaries, different insertion point, or restructuring your edit strategy).
- Use content-based search (grep for `### Validation` or `Any FAIL`) to locate sections — never rely solely on line numbers, as they shift after edits.

## Stuck-State Instructions

- If SKILL.md structure has changed (steps renumbered, sections moved): read the full file, identify sections by their content/headings, and modify those
- If finesse.md or finesse-resume.md validation sections are at different line numbers than expected: search for `### Validation` to find them
- If the validation sections in finesse.md and finesse-resume.md have diverged: use finesse.md as the source of truth and make finesse-resume.md match
- If you're unsure whether a section should reference tiers: if it currently references "FAIL" or "NEEDS_REWORK" in the context of blocking/proceeding decisions, it should use tiers
- If Safety Escalation (HIGH_RISK handling) conflicts with the CRITICAL tier: the CRITICAL tier governs the gate decision (must fix before presenting); the safety escalation is an additional user-acknowledgment requirement that applies on top. Both are preserved.
- If an edit fails because old_string was not found: re-read the file with the Read tool, find the actual current content at that location, and reconstruct your edit with the correct old_string. Do NOT retry with the same old_string.
- If you have already applied changes from a prior iteration (e.g., the tier table is already in SKILL.md), skip that sub-step and proceed to the next one. Check for the presence of "CRITICAL" and "HIGH" and "MEDIUM" and "LOW" in a tier table format to detect prior application.
- After completing Phase 1 edits to SKILL.md, use grep to search for "Any FAIL" and "Any NEEDS_REWORK" across all three files. These are the flat gate patterns that must be replaced. If any remain, fix them before proceeding to Phase 2.
- For Phase 3 (making finesse-resume.md match finesse.md): first complete Phase 2 on finesse.md, then read the validation section of finesse.md to capture the exact final text, then find the corresponding section in finesse-resume.md by searching for `### Validation`, and replace it with the captured text. Do not attempt to reproduce the edits from memory.
- If verification after a phase reveals duplicated content, missing content, or broken formatting: undo the problematic edit by replacing the broken section with the correct version — do NOT re-apply the entire phase's changes on top of the existing state.
- If unable to make progress after 5 total failed edit attempts across all phases, document what is blocking you and output SEVERITY_TIERS_BLOCKED.

## Anti-Premature-Exit

Do NOT output the completion signal until ALL of the following have been verified by reading the actual file contents (not from memory):

1. Read SKILL.md and confirm: (a) a markdown table with CRITICAL, HIGH, MEDIUM, LOW appears between the verdict vocabulary line and Step 2; (b) Step 2 does not contain "Any FAIL" or "Any NEEDS_REWORK"; (c) Step 3 contains "CRITICAL" and "50%"; (d) Refinement Budget section contains "50%" and references tiers; (e) Step 4 still contains "SAFETY LEVEL: HIGH_RISK"; (f) Step 5 still contains "Do NOT guess or fill in blanks"; (g) Step 6 still contains "goal-achievement-auditor"; (h) Post-Acceptance still contains "ralph-plans/".
2. Read finesse.md validation section and confirm: (a) tier table present; (b) no "Any FAIL" or "Any NEEDS_REWORK"; (c) "50%" threshold present.
3. Read finesse-resume.md validation section and confirm identical content to finesse.md validation section.
4. Run: `grep -rn "Any FAIL\|Any NEEDS_REWORK" /workspace/plugins/finesse/skills/prompt-validation/SKILL.md /workspace/plugins/finesse/commands/finesse.md /workspace/plugins/finesse/commands/finesse-resume.md` — must return no output.

Only after all checks pass, output: SEVERITY_TIERS_COMPLETE

<promise>
All of these are true: (1) SKILL.md contains a markdown table mapping CRITICAL to scope-safety-reviewer FAIL, HIGH to clarity-checker/phase-structure-analyzer/completion-validator FAIL, MEDIUM to goal-achievement-auditor/failure-mode-auditor FAIL, and LOW to any NEEDS_REWORK. (2) SKILL.md Step 2 contains "CRITICAL" and "HIGH" and "MEDIUM" and "LOW" in its gate logic, and does NOT contain "Any FAIL" or "Any NEEDS_REWORK". (3) SKILL.md Step 3 contains "50%" in budget-aware prioritization context and fixes in CRITICAL→HIGH→MEDIUM→LOW priority order. (4) SKILL.md Refinement Budget section contains "50%" and references severity tiers. (5) SKILL.md multi-workflow aggregation references CRITICAL/HIGH blocking instead of flat "A FAIL on any single sub-workflow blocks". (6) Grepping for "Any FAIL" and "Any NEEDS_REWORK" in all three files returns zero matches. (7) The validation sections in finesse.md and finesse-resume.md are identical to each other and both contain the tier table and 50% threshold. (8) SKILL.md Step 4 still contains "SAFETY LEVEL: HIGH_RISK", Step 5 still contains "Do NOT guess or fill in blanks", Step 6 still contains "goal-achievement-auditor", and Post-Acceptance still contains "ralph-plans/".
</promise>
