You are iterating on the Finesse plugin (plugins/finesse/). Before doing anything, read the following files to understand current state:
- plugins/finesse/commands/finesse.md
- plugins/finesse/commands/finesse-resume.md (may not exist yet — that's expected)
- plugins/finesse/commands/finesse-help.md
- plugins/finesse/commands/finesse-version.md
- plugins/finesse/.claude-plugin/plugin.json
- .claude-plugin/marketplace.json

Determine what has already been completed and what remains. For each phase below, run that phase's verification commands FIRST — if they all already pass, skip the phase entirely and move to the next one. This is critical for ralph-loop convergence: do not redo completed work.

## Requirements (in order)

Phase 1: Enhance working file format in finesse.md
  - In the "## Context Compaction Handling" section of plugins/finesse/commands/finesse.md, enhance the working file format with structured YAML frontmatter. Keep all existing content but restructure item 2 (Working file structure) to define a mandatory YAML frontmatter schema.
  - The enhanced item 2 must define the YAML frontmatter that ALL working files MUST include at the top of the file, before any markdown body content. The schema:
    ```yaml
    ---
    task_type: <feature|bugfix|refactor|testing|performance|research>
    workflow: <feature-development|bug-fix|refactor-chore|testing|performance-optimization|research>
    current_phase: <phase code, e.g., F5, B3, RE4>
    completed_phases: [<list of completed phase codes, e.g., F1, F2, F3, F4>]
    uat_fast_forward: <true|false>
    session_name: <kebab-case session descriptor>
    decomposed: <true|false>
    sub_workflows:  # only present if decomposed: true
      - name: <sub-workflow kebab-case name>
        type: <task type>
        wave: <wave number>
        current_phase: <phase code>
        completed_phases: [<completed phase codes>]
    ---
    ```
  - Below the YAML frontmatter, the working file body remains free-form markdown containing: codebase findings, UAT checkpoint decisions and their outcomes, prompt draft (if one exists), promise draft (if one exists), open questions or blockers. This body content is unchanged from the current spec.
  - Add a new item titled "6. **Phase code reference**:" (after the existing items but before "### Post-Compaction Rules") defining the phase code reference for all 6 workflows:
    - Feature: F1 (Discovery), F2 (Codebase Exploration), F3 (Scope Analysis), F4 (Clarifying Questions), F5 (Architecture Design), F6 (Plan Construction), F7 (Validation), F8 (Presentation)
    - Bug Fix: B1 (Bug Understanding), B2 (Codebase Investigation), B3 (Scope Analysis), B4 (Root Cause Analysis), B5 (Fix Strategy), B6 (Plan Construction), B7 (Validation + Presentation)
    - Refactor: R1 (Scope Definition), R2 (Current State Analysis), R3 (Scope Analysis), R4 (Target State Design), R5 (Migration Strategy), R6 (Plan Construction), R7 (Validation + Presentation)
    - Testing: T1 (Coverage Analysis), T2 (Scope Analysis), T3 (Test Strategy), T4 (Clarifying Questions), T5 (Plan Construction), T6 (Validation + Presentation)
    - Performance: P1 (Problem Definition), P2 (Profiling & Analysis), P3 (Scope Analysis), P4 (Optimization Strategy), P5 (Plan Construction), P6 (Validation + Presentation)
    - Research: RE1 (Goal Definition), RE2 (Source Identification), RE3 (Scope Analysis), RE4 (Research Plan & Questions), RE5 (Investigation Strategy), RE6 (Plan Construction), RE7 (Validation), RE8 (Presentation)
  - Update item 1 (Early persistence) to mention that the YAML frontmatter must be included from the first write and updated at each phase boundary.
  - Update item 3 (Recovery) to state that the YAML frontmatter is parsed first to determine the exact resume point, followed by reading the markdown body for phase-specific content.
  - Keep items 4 (Working file naming) and 5 (Cleanup) intact.
  - Keep the "### Post-Compaction Rules" subsection completely intact — do NOT remove or modify it.
  Verify: grep "task_type:" plugins/finesse/commands/finesse.md matches
  Verify: grep "current_phase:" plugins/finesse/commands/finesse.md matches
  Verify: grep "completed_phases:" plugins/finesse/commands/finesse.md matches
  Verify: grep "uat_fast_forward:" plugins/finesse/commands/finesse.md matches
  Verify: grep "Post-Compaction Rules" plugins/finesse/commands/finesse.md matches (confirming it was NOT removed)
  Verify: grep "Phase code reference" plugins/finesse/commands/finesse.md matches OR grep "phase code" plugins/finesse/commands/finesse.md matches (confirming mapping was added)

Phase 2: Create finesse-resume.md command
  - Create a new file at plugins/finesse/commands/finesse-resume.md using the Write tool.
  - The file must have YAML frontmatter with these exact fields:
    ```yaml
    ---
    description: "Resume an interrupted Finesse planning session from a working file"
    argument-hint: "[PATH_TO_WORKING_FILE]"
    allowed-tools: ["Task", "Read", "Glob", "Grep", "Bash(mkdir -p ralph-plans/*)", "Bash(mkdir -p ralph-plans/**/*)", "Write(ralph-plans/*)", "Write(ralph-plans/**/*)", "AskUserQuestion", "EnterPlanMode", "ExitPlanMode"]
    hide-from-slash-command-tool: "true"
    ---
    ```
  - The command body must contain ALL of the following sections. Read plugins/finesse/commands/finesse.md to get the exact text for sections that must be inlined. Each section below is mandatory:
    a) **Title and purpose**: "# Finesse Resume" heading followed by a statement that this command resumes interrupted Finesse planning sessions from working files. State that this is a PLANNING-ONLY command — it NEVER implements or executes code changes.
    b) **Argument Parsing** section:
       - No argument mode: Use Glob to scan `ralph-plans/` for `*-working.md` files. If none found, say "No working files found in ralph-plans/." and stop. If exactly one found, load it automatically. If multiple found, list each with its task_type and current_phase extracted from YAML frontmatter, and use AskUserQuestion to let the user pick one.
       - With path argument: Load the specified file directly. If it doesn't exist or can't be read, tell the user and stop.
    c) **Enter Plan Mode**: Enter plan mode immediately after selecting the working file.
    d) **Working File Parsing** section: Read the selected working file. Parse the YAML frontmatter to extract: task_type, workflow, current_phase, completed_phases, uat_fast_forward, session_name, decomposed, sub_workflows (if applicable). Then read the markdown body for: codebase findings, UAT checkpoint decisions, prompt draft, promise draft, open questions/blockers. If the YAML frontmatter is missing or malformed, tell the user the working file is not in the enhanced format and cannot be resumed — suggest they start a new /finesse session instead.
    e) **State Recovery Summary** section: Present a structured summary to the user containing:
       - Task type and session name
       - Workflow type
       - Completed phases (list with names from the phase code reference)
       - Current/interrupted phase
       - Key decisions made at UAT checkpoints (from markdown body)
       - UAT fast-forward status
       - If decomposed: sub-workflow status summary (which sub-workflows are complete, in progress, or pending)
       - What the next phase will be
    f) **User Confirmation** section: Use AskUserQuestion: "Resume this planning session from [next phase name]?" with options:
       - "Yes — resume from [phase]"
       - "No — start fresh instead" (tell user to run /finesse with their task description)
       - "No — cancel" (stop, say "Resume cancelled.")
    g) **Resume Point Determination** section: Rules for determining where to resume:
       - If current_phase is a Discovery phase (F1, B1, R1, P1, RE1): Restart Discovery from scratch. The recovered working file notes serve as background context but Discovery requires fresh interactive dialogue. State this explicitly to the user: "Discovery phases require live back-and-forth and cannot be resumed mid-conversation. Restarting Discovery with your previous notes as context."
       - If current_phase is any later phase: Resume from that phase. The working file body contains the completed phase outputs that serve as input.
       - If current_phase is a Plan Construction phase or later (F6/B6/R6/T5/P5/RE6 or beyond): Resume plan construction with any existing prompt draft from the working file.
       - If uat_fast_forward is true: Note that UAT was previously fast-forwarded; auto-accept remaining UAT checkpoints (but Discovery confirmations always happen, as per finesse.md rules).
    h) **Workflow Continuation** section: After the user confirms:
       - State: "Continue following the [workflow name] workflow from Phase [code] ([phase name]). Apply all rules from the main finesse command."
       - List the full phase sequence for the recovered workflow type (from the task-workflows skill) so the agent knows what phases remain.
       - Reference the task-workflows skill: "Follow the phase-by-phase instructions from the task-workflows skill for the [task_type] workflow, starting from Phase [N]."
    i) **UAT Checkpoint Procedure** (inline copy from finesse.md): Copy the complete UAT Checkpoint Procedure section from finesse.md. This includes: the 3-step procedure (present, ask with 4 options, handle response), the UAT-replaces-inline-confirmations rule, and the Discovery exception.
    j) **Common Final Phases** (inline copy from finesse.md): Copy these subsections from finesse.md's "## Common Final Phases" section:
       - "### Plan Construction" — including the **Git Configuration** pre-step, the **Subagent Configuration** pre-step, and the 7-item prompt construction checklist with iteration count guidance
       - "### Git Configuration Prompt" — the full mandatory git configuration question flow
       - "### Subagent Configuration Prompt" — the full mandatory subagent analysis and question flow
       - "### Multi-Workflow Plan Construction" — all numbered items including git and subagent configuration
       - "### Validation" — the 5 validator agents, verdict vocabulary, handling rules
       - "### Presentation" — ExitPlanMode with required content
       - "### User Decision" — both single-workflow and multi-workflow accepted/rejected flows
    k) **Critical Rules** (inline from finesse.md): Copy all critical rules from finesse.md. These include: NEVER IMPLEMENT, always plan mode, always classify task type, always explore before designing, UAT checkpoint rules, three-file output structure, multi-workflow format rules, etc.
    l) **Context Compaction Handling**: State that if context compaction occurs during a resumed session, follow the same working file update and Post-Compaction Rules defined in finesse.md. Update the working file's YAML frontmatter with the current phase before any recovery attempt.
  Verify: test -f plugins/finesse/commands/finesse-resume.md (file exists)
  Verify: grep "allowed-tools" plugins/finesse/commands/finesse-resume.md matches
  Verify: grep "working.md" plugins/finesse/commands/finesse-resume.md matches (scanning logic)
  Verify: grep "task-workflows" plugins/finesse/commands/finesse-resume.md matches (skill reference)
  Verify: grep "Plan Construction" plugins/finesse/commands/finesse-resume.md matches (Common Final Phases inlined)
  Verify: grep "Discovery" plugins/finesse/commands/finesse-resume.md matches (restart logic)
  Verify: grep "AskUserQuestion" plugins/finesse/commands/finesse-resume.md matches (user interaction)
  Verify: grep "UAT Checkpoint" plugins/finesse/commands/finesse-resume.md matches (procedure inlined)
  Verify: grep "NEVER IMPLEMENT" plugins/finesse/commands/finesse-resume.md matches (critical rules)
  Verify: grep "Git Configuration" plugins/finesse/commands/finesse-resume.md matches (git config inlined)
  Verify: grep "Subagent Configuration" plugins/finesse/commands/finesse-resume.md matches (subagent config inlined)

