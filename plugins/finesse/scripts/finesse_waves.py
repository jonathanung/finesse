#!/usr/bin/env python3
"""
Finesse Waves - Wave execution orchestrator for multi-workflow plans.

Launches parallel sub-workflows in isolated git worktrees via tmux,
monitors completion via run-log.json polling, and handles sequential
merge reconciliation between waves.
"""

import argparse
import json
import os
import re
import signal
import shlex
import subprocess
import sys
import tempfile
import time
import random
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SESSIONS_DIR = ".finesse/sessions"
WORKTREES_DIR = ".finesse/worktrees"
CONFIG_FILE = ".finesse/config.json"
DEFAULT_POLL_INTERVAL = 5
PLUGIN_ROOT = Path(__file__).resolve().parent.parent  # -> plugins/finesse/


# ---------------------------------------------------------------------------
# GraphParser
# ---------------------------------------------------------------------------

class GraphParser:
    """Parse execution-graph.md to extract wave structure and task details."""

    def parse(self, graph_path: str) -> dict:
        """Parse execution-graph.md and return structured wave data.

        Returns:
            dict with keys:
                overview: {session_name, total_waves, total_workflows, total_estimated_iterations}
                waves: list of {wave_num, tasks: [{name, task_type, est_iterations, scope, dependencies, prompt_file, promise_file, max_iterations}]}
        """
        content = Path(graph_path).read_text()
        lines = content.split("\n")

        session_name = Path(graph_path).parent.name
        waves = []
        current_wave = None
        current_tasks = []
        total_workflows = 0
        total_estimated_iterations = 0

        i = 0
        while i < len(lines):
            line = lines[i]

            # Detect wave headers: ## Wave N
            wave_match = re.match(r"^##\s+Wave\s+(\d+)", line)
            if wave_match:
                if current_wave is not None:
                    waves.append({"wave_num": current_wave, "tasks": current_tasks})
                current_wave = int(wave_match.group(1))
                current_tasks = []
                i += 1
                continue

            # Detect table rows: | name | type | est_iters | scope | deps |
            if line.startswith("|") and current_wave is not None:
                cols = [c.strip() for c in line.split("|")]
                # Filter empty strings from split
                cols = [c for c in cols if c]
                # Skip header and separator rows
                if len(cols) >= 5 and not cols[0].startswith("-") and cols[0] != "Name":
                    task_name = cols[0]
                    task_type = cols[1] if len(cols) > 1 else "feature"
                    try:
                        est_iterations = int(cols[2]) if len(cols) > 2 else 0
                    except ValueError:
                        est_iterations = 0
                    scope = cols[3] if len(cols) > 3 else ""
                    dependencies = cols[4] if len(cols) > 4 else "none"
                    current_tasks.append({
                        "name": task_name,
                        "task_type": task_type,
                        "est_iterations": est_iterations,
                        "scope": scope,
                        "dependencies": dependencies,
                        "prompt_file": None,
                        "promise_file": None,
                        "max_iterations": est_iterations,
                    })
                    total_workflows += 1
                    total_estimated_iterations += est_iterations
                i += 1
                continue

            # Detect command blocks for prompt/promise/max-iterations extraction
            cmd_match = re.search(
                r"--prompt-file\s+(\S+)", line
            )
            if cmd_match and current_tasks:
                prompt_file = cmd_match.group(1)
                # Find which task this command belongs to
                for task in current_tasks:
                    if task["name"] in prompt_file:
                        task["prompt_file"] = prompt_file
                        break
                else:
                    # Assign to last task if no name match
                    if current_tasks:
                        current_tasks[-1]["prompt_file"] = prompt_file

            promise_match = re.search(
                r"--completion-promise-file\s+(\S+)", line
            )
            if promise_match and current_tasks:
                promise_file = promise_match.group(1)
                for task in current_tasks:
                    if task["name"] in promise_file:
                        task["promise_file"] = promise_file
                        break
                else:
                    if current_tasks:
                        current_tasks[-1]["promise_file"] = promise_file

            max_iter_match = re.search(
                r"--max-iterations\s+(\d+)", line
            )
            if max_iter_match and current_tasks:
                max_iters = int(max_iter_match.group(1))
                for task in current_tasks:
                    if task["prompt_file"] and task["name"] in line:
                        task["max_iterations"] = max_iters
                        break
                else:
                    if current_tasks:
                        current_tasks[-1]["max_iterations"] = max_iters

            i += 1

        # Append the last wave
        if current_wave is not None:
            waves.append({"wave_num": current_wave, "tasks": current_tasks})

        return {
            "overview": {
                "session_name": session_name,
                "total_waves": len(waves),
                "total_workflows": total_workflows,
                "total_estimated_iterations": total_estimated_iterations,
            },
            "waves": waves,
        }


