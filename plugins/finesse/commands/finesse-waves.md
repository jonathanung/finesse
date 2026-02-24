---
description: "Wave execution orchestration for multi-workflow plans"
argument-hint: "<subcommand> [session-name]"
allowed-tools: ["Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/finesse_waves.py:*)", "Read(.finesse/*)", "Glob(finesse-plans/*)"]
---

# Finesse Waves

Wave execution orchestration for multi-workflow plans. Launches parallel sub-workflows in isolated git worktrees via tmux, monitors completion, and handles merge reconciliation.

This command executes the waves orchestrator directly via Bash.

## Determine Plugin Root

The plugin root is the directory containing this command file. Resolve it from `${CLAUDE_PLUGIN_ROOT}` or by navigating from this file's location to the parent `plugins/finesse/` directory.

## Parse Subcommand

Parse `$ARGUMENTS` for the subcommand and optional session name.

### If no arguments or empty $ARGUMENTS:

Show usage help:

```
Finesse Waves — Wave execution orchestration

Subcommands:
  start <session-name>    Parse execution-graph.md, show dry-run, launch waves
  status                  Show status of all active wave sessions
  attach <session-name>   Attach to tmux session for observation
  stop <session-name>     Gracefully stop a wave session
  cleanup <session-name>  Remove worktrees and tmux sessions
  merge <session-name>    Manually trigger merge reconciliation

Usage:
  /finesse-waves start my-api-project
  /finesse-waves status
  /finesse-waves attach my-api-project
```

### If subcommand is recognized:

Execute the waves orchestrator directly via Bash:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/finesse_waves.py" <subcommand> <session-name>
```

Where `<subcommand>` and `<session-name>` are taken from `$ARGUMENTS`.

## Prerequisites

Before starting wave execution, ensure:
1. A multi-workflow plan exists at `finesse-plans/<session-name>/execution-graph.md`
2. `tmux` is installed and available
3. `git` worktree support is available (Git 2.5+)
4. `claude` CLI is accessible from the terminal

## Notes

- The orchestrator is launched via Bash from within Claude Code
- Use `attach` to observe running workflows in tmux
- Use `stop` for graceful shutdown (marks session as stopped and kills tmux sessions)
- Use `cleanup` after completion to remove worktrees and tmux sessions
- If merge conflicts occur, resolve them manually and run `merge` to retry