Phase 3: Update finesse-help.md
  - In the "## Available Commands" section, add a new subsection after the existing "/cancel-finesse" entry (around line 49) and before "## What Happens" (around line 51). The new subsection:
    ```
    ### /finesse-resume [PATH]

    Resume an interrupted Finesse planning session from a working file.

    **Arguments:**
    - No arguments — scans `ralph-plans/` for working files, lists if multiple
    - `PATH` — path to a specific working file to resume from

    **Usage:**
    ```
    /finesse-resume
    /finesse-resume ralph-plans/build-rest-api-working.md
    ```
    ```
  - After the "## Plan Rejection" section (around line 128) and before "## When to Use Finesse" (around line 130), add a new "## Resuming Sessions" section:
    ```
    ## Resuming Sessions

    Finesse saves progress to working files during long planning sessions. If a session is interrupted (context compaction, crash, new session), use `/finesse-resume` to continue:

    - The resume command recovers task type, completed phases, user decisions, and prompt drafts
    - Discovery phases are restarted from scratch (they require live interaction)
    - Later phases resume from where they left off
    - All UAT checkpoint decisions are preserved
    - Works with both single-workflow and multi-workflow (decomposed) sessions
    ```
  Verify: grep "finesse-resume" plugins/finesse/commands/finesse-help.md matches
  Verify: grep "Resuming Sessions" plugins/finesse/commands/finesse-help.md matches

