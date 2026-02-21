You are iterating on the Finesse plugin (plugins/finesse/). Before doing anything, read the following files to understand current state:
- plugins/finesse/commands/finesse.md
- plugins/finesse/skills/meta-prompting/SKILL.md
- plugins/finesse/.claude-plugin/plugin.json
- plugins/finesse/commands/finesse-version.md

Determine what has already been completed and what remains.

## Requirements (in order)

Phase 1: Add Git Configuration Prompt section to finesse.md
  - In the "Common Final Phases" > "Plan Construction" section, add a pre-step before the 7-item numbered list that reads:
    "**Git Configuration**: Before assembling the prompt, prompt the user about git usage (see Git Configuration Prompt below). The answers determine which git rules are included in the prompt's Rules section."
  - Add a new "### Git Configuration Prompt" subsection after the Plan Construction numbered list but before "### Multi-Workflow Plan Construction". This subsection must contain:
    - A statement that this prompt is mandatory and NOT affected by UAT fast-forward.
    - Instruction to use AskUserQuestion for all git configuration questions.
    - Question 1: "Should the ralph-loop agent use git to checkpoint progress?" with options "Yes" / "No".
    - If the user answers Yes, ask Questions 2 and 3 together in a single AskUserQuestion call:
      - Question 2: "What commit granularity should the agent use?" with options "After each phase" / "After each change" / "Custom" (user provides free text via Other).
      - Question 3: "Should the agent push commits to the remote?" with options "Yes" / "No".
    - A direction to include appropriate git rules per the Git Configuration Rules section in the meta-prompting skill.
    - A note that in Multi-Workflow mode, git configuration is asked once and applied uniformly to all sub-workflow prompts.
  - In the "### Multi-Workflow Plan Construction" subsection, add a new numbered item: "**Git configuration**: The git rules from the Git Configuration Prompt apply uniformly to ALL sub-workflow prompts. Do NOT re-prompt for each sub-workflow."
  Verify: grep -c "Git Configuration" plugins/finesse/commands/finesse.md returns at least 3

Phase 2: Update meta-prompting/SKILL.md template and add Git Configuration Rules section
  - In the template's ## Rules section (around line 76), replace the hardcoded line "- Do NOT push to remote repositories." with:
    "- [Git rules — include checkpoint and push rules based on user's git configuration. See Git Configuration Rules section.]"
  - In Mandatory Attribute #6 "Guardrails Against Failure Modes" (around lines 34-39), add a note after the existing bullet list stating that git commit/push rules are user-configured during Plan Construction rather than hardcoded. For example, add: "Note: Git commit and push rules are configured per-plan during Plan Construction — see Git Configuration Rules section below." Do NOT search for existing push-related text to replace in this section — there is none. Add new text instead.
  - Add a new "## Git Configuration Rules" section AFTER the "## File Output Format" section and BEFORE the "## Multi-Workflow Output Format" section. This section must define the exact rules to inject for each user choice combination:

    **No checkpointing selected:**
    - "Do NOT make git commits."
    - "Do NOT push to remote repositories."

    **Checkpointing enabled, no push:**
    The checkpoint rule varies by granularity:
    - After each phase: "After completing each phase and verifying it passes, create a git commit with a descriptive message referencing the completed phase."
    - After each change: "After each logical unit of work, create a git commit with a descriptive message describing the change."
    - Custom: Use the user's verbatim description as the checkpoint rule.
    Plus: "Do NOT push to remote repositories."

    **Checkpointing enabled + push:**
    The checkpoint rule (same granularity variants as above) plus:
    "Push commits to the remote repository after committing."

  Verify: grep -c "Git Configuration Rules" plugins/finesse/skills/meta-prompting/SKILL.md returns at least 1
  Verify: grep "Do NOT push to remote repositories" in the template's ## Rules code block should no longer match (the placeholder text should appear instead). The phrase will still appear in the new Git Configuration Rules section as a conditional option.

Phase 3: Version bump to v0.3.1
  - In plugins/finesse/.claude-plugin/plugin.json, change "version": "0.3.0" to "version": "0.3.1"
  - In plugins/finesse/commands/finesse-version.md, change "Finesse v0.3.0" to "Finesse v0.3.1"
  Verify: grep "0.3.1" plugins/finesse/.claude-plugin/plugin.json
  Verify: grep "v0.3.1" plugins/finesse/commands/finesse-version.md

## Rules
- ONLY modify these 4 files:
  - plugins/finesse/commands/finesse.md
  - plugins/finesse/skills/meta-prompting/SKILL.md
  - plugins/finesse/.claude-plugin/plugin.json
  - plugins/finesse/commands/finesse-version.md
- Do NOT modify any other files in the codebase.
- Do NOT rewrite files from scratch. Make targeted edits using the Edit tool.
- Do NOT add unnecessary abstractions or extra files.
- Do NOT make git commits.
- Do NOT push to remote repositories.
- Read the actual file content before making edits. Understand the existing structure.
- Preserve existing formatting, markdown style, and indentation in all files.
- The Git Configuration Prompt section must use AskUserQuestion as the interaction mechanism.
- The Git Configuration Rules section must cover ALL combinations: no checkpoint, checkpoint+no push (3 granularity variants), checkpoint+push (3 granularity variants).
- The replacement in the template must use square brackets like other placeholders (e.g., [test command], [scoped directories]).
- When editing Mandatory Attribute #6 in SKILL.md, add new text after the existing bullet list. Do not try to find and replace push-related text that does not exist in that section.
- If stuck on the same error for 3+ attempts, try an alternative approach.
- If unable to make progress after 5 iterations, document blockers and output <promise>BLOCKED</promise>.

## Completion
When ALL phases are complete and ALL verification commands pass cleanly,
output <promise>FINESSE_V031_GIT_CONFIG_COMPLETE</promise>. This must be unequivocally true.
Do not output the completion promise unless every criterion is met.
