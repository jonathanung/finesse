# Finesse v0.4.0 — Subagent Spawning Instructions

## Task Type
Feature

## Summary
Add subagent spawning instructions to the ralph-loop prompts that Finesse generates. During plan construction, Finesse analyzes the phase structure, identifies subagent-eligible phases based on three heuristics (independent subtasks, parallel verification, exploration benefit), presents the analysis to the user, and conditionally embeds Task tool usage instructions into the generated prompt.

## Codebase Context
- **meta-prompting/SKILL.md** (236 lines): Prompt construction guide. Template at lines 57-90. Git Configuration Rules at lines 106-159. Multi-Workflow Output Format at lines 161-235. New Subagent Configuration section inserts between Git Config Rules and Multi-Workflow Output.
- **finesse.md** (322 lines): Main orchestrator. Plan Construction at lines 128-173. Git Configuration Prompt at lines 144-163. Multi-Workflow Plan Construction at lines 165-173. New Subagent Configuration Prompt inserts after Git Config Prompt.
- **task-workflows/SKILL.md** (732 lines): Phase definitions for 6 workflows. Each Plan Construction phase gets a subagent analysis note.
- **finesse-help.md** (143 lines): User-facing help. Step 6 gets subagent mention.
- **Version files**: plugin.json, marketplace.json, finesse-version.md — all 0.3.1 → 0.4.0.

## Chosen Approach
Mirror Git Config Pattern — follow the proven structural pattern from v0.3.1:
- meta-prompting/SKILL.md: new "## Subagent Configuration" section with heuristics, formats, guardrails
- finesse.md: new "### Subagent Configuration Prompt" subsection (analysis → presentation → question → injection)
- task-workflows/SKILL.md: identical notes in all 6 Plan Construction phases
- Template: conditional [placeholder] additions

Rationale: Proven pattern, minimal disruption, co-located with existing config sections, no new files.

## Recommended --max-iterations
**12** — Medium feature, 7 files, 5 phases. Targeted edits to well-understood insertion points. Similar to v0.3.1 scope but with more files.

## Validation Results
| Validator | Verdict |
|---|---|
| scope-safety-reviewer | PASS (LOW_RISK) |
| phase-structure-analyzer | PASS |
| clarity-checker | NEEDS_REWORK → Fixed |
| completion-validator | NEEDS_REWORK → Fixed |
| failure-mode-auditor | NEEDS_REWORK → Fixed |

Fixes applied: Added exact placeholder text, concrete annotation example, clarified identical note across workflows, added template placeholder verification, grep diagnosis rules, code block nesting check.
