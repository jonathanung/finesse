#!/usr/bin/env python3
"""
Task Guard Hook — PreToolUse hook that enforces allowed subagent types
during active Finesse planning sessions.

Prevents Claude from using generic agent types (Explore, Plan, general-purpose,
Bash) and forces use of Finesse-specific agents (exploration-orchestrator,
code-explorer, etc.).

Only activates when a Finesse planning session is detected (via session marker
written by identity_hook.py).
"""

import json
import os
import sys
import time
from pathlib import Path

SESSION_MARKER = ".finesse/.planning-session"
LOOP_STATE = ".finesse/loop-state.md"  # Present during execution — skip enforcement
SESSION_TTL = 7200  # 2 hours — match phase_gate_hook

LOG_PREFIX = "[finesse:task-guard]"

# Agent types allowed during Finesse planning sessions (without plugin prefix).
# These match the agent filenames in the plugin's agents/ directory.
ALLOWED_AGENTS = {
    "code-explorer",
    "code-architect",
    "task-decomposer",
    "clarity-checker",
    "completion-validator",
    "scope-safety-reviewer",
    "phase-structure-analyzer",
    "failure-mode-auditor",
    "goal-achievement-auditor",
    "exploration-orchestrator",
    "scope-analyzer",
    "architecture-designer",
    "plan-constructor",
    "plan-validator",
}

# Map generic agent types to their Finesse equivalents for the error message
AGENT_ALTERNATIVES = {
    "Explore": "finesse:exploration-orchestrator (for codebase exploration) or finesse:code-explorer (for targeted file analysis)",
    "Plan": "Follow the Finesse phase workflow — there is no Plan agent in Finesse. Use finesse:architecture-designer for architecture design.",
    "general-purpose": "finesse:code-explorer (for research) or finesse:exploration-orchestrator (for broad exploration)",
    "Bash": "Finesse planning sessions do not launch Bash agents. Use the Bash tool directly for git commands.",
}


def log(msg: str):
    """Write a debug log line to stderr."""
    print(f"{LOG_PREFIX} {msg}", file=sys.stderr)


def is_allowed_agent(subagent_type: str) -> bool:
    """Check if the agent type is allowed during Finesse sessions."""
    # Allow exact matches (bare name)
    if subagent_type in ALLOWED_AGENTS:
        return True
    # Allow prefixed matches (e.g., "finesse:code-explorer")
    if ":" in subagent_type:
        _, _, name = subagent_type.partition(":")
        return name in ALLOWED_AGENTS
    return False


def block(reason: str):
    """Output a block decision and exit."""
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)


def main():
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        hook_input = {}

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    if tool_name != "Task":
        sys.exit(0)

    # Skip enforcement during execution loops — the ralph-loop prompt may
    # legitimately use generic agents (Explore, Bash, general-purpose) via
    # its subagent instructions.
    if Path(LOOP_STATE).exists():
        sys.exit(0)

    # Only enforce during active Finesse planning sessions
    marker = Path(SESSION_MARKER)
    if not marker.exists():
        sys.exit(0)

    # Check TTL — ignore stale markers from old sessions
    try:
        marker_age = time.time() - os.path.getmtime(str(marker))
        if marker_age > SESSION_TTL:
            log(f"session marker stale ({marker_age:.0f}s old), ignoring")
            sys.exit(0)
    except OSError:
        sys.exit(0)

    # Get the subagent type
    subagent_type = tool_input.get("subagent_type", "")
    if not subagent_type:
        sys.exit(0)

    # Check if allowed
    if is_allowed_agent(subagent_type):
        log(f"allowed agent type: {subagent_type}")
        sys.exit(0)

    # Build block message with specific alternative
    alternative = AGENT_ALTERNATIVES.get(subagent_type, None)
    if alternative:
        alt_msg = f"\nInstead of '{subagent_type}', use: {alternative}"
    else:
        alt_msg = ""

    allowed_list = ", ".join(sorted(ALLOWED_AGENTS))

    log(f"BLOCKED agent type: {subagent_type}")

    block(
        f"FINESSE TASK GUARD: Agent type '{subagent_type}' is not allowed "
        f"during Finesse planning sessions.\n\n"
        f"Allowed agent types: {allowed_list}\n"
        f"(Use with 'finesse:' prefix, e.g., 'finesse:code-explorer')\n"
        f"{alt_msg}\n\n"
        f"During Finesse planning sessions, you MUST use Finesse-specific "
        f"agents listed above. These agents follow the Finesse workflow and "
        f"produce structured outputs for UAT checkpoints.\n\n"
        f"Review the workflow phases for your task type and use the "
        f"appropriate agent for each phase."
    )


if __name__ == "__main__":
    main()
