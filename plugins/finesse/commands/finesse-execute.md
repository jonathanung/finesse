---
description: "Launch a Finesse-managed ralph loop from a plan or inline prompt"
argument-hint: "[--prompt-file PATH] [--completion-promise-file PATH] [--max-iterations N] [PROMPT...]"
allowed-tools: ["Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/finesse_execute.py:*)", "Read(finesse-plans/*)", "Read(finesse-plans/**/*)", "Read(.finesse/*)", "Glob(finesse-plans/*)", "Glob(finesse-plans/**/*)", "AskUserQuestion"]
hide-from-slash-command-tool: "true"
---

# Finesse Execute

Launch a Finesse-managed ralph loop. This is a forked execution layer based on the ralph-wiggum plugin, enhanced with file-based input, pre-execution git snapshots, and per-iteration telemetry for retro analysis.

## Argument Parsing

Parse `$ARGUMENTS` for these patterns:

### Pattern 1: Direct plan reference (most common after /finesse)

If `$ARGUMENTS` contains `--prompt-file`, pass all arguments directly to the setup script:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/finesse_execute.py" $ARGUMENTS
```

### Pattern 2: Auto-detect from finesse-plans/

If `$ARGUMENTS` is empty or blank:

1. Use `Glob` to scan `finesse-plans/` for plan files:
   - Single-workflow: `finesse-plans/*-promise.txt` (paired with `finesse-plans/*.md`)
   - Multi-workflow: `finesse-plans/*/execution-graph.md`

2. If no plans found, say "No plans found in finesse-plans/. Run /finesse first to generate a plan, or provide a prompt inline." and stop.

3. If exactly one single-workflow plan found:
   - Read the `-plan.md` file to extract task type, approach summary, and iteration count
   - Present a summary:
     ```
     Found plan: <plan-name>
     Task type: <type>
     Max iterations: <N>
     Prompt: <first 3 lines of prompt file>...
     Estimated cost: <range from plan metadata>
     ```
   - Ask: "Execute this plan? [Yes / No / Show full prompt]"
   - On Yes: execute with `--prompt-file` and `--completion-promise-file` pointing to the plan files
   - On Show full prompt: display the full prompt, then ask again

4. If exactly one multi-workflow session found:
   - Read `execution-graph.md` to show the wave structure
   - Present wave-by-wave summary
   - Say "Multi-workflow execution is not yet supported by /finesse:finesse-execute. Use the commands from execution-graph.md to run each sub-workflow manually."
   - Stop.

5. If multiple plans found:
   - List each plan with its name, task type, and iteration count (read from `-plan.md` or `plan.md`)
   - Ask the user to pick one using `AskUserQuestion`
   - Proceed with the selected plan as in step 3

### Pattern 3: Inline prompt

If `$ARGUMENTS` contains text that is NOT a recognized flag, pass all arguments to the setup script:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/finesse_execute.py" $ARGUMENTS
```

## Auto-Detection File Resolution

When auto-detecting a single-workflow plan, the three files follow this naming:
- Prompt: `finesse-plans/<n>.md`
- Promise: `finesse-plans/<n>-promise.txt`
- Metadata: `finesse-plans/<n>-plan.md`

To construct the execute command from a detected plan named `<n>`:
```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/finesse_execute.py" --prompt-file "finesse-plans/<n>.md" --completion-promise-file "finesse-plans/<n>-promise.txt" --max-iterations <N>
```

Where `<N>` is extracted from the `-plan.md` metadata. If the metadata file is missing or doesn't contain an iteration count, ask the user for a max-iterations value.

## Execution Flow

After the setup script runs:

1. The script creates `.finesse/loop-state.md` (state file for the stop hook)
2. The script creates `.finesse/run-log.json` (telemetry for retro)
3. The script captures the current git hash (pre-execution snapshot)
4. The script prints the prompt and completion promise requirements
5. The stop hook (registered in hooks/hooks.json) activates automatically
6. Claude begins working on the prompt
7. On each exit attempt, the stop hook intercepts, increments iteration, writes telemetry, and re-feeds the same prompt
8. Loop ends when: completion promise is matched, max iterations reached, or user cancels with /cancel-finesse-execute

## Post-Execution

When the loop ends (promise matched or max iterations), the telemetry in `.finesse/run-log.json` contains:
- Start/end timestamps
- Per-iteration timestamps
- Final outcome (completed, max_iterations, cancelled, error)
- Pre-execution git hash (for retro PR review diffing)

This data is consumed by `/finesse-retro` (when implemented) to generate post-execution retrospectives.

## Important Notes

- This command does NOT require the vanilla ralph-loop plugin. Finesse ships its own execution layer.
- If the vanilla ralph-loop plugin IS installed, both stop hooks will fire. The Finesse hook checks `.finesse/loop-state.md`, the vanilla hook checks `.claude/ralph-loop.local.md`. They don't conflict as long as you don't run both simultaneously.
- The setup script warns if a vanilla ralph-loop is already active.
- The setup script refuses to start if a Finesse loop is already active.

## Examples

```
# Auto-detect the most recent plan from finesse-plans/
/finesse:finesse-execute

# Execute a specific plan file
/finesse:finesse-execute --prompt-file finesse-plans/fix-token-refresh-auth.md --completion-promise-file finesse-plans/fix-token-refresh-auth-promise.txt --max-iterations 8

# Inline prompt (bypass /finesse planning, useful for simple tasks)
/finesse:finesse-execute "Fix the linting errors in src/utils/" --max-iterations 5 --completion-promise "COMPLETE"

# Multi-workflow sub-task
/finesse:finesse-execute --prompt-file finesse-plans/build-todo-api/wave-1/auth-endpoints/prompt.md --completion-promise-file finesse-plans/build-todo-api/wave-1/auth-endpoints/promise.txt --max-iterations 12
```