Phase 4: Version bump to v0.5.0
  - In plugins/finesse/.claude-plugin/plugin.json, change "version": "0.4.0" to "version": "0.5.0"
  - In .claude-plugin/marketplace.json (at repo root, NOT under plugins/), change "0.4.0" to "0.5.0" in the finesse plugin entry
  - In plugins/finesse/commands/finesse-version.md, change "Finesse v0.4.0" to "Finesse v0.5.0"
  Verify: grep '"0.5.0"' plugins/finesse/.claude-plugin/plugin.json matches
  Verify: grep '"0.5.0"' .claude-plugin/marketplace.json matches
  Verify: grep "v0.5.0" plugins/finesse/commands/finesse-version.md matches

## Rules
- ONLY modify/create these 6 files:
  - plugins/finesse/commands/finesse.md (MODIFY)
  - plugins/finesse/commands/finesse-resume.md (CREATE — new file)
  - plugins/finesse/commands/finesse-help.md (MODIFY)
  - plugins/finesse/commands/finesse-version.md (MODIFY)
  - plugins/finesse/.claude-plugin/plugin.json (MODIFY)
  - .claude-plugin/marketplace.json (at repo root) (MODIFY)
- Do NOT modify any other files in the codebase.
- For existing files, do NOT rewrite from scratch. Make targeted edits using the Edit tool.
- For the new finesse-resume.md file, use Write tool for initial creation. For subsequent fixes, use Edit for targeted changes.
- Do NOT add unnecessary abstractions or extra files.
- Do NOT make git commits.
- Do NOT push to remote repositories.
- Read the actual file content before making edits. Understand the existing structure.
- Preserve existing formatting, markdown style, and indentation in all files.
- The YAML frontmatter schema in finesse.md must define ALL fields: task_type, workflow, current_phase, completed_phases, uat_fast_forward, session_name, decomposed, sub_workflows.
- The finesse-resume.md command must be SELF-CONTAINED. It cannot depend on reading finesse.md at runtime for its behavior. All Common Final Phases, UAT Checkpoint Procedure, Critical Rules, and workflow continuation logic must be included directly in the file.
- The finesse-resume.md allowed-tools list must EXACTLY match finesse.md's allowed-tools list.
- When creating finesse-resume.md, read finesse.md first to copy the exact text of: Common Final Phases (Plan Construction through User Decision), UAT Checkpoint Procedure, and Critical Rules. Do not paraphrase — copy the authoritative text.
- Discovery phases (F1, B1, R1, P1, RE1) must be restarted from scratch when resumed. They CANNOT be "continued" since they require interactive back-and-forth.
- The phase code mapping must cover ALL 6 workflow types with ALL phases.
- The Post-Compaction Rules subsection in finesse.md must remain completely intact after Phase 1 edits.
- When adding sections to finesse-help.md, preserve the existing section ordering and markdown style.
- If a grep verification fails, run grep -n to inspect the file context around the expected match before re-editing. Diagnose the root cause first, then fix. Do NOT blindly retry the same edit.
- If an Edit tool call fails (e.g., old_string not found), read the file to find the actual current text, then retry with the correct old_string. Do NOT guess or retry without reading.
- For each phase, check if the verification commands already pass before starting that phase's work. If all verifications for a phase already pass, skip that phase entirely and move to the next one.
- If stuck on the same error for 3+ attempts, try an alternative approach.
- If unable to make progress after 5 iterations, document blockers and output <promise>BLOCKED</promise>.
- Do NOT output the completion promise prematurely. Run ALL verification commands first and confirm every single one passes. If any verification fails, fix the issue before re-checking.

