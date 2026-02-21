#!/usr/bin/env python3
"""
Phase Gate Hook — PreToolUse hook that blocks ExitPlanMode if required
Finesse planning phases are incomplete.

Only activates when a Finesse planning session is detected (via session marker
written by identity_hook.py). Reads the working file's YAML frontmatter to
check completed_phases against minimum required phases for the task type.
"""

import json
import os
import sys
import time
from glob import glob
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

SESSION_MARKER = ".finesse/.planning-session"
SESSION_TTL = 7200  # 2 hours — ignore stale markers from old sessions

LOG_PREFIX = "[finesse:phase-gate]"

# Minimum phases that MUST be in completed_phases before ExitPlanMode is allowed.
# Includes validation phases — the planner must mark validation complete in the
# working file AFTER plan-validator returns and BEFORE calling ExitPlanMode.
# Presentation phases are excluded (ExitPlanMode IS the presentation).
# Optional phases (Clarifying Questions) are omitted — they may genuinely have none.
REQUIRED_PHASES = {
    "feature": ["F1", "F2", "F3", "F5", "F6", "F7"],
    "bugfix": ["B1", "B2", "B3", "B4", "B5", "B6", "B7"],
    "refactor": ["R1", "R2", "R3", "R4", "R5", "R6", "R7"],
    "testing": ["T1", "T2", "T3", "T5", "T6"],
    "performance": ["P1", "P2", "P3", "P4", "P5", "P6"],
    "research": ["RE1", "RE2", "RE3", "RE4", "RE5", "RE6", "RE7"],
}


def log(msg: str):
    """Write a debug log line to stderr."""
    print(f"{LOG_PREFIX} {msg}", file=sys.stderr)


def parse_yaml_frontmatter(content: str) -> dict | None:
    """Parse YAML frontmatter from markdown content. Returns None on failure."""
    if not content.startswith("---\n"):
        return None
    end = content.find("\n---", 4)
    if end == -1:
        return None
    yaml_text = content[4:end]

    if yaml is not None:
        try:
            return yaml.safe_load(yaml_text)
        except yaml.YAMLError:
            return None

    # Fallback: minimal key-value parsing when PyYAML is unavailable
    result = {}
    for line in yaml_text.split("\n"):
        line = line.strip()
        if ":" not in line or line.startswith("#"):
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        # Handle list values like [F1, F2, F3]
        if value.startswith("[") and value.endswith("]"):
            items = value[1:-1].split(",")
            result[key] = [item.strip().strip("'\"") for item in items if item.strip()]
        else:
            result[key] = value.strip("'\"")
    return result


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

    if tool_name != "ExitPlanMode":
        sys.exit(0)

    # Only enforce during active finesse sessions
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

    log("ExitPlanMode intercepted during finesse session")

    # Find the working file
    working_files = glob("finesse-plans/*-working.md")
    if not working_files:
        log("no working file found — blocking")
        block(
            "FINESSE PHASE GATE: No working file found in finesse-plans/.\n\n"
            "You MUST maintain a working file (finesse-plans/<name>-working.md) "
            "with YAML frontmatter tracking completed_phases. This file must be "
            "created after exploration and updated at every phase boundary.\n\n"
            "Create the working file and complete ALL required phases before "
            "calling ExitPlanMode."
        )

    # Read the most recent working file
    working_file = sorted(working_files, key=os.path.getmtime)[-1]
    log(f"reading working file: {working_file}")

    try:
        content = Path(working_file).read_text()
    except OSError as e:
        log(f"WARNING: could not read working file: {e}")
        sys.exit(0)  # Graceful degradation

    # Parse YAML frontmatter
    frontmatter = parse_yaml_frontmatter(content)
    if frontmatter is None:
        log("no valid YAML frontmatter — blocking")
        block(
            "FINESSE PHASE GATE: Working file has no valid YAML frontmatter.\n\n"
            "The working file must have YAML frontmatter with task_type and "
            "completed_phases fields. Fix the working file and retry."
        )
        return  # unreachable, but satisfies type checker

    task_type = frontmatter.get("task_type", "")
    completed = frontmatter.get("completed_phases", [])

    if not isinstance(completed, list):
        completed = []

    if task_type not in REQUIRED_PHASES:
        log(f"unknown task_type '{task_type}', approving")
        sys.exit(0)

    required = REQUIRED_PHASES[task_type]
    missing = [p for p in required if p not in completed]

    if missing:
        log(f"missing phases for {task_type}: {missing}")
        block(
            f"FINESSE PHASE GATE: Cannot present plan — required phases incomplete.\n\n"
            f"Task type: {task_type}\n"
            f"Completed phases: {', '.join(completed) if completed else 'none'}\n"
            f"Missing required phases: {', '.join(missing)}\n\n"
            f"You MUST complete these phases before calling ExitPlanMode. "
            f"Return to phase {missing[0]} and continue the workflow in order.\n\n"
            f"Update the working file's completed_phases as you finish each phase."
        )

    # All required phases complete
    log(f"all required phases complete for {task_type}: {completed}")
    sys.exit(0)


if __name__ == "__main__":
    main()
