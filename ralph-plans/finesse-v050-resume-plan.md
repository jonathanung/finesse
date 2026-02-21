# Finesse v0.5.0 — Resume Command

## Task Type
Feature

## Summary
Add a `/finesse-resume` command that recovers interrupted planning sessions from working files, plus enhance the working file format with structured YAML frontmatter for reliable phase detection.

## Codebase Context
- **finesse.md** (~360 lines): Main orchestrator. Context Compaction Handling at lines ~336-358 defines the working file spec (free-form) and Post-Compaction Rules. Common Final Phases at lines ~126-197 (Plan Construction, Git Config, Subagent Config, Validation, Presentation, User Decision). These must be inlined into the resume command.
- **cancel-finesse.md** (13 lines): Minimal secondary command pattern — description + hide-from-slash-command-tool frontmatter, short procedural body.
- **finesse-help.md** (143 lines): Available Commands section lists /finesse and /cancel-finesse. What Happens section has 10-step overview.
- **task-workflows/SKILL.md** (744 lines): 6 workflow types with phase definitions — Feature F1-F8, Bugfix B1-B7, Refactor R1-R7, Testing T1-T6, Performance P1-P6, Research RE1-RE8.
- **Version files**: plugin.json, marketplace.json, finesse-version.md — all v0.4.0 → v0.5.0.

## Chosen Approach
**Approach 1: Minimal — New Command + Enhanced Working File**

- New `finesse-resume.md` command (~280-320 lines) self-contained with all resume logic
- Enhanced working file format in finesse.md (YAML frontmatter schema added to Context Compaction Handling)
- Resume command inlines Common Final Phases, UAT Checkpoint Procedure, and Critical Rules (necessary since commands are standalone prompts)
- References task-workflows skill for workflow phase definitions
- 6 files total (1 new + 5 modified)

**Rationale**: Follows existing secondary command pattern (cancel-finesse.md). Exactly 6 files. Accepts ~100 lines of Common Final Phases duplication as inherent to standalone command architecture (no import mechanism in Claude Code plugin commands). Avoids over-engineering (Approach 2's shared skill) and requirement mismatch (Approach 3's --resume flag).

## User Decisions from Discovery
- Enhanced working file format with YAML frontmatter (not free-form parsing)
- Present summary then continue (not re-present UAT or jump straight)
- All 6 workflow types supported from day one
- Both single-workflow and multi-workflow (decomposed) sessions supported
- Discovery phases restart from scratch when resumed (recovered notes serve as context)
- Inline workflow reference in resume command (self-contained, not handoff to /finesse)
- Version: v0.5.0
- Both modes: no-arg scan + path-arg direct load
- No git checkpointing
- No subagent instructions (no phases meaningfully eligible)

## Recommended --max-iterations
**14** — Medium-to-complex feature. 6 files (1 new creation + 5 modifications). Phase 2 is substantial: creating a ~280-320 line self-contained command file that inlines content from finesse.md. Phase 1 is a structured rewrite of an existing section. Phases 3-4 are straightforward.

## Validation Results
All 5 validators returned PASS:
- clarity-checker: PASS
- completion-validator: PASS
- scope-safety-reviewer: PASS (LOW_RISK)
- phase-structure-analyzer: PASS
- failure-mode-auditor: PASS
