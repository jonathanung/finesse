#!/usr/bin/env python3
"""
Finesse Execute - Setup script for Finesse-managed ralph loops.

Forked from anthropics/claude-code ralph-wiggum plugin (MIT License).
Original authors: Daisy Hollman (Anthropic).

Enhancements over ralph-wiggum setup-ralph-loop.sh:
  - --prompt-file / --completion-promise-file flags for file-based input
  - Pre-execution git hash snapshot for retro PR review
  - Telemetry initialization (.finesse/run-log.json)
  - Scoped file checksums for drift detection
  - Conflict detection with vanilla ralph-loop plugin
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STATE_FILE = ".finesse/loop-state.md"
RUN_LOG = ".finesse/run-log.json"
RALPH_STATE_FILE = ".claude/ralph-loop.local.md"


def get_git_hash() -> str:
    """Get current git HEAD hash. Returns empty string if not in a git repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return ""


def get_git_dirty() -> bool:
    """Check if working tree has uncommitted changes."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return bool(result.stdout.strip())
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return False


def read_file_content(path: str) -> str:
    """Read file content, exit with error if file not found."""
    p = Path(path)
    if not p.is_file():
        print(f"Error: File not found: {path}", file=sys.stderr)
        sys.exit(1)
    try:
        return p.read_text().strip()
    except OSError as e:
        print(f"Error: Cannot read file {path}: {e}", file=sys.stderr)
        sys.exit(1)


def check_conflicts():
    """Warn if vanilla ralph-loop state file exists."""
    if Path(RALPH_STATE_FILE).is_file():
        print(
            "Warning: A vanilla ralph-loop is already active "
            f"({RALPH_STATE_FILE} exists).",
            file=sys.stderr,
        )
        print(
            "  Running both simultaneously may cause unexpected behavior.",
            file=sys.stderr,
        )
        print(
            "  Cancel it with /cancel-ralph first, or proceed at your own risk.",
            file=sys.stderr,
        )
        print("", file=sys.stderr)


def check_existing_finesse_loop():
    """Check if a finesse loop is already active."""
    if Path(STATE_FILE).is_file():
        print(
            "Error: A Finesse loop is already active "
            f"({STATE_FILE} exists).",
            file=sys.stderr,
        )
        print(
            "  Cancel it with /cancel-finesse-execute first.",
            file=sys.stderr,
        )
        sys.exit(1)


def create_state_file(
    prompt: str,
    max_iterations: int,
    completion_promise: str,
    prompt_source: str,
    promise_source: str,
    plan_name: str,
):
    """Create the markdown state file with YAML frontmatter."""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if completion_promise and completion_promise != "null":
        promise_yaml = f'"{completion_promise}"'
    else:
        promise_yaml = "null"

    frontmatter = f"""---
