---
description: "Resume an interrupted Finesse planning session from a working file"
argument-hint: "[PATH_TO_WORKING_FILE]"
allowed-tools: ["Task", "Read", "Glob", "Grep", "Bash(mkdir -p finesse-plans/*)", "Bash(mkdir -p finesse-plans/**/*)", "Write(finesse-plans/*)", "Write(finesse-plans/**/*)", "Bash(mkdir -p .finesse)", "Write(.finesse/*)", "Bash(git rev-parse HEAD)", "Bash(git diff --name-only *)", "Skill", "AskUserQuestion", "EnterPlanMode", "ExitPlanMode"]
hide-from-slash-command-tool: "true"
---

# Finesse Resume

## Critical Rules — READ BEFORE ANYTHING ELSE

All identity rules are defined in the **planner-identity** skill and injected by `identity_hook.py`. Those are non-negotiable and not repeated here. All workflow rules (task classification, UAT checkpoints, multi-workflow, context budget, discovery depth) are defined in `finesse.md` and apply equally to resumed sessions. The only resume-specific rules are:

- The final deliverable is ALWAYS the ralph-loop command using file references — NEVER output the raw prompt inline. After handling the user's acceptance option, STOP.
- Resumed sessions use the same orchestrator delegation pattern as `finesse.md` (exploration-orchestrator, scope-analyzer, architecture-designer, plan-constructor, plan-validator agents).

## Mandatory Workflow Checklist

Before calling ExitPlanMode, verify these final-phase gates were completed (in addition to all task-type-specific phases from the resume point):

1. ALL 6 validation agents launched in parallel
2. All CRITICAL and HIGH validation issues resolved
3. Pre-flight validation run (execution layer, git tracking, scoped files, verification commands)

If ANY step was skipped, STOP and return to the first skipped step.

---

## Argument Parsing

Parse `$ARGUMENTS`:

### No argument mode

If `$ARGUMENTS` is empty or blank:

1. Use `Glob` to scan `finesse-plans/` for `*-working.md` files.
2. If none found, say "No working files found in finesse-plans/." and stop.
3. If exactly one found, load it automatically.
4. If multiple found, read each file's YAML frontmatter to extract `task_type` and `current_phase`. List each working file with its task type and current phase, then use `AskUserQuestion` to let the user pick one.

### With path argument

If `$ARGUMENTS` contains a path:

1. Load the specified file directly.
2. If it doesn't exist or can't be read, tell the user "Working file not found at [path]. Please check the path and try again." and stop.

## Enter Plan Mode

Enter plan mode immediately after selecting the working file. All work happens in plan mode until the plan is presented.

## Working File Parsing

Read the selected working file in full. Parse the contents in two stages:

### Stage 1: YAML Frontmatter

Extract the following fields from the YAML frontmatter block at the top of the file:

- `task_type` — feature, bugfix, refactor, testing, performance, or research
- `workflow` — the workflow identifier (e.g., feature-development, bug-fix)
- `current_phase` — the phase code where the session was interrupted (e.g., F5, B3, RE4)
- `completed_phases` — list of phase codes that were completed before interruption
- `uat_fast_forward` — whether UAT was fast-forwarded (true/false)
- `session_name` — the kebab-case session descriptor
- `decomposed` — whether the task was decomposed into sub-workflows (true/false)
- `sub_workflows` — (if decomposed is true) list of sub-workflow objects with name, type, wave, current_phase, completed_phases

If the YAML frontmatter is missing or malformed (cannot parse the required fields), tell the user: "This working file is not in the enhanced format and cannot be resumed. Please start a new /finesse session instead." and stop.

### Stage 2: Markdown Body

Read the markdown body (everything after the YAML frontmatter closing `---`) for:

- Codebase findings (file paths, patterns, conventions)
- UAT checkpoint decisions and their outcomes
- Prompt draft (if one exists)
- Promise draft (if one exists)
- Open questions or blockers

## State Recovery Summary

Present a structured summary to the user:

**Recovered Session: [session_name]**

- **Task type**: [task_type]
- **Workflow**: [workflow name]
- **Completed phases**: [list each completed phase code with its name from the phase code reference]
- **Interrupted at**: [current_phase code] ([phase name])
- **Key decisions from UAT checkpoints**: [summarize decisions from the markdown body]
- **UAT fast-forward**: [enabled/disabled]
- **Decomposed**: [yes/no]
  - (If decomposed) **Sub-workflow status**:
    - [sub-workflow name]: [current_phase] — completed [completed_phases]
    - ...
- **Next phase**: [the phase to resume from — see Resume Point Determination]

## User Confirmation

Use `AskUserQuestion`: "Resume this planning session from [next phase name]?" with options:

1. **Yes — resume from [phase name]** — proceed with session recovery
2. **No — start fresh instead** — tell the user: "To start fresh, run /finesse with your task description." and stop.
3. **No — cancel** — say "Resume cancelled." and stop.

## Resume Point Determination

Rules for determining where to resume:

### Discovery phases (F1, B1, R1, P1, RE1)

If `current_phase` is a Discovery phase: **Restart Discovery from scratch.** The recovered working file notes serve as background context but Discovery requires fresh interactive dialogue. State this explicitly to the user: "Discovery phases require live back-and-forth and cannot be resumed mid-conversation. Restarting Discovery with your previous notes as context."

### Later phases

If `current_phase` is any phase after Discovery: **Resume from that phase.** The working file body contains the completed phase outputs that serve as input for this phase.

### Plan Construction or later (F6/B6/R6/T5/P5/RE6 or beyond)

