#!/usr/bin/env python3
"""
Finesse Identity Hook — PreToolUse hook that injects planner identity rules
before any planning command executes.

Strategy: Block-then-approve. On the first Skill invocation of a planning
command, blocks with the full identity rules as the block reason (guaranteeing
Claude reads them). Writes a 30-second checkpoint. On retry (within 30s),
approves the invocation.
"""

import json
import os
import sys
import time
from pathlib import Path

# Planning commands that require identity injection (short and fully-qualified)
PLANNING_SKILLS = {
    "finesse",
    "finesse:finesse",
    "finesse-edit",
    "finesse:finesse-edit",
    "finesse-mini",
    "finesse:finesse-mini",
    "finesse-resume",
    "finesse:finesse-resume",
}

CHECKPOINT_FILE = ".finesse/.identity-checkpoint"
SESSION_MARKER = ".finesse/.planning-session"
CHECKPOINT_TTL = 30  # seconds

LOG_PREFIX = "[finesse:identity]"

# Resolve identity file relative to this hook's location (plugin root)
PLUGIN_ROOT = Path(__file__).resolve().parent.parent
IDENTITY_FILE = PLUGIN_ROOT / "skills" / "planner-identity" / "SKILL.md"


def strip_yaml_frontmatter(text: str) -> str:
    """Remove YAML frontmatter (--- delimited block) from markdown."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return text
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[i + 1 :]).strip()
    return text


def read_identity() -> str | None:
    """Read and return identity rules with frontmatter stripped.
    Returns None if the file cannot be read."""
    try:
        content = IDENTITY_FILE.read_text()
        return strip_yaml_frontmatter(content)
    except (OSError, IOError):
        return None


def read_checkpoint() -> float | None:
    """Read the checkpoint timestamp. Returns None if missing or expired."""
    try:
        ts = float(Path(CHECKPOINT_FILE).read_text().strip())
        if time.time() - ts <= CHECKPOINT_TTL:
            return ts
        return None
    except (OSError, ValueError):
        return None


def write_checkpoint():
    """Write a checkpoint with the current timestamp."""
    os.makedirs(os.path.dirname(CHECKPOINT_FILE), exist_ok=True)
    Path(CHECKPOINT_FILE).write_text(str(time.time()))


def clear_checkpoint():
    """Remove the checkpoint file."""
    try:
        Path(CHECKPOINT_FILE).unlink(missing_ok=True)
    except OSError:
        pass


def write_session_marker():
    """Write a session marker so the phase-gate hook knows a finesse session is active."""
    os.makedirs(os.path.dirname(SESSION_MARKER), exist_ok=True)
    Path(SESSION_MARKER).write_text(str(time.time()))


def log(msg: str):
    """Write a debug log line to stderr."""
    print(f"{LOG_PREFIX} {msg}", file=sys.stderr)


def main():
    # Read hook input from stdin
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        hook_input = {}

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    log(f"hook fired for tool={tool_name}")

    # Only intercept Skill tool calls
    if tool_name != "Skill":
        sys.exit(0)

    # Check if this is a planning command
    skill_name = tool_input.get("skill", "")
    if skill_name not in PLANNING_SKILLS:
        log(f"skipping non-planning skill: {skill_name}")
        sys.exit(0)

    log(f"intercepted planning skill: {skill_name}")

    # Check for existing valid checkpoint (retry within TTL)
    if read_checkpoint() is not None:
        log("checkpoint valid, approving retry")
        clear_checkpoint()
        result = {"decision": "approve"}
        print(json.dumps(result))
        sys.exit(0)

    # First invocation — block with identity rules
    identity = read_identity()
    if identity is None:
        # Graceful degradation: approve with warning if identity file unreadable
        log(f"WARNING: could not read identity file at {IDENTITY_FILE}")
        result = {"decision": "approve"}
        print(json.dumps(result))
        sys.exit(0)

    # Write checkpoint for the retry and session marker for phase-gate hook
    write_checkpoint()
    write_session_marker()
    log("first invocation, blocking with identity rules + session marker written")

    # Block with identity rules as reason
    reason = (
        f"FINESSE PLANNER IDENTITY — READ THESE RULES BEFORE PROCEEDING\n\n"
        f"{identity}\n\n"
        f"ACTION REQUIRED: Re-invoke the same command now."
    )

    result = {"decision": "block", "reason": reason}
    print(json.dumps(result))
    sys.exit(0)


if __name__ == "__main__":
    main()
