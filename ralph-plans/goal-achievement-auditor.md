You are iterating on adding a new validation agent called `goal-achievement-auditor` to the Finesse plugin at `/workspace/plugins/finesse/`. This agent performs goal-backward validation — it checks whether a drafted ralph-loop prompt will actually achieve its stated goal by deriving observable truths and verifying each is covered by plan phases. The agent is being ADDED as a 6th validator alongside the existing 5 (clarity-checker, completion-validator, scope-safety-reviewer, phase-structure-analyzer, failure-mode-auditor). All 6 validators must be launched in parallel during validation.

On cold start, determine your resume point by running these checks in reverse phase order — the first check that FAILS is where you resume:

1. Final check: Run `grep -r "5 valid\|FIVE\|5 agent\|ALL 5\|all 5\|5 standard" plugins/finesse/ --include="*.md"`. If no matches AND `grep -rl "goal-achievement-auditor" plugins/finesse/ --include="*.md" | wc -l` returns 5: all work is done. Output the completion promise.
2. Check Phase 6: `grep "goal-achievement-auditor" plugins/finesse/commands/finesse-help.md` — if no match, resume at Phase 6.
3. Check Phase 5: `grep "goal-achievement-auditor" plugins/finesse/commands/finesse-resume.md` — if no match, resume at Phase 5.
4. Check Phase 4: `grep "goal-achievement-auditor" plugins/finesse/commands/finesse.md` — if no match, resume at Phase 4.
5. Check Phase 3: `grep "6 validation" plugins/finesse/skills/task-workflows/SKILL.md` — if no match, resume at Phase 3.
6. Check Phase 2: `grep "goal-achievement-auditor" plugins/finesse/skills/prompt-validation/SKILL.md` — if no match, resume at Phase 2.
7. Check Phase 1: `test -f plugins/finesse/agents/goal-achievement-auditor.md` — if file doesn't exist, start at Phase 1.

## Requirements

### Phase 1: Create the goal-achievement-auditor agent

Create `plugins/finesse/agents/goal-achievement-auditor.md` following the exact structural pattern of existing validators. Read `plugins/finesse/agents/clarity-checker.md` first as the structural template.

The file must contain:

**YAML Frontmatter:**

```yaml
---
description: "Checks whether a drafted ralph-loop prompt will actually achieve its stated goal by deriving observable truths and verifying phase coverage"
---
```

**Title and introductory paragraph:**

```markdown
# Goal Achievement Auditor

You are reviewing a drafted ralph-loop plan. Your sole focus is **whether the plan will actually achieve its stated goal**. You work backward from the goal: extract it, derive the observable truths that must hold when the goal is met, and verify that the plan's phases and completion criteria cover every truth.
```

**"## What to Check" section with 5 numbered subsections:**

### 1. Goal Extraction
Extract the primary goal from the cold start paragraph. The goal is the concrete end-state the user expects after the ralph-loop completes — stated as a 1-2 sentence description of what will be different when done. If the cold start paragraph does not clearly state a goal (no discernible end-state, purely procedural instructions with no outcome), verdict is FAIL.

For each plan, output the extracted goal so the parent agent can verify you interpreted it correctly.

### 2. Truth Derivation
From the extracted goal, derive 3-7 observable truths that MUST be true when the goal is achieved. Each truth must be:
- **Post-execution observable**: A concrete, verifiable outcome after the ralph-loop runs (e.g., "all tests pass", "endpoint returns 200 for valid input", "file X exists with content Y"). NOT implementation-level details (e.g., "function uses recursion" or "variable is renamed").
- **User-perspective**: Framed as what the user would observe or verify, not internal code structure. Good: "user can log in with OAuth". Bad: "JWT token is generated with correct claims".
- **Independent**: Each truth captures a distinct aspect of goal achievement. No truth should be a subset of another.
- **Exhaustive**: Together, the truths fully characterize what it means for the goal to be achieved. If all truths are satisfied, the goal IS achieved.