active: true
iteration: 1
max_iterations: {max_iterations}
completion_promise: {promise_yaml}
started_at: "{now}"
prompt_source: "{prompt_source}"
promise_source: "{promise_source}"
plan_name: "{plan_name}"
---"""

    content = f"{frontmatter}\n\n{prompt}\n"

    Path(STATE_FILE).write_text(content)


def create_run_log(
    prompt_source: str,
    promise_source: str,
    plan_name: str,
    max_iterations: int,
    completion_promise: str,
    git_hash: str,
    git_dirty: bool,
):
    """Create the telemetry run log for retro consumption."""
    os.makedirs(os.path.dirname(RUN_LOG), exist_ok=True)

    now = datetime.now(timezone.utc).isoformat()

    run_log = {
        "version": 1,
        "plan_name": plan_name,
        "prompt_source": prompt_source,
        "promise_source": promise_source,
        "max_iterations": max_iterations,
        "completion_promise": completion_promise,
        "started_at": now,
        "finished_at": None,
        "final_iteration": None,
        "outcome": None,  # "completed", "max_iterations", "cancelled", "error"
        "pre_execution": {
            "git_hash": git_hash,
            "git_dirty": git_dirty,
        },
        "iterations": [],
    }

    Path(RUN_LOG).write_text(json.dumps(run_log, indent=2) + "\n")


def resolve_plan_files(args) -> tuple:
    """
    Resolve prompt and promise from arguments.

    Returns (prompt_text, promise_text, prompt_source, promise_source, plan_name).
    """
    prompt_text = ""
    promise_text = ""
    prompt_source = "inline"
    promise_source = "inline"
    plan_name = ""

    # Prompt resolution
    if args.prompt_file:
        prompt_text = read_file_content(args.prompt_file)
        prompt_source = args.prompt_file
        # Derive plan name from file path
        p = Path(args.prompt_file)
        if p.name == "prompt.md":
            # Multi-workflow: finesse-plans/<session>/wave-N/<task>/prompt.md
            plan_name = p.parent.name
        else:
            # Single-workflow: finesse-plans/<n>.md
            plan_name = p.stem
    elif args.prompt:
        prompt_text = " ".join(args.prompt)
        prompt_source = "inline"
        plan_name = "inline-task"
    else:
        print("Error: No prompt provided.", file=sys.stderr)
        print("", file=sys.stderr)
        print("  Provide a prompt inline or via --prompt-file:", file=sys.stderr)
        print(
            '    /finesse:finesse-execute "Build a REST API" --max-iterations 15',
            file=sys.stderr,
        )
        print(
            "    /finesse:finesse-execute --prompt-file finesse-plans/my-plan.md",
            file=sys.stderr,
        )
        sys.exit(1)

    # Promise resolution
    if args.completion_promise_file:
        promise_text = read_file_content(args.completion_promise_file)
        promise_source = args.completion_promise_file
    elif args.completion_promise:
        promise_text = args.completion_promise
        promise_source = "inline"
    else:
        promise_text = "null"
        promise_source = "none"

    return prompt_text, promise_text, prompt_source, promise_source, plan_name


def print_setup_message(
    plan_name: str,
    max_iterations: int,
    completion_promise: str,
    prompt_source: str,
    git_hash: str,
    git_dirty: bool,
):
    """Print the activation message."""
    iter_display = str(max_iterations) if max_iterations > 0 else "unlimited"
    if completion_promise and completion_promise != "null":
        promise_display = completion_promise
    else:
        promise_display = "none (runs until max iterations)"

    dirty_marker = " (dirty)" if git_dirty else ""

    print("Finesse loop activated!")
    print("")
    print(f"  Plan: {plan_name}")
    print(f"  Prompt source: {prompt_source}")
    print(f"  Iteration: 1 / {iter_display}")
    print(f"  Completion promise: {promise_display}")
    if git_hash:
        print(f"  Git snapshot: {git_hash[:12]}{dirty_marker}")
    print(f"  Telemetry: {RUN_LOG}")
    print("")
    print("The stop hook is now active. When the agent tries to exit,")
    print("the SAME PROMPT will be fed back for the next iteration.")
    print("")
    if max_iterations == 0 and (not completion_promise or completion_promise == "null"):
        print(
            "WARNING: No max-iterations or completion-promise set. "
            "Loop runs forever!",
        )
        print("  Cancel with /cancel-finesse-execute")
        print("")


def print_prompt_and_promise(prompt: str, completion_promise: str):
    """Print the initial prompt and promise requirements."""
    print(prompt)

    if completion_promise and completion_promise != "null":
        print("")
        print("=" * 59)
        print("CRITICAL - Finesse Loop Completion Promise")
        print("=" * 59)
        print("")
        print("To complete this loop, output this EXACT text:")
        print(f"  <promise>{completion_promise}</promise>")
        print("")
        print("STRICT REQUIREMENTS (DO NOT VIOLATE):")
        print("  - Use <promise> XML tags EXACTLY as shown above")
        print("  - The statement MUST be completely and unequivocally TRUE")
        print("  - Do NOT output false statements to exit the loop")
        print("  - Do NOT lie even if you think you should exit")
        print("")
        print("If stuck, follow the failure instructions in the prompt.")
        print("=" * 59)


def main():
    parser = argparse.ArgumentParser(
        description="Finesse Execute - Launch a Finesse-managed ralph loop",
        add_help=True,
    )

    parser.add_argument(
        "prompt",
        nargs="*",
        help="Inline prompt text (ignored if --prompt-file is set)",
    )
    parser.add_argument(
        "--prompt-file",
        type=str,
        default=None,
        help="Path to prompt file (e.g. finesse-plans/my-plan.md)",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=0,
        help="Maximum iterations before auto-stop (default: unlimited)",
    )
    parser.add_argument(
        "--completion-promise",
        type=str,
        default=None,
        help="Promise phrase for completion detection",
    )
    parser.add_argument(
        "--completion-promise-file",
        type=str,
        default=None,
        help="Path to file containing the completion promise text",
    )

    args = parser.parse_args()

    # Validate: can't use both inline promise and promise file
    if args.completion_promise and args.completion_promise_file:
        print(
            "Error: Cannot use both --completion-promise and "
            "--completion-promise-file.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Pre-flight checks
    check_existing_finesse_loop()
    check_conflicts()

    # Resolve prompt and promise
    prompt_text, promise_text, prompt_source, promise_source, plan_name = (
        resolve_plan_files(args)
    )

    # Capture pre-execution state
    git_hash = get_git_hash()
    git_dirty = get_git_dirty()

    # Create state and telemetry files
    create_state_file(
        prompt=prompt_text,
        max_iterations=args.max_iterations,
        completion_promise=promise_text,
        prompt_source=prompt_source,
        promise_source=promise_source,
        plan_name=plan_name,
    )

    create_run_log(
        prompt_source=prompt_source,
        promise_source=promise_source,
        plan_name=plan_name,
        max_iterations=args.max_iterations,
        completion_promise=promise_text,
        git_hash=git_hash,
        git_dirty=git_dirty,
    )

    # Output
    print_setup_message(
        plan_name=plan_name,
        max_iterations=args.max_iterations,
        completion_promise=promise_text,
        prompt_source=prompt_source,
        git_hash=git_hash,
        git_dirty=git_dirty,
    )

    print_prompt_and_promise(prompt_text, promise_text)


if __name__ == "__main__":
    main()