If `current_phase` is a Plan Construction phase or later: **Resume plan construction** with any existing prompt draft from the working file. If a prompt draft exists in the markdown body, use it as the starting point for plan construction rather than building from scratch.

### UAT fast-forward

If `uat_fast_forward` is true: Note that UAT was previously fast-forwarded. Auto-accept remaining UAT checkpoints (but Discovery confirmations always happen, as per the rules).

## Workflow Continuation

After the user confirms:

State: "Continue following the [workflow name] workflow from Phase [code] ([phase name]). Apply all rules from the main finesse command."

### Phase sequences by workflow type

Reference the **task-workflows** skill for detailed phase-by-phase instructions. The full phase sequences are:

- **Feature (feature-development)**: F1 (Discovery) → F2 (Codebase Exploration) [UAT] → F3 (Scope Analysis) [UAT] → F4 (Clarifying Questions) → F5 (Architecture Design) [UAT] → F6 (Plan Construction) [UAT] → F7 (Validation) → Pre-flight → F8 (Presentation)
- **Bug Fix (bug-fix)**: B1 (Bug Understanding) → B2 (Codebase Investigation) [UAT] → B3 (Scope Analysis) [UAT] → B4 (Root Cause Analysis) [UAT] → B5 (Fix Strategy) [UAT] → B6 (Plan Construction) → B7 (Validation + Pre-flight + Presentation)
- **Refactor (refactor-chore)**: R1 (Scope Definition) → R2 (Current State Analysis) [UAT] → R3 (Scope Analysis) [UAT] → R4 (Target State Design) [UAT] → R5 (Migration Strategy) [UAT] → R6 (Plan Construction) → R7 (Validation + Pre-flight + Presentation)
- **Testing (testing)**: T1 (Coverage Analysis) [UAT] → T2 (Scope Analysis) [UAT] → T3 (Test Strategy) [UAT] → T4 (Clarifying Questions) → T5 (Plan Construction) → T6 (Validation + Pre-flight + Presentation)
- **Performance (performance-optimization)**: P1 (Problem Definition) → P2 (Profiling & Analysis) [UAT] → P3 (Scope Analysis) [UAT] → P4 (Optimization Strategy) [UAT] → P5 (Plan Construction) → P6 (Validation + Pre-flight + Presentation)
- **Research (research)**: RE1 (Goal Definition) → RE2 (Source Identification) [UAT] → RE3 (Scope Analysis) [UAT] → RE4 (Research Plan & Questions) [UAT] → RE5 (Investigation Strategy) [UAT] → RE6 (Plan Construction) → RE7 (Validation) → Pre-flight → RE8 (Presentation)

Follow the phase-by-phase instructions from the **task-workflows** skill for the recovered task type's workflow, starting from the determined resume phase.

### Exploration Cache

When resuming a session that will re-enter an exploration phase (F2, B2, R2, T1, P2, RE2), follow the Exploration Cache loading procedure from the main finesse command: check `.finesse/exploration-cache.json`, prune stale entries, and decide between cache-hit (lighter exploration) or cache-miss (full exploration) based on the staleness threshold.

After exploration completes, save findings to the cache following the Cache Saving procedure from the main finesse command.

Cache operations are best-effort — if the cache is missing or malformed, proceed with full exploration.

---

## Common Final Phases

From the resume phase onward, follow the same orchestrator delegation pattern as `finesse.md`. Specifically:

- **UAT Checkpoints**: Follow the **uat-procedure** skill at every `[UAT]` phase. For diff summaries, see the Diff Summary Format in the uat-procedure skill.
- **Exploration phases**: Delegate to the **exploration-orchestrator** agent via Task tool.
- **Scope Analysis phases**: Delegate to the **scope-analyzer** agent.
- **Architecture Design phases**: Delegate to the **architecture-designer** agent.
- **Plan Construction**: Prompt the user for Git Configuration and Subagent Configuration inline (mandatory, not skippable). Then delegate prompt assembly and context budget estimation to the **plan-constructor** agent. If critical pressure (>80%), handle re-route as defined in finesse.md.
- **Validation & Pre-flight**: Delegate to the **plan-validator** agent. All 6 validators run in parallel; verdicts are classified by severity tier (CRITICAL/HIGH/MEDIUM/LOW). CRITICAL and HIGH must be resolved before presenting.
- **Presentation**: Present via ExitPlanMode with all required fields (see finesse.md Presentation section).
- **User Decision**: Write plan files, present acceptance options (Execute now / Copy command / Save plan only), handle selection — all per finesse.md User Decision section.
- **Rejection**: Targeted edits, diff summary, re-validate via plan-validator, re-present. Per finesse.md rejection handling.

**STOP** after handling the user's acceptance option. Do NOT implement the plan.

---

## Context Compaction Handling

If context compaction occurs during a resumed session, before any recovery attempt update the working file's YAML frontmatter (`current_phase`, `completed_phases`) and write in-progress phase outputs to the markdown body.

Identity-level post-compaction rules (planning-only, no code changes, no implementation agents, present-don't-implement) are in the **planner-identity** skill's Post-Compaction Identity Recovery section. Those apply automatically.

The following procedural rules are specific to recovery in the `/finesse-resume` workflow:

1. **STOP all work immediately.** Your recall of prior phases is unreliable after compaction.
2. **Read the working file first.** Read `finesse-plans/<name>-working.md` in full. This is your single source of truth.
3. **Verify plan mode.** Check the `mode` field in YAML frontmatter. If `planning-only`, you are in a Finesse session. If not in plan mode, call EnterPlanMode before doing anything else.
4. **Re-orient with the user.** Output a summary of current phase, completed work, and next step. Wait for confirmation before proceeding.