If you cannot derive at least 3 meaningful truths, the goal may be too narrow. If you need more than 7, the goal may be too broad. Note this in your output but do not change the verdict for this reason alone.

### 3. Phase Coverage
For each derived truth, identify at least one phase in the plan that addresses it. Build a coverage matrix:
- Map each truth to its covering phase(s)
- For each mapping, provide a 1-sentence rationale explaining WHY that phase addresses the truth
- If ANY truth has zero covering phases, verdict is FAIL — the plan has a structural gap that means it cannot achieve the goal even if executed perfectly

### 4. Dependency Flow
For each truth's covering phases, verify they appear in the correct logical order:
- Phases that produce artifacts, files, or state needed by later phases MUST come before those later phases
- When multiple phases cover one truth, they must build on each other in sequence (e.g., "create file" before "edit file")
- Cross-truth phase ordering must be consistent: if Phase N covers Truth A and Phase M covers Truth B, and Truth B's phase depends on Truth A's output, then N must come before M
- If dependency violations are found but all truths are still covered, verdict is NEEDS_REWORK (not FAIL — the coverage exists, just the ordering needs fixing)

### 5. Completion Criteria Verification
Examine the plan's completion criteria (the `<promise>` section and any "When ALL of the following are true" conditions). For each derived truth, verify the completion criteria include at least one condition that proves the truth is satisfied. This means:
- Each truth must map to a completion criterion that would fail if the truth were NOT satisfied
- Criteria must be binary (pass/fail), not subjective
- If ALL truths are covered by phases but the completion criteria do NOT verify all truths, verdict is NEEDS_REWORK — the plan might achieve the goal but can't prove it did

**Output Format:**

```
VERDICT: PASS | FAIL | NEEDS_REWORK

GOAL:
[extracted goal from cold start paragraph]

OBSERVABLE TRUTHS:
1. [truth statement]: [why this must be true for goal achievement]
2. [truth statement]: [why this must be true for goal achievement]
...

COVERAGE MATRIX:
| # | Truth | Covering Phase(s) | Rationale |
|---|---|---|---|
| 1 | [truth] | Phase N, Phase M | [1-sentence why these phases address this truth] |
| 2 | [truth] | Phase N | [1-sentence why] |
...

UNCOVERED TRUTHS (if any):
- Truth N: [no phase addresses this truth]

DEPENDENCY ISSUES (if any):
- [phase ordering issue]: [what depends on what and why the order is wrong]

COMPLETION CRITERIA GAPS (if any):
- Truth N: [not verified by any completion criterion]

ISSUES (if FAIL or NEEDS_REWORK):
- [specific issue]: [what to fix]
```

**Verdict rules:**
- **PASS**: All truths have covering phases in correct dependency order, and completion criteria verify all truths.
- **FAIL**: Any truth has no covering phase, OR the cold start paragraph has no extractable goal. The plan cannot achieve its stated goal as structured.
- **NEEDS_REWORK**: All truths are covered by phases but completion criteria don't verify them all, OR dependency flow has ordering issues that the planner can fix without restructuring.

Guidance: Be specific about which truths are uncovered and which phases could address them. The parent agent needs actionable feedback to fix the plan.

Verify:
- `test -f plugins/finesse/agents/goal-achievement-auditor.md && echo EXISTS` prints EXISTS
- `head -1 plugins/finesse/agents/goal-achievement-auditor.md` prints `---`
- `grep -c "^### " plugins/finesse/agents/goal-achievement-auditor.md` returns 5
- `grep -c "COVERAGE MATRIX\|Coverage Matrix\|coverage matrix" plugins/finesse/agents/goal-achievement-auditor.md` returns >= 1
- `grep "PASS" plugins/finesse/agents/goal-achievement-auditor.md` AND `grep "FAIL" plugins/finesse/agents/goal-achievement-auditor.md` AND `grep "NEEDS_REWORK" plugins/finesse/agents/goal-achievement-auditor.md` all return matches

### Phase 2: Update prompt-validation skill

