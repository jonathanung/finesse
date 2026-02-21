# Finesse v0.3.1 — Git Configuration Prompt

## Task Type
Feature (minor)

## Summary
Add a mandatory git configuration prompt during Plan Construction that allows users to control whether the ralph-loop agent uses git to checkpoint progress (commit between phases) and whether it pushes to remote. Replaces the hardcoded "Do NOT push to remote repositories." universal rule with user-configurable git rules.

## Codebase Context
- **finesse.md** (298 lines): Main orchestrator. Common Final Phases > Plan Construction at lines 126-150 defines the 7-item prompt assembly list. Multi-Workflow Plan Construction at lines 142-149.
- **meta-prompting/SKILL.md** (179 lines): Prompt construction guide. Template at lines 57-88 with hardcoded "Do NOT push to remote repositories." at line 76. Mandatory Attribute #6 at lines 34-39 (no push mention). File Output Format section ends ~line 101, Multi-Workflow Output Format starts ~line 104.
- **plugin.json**: Version 0.3.0
- **finesse-version.md**: Displays "Finesse v0.3.0"

## Chosen Approach
Split git configuration between orchestration (finesse.md) and content (meta-prompting/SKILL.md):
- **finesse.md** gets a new "Git Configuration Prompt" subsection defining the AskUserQuestion flow (3 conditional questions)
- **meta-prompting/SKILL.md** gets the template placeholder and a new "Git Configuration Rules" section defining exact rules for each combination

Rationale: Respects existing separation of concerns. Follows the existing [placeholder] pattern in the template.

## Recommended --max-iterations
**8** — Simple feature, 4 files, clear edit targets, low complexity.

## Validation Results
| Validator | Verdict |
|---|---|
| clarity-checker | NEEDS_REWORK → Fixed |
| completion-validator | PASS |
| scope-safety-reviewer | PASS (LOW_RISK) |
| phase-structure-analyzer | PASS |
| failure-mode-auditor | PASS |

Fix applied: Phase 2 Mandatory Attribute #6 instruction changed from "update the mention of pushing" to "add a note after the existing bullet list" since no push mention exists in that section.
