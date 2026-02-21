---
description: "Context compaction handling for Finesse planning sessions — working file schema, recovery rules, and phase codes"
---

# Context Compaction Handling

When a planning session is long, Claude Code may compact context. To ensure critical information survives compaction:

## Working File Persistence

1. **Early persistence**: As soon as codebase exploration results are gathered, write key findings to `finesse-plans/<name>-working.md`. Update this file at each major phase boundary. The YAML frontmatter (see item 2) must be included from the first write and updated at each phase boundary.
2. **Working file structure**: ALL working files MUST include a YAML frontmatter block at the top of the file, before any markdown body content. The mandatory schema:
   ```yaml
   ---
   mode: planning-only  # CRITICAL: Never edit source code. Never implement.
   allowed_agents: [code-explorer, code-architect, task-decomposer, clarity-checker, completion-validator, scope-safety-reviewer, phase-structure-analyzer, failure-mode-auditor, goal-achievement-auditor]
   task_type: <feature|bugfix|refactor|testing|performance|research>
   workflow: <feature-development|bug-fix|refactor-chore|testing|performance-optimization|research>
   current_phase: <phase code, e.g., F5, B3, RE4>
   completed_phases: [<list of completed phase codes, e.g., F1, F2, F3, F4>]
   uat_fast_forward: <true|false>
   session_name: <kebab-case session descriptor>
   decomposed: <true|false>
   refinement_budget: <number>  # --max-refinements value, populated during Validation
   refinement_cycles_used: <number>  # cycles consumed so far, updated during Validation
   context_pressure: <low|moderate|high|critical>  # populated during Plan Construction
   context_budget:  # populated during Plan Construction
     peak_iteration_tokens: <number>
     context_window: <number>
     pressure_pct: <number>
     estimated_cost_range: <string>
     file_count: <number>
     file_categories:
       small: <number>
       medium: <number>
       large: <number>
   sub_workflows: # only present if decomposed: true
     - name: <sub-workflow kebab-case name>
       type: <task type>
       wave: <wave number>
       current_phase: <phase code>
       completed_phases: [<completed phase codes>]
       context_pressure: <low|moderate|high|critical>  # per-sub-workflow, populated during Plan Construction
       context_budget:  # per-sub-workflow, populated during Plan Construction
         peak_iteration_tokens: <number>
         pressure_pct: <number>
         estimated_cost_range: <string>
   ---
   ```
   Below the YAML frontmatter, the working file body MUST start with a Session Constraints block, followed by free-form markdown:
   ```markdown
   ## Session Constraints (DO NOT DELETE)
   - PLANNING-ONLY session. Output is a ralph-loop command. NEVER edit source code.
   - Task agents ONLY for: code-explorer, code-architect, task-decomposer, and 6 validation agents
   - Write ONLY to finesse-plans/ and .finesse/
   - NEXT ACTION: [describe the current/next phase step]
   - DO NOT: edit source files, launch general-purpose agents, implement the plan
   ```
   After the Session Constraints block, include: codebase findings, UAT checkpoint decisions and their outcomes, prompt draft (if one exists), promise draft (if one exists), open questions or blockers.
3. **Recovery**: If you detect that context has been compacted (e.g., you cannot recall earlier phase outputs), read `finesse-plans/<name>-working.md` to recover state. The YAML frontmatter is parsed first to determine the exact resume point, followed by reading the markdown body for phase-specific content.
4. **Working file naming**: Use `finesse-plans/<name>-working.md` where `<name>` matches the eventual plan name. If the plan name is not yet determined, derive a session descriptor from the first 3-4 words of the task description in kebab-case (e.g., `finesse-plans/_working-fix-token-refresh.md`).
5. **Cleanup**: After plan acceptance and final file output, keep the working file for reference.

## Phase Code Reference

- **Feature**: F1 (Discovery), F2 (Codebase Exploration), F3 (Scope Analysis), F4 (Clarifying Questions), F5 (Architecture Design), F6 (Plan Construction), F7 (Validation), F8 (Presentation)
- **Bug Fix**: B1 (Bug Understanding), B2 (Codebase Investigation), B3 (Scope Analysis), B4 (Root Cause Analysis), B5 (Fix Strategy), B6 (Plan Construction), B7 (Validation + Presentation)
- **Refactor**: R1 (Scope Definition), R2 (Current State Analysis), R3 (Scope Analysis), R4 (Target State Design), R5 (Migration Strategy), R6 (Plan Construction), R7 (Validation + Presentation)
- **Testing**: T1 (Coverage Analysis), T2 (Scope Analysis), T3 (Test Strategy), T4 (Clarifying Questions), T5 (Plan Construction), T6 (Validation + Presentation)
- **Performance**: P1 (Problem Definition), P2 (Profiling & Analysis), P3 (Scope Analysis), P4 (Optimization Strategy), P5 (Plan Construction), P6 (Validation + Presentation)
- **Research**: RE1 (Goal Definition), RE2 (Source Identification), RE3 (Scope Analysis), RE4 (Research Plan & Questions), RE5 (Investigation Strategy), RE6 (Plan Construction), RE7 (Validation), RE8 (Presentation)

## Post-Compaction Rules (CRITICAL)

Identity-level post-compaction rules (planning-only, no code changes, no implementation agents, present-don't-implement) are in the **planner-identity** skill's Post-Compaction Identity Recovery section. Those apply automatically.

The following procedural rules are specific to recovery in the full `/finesse` workflow:

1. **STOP all work immediately.** Do NOT continue where you left off from memory. Your recall of prior phases is unreliable after compaction.
2. **Read the working file first.** Before doing ANYTHING else, read `finesse-plans/<name>-working.md` in full. This is your single source of truth.
3. **Verify plan mode.** After reading the working file, check the `mode` field in YAML frontmatter. If it says `planning-only`, you are in a Finesse session. If you are not in plan mode, call EnterPlanMode before doing anything else.
4. **NEVER act on stale context.** If the working file does not contain enough information to continue the current phase, tell the user what is missing and ask how to proceed. Do NOT guess or reconstruct from fragments.
5. **Re-orient before resuming.** After reading the working file, output a brief summary to the user: what phase you are in, what has been completed, and what the next step is. Wait for user confirmation before proceeding.
6. **No silent continuation.** You must ALWAYS surface to the user after compaction. Never silently pick up mid-phase and start producing output without first confirming recovered state with the user.