Edit `plugins/finesse/skills/prompt-validation/SKILL.md`:

1. Line 13: Change `ALL FIVE agents` to `ALL SIX agents`
2. After the line containing `5. **failure-mode-auditor**`, add: `6. **goal-achievement-auditor** — Does the prompt actually achieve the stated goal? Are all observable truths covered by phases and verified by completion criteria?`
3. Change ALL 3 remaining occurrences of validator count references in the file:
   - `all 5 validators` → `all 6 validators` (2 occurrences, around lines 27 and 33)
   - `ALL 5 validators` → `ALL 6 validators` (1 occurrence, around line 52)
4. After the existing `### Step 5: User Clarification` section (around lines 59-66), add:

```markdown
### Step 6: Goal Achievement Escalation

When the goal-achievement-auditor identifies issues that require user input:
- If the cold start paragraph has no extractable goal: ask the user to clarify the intended end-state of the ralph-loop. What should be different when done?
- If derived truths have no covering phases: present the uncovered truths and ask whether they should be added as new phases or whether the truths are incorrect
- If completion criteria don't verify all truths: present the gaps and suggest specific additions to the promise section
- Do NOT invent phases or modify the goal yourself — surface the gaps for user decision
```

Verify:
- `grep -c "goal-achievement-auditor" plugins/finesse/skills/prompt-validation/SKILL.md` returns at least 2
- `grep "ALL FIVE\|all 5\|ALL 5" plugins/finesse/skills/prompt-validation/SKILL.md` returns no matches
- `grep "Goal Achievement Escalation" plugins/finesse/skills/prompt-validation/SKILL.md` returns a match

### Phase 3: Update task-workflows skill

Edit `plugins/finesse/skills/task-workflows/SKILL.md`:

1. Change `all 5 validation agents` → `all 6 validation agents` (2 occurrences, around lines 198 and 757)
2. Change `all 5 standard validation agents` → `all 6 standard validation agents` (1 occurrence, around line 779)

Verify:
- `grep "5 validation\|5 standard" plugins/finesse/skills/task-workflows/SKILL.md` returns no matches
- `grep -c "6 validation\|6 standard" plugins/finesse/skills/task-workflows/SKILL.md` returns 3

### Phase 4: Update finesse.md command

Edit `plugins/finesse/commands/finesse.md`:

1. Around line 275: Change `ALL 5 validation agents` → `ALL 6 validation agents`
2. After the line containing `5. **failure-mode-auditor**` in the validator list, add: `6. **goal-achievement-auditor** — goal achievement, truth coverage, dependency flow`
3. Change all 3 remaining count references (each "ALL 5" / "all 5" appears in a different sentence — include the full sentence as old_string for uniqueness):
   - Around line 289: `ALL 5 agents` → `ALL 6 agents` (in the sentence about revalidating after fixes)
   - Around line 293: `all 5 validators` → `all 6 validators` (in the Multi-Workflow validation sentence)
   - Around line 349: `ALL 5 agents` → `ALL 6 agents` (in the rejection handling section)

Verify:
- `grep "ALL 5\|all 5" plugins/finesse/commands/finesse.md` returns no matches
- `grep -c "goal-achievement-auditor" plugins/finesse/commands/finesse.md` returns at least 1
- `grep -c "ALL 6\|all 6" plugins/finesse/commands/finesse.md` returns 4

### Phase 5: Update finesse-resume.md command

Edit `plugins/finesse/commands/finesse-resume.md`:

1. Around line 326: Change `ALL 5 validation agents` → `ALL 6 validation agents`
2. After the line containing `5. **failure-mode-auditor**` in the validator list, add: `6. **goal-achievement-auditor** — goal achievement, truth coverage, dependency flow`
3. Change all 3 remaining count references (each appears in a different sentence — include full sentence as old_string):
   - Around line 340: `ALL 5 agents` → `ALL 6 agents` (revalidating after fixes sentence)
   - Around line 344: `all 5 validators` → `all 6 validators` (Multi-Workflow validation sentence)
   - Around line 400: `ALL 5 agents` → `ALL 6 agents` (rejection handling section)