# ---------------------------------------------------------------------------
# WorktreeManager
# ---------------------------------------------------------------------------

class WorktreeManager:
    """Manage git worktrees for isolated sub-workflow execution."""

    def create(self, session: str, task_name: str, base_branch: str) -> str:
        """Create a git worktree for a task.

        Returns the absolute worktree path.
        """
        worktree_path = str(
            Path(WORKTREES_DIR) / session / task_name
        )
        branch = f"finesse/{task_name}"

        os.makedirs(Path(worktree_path).parent, exist_ok=True)

        result = subprocess.run(
            ["git", "worktree", "add", worktree_path, "-b", branch],
            capture_output=True,
            text=True,
        )

        if result.returncode == 128:
            # Branch already exists — try suffixed name
            suffix = format(random.getrandbits(16), "04x")
            branch = f"finesse/{task_name}-{suffix}"
            worktree_path = str(
                Path(WORKTREES_DIR) / session / f"{task_name}-{suffix}"
            )
            result = subprocess.run(
                ["git", "worktree", "add", worktree_path, "-b", branch],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(
                    f"Error creating worktree: {result.stderr}",
                    file=sys.stderr,
                )
                sys.exit(1)
        elif result.returncode != 0:
            print(
                f"Error creating worktree: {result.stderr}",
                file=sys.stderr,
            )
            sys.exit(1)

        return str(Path(worktree_path).resolve())

    def remove(self, worktree_path: str, delete_branch: bool = True):
        """Remove a worktree and optionally its branch."""
        # Extract branch name before removing
        branch = None
        if delete_branch:
            result = subprocess.run(
                ["git", "-C", worktree_path, "branch", "--show-current"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                branch = result.stdout.strip()

        subprocess.run(
            ["git", "worktree", "remove", worktree_path, "--force"],
            capture_output=True,
            text=True,
        )

        if delete_branch and branch:
            subprocess.run(
                ["git", "branch", "-D", branch],
                capture_output=True,
                text=True,
            )

    def merge(self, branch: str, base_branch: str) -> tuple:
        """Merge a branch into the base branch.

        Returns (success: bool, conflict_details: str).
        """
        subprocess.run(
            ["git", "checkout", base_branch],
            capture_output=True,
            text=True,
        )

        result = subprocess.run(
            ["git", "merge", branch, "--no-edit"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return (True, "")

        # Merge conflict — get conflicted files
        conflict_result = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=U"],
            capture_output=True,
            text=True,
        )
        conflict_details = conflict_result.stdout.strip()

        # Abort the failed merge
        subprocess.run(
            ["git", "merge", "--abort"],
            capture_output=True,
            text=True,
        )

        return (False, conflict_details)

    def cleanup_session(self, session: str):
        """Remove all worktrees and branches for a session."""
        session_dir = Path(WORKTREES_DIR) / session
        if not session_dir.is_dir():
            return

        for worktree_dir in session_dir.iterdir():
            if worktree_dir.is_dir():
                self.remove(str(worktree_dir), delete_branch=True)

        # Remove session directory
        try:
            session_dir.rmdir()
        except OSError:
            pass


# ---------------------------------------------------------------------------
# TmuxManager
# ---------------------------------------------------------------------------

class TmuxManager:
    """Manage tmux sessions for parallel workflow observation."""

    def create_session(self, name: str) -> str:
        """Create a new tmux session. Returns actual session name used."""
        result = subprocess.run(
            ["tmux", "new-session", "-d", "-s", name],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return name

        # Collision — retry with random suffix
        for _ in range(3):
            suffix = format(random.getrandbits(16), "04x")
            alt_name = f"{name}-{suffix}"
            result = subprocess.run(
                ["tmux", "new-session", "-d", "-s", alt_name],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return alt_name

        print(f"Error: Could not create tmux session '{name}'.", file=sys.stderr)
        sys.exit(1)

    def add_pane(self, session: str, command: str, pane_name: str = "",
                 is_first: bool = True):
        """Add a pane to a tmux session and run a command in it."""
        if is_first:
            subprocess.run(
                ["tmux", "send-keys", "-t", session, command, "Enter"],
                capture_output=True,
                text=True,
            )
        else:
            subprocess.run(
                ["tmux", "split-window", "-t", session, "-h"],
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["tmux", "send-keys", "-t", session, command, "Enter"],
                capture_output=True,
                text=True,
            )

    def kill_session(self, name: str):
        """Kill a tmux session."""
        subprocess.run(
            ["tmux", "kill-session", "-t", name],
            capture_output=True,
            text=True,
        )

    def attach(self, name: str):
        """Attach to a tmux session (replaces current terminal)."""
        os.execlp("tmux", "tmux", "attach-session", "-t", name)

    def session_exists(self, name: str) -> bool:
        """Check if a tmux session exists."""
        result = subprocess.run(
            ["tmux", "has-session", "-t", name],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    def list_sessions(self, prefix: str = "finesse-") -> list:
        """List tmux sessions matching a prefix."""
        result = subprocess.run(
            ["tmux", "list-sessions", "-F", "#{session_name}"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return []
        sessions = result.stdout.strip().split("\n")
        return [s for s in sessions if s.startswith(prefix)]


# ---------------------------------------------------------------------------
# SessionTracker
# ---------------------------------------------------------------------------

class SessionTracker:
    """Track wave execution session state via JSON files."""

    def create(self, session: str, graph_data: dict, base_branch: str) -> dict:
        """Initialize a new session state and save it."""
        os.makedirs(SESSIONS_DIR, exist_ok=True)

        waves_state = {}
        for wave in graph_data["waves"]:
            wave_num = str(wave["wave_num"])
            workflows = {}
            for task in wave["tasks"]:
                workflows[task["name"]] = {
                    "status": "pending",
                    "worktree_path": None,
                    "branch": None,
                    "iteration": 0,
                    "max_iterations": task.get("max_iterations", 0),
                    "outcome": None,
                    "started_at": None,
                    "finished_at": None,
                    "prompt_file": task.get("prompt_file"),
                    "promise_file": task.get("promise_file"),
                }
            waves_state[wave_num] = {
                "tmux_session": None,
                "status": "pending",
                "workflows": workflows,
            }

        state = {
            "version": 1,
            "session_name": session,
            "base_branch": base_branch,
            "graph_path": str(graph_data.get("_graph_path", "")),
            "started_at": datetime.now(timezone.utc).isoformat(),
            "finished_at": None,
            "status": "running",
            "current_wave": 1,
            "headless_mode": None,
            "waves": waves_state,
        }

        self.save(session, state)
        return state

    def load(self, session: str) -> dict:
        """Load session state from file."""
        path = Path(SESSIONS_DIR) / f"{session}.json"
        if not path.is_file():
            print(f"Error: Session '{session}' not found.", file=sys.stderr)
            sys.exit(1)
        return json.loads(path.read_text())

    def save(self, session: str, state: dict):
        """Atomic write of session state."""
        os.makedirs(SESSIONS_DIR, exist_ok=True)
        target = Path(SESSIONS_DIR) / f"{session}.json"
        fd, tmp_path = tempfile.mkstemp(
            dir=SESSIONS_DIR, suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(state, f, indent=2)
                f.write("\n")
            os.replace(tmp_path, str(target))
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def update_workflow(self, session: str, wave_num: int, task_name: str,
                        updates: dict):
        """Merge updates into a workflow entry and save."""
        state = self.load(session)
        wf = state["waves"][str(wave_num)]["workflows"][task_name]
        wf.update(updates)
        self.save(session, state)

    def list_active(self) -> list:
        """Return list of session states with status == 'running'."""
        sessions_path = Path(SESSIONS_DIR)
        if not sessions_path.is_dir():
            return []
        active = []
        for f in sessions_path.glob("*.json"):
            try:
                state = json.loads(f.read_text())
                if state.get("status") == "running":
                    active.append(state)
            except (json.JSONDecodeError, OSError):
                continue
        return active


# ---------------------------------------------------------------------------
# HeadlessDetector
# ---------------------------------------------------------------------------

class HeadlessDetector:
    """Detect whether the environment supports hooks-based headless mode."""

    def detect(self) -> str:
        """Detect headless mode: 'hooks' or 'wrapper'.

        Checks CONFIG_FILE cache first, then runs a quick test.
        """
        # Check cache
        if Path(CONFIG_FILE).is_file():
            try:
                config = json.loads(Path(CONFIG_FILE).read_text())
                cached = config.get("headless_mode")
                if cached in ("hooks", "wrapper"):
                    return cached
            except (json.JSONDecodeError, OSError):
                pass

        # Run quick test
        mode = self._run_detection_test()

        # Cache result
        self._cache_result(mode)
        return mode

    def _run_detection_test(self) -> str:
        """Run a quick test to determine headless mode support."""
        try:
            test_promise = "FINESSE_HEADLESS_TEST"
            result = subprocess.run(
                ["claude", "-p", f"Output <promise>{test_promise}</promise>"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            # Check if run-log.json was created and shows completion
            run_log_path = Path(".finesse/run-log.json")
            if run_log_path.is_file():
                run_log = json.loads(run_log_path.read_text())
                if run_log.get("outcome") == "completed":
                    return "hooks"
        except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError,
                OSError):
            pass
        return "wrapper"

    def _cache_result(self, mode: str):
        """Cache the detected mode in CONFIG_FILE."""
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        config = {}
        if Path(CONFIG_FILE).is_file():
            try:
                config = json.loads(Path(CONFIG_FILE).read_text())
            except (json.JSONDecodeError, OSError):
                pass
        config["headless_mode"] = mode
        Path(CONFIG_FILE).write_text(json.dumps(config, indent=2) + "\n")

    def get_launch_command(self, mode: str, prompt_text: str,
                           worktree_path: str) -> str:
        """Return the shell command to launch a claude invocation."""
        quoted_path = shlex.quote(worktree_path)
        quoted_prompt = shlex.quote(prompt_text)

        if mode == "hooks":
            return f"cd {quoted_path} && claude -p {quoted_prompt}"

        # Wrapper mode: loop that checks run-log.json outcome
        return (
            f"cd {quoted_path} && "
            f"while true; do "
            f"claude -p {quoted_prompt}; "
            f"outcome=$(python3 -c \"import json; "
            f"d=json.load(open('.finesse/run-log.json')); "
            f"print(d.get('outcome',''))\" 2>/dev/null); "
            f"[ -n \\\"$outcome\\\" ] && break; "
            f"sleep 1; "
            f"done"
        )


# ---------------------------------------------------------------------------
# Main (argparse stub)
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Finesse Wave Execution Orchestrator"
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=None,
        help="Polling interval in seconds (default: 5 or from config)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("start", help="Start wave execution for a session")
    subparsers.add_parser("status", help="Show status of active wave sessions")
    subparsers.add_parser("attach", help="Attach to tmux session for observation")
    subparsers.add_parser("stop", help="Gracefully stop a wave session")
    subparsers.add_parser("cleanup", help="Remove worktrees and tmux sessions")
    subparsers.add_parser("merge", help="Manually trigger merge reconciliation")

    args = parser.parse_args()
    print(f"Subcommand '{args.command}' not yet implemented.")


if __name__ == "__main__":
    main()
