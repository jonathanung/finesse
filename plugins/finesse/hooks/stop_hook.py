#!/usr/bin/env python3
"""
Finesse Stop Hook - Intercepts Claude Code session exit for loop continuation.

Forked from anthropics/claude-code ralph-wiggum plugin (MIT License).
Original authors: Daisy Hollman (Anthropic).

Enhancements over ralph-wiggum stop-hook.sh:
  - Pure Python (no jq/perl dependencies)
  - Per-iteration telemetry written to .finesse/run-log.json
  - Iteration timestamps for retro analysis
"""

import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

STATE_FILE = ".finesse/loop-state.md"
RUN_LOG = ".finesse/run-log.json"


def parse_frontmatter(content: str) -> dict:
    """Parse YAML-like frontmatter from markdown state file."""
    lines = content.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}

    frontmatter = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            # Strip surrounding quotes
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            frontmatter[key] = value

    return frontmatter


def extract_prompt(content: str) -> str:
    """Extract prompt text (everything after the closing --- of frontmatter)."""
    lines = content.split("\n")
    fence_count = 0
    for i, line in enumerate(lines):
        if line.strip() == "---":
            fence_count += 1
            if fence_count == 2:
                # Everything after this line is prompt
                return "\n".join(lines[i + 1 :]).strip()
    return ""


def extract_promise_text(output: str) -> str:
    """Extract text from <promise>...</promise> tags. Returns first match."""
    match = re.search(r"<promise>(.*?)</promise>", output, re.DOTALL)
    if match:
        # Normalize whitespace like the original perl version
        text = match.group(1).strip()
        text = re.sub(r"\s+", " ", text)
        return text
    return ""


def get_last_assistant_output(transcript_path: str) -> str:
    """Read last assistant message from JSONL transcript."""
    last_line = ""
    try:
        with open(transcript_path, "r") as f:
            for line in f:
                if '"role":"assistant"' in line or '"role": "assistant"' in line:
                    last_line = line.strip()
    except (OSError, IOError):
        return ""

    if not last_line:
        return ""

    try:
        data = json.loads(last_line)
        content = data.get("message", {}).get("content", [])
        texts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                texts.append(block.get("text", ""))
        return "\n".join(texts)
    except (json.JSONDecodeError, TypeError, KeyError):
        return ""


def update_iteration(content: str, new_iteration: int) -> str:
    """Update the iteration field in frontmatter."""
    return re.sub(
        r"^iteration: .*$",
        f"iteration: {new_iteration}",
        content,
        count=1,
        flags=re.MULTILINE,
    )


def write_telemetry(iteration: int, outcome: str, promise_matched: bool):
    """Append iteration entry to run-log.json."""
    try:
        if not Path(RUN_LOG).is_file():
            return

        run_log = json.loads(Path(RUN_LOG).read_text())

        now = datetime.now(timezone.utc).isoformat()

        entry = {
            "iteration": iteration,
            "timestamp": now,
            "outcome": outcome,  # "continue", "promise_matched", "max_iterations"
            "promise_checked": promise_matched,
        }

        run_log["iterations"].append(entry)

        # If this is a terminal event, update top-level fields
        if outcome != "continue":
            run_log["finished_at"] = now
            run_log["final_iteration"] = iteration
            if outcome == "promise_matched":
                run_log["outcome"] = "completed"
            elif outcome == "max_iterations":
                run_log["outcome"] = "max_iterations"
            else:
                run_log["outcome"] = outcome

        Path(RUN_LOG).write_text(json.dumps(run_log, indent=2) + "\n")
    except (json.JSONDecodeError, OSError, KeyError):
        # Telemetry is best-effort. Don't break the loop.
        pass


def finalize_telemetry(outcome: str, iteration: int):
    """Mark the run as finished in the run log."""
    try:
        if not Path(RUN_LOG).is_file():
            return

        run_log = json.loads(Path(RUN_LOG).read_text())
        now = datetime.now(timezone.utc).isoformat()
        run_log["finished_at"] = now
        run_log["final_iteration"] = iteration
        run_log["outcome"] = outcome

        Path(RUN_LOG).write_text(json.dumps(run_log, indent=2) + "\n")
    except (json.JSONDecodeError, OSError, KeyError):
        pass


def allow_exit():
    """Allow normal session exit."""
    sys.exit(0)