Verify:
- `grep "ALL 5\|all 5" plugins/finesse/commands/finesse-resume.md` returns no matches
- `grep -c "goal-achievement-auditor" plugins/finesse/commands/finesse-resume.md` returns at least 1
- `grep -c "ALL 6\|all 6" plugins/finesse/commands/finesse-resume.md` returns 4

### Phase 6: Update finesse-help.md command

Edit `plugins/finesse/commands/finesse-help.md`:

1. Around line 77: Change `5 agents review the plan simultaneously` → `6 agents review the plan simultaneously`
2. After the failure-mode-auditor row in the Validation Agents table (around line 109), add: `| goal-achievement-auditor | Does the prompt achieve the stated goal? Truth coverage + dependency flow |`
3. Around line 141: Change `All 5 validators re-run` → `All 6 validators re-run`

Verify:
- `grep "5 agents\|5 validator\|All 5" plugins/finesse/commands/finesse-help.md` returns no matches
- `grep "goal-achievement-auditor" plugins/finesse/commands/finesse-help.md` returns a match

### Phase 7: Final cross-file verification

Run ALL of these checks — every one must pass:

1. `grep -r "5 valid\|FIVE\|5 agent\|ALL 5\|all 5\|5 standard" plugins/finesse/ --include="*.md"` — MUST return no matches
2. `grep -rl "goal-achievement-auditor" plugins/finesse/ --include="*.md" | wc -l` — MUST return exactly 5 (agent file + prompt-validation SKILL + finesse.md + finesse-resume.md + finesse-help.md; task-workflows only changes numbers, not agent names)
3. `grep "Goal Achievement Escalation" plugins/finesse/skills/prompt-validation/SKILL.md` — MUST return a match
4. `grep -c "6 validation\|6 standard" plugins/finesse/skills/task-workflows/SKILL.md` — MUST return 3
5. Non-validator regression check: `grep -rn "6 refinement" plugins/finesse/ --include="*.md"` — MUST return no matches (if any match, a non-validator "5" was accidentally changed — revert it)

If any check fails, fix the issue and re-run ALL checks.

## Scope

### Files to create
- `plugins/finesse/agents/goal-achievement-auditor.md`

### Files to edit
- `plugins/finesse/skills/prompt-validation/SKILL.md`
- `plugins/finesse/skills/task-workflows/SKILL.md`
- `plugins/finesse/commands/finesse.md`
- `plugins/finesse/commands/finesse-resume.md`
- `plugins/finesse/commands/finesse-help.md`

### Files to read (reference only)
- `plugins/finesse/agents/clarity-checker.md` — structural template

### Do NOT modify
- Any existing agent files (clarity-checker.md, completion-validator.md, scope-safety-reviewer.md, phase-structure-analyzer.md, failure-mode-auditor.md, code-explorer.md, code-architect.md, task-decomposer.md)
- `plugins/finesse/.claude-plugin/plugin.json`
- `plugins/finesse/skills/meta-prompting/SKILL.md`
- `plugins/finesse/commands/cancel-finesse.md`
- `plugins/finesse/commands/finesse-version.md`
- Any files outside `plugins/finesse/`

## Rules