## Completion
When ALL phases are complete and ALL verification commands pass cleanly,
output <promise>FINESSE_V050_RESUME_COMPLETE</promise>. This must be unequivocally true.

Do not output the completion promise unless EVERY criterion below is met:
1. plugins/finesse/commands/finesse.md Context Compaction Handling section contains the YAML frontmatter schema with ALL fields (task_type, workflow, current_phase, completed_phases, uat_fast_forward, session_name, decomposed, sub_workflows) and the phase code reference for all 6 workflows (Feature F1-F8, Bug Fix B1-B7, Refactor R1-R7, Testing T1-T6, Performance P1-P6, Research RE1-RE8).
2. plugins/finesse/commands/finesse.md Post-Compaction Rules subsection is intact — verify with: grep "Post-Compaction Rules" plugins/finesse/commands/finesse.md returns a match.
3. plugins/finesse/commands/finesse-resume.md exists with correct YAML frontmatter (description, argument-hint, allowed-tools matching finesse.md exactly, hide-from-slash-command-tool).
4. finesse-resume.md contains ALL required sections: argument parsing (no-arg scan + path-arg), plan mode entry, working file parsing (YAML frontmatter + markdown body), state recovery summary, user confirmation (AskUserQuestion with 3 options), resume point determination (Discovery restart rule + later-phase continuation), workflow continuation (task-workflows reference + full phase sequence), inline UAT Checkpoint Procedure, inline Common Final Phases (Plan Construction + Git Config + Subagent Config + Multi-Workflow + Validation + Presentation + User Decision), inline Critical Rules, Context Compaction Handling reference.
5. finesse-resume.md references the task-workflows skill for workflow phase definitions.
6. plugins/finesse/commands/finesse-help.md documents /finesse-resume in Available Commands (with a fenced code block showing usage) AND has a "Resuming Sessions" section.
7. Version is "0.5.0" in plugin.json, marketplace.json, and finesse-version.md.
8. All verification commands from all 4 phases pass cleanly.

Before outputting the promise, run ALL verification commands from all 4 phases in sequence and confirm every single one passes. Do not output the promise if any verification fails.