def block_exit(prompt: str, system_msg: str):
    """Block exit and feed prompt back to Claude."""
    result = {
        "decision": "block",
        "reason": prompt,
        "systemMessage": system_msg,
    }
    print(json.dumps(result))
    sys.exit(0)


def error_cleanup(message: str):
    """Log error, remove state file, allow exit."""
    print(f"Finesse loop: {message}", file=sys.stderr)
    try:
        Path(STATE_FILE).unlink(missing_ok=True)
    except OSError:
        pass
    allow_exit()


def main():
    # Read hook input from stdin
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        hook_input = {}

    # Check if finesse loop is active
    if not Path(STATE_FILE).is_file():
        allow_exit()

    # Read and parse state file
    try:
        content = Path(STATE_FILE).read_text()
    except OSError:
        error_cleanup("Cannot read state file")
        return

    frontmatter = parse_frontmatter(content)

    # Extract fields
    try:
        iteration = int(frontmatter.get("iteration", "0"))
    except ValueError:
        finalize_telemetry("error", 0)
        error_cleanup(
            f"State file corrupted: 'iteration' is not a number "
            f"(got: '{frontmatter.get('iteration', '')}'). "
            "Run /finesse:finesse-execute again to start fresh."
        )
        return

    try:
        max_iterations = int(frontmatter.get("max_iterations", "0"))
    except ValueError:
        finalize_telemetry("error", iteration)
        error_cleanup(
            f"State file corrupted: 'max_iterations' is not a number "
            f"(got: '{frontmatter.get('max_iterations', '')}'). "
            "Run /finesse:finesse-execute again to start fresh."
        )
        return

    completion_promise = frontmatter.get("completion_promise", "null")
    if completion_promise == "null":
        completion_promise = ""

    # Check max iterations
    if max_iterations > 0 and iteration >= max_iterations:
        write_telemetry(iteration, "max_iterations", False)
        print(f"Finesse loop: Max iterations ({max_iterations}) reached.")
        try:
            Path(STATE_FILE).unlink(missing_ok=True)
        except OSError:
            pass
        allow_exit()

    # Get transcript path from hook input
    transcript_path = hook_input.get("transcript_path", "")

    if not transcript_path or not Path(transcript_path).is_file():
        finalize_telemetry("error", iteration)
        error_cleanup("Transcript file not found. Stopping loop.")
        return

    # Read last assistant output
    last_output = get_last_assistant_output(transcript_path)

    if not last_output:
        finalize_telemetry("error", iteration)
        error_cleanup("No assistant messages found in transcript. Stopping loop.")
        return

    # Check completion promise
    if completion_promise:
        promise_text = extract_promise_text(last_output)
        if promise_text and promise_text == completion_promise:
            write_telemetry(iteration, "promise_matched", True)
            print(f"Finesse loop: Detected <promise>{completion_promise}</promise>")
            try:
                Path(STATE_FILE).unlink(missing_ok=True)
            except OSError:
                pass
            allow_exit()

    # Not complete. Continue loop with SAME PROMPT.
    next_iteration = iteration + 1

    prompt_text = extract_prompt(content)

    if not prompt_text:
        finalize_telemetry("error", iteration)
        error_cleanup("State file has no prompt text. Stopping loop.")
        return

    # Update iteration in state file (atomic write via temp file)
    updated_content = update_iteration(content, next_iteration)
    try:
        fd, tmp_path = tempfile.mkstemp(
            dir=os.path.dirname(STATE_FILE), suffix=".tmp"
        )
        with os.fdopen(fd, "w") as f:
            f.write(updated_content)
        os.replace(tmp_path, STATE_FILE)
    except OSError as e:
        # Non-fatal. The iteration count will be stale but the loop continues.
        print(
            f"Finesse loop: Warning: Could not update iteration count: {e}",
            file=sys.stderr,
        )

    # Write telemetry for this iteration
    write_telemetry(iteration, "continue", bool(completion_promise))

    # Build system message
    if completion_promise:
        system_msg = (
            f"Finesse iteration {next_iteration}"
            f" | To stop: output <promise>{completion_promise}</promise>"
            " (ONLY when statement is TRUE)"
        )
    else:
        system_msg = (
            f"Finesse iteration {next_iteration}"
            " | No completion promise set"
        )

    block_exit(prompt_text, system_msg)


if __name__ == "__main__":
    main()