- Do NOT change the behavior or content of any existing validator agent
- Do NOT rewrite files from scratch — make targeted edits only
- Do NOT change the verdict vocabulary (PASS/FAIL/NEEDS_REWORK) — the new agent uses the same
- The new agent MUST follow the exact structural pattern of existing validators (YAML frontmatter → H1 title → introductory paragraph → "## What to Check" with numbered ### subsections → "## Output Format" → verdict rules)
- Do NOT change any occurrence of "5" that refers to: refinement cycles (e.g., "5 refinement cycles"), step numbers (e.g., "Step 5"), numbered list ordinals (e.g., "5. Each cycle costs..."), or any other non-validator-pipeline-count context. ONLY change "5" when it explicitly refers to the count of validation agents (e.g., "ALL 5 validation agents", "all 5 validators", "ALL FIVE agents", "5 agents review", "5 standard validation agents")
- When using the Edit tool, always include enough surrounding context in old_string to ensure uniqueness. If the same pattern (e.g., "ALL 5") appears multiple times in a file, include the full sentence or surrounding lines. If an edit fails due to non-unique match, expand old_string — never make it shorter
- After completing edits in each file, re-read the file and verify no unintended changes were made to non-validator "5" references (especially "5 refinement cycles", "Step 5", numbered list items)
- Observable truths in the new agent must be post-execution verifiable outcomes, not implementation details
- The coverage matrix MUST include a 1-sentence rationale per truth-to-phase mapping
- Do NOT add git commits during execution
- Do NOT push to remote

## When Stuck

- If unsure about exact line numbers: read the full file first, search for the specific pattern, then edit
- If a "5" reference is ambiguous: read the surrounding 5 lines. Only change if context explicitly refers to the validation agent pipeline count
- If the agent prompt structure doesn't match other validators: re-read `plugins/finesse/agents/clarity-checker.md` and mirror its exact organization
- If an Edit tool call fails with "old_string is not unique": expand old_string to include more surrounding context (full paragraph or lines before/after). Do NOT fix by making old_string shorter
- If verification commands fail: re-read the file, compare with expected content, fix discrepancies
- If you accidentally change a non-validator "5" (e.g., "5 refinement cycles" → "6 refinement cycles"): revert that specific edit immediately before continuing
- If unable to make progress after 3 consecutive attempts on the same issue: output `<promise>BLOCKED: [description of what's stuck]</promise>`

## Completion

When ALL of the following are true, output the completion signal:

1. `plugins/finesse/agents/goal-achievement-auditor.md` exists with YAML frontmatter, 5 numbered "### " subsections under "## What to Check", an "## Output Format" section containing a coverage matrix, and verdict rules defining PASS, FAIL, and NEEDS_REWORK
2. `plugins/finesse/skills/prompt-validation/SKILL.md` says "ALL SIX agents", lists goal-achievement-auditor as item 6, has "all 6 validators" / "ALL 6 validators" in all 3 count-reference locations, and has a "Goal Achievement Escalation" section
3. `plugins/finesse/skills/task-workflows/SKILL.md` says "all 6 validation agents" in 2 locations and "all 6 standard validation agents" in 1 location (3 total)
4. `plugins/finesse/commands/finesse.md` says "ALL 6" in 3 locations and "all 6" in 1 location (4 total), and lists goal-achievement-auditor in the validator list
5. `plugins/finesse/commands/finesse-resume.md` says "ALL 6" in 3 locations and "all 6" in 1 location (4 total), and lists goal-achievement-auditor in the validator list
6. `plugins/finesse/commands/finesse-help.md` says "6 agents" in 1 location and "6 validators" in 1 location, and lists goal-achievement-auditor in the Validation Agents table
7. `grep -r "5 valid\|FIVE\|5 agent\|ALL 5\|all 5\|5 standard" plugins/finesse/ --include="*.md"` returns no matches
8. `grep -rl "goal-achievement-auditor" plugins/finesse/ --include="*.md" | wc -l` returns exactly 5
9. No non-validator "5" references were changed: `grep -rn "6 refinement" plugins/finesse/ --include="*.md"` returns no matches

<promise>The goal-achievement-auditor agent has been created at plugins/finesse/agents/goal-achievement-auditor.md following the validator pattern with 5 check sections (Goal Extraction, Truth Derivation, Phase Coverage, Dependency Flow, Completion Criteria Verification), coverage matrix output, and PASS/FAIL/NEEDS_REWORK verdicts. All references to 5 validators across prompt-validation SKILL, task-workflows SKILL, finesse.md, finesse-resume.md, and finesse-help.md have been updated to 6. The prompt-validation skill includes a Goal Achievement Escalation section. No orphaned references to 5 validators remain in the plugin. No non-validator references were changed.</promise>