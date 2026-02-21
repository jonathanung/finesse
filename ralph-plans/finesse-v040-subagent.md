You are iterating on the Finesse plugin (plugins/finesse/). Before doing anything, read the following files to understand current state:
- plugins/finesse/skills/meta-prompting/SKILL.md
- plugins/finesse/commands/finesse.md
- plugins/finesse/skills/task-workflows/SKILL.md
- plugins/finesse/commands/finesse-help.md
- plugins/finesse/commands/finesse-version.md
- plugins/finesse/.claude-plugin/plugin.json
- .claude-plugin/marketplace.json

Determine what has already been completed and what remains. For each phase below, check if the verification commands already pass before starting that phase's work.

## Requirements (in order)

Phase 1: Add Subagent Configuration section to meta-prompting/SKILL.md
  - Insert a new "## Subagent Configuration" section AFTER the "## Git Configuration Rules" section (which ends at the last "Custom:" subsection with push rules, around line 159) and BEFORE the "## Multi-Workflow Output Format" section (around line 161) in plugins/finesse/skills/meta-prompting/SKILL.md.
  - The section must contain these subsections in order:
    a) Opening paragraph with this exact text: "During Plan Construction, the user is optionally offered subagent instructions for phases where parallel execution would improve efficiency. Based on the user's choice, include or omit the following sections in the generated prompt."
    b) "### Subagent Eligibility Heuristics" subsection defining three numbered heuristics:
       1. Independent subtasks: phase contains work on separate file sets with no shared writes. Recommended subagent type: `general-purpose`.
       2. Parallel verification: phase's verification commands can run alongside next phase's work without gating it. Recommended subagent type: `Bash`.
       3. Exploration benefit: phase touches unfamiliar code that benefits from dedicated investigation. Recommended subagent type: `Explore`.
       Conclude with: "A phase is subagent-eligible if it matches at least one heuristic."
    c) "### Subagent Section Format" subsection containing a fenced code block showing the EXACT content to include in generated prompts when opted in. The code block must contain:
       - A "## Subagent Instructions" heading
       - Opening line: "You may use the Task tool to spawn subagents for parallel work. Follow these guidelines:"
       - "### Available Subagent Types" with three bullet entries: Bash (test suites, linting, verification in parallel), Explore (investigating unfamiliar code, researching patterns, tracing flows), general-purpose (file modifications on independent non-overlapping file sets)
       - "### Guardrails" with six bullet rules: max 2 concurrent subagents, no git commits/push from subagents, no modifications outside assigned scope, wait for all results before marking phase complete, retry once on failure then do it yourself, provide clear scoped instructions
    d) "### Per-Phase Annotation Format" subsection defining the annotation format and showing a concrete example. The annotation goes on a new line after a phase's Verify: line, indented to match the phase content. Format:
       [Subagent opportunity]: <description of what to parallelize>, using <subagent_type> subagent. <why it's safe>.
       Example (show this as a code block):
       Phase 2: Implement authentication endpoint
         - Add JWT validation middleware to src/middleware/auth.ts
         - Create /api/auth route handler in src/routes/auth.ts
         Verify: npm test -- --grep "auth"
         [Subagent opportunity]: Spawn a Bash subagent to run the full test suite while beginning Phase 3. Phase 3 modifies different files (src/routes/users.ts) so there is no write conflict.
    e) "### No Subagent Instructions Selected" subsection stating: "If the user declines subagent instructions, omit the `## Subagent Instructions` section and all `[Subagent opportunity]` annotations entirely. The prompt is generated without any subagent content."
  - Update the template code block (around lines 57-90) to add two conditional placeholders:
    - AFTER the cold start paragraph ("...identify what's done vs remaining.") and BEFORE the "## Requirements (in order)" line, add a blank line then this exact text:
      [If subagent instructions opted in: include ## Subagent Instructions section here. See Subagent Configuration section.]
    - Inside the Phase template entries, AFTER each "Verify: [exact command to run]" line, add this exact text on the next line with matching indentation:
      [If subagent eligible: include [Subagent opportunity] annotation here. See Subagent Configuration section.]
  Verify: grep -c "Subagent Configuration" plugins/finesse/skills/meta-prompting/SKILL.md returns at least 1
  Verify: grep "Subagent Eligibility Heuristics" plugins/finesse/skills/meta-prompting/SKILL.md matches
  Verify: grep "Subagent Section Format" plugins/finesse/skills/meta-prompting/SKILL.md matches
  Verify: grep "Subagent opportunity" plugins/finesse/skills/meta-prompting/SKILL.md matches
  Verify: grep "No Subagent Instructions Selected" plugins/finesse/skills/meta-prompting/SKILL.md matches
  Verify: grep "subagent instructions opted in" plugins/finesse/skills/meta-prompting/SKILL.md matches

Phase 2: Add Subagent Configuration Prompt to finesse.md
  - In "## Common Final Phases (all task types)" > "### Plan Construction" section, add a new line after the existing "**Git Configuration**:" line (around line 130-131) and before the "Build a complete ralph-loop prompt" paragraph (around line 132):
    "**Subagent Configuration**: After the git configuration prompt, analyze phases for subagent eligibility and ask the user whether to include subagent instructions (see Subagent Configuration Prompt below). The answer determines whether subagent sections are included in the prompt."
  - Add a new "### Subagent Configuration Prompt" subsection AFTER "### Git Configuration Prompt" (which ends around line 163) and BEFORE "### Multi-Workflow Plan Construction" (around line 165). This subsection must contain:
    - A statement: "After the Git Configuration prompt and before assembling the final prompt, analyze the designed phases for subagent eligibility. This analysis is mandatory, but inclusion of subagent instructions is user-gated. This prompt is NOT affected by UAT fast-forward — it must always appear."
    - **Analysis step**: "For each phase of the designed architecture, evaluate against the three subagent eligibility heuristics defined in the meta-prompting skill's Subagent Configuration section:" followed by listing all three: (1) Independent subtasks — separate file sets with no shared writes, (2) Parallel verification — verification can run alongside next phase, (3) Exploration benefit — unfamiliar code benefits from dedicated investigation.
    - **Presentation**: "Present the analysis results as context for the question. For each eligible phase, state: the phase name, which heuristic(s) it matched, and what a subagent would do (concrete action and recommended subagent_type). If no phases are subagent-eligible, skip the question and proceed without subagent instructions."
    - **Question**: "Use `AskUserQuestion`: 'Would you like subagent instructions included in the ralph-loop prompt?' with options 'Yes' / 'No'."
    - **If Yes**: "Include a `## Subagent Instructions` section in the prompt after the cold start paragraph and before `## Requirements`, using the exact format from the Subagent Section Format in the meta-prompting skill. Include `[Subagent opportunity]` annotations for each eligible phase, after its `Verify:` line, using the Per-Phase Annotation Format from the meta-prompting skill. The subagent guardrails are fixed — they do not vary based on git configuration."
    - **If No**: "Generate the prompt without any subagent instructions or annotations (unchanged behavior)."
    - **Multi-Workflow note**: "In Multi-Workflow mode, subagent analysis is performed per sub-workflow prompt. The question is asked once and the answer applies to all sub-workflow prompts."
  - In "### Multi-Workflow Plan Construction" (around line 165-173), add a new numbered item after the existing items:
    "6. **Subagent configuration**: The subagent analysis is performed per sub-workflow prompt. The user's choice from the Subagent Configuration Prompt applies uniformly to ALL sub-workflow prompts. Do NOT re-prompt for each sub-workflow."
  Verify: grep -c "Subagent Configuration" plugins/finesse/commands/finesse.md returns at least 3
  Verify: grep "subagent eligibility" plugins/finesse/commands/finesse.md matches
  Verify: grep "Subagent Configuration Prompt" plugins/finesse/commands/finesse.md matches

Phase 3: Update task-workflows/SKILL.md Plan Construction phases
  - For each of the 6 workflows, locate the Plan Construction phase and add the following note. The note text is IDENTICAL for all 6 workflows — do not customize per workflow type. Insert the note after the existing plan construction content (after the bullet list or description of what the prompt should include) but BEFORE the iteration count guidance ("Ralph-loop iterations:" or "Determine ralph-loop `--max-iterations`").
  - The exact note text to insert (as a bold-labeled paragraph):

    **Subagent analysis**: After git configuration, analyze the designed phases for subagent eligibility using the heuristics from the meta-prompting skill. If eligible phases exist, ask the user whether to include subagent instructions via the Subagent Configuration Prompt in finesse.md.

  - The 6 insert locations (find each by searching for the workflow's Plan Construction heading):
    1. Feature Phase 6: Plan Construction [UAT] — insert after the "- Completion criteria derived from the requirements" bullet and before "Determine ralph-loop `--max-iterations` with reasoning:"
    2. Bug Fix Phase 6: Plan Construction — insert after the "- Guardrails:" bullets and before "Ralph-loop iterations:"
    3. Refactor Phase 6: Plan Construction — insert after "- Completion: all tests pass, no references to old pattern remain" and before "Ralph-loop iterations:"
    4. Testing Phase 5: Plan Construction — insert after the "- Guardrails:" bullets and before "Ralph-loop iterations:"
    5. Performance Phase 5: Plan Construction — insert after "- Completion: benchmark meets target threshold" and before "Ralph-loop iterations:"
    6. Research Phase 6: Plan Construction — insert after the completion criteria bullets and before "Ralph-loop iterations:"
  Verify: grep -c "Subagent analysis" plugins/finesse/skills/task-workflows/SKILL.md returns exactly 6
  Verify: If count is not 6, run grep -n "Subagent analysis" to identify which workflows have the note and which are missing.

Phase 4: Update finesse-help.md
  - In the "What Happens" numbered list (around line 62), update step 6 from:
    "**Plan construction** — Builds a structured ralph-loop prompt with cold start, phases, verification commands, guardrails"
    to:
    "**Plan construction** — Builds a structured ralph-loop prompt with cold start, phases, verification commands, guardrails. Optionally includes subagent spawning instructions for parallel execution."
  Verify: grep "subagent" plugins/finesse/commands/finesse-help.md matches

Phase 5: Version bump to v0.4.0
  - In plugins/finesse/.claude-plugin/plugin.json, change "version": "0.3.1" to "version": "0.4.0"
  - In .claude-plugin/marketplace.json (at repo root, NOT under plugins/), change "0.3.1" to "0.4.0" in the finesse plugin entry
  - In plugins/finesse/commands/finesse-version.md, change "Finesse v0.3.1" to "Finesse v0.4.0"
  Verify: grep '"0.4.0"' plugins/finesse/.claude-plugin/plugin.json matches
  Verify: grep '"0.4.0"' .claude-plugin/marketplace.json matches
  Verify: grep "v0.4.0" plugins/finesse/commands/finesse-version.md matches

## Rules
- ONLY modify these 7 files:
  - plugins/finesse/skills/meta-prompting/SKILL.md
  - plugins/finesse/commands/finesse.md
  - plugins/finesse/skills/task-workflows/SKILL.md
  - plugins/finesse/commands/finesse-help.md
  - plugins/finesse/commands/finesse-version.md
  - plugins/finesse/.claude-plugin/plugin.json
  - .claude-plugin/marketplace.json (at repo root)
- Do NOT modify any other files in the codebase.
- Do NOT rewrite files from scratch. Make targeted edits using the Edit tool.
- Do NOT add unnecessary abstractions or extra files.
- Do NOT make git commits.
- Do NOT push to remote repositories.
- Read the actual file content before making edits. Understand the existing structure.
- Preserve existing formatting, markdown style, and indentation in all files.
- The Subagent Configuration section in meta-prompting/SKILL.md must define: 3 heuristics with concrete subagent_types, the Subagent Instructions section format as a code block (with Available Subagent Types and Guardrails subsections), per-phase annotation format with a concrete example, and the no-subagent case.
- The Subagent Configuration Prompt in finesse.md must follow the same structural pattern as Git Configuration Prompt: analysis step, presentation, AskUserQuestion, conditional injection.
- All 6 workflows in task-workflows/SKILL.md must get the IDENTICAL subagent analysis note in their Plan Construction phase.
- When editing meta-prompting/SKILL.md template, add conditional placeholders using the existing [placeholder] convention (matching the style of "[Git rules — ...]" and "[test command]").
- The Subagent Instructions section in generated prompts goes BETWEEN the cold start paragraph and ## Requirements — NOT in ## Rules.
- Per-phase [Subagent opportunity] annotations go AFTER the Verify: line of each eligible phase.
- When inserting new sections in meta-prompting/SKILL.md, verify the insertion is OUTSIDE any existing code block by reading 10 lines before the insertion point. If you see unclosed triple backticks, insert after the code block closes.
- If a grep count verification fails, run grep -n to inspect individual matches before re-editing. Determine whether the count is too low (content missing) or too high (duplicate/false positive). Diagnose first, then fix.
- For Phase 3: if grep -c returns fewer than 6, identify which specific workflow(s) are missing the note by searching for each workflow's Plan Construction heading individually.
- If stuck on the same error for 3+ attempts, try an alternative approach.
- If unable to make progress after 5 iterations, document blockers and output <promise>BLOCKED</promise>.

## Completion
When ALL phases are complete and ALL verification commands pass cleanly,
output <promise>FINESSE_V040_SUBAGENT_COMPLETE</promise>. This must be unequivocally true.

Do not output the completion promise unless EVERY criterion below is met:
1. plugins/finesse/skills/meta-prompting/SKILL.md contains "## Subagent Configuration" section with all 5 subsections: opening paragraph, Subagent Eligibility Heuristics (3 heuristics with subagent_types), Subagent Section Format (code block with Available Subagent Types and Guardrails), Per-Phase Annotation Format (with concrete example), No Subagent Instructions Selected.
2. plugins/finesse/skills/meta-prompting/SKILL.md template (the code block starting with "You are iterating on [PROJECT]") has been updated with two conditional placeholders: one for the Subagent Instructions section (between cold start and Requirements), one for per-phase annotations (after Verify line). Verify: grep "subagent instructions opted in" returns a match within the template.
3. plugins/finesse/commands/finesse.md contains "### Subagent Configuration Prompt" subsection with: analysis step (3 heuristics listed), presentation format, AskUserQuestion with Yes/No, conditional injection rules (yes/no paths), multi-workflow note.
4. plugins/finesse/commands/finesse.md Plan Construction has "**Subagent Configuration**" pre-step line alongside the existing "**Git Configuration**" pre-step.
5. plugins/finesse/commands/finesse.md Multi-Workflow Plan Construction includes subagent configuration numbered item.
6. plugins/finesse/skills/task-workflows/SKILL.md has "**Subagent analysis**:" note in ALL 6 workflows' Plan Construction phases. Verify: grep -c "Subagent analysis" returns exactly 6.
7. plugins/finesse/commands/finesse-help.md mentions "subagent" in the Plan construction step.
8. Version is "0.4.0" in plugin.json, marketplace.json, and finesse-version.md.
9. All verification commands from all 5 phases pass cleanly.

Before outputting the promise, run ALL verification commands from all 5 phases in sequence and confirm every single one passes. Do not output the promise if any verification fails.
