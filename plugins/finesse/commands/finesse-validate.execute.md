---
description: "Validate the Finesse execution layer (scripts, hooks, commands)"
allowed-tools: ["Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate_execute.py)"]
hide-from-slash-command-tool: "true"
---

# Finesse Validate Execute

Run the validation suite for the Finesse execution layer. This checks structural integrity and runs functional tests against the setup script, stop hook, hook registration, and command definitions.

Execute the validator:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/validate_execute.py"
```

## What It Checks

### Structural Checks
- All required files exist (scripts, hooks, commands)
- Python files compile without syntax errors
- hooks.json is valid JSON with correct Stop hook structure
- Command markdown files have correct YAML frontmatter
- Python scripts use only stdlib modules (no external dependencies)
- State file path is consistent between setup script and stop hook
- Run log path is consistent between setup script and stop hook

### Functional Tests
- Setup script creates state file with correct YAML frontmatter
- Setup script creates run-log.json with git hash and timestamps
- Setup script rejects double-start (existing loop active)
- Setup script rejects empty prompt
- Setup script rejects missing prompt file
- Setup script accepts inline prompt text
- Stop hook blocks exit and re-feeds prompt when no promise match
- Stop hook increments iteration counter
- Stop hook writes per-iteration telemetry
- Stop hook detects promise match and allows exit
- Stop hook removes state file on completion
- Stop hook marks telemetry as completed on promise match
- Stop hook stops at max iterations
- Stop hook marks telemetry as max_iterations
- Stop hook is a no-op when no state file exists

## Interpreting Results

- **PASS**: Check passed.
- **FAIL**: Check failed. Detail explains what went wrong.
- **WARN**: Non-blocking issue worth noting.

Exit code 0 means all checks pass. Exit code 1 means at least one check failed.

## When to Run

- After modifying any file in `scripts/`, `hooks/`, or the execute-related commands
- Before committing changes to the execution layer
- After cloning the repo on a new machine to verify Python 3 compatibility