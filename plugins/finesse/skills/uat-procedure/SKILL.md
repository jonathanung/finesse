---
description: "UAT Checkpoint Procedure for Finesse planning sessions — presentation format, response handling, and diff summary rules"
---

# UAT Checkpoint Procedure

Phases marked `[UAT]` in the workflow sequences require a User Acceptance Testing checkpoint before proceeding. When you reach a `[UAT]` phase:

## 1. Present the phase output

Format the output for review using this structure:

**UAT Checkpoint: [Phase Name]**

- **What was done**: 1-2 sentence summary of the phase's activity
- **Key findings / decisions**: Bulleted list of substantive outputs (architecture choices, files identified, root cause hypothesis, etc.)
- **Impact on next phases**: How this output shapes what comes next

## 2. Ask the user

Use `AskUserQuestion` with these 4 options:
1. **Accept** — proceed to the next phase
2. **Provide feedback** — re-run this phase incorporating the user's free-text feedback
3. **Make specific changes** — apply the user's targeted edits to the phase output without re-running
4. **Accept and skip remaining UAT** — auto-approve all future UAT checkpoints in this planning session

## 3. Handle the response

- **Accept**: Proceed to the next phase.
- **Provide feedback**: The user gives free-text feedback. Snapshot the current phase output, then re-run the phase from scratch incorporating their feedback as additional constraints. Generate a **diff summary** comparing the pre-feedback and post-feedback phase output (see Diff Summary Format below). Present the revised output at the same UAT checkpoint again, with the diff summary included under a "What changed since last review:" heading above the phase output.
- **Make specific changes**: The user specifies targeted edits (e.g., "change the database from PostgreSQL to SQLite in the architecture"). Snapshot the current phase output, then apply the edits directly without re-running the full phase. Generate a **diff summary** comparing the pre-edit and post-edit phase output (see Diff Summary Format below). Present the revised output at the same UAT checkpoint again, with the diff summary included under a "What changed since last review:" heading above the phase output.
- **Accept and skip remaining UAT**: Note that UAT is fast-forwarded. For all subsequent `[UAT]` phases, auto-accept and proceed without presenting the checkpoint. Discovery/Understanding phase confirmations are NOT affected by fast-forward — those always happen.

## UAT replaces inline confirmations

Previous inline confirmation gates within `[UAT]`-marked phases (e.g., "Present the strategy. Confirm with user." or "Ask which approach the user prefers.") are now handled by the UAT checkpoint at the end of that phase. Do NOT ask for confirmation mid-phase AND at the UAT checkpoint — that would double-gate. The UAT checkpoint IS the confirmation.

**Exception**: Discovery/Understanding phases (F1, B1, R1, P1, RE1) are NOT UAT-gated. They retain their own deeper confirmation flow because Discovery requires iterative back-and-forth, not a single accept/reject gate.

## Diff Summary Format

When generating a diff summary (for UAT feedback cycles or plan rejection cycles), compare the pre-edit and post-edit text and produce a concise bulleted list of semantic changes. This is NOT a unified diff — it is a human-readable summary.

**Rules:**
- Start each bullet with a prescribed action verb: **Added**, **Removed**, **Changed**, **Moved**, **Replaced**, **Tightened**, **Relaxed**, **Merged**, **Split**
- Use natural phrasing after the verb — no rigid template
- Include before/after values when relevant (e.g., "Changed Phase 2 verification command from `npm test` to `npm run test:integration`")
- Group bullets by section when there are many changes (e.g., "Cold start", "Phase 2", "Rules", "Completion criteria")
- Omit sections with no changes
- Keep each bullet to one line
- Maximum 15 bullets — if more changes exist, summarize the remainder as "... and N additional minor edits"
- The diff summary is generated inline by comparing the two versions already in context. No separate agent or script is needed.

**Examples:**
- Added guardrail: Do NOT modify config files
- Changed Phase 2 verification command from `npm test` to `npm run test:integration`
- Increased max-iterations recommendation from 12 to 15 with reasoning
- Added new Phase 3 for database migration
- Removed scope constraint on `src/legacy/` directory
- Tightened completion criteria to require all linter warnings resolved, not just errors
