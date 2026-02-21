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
# Helpers
# ---------------------------------------------------------------------------

def _kill_session_claude_processes(state: dict):
    """Best-effort cleanup of orphaned claude processes in session worktrees.

    After tmux sessions are killed, claude processes may survive if they
    don't respond to SIGHUP. This finds any claude processes whose cwd
    matches a session worktree and sends SIGTERM.

    Linux-only (/proc-based). On macOS, tmux SIGHUP is typically sufficient.
    """
    worktree_paths = set()
    for wave_data in state.get("waves", {}).values():
        for wf in wave_data.get("workflows", {}).values():
            path = wf.get("worktree_path")
            if path:
                worktree_paths.add(os.path.realpath(path))

    if not worktree_paths or not Path("/proc").is_dir():
        return

    try:
        result = subprocess.run(
            ["pgrep", "-x", "claude"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return

        for pid_str in result.stdout.strip().split("\n"):
            pid_str = pid_str.strip()
            if not pid_str:
                continue
            try:
                pid = int(pid_str)
                cwd = os.path.realpath(os.readlink(f"/proc/{pid}/cwd"))
                if cwd in worktree_paths:
                    os.kill(pid, signal.SIGTERM)
            except (OSError, ValueError):
                continue
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass


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
                # Find which task this command belongs to using path segment match
                # to avoid substring collisions (e.g., "auth" matching "auth-endpoints")
                for task in current_tasks:
                    if f"/{task['name']}/" in prompt_file or prompt_file.endswith(f"/{task['name']}/prompt.md"):
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
                    if f"/{task['name']}/" in promise_file or promise_file.endswith(f"/{task['name']}/promise.txt"):
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
                    if task["prompt_file"] and (f"/{task['name']}/" in line or task["name"] == line.strip()):
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

    def create(self, session: str, task_name: str, base_branch: str) -> tuple:
        """Create a git worktree for a task.

        Returns (worktree_path: str, branch: str) — the absolute worktree path
        and the actual branch name used (which may have a collision suffix).
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

        return (str(Path(worktree_path).resolve()), branch)

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

        wt_result = subprocess.run(
            ["git", "worktree", "remove", worktree_path, "--force"],
            capture_output=True,
            text=True,
        )
        if wt_result.returncode != 0:
            print(
                f"Warning: Failed to remove worktree {worktree_path}: "
                f"{wt_result.stderr.strip()}",
                file=sys.stderr,
            )

        if delete_branch and branch:
            br_result = subprocess.run(
                ["git", "branch", "-D", branch],
                capture_output=True,
                text=True,
            )
            if br_result.returncode != 0:
                print(
                    f"Warning: Failed to delete branch {branch}: "
                    f"{br_result.stderr.strip()}",
                    file=sys.stderr,
                )

    def merge(self, branch: str, base_branch: str) -> tuple:
        """Merge a branch into the base branch.

        Returns (success: bool, conflict_files: str, conflict_diff: str).
        """
        checkout_result = subprocess.run(
            ["git", "checkout", base_branch],
            capture_output=True,
            text=True,
        )
        if checkout_result.returncode != 0:
            return (False, f"Failed to checkout {base_branch}: {checkout_result.stderr.strip()}", "")

        result = subprocess.run(
            ["git", "merge", branch, "--no-edit"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return (True, "", "")

        # Merge conflict — capture diff before aborting (shows conflict markers)
        diff_result = subprocess.run(
            ["git", "diff"],
            capture_output=True,
            text=True,
        )
        conflict_diff = diff_result.stdout.strip()

        # Get conflicted file list
        conflict_result = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=U"],
            capture_output=True,
            text=True,
        )
        conflict_files = conflict_result.stdout.strip()

        # Abort the failed merge
        subprocess.run(
            ["git", "merge", "--abort"],
            capture_output=True,
            text=True,
        )

        return (False, conflict_files, conflict_diff)

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
                 is_first: bool = True) -> bool:
        """Add a pane to a tmux session and run a command in it.

        Returns True if the pane was created and command sent successfully.
        """
        if is_first:
            result = subprocess.run(
                ["tmux", "send-keys", "-t", session, command, "Enter"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(
                    f"Warning: Failed to send command to tmux session {session}: "
                    f"{result.stderr.strip()}",
                    file=sys.stderr,
                )
                return False
        else:
            split_result = subprocess.run(
                ["tmux", "split-window", "-t", session, "-h"],
                capture_output=True,
                text=True,
            )
            if split_result.returncode != 0:
                print(
                    f"Warning: Failed to split tmux pane in {session}: "
                    f"{split_result.stderr.strip()}",
                    file=sys.stderr,
                )
                return False
            result = subprocess.run(
                ["tmux", "send-keys", "-t", session, command, "Enter"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(
                    f"Warning: Failed to send command to tmux pane in {session}: "
                    f"{result.stderr.strip()}",
                    file=sys.stderr,
                )
                return False
        return True

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

        Checks CONFIG_FILE cache first. If no cache, defaults to 'hooks' mode
        to avoid spending API credits on a detection test. The WaveOrchestrator
        verifies hooks are working after launching the first wave and falls
        back to 'wrapper' mode automatically if they aren't.
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

        # Default to hooks — verified on first wave launch
        mode = "hooks"
        self._cache_result(mode)
        return mode

    def fallback_to_wrapper(self) -> str:
        """Switch to wrapper mode and update cache. Returns 'wrapper'."""
        self._cache_result("wrapper")
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
        """Return the shell command to launch a claude invocation.

        Writes the prompt to a temp file to avoid ARG_MAX limits on large prompts.
        """
        quoted_path = shlex.quote(worktree_path)

        # Write prompt to a temp file in the worktree to avoid ARG_MAX limits
        prompt_file = Path(worktree_path) / ".finesse" / "prompt-input.txt"
        os.makedirs(prompt_file.parent, exist_ok=True)
        prompt_file.write_text(prompt_text)
        quoted_prompt_file = shlex.quote(str(prompt_file))

        if mode == "hooks":
            return f"cd {quoted_path} && claude -p \"$(cat {quoted_prompt_file})\""

        # Wrapper mode: loop that checks run-log.json outcome
        return (
            f"cd {quoted_path} && "
            f"while true; do "
            f"claude -p \"$(cat {quoted_prompt_file})\"; "
            f"outcome=$(python3 -c \"import json; "
            f"d=json.load(open('.finesse/run-log.json')); "
            f"print(d.get('outcome',''))\" 2>/dev/null); "
            f"[ -n \\\"$outcome\\\" ] && break; "
            f"sleep 1; "
            f"done"
        )


# ---------------------------------------------------------------------------
# WaveOrchestrator
# ---------------------------------------------------------------------------

def _estimate_cost(est_iterations: int) -> str:
    """Estimate cost range for a given iteration count (low-moderate pressure)."""
    if est_iterations < 5:
        return "Under $5"
    if est_iterations <= 8:
        return "Under $5"
    if est_iterations <= 15:
        return "$5-20"
    if est_iterations <= 22:
        return "$20-50"
    return "$50-100+"


class WaveOrchestrator:
    """Orchestrate wave-based execution of multi-workflow plans."""

    def __init__(self, session: str, graph_path: str = None):
        self.session = session
        self.graph_parser = GraphParser()
        self.worktree_mgr = WorktreeManager()
        self.tmux_mgr = TmuxManager()
        self.session_tracker = SessionTracker()
        self.headless_detector = HeadlessDetector()
        self._shutdown = False
        self.graph_data = None
        self.total_waves = 0

        if graph_path:
            self.graph_data = self.graph_parser.parse(graph_path)
            self.graph_data["_graph_path"] = graph_path
            self.total_waves = self.graph_data["overview"]["total_waves"]

            # Determine base branch from current HEAD
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
            )
            self.base_branch = result.stdout.strip() if result.returncode == 0 else "main"

            self.state = self.session_tracker.create(
                session, self.graph_data, self.base_branch
            )
        else:
            self.state = self.session_tracker.load(session)
            self.base_branch = self.state.get("base_branch", "main")
            self.total_waves = len(self.state.get("waves", {}))

        # Register signal handler
        signal.signal(signal.SIGINT, self._handle_sigint)

    def _handle_sigint(self, signum, frame):
        """Handle SIGINT by setting shutdown flag and cleaning up tmux sessions."""
        print("\nReceived interrupt. Finishing current operations...")
        self._shutdown = True
        # Kill tmux sessions
        for wave_key, wave_data in self.state.get("waves", {}).items():
            tmux_name = wave_data.get("tmux_session")
            if tmux_name:
                self.tmux_mgr.kill_session(tmux_name)
        # Kill any orphaned claude processes that survived tmux SIGHUP
        _kill_session_claude_processes(self.state)

    def dry_run(self) -> bool:
        """Display execution plan and ask for confirmation. Returns True if user confirms."""
        overview = self.graph_data["overview"]
        waves = self.graph_data["waves"]

        print(f"\n=== Finesse Wave Execution: {self.session} ===\n")

        total_low = 0
        total_high = 0

        for wave in waves:
            n_tasks = len(wave["tasks"])
            print(f"Wave {wave['wave_num']} ({n_tasks} workflow{'s' if n_tasks != 1 else ''}):")
            wave_iters = 0
            for task in wave["tasks"]:
                est = task.get("est_iterations", 0)
                wave_iters += est
                print(f"  {task['name']}: ~{est} iterations")

            cost_str = _estimate_cost(wave_iters)
            print(f"  Estimated cost: {cost_str}")
            # Parse cost range for totals
            cost_str_clean = cost_str.replace("Under ", "").replace("$", "").replace("+", "")
            if "-" in cost_str_clean:
                parts = cost_str_clean.split("-")
                total_low += int(parts[0])
                total_high += int(parts[1])
            else:
                val = int(cost_str_clean) if cost_str_clean.isdigit() else 5
                total_low += max(1, val // 2)
                total_high += val
            print()

        print(f"Total: {overview['total_workflows']} workflows across {overview['total_waves']} waves")
        print(f"Estimated total cost: ${total_low}-{total_high}")
        print("Note: Each worktree is a full working copy of the repository.\n")

        tmux_names = [
            f"finesse-{self.session}-w{w['wave_num']}" for w in waves
        ]
        print(f"tmux sessions: {', '.join(tmux_names)}")
        print(f"Worktree paths: {WORKTREES_DIR}/{self.session}/...\n")

        try:
            answer = input("Proceed? [y/N] ").strip()
        except EOFError:
            return False
        return answer.lower() == "y"

    def run_wave(self, wave_num: int):
        """Launch all tasks in a wave."""
        wave_key = str(wave_num)
        wave_data = None
        for w in self.graph_data["waves"]:
            if w["wave_num"] == wave_num:
                wave_data = w
                break

        if not wave_data:
            print(f"Error: Wave {wave_num} not found.", file=sys.stderr)
            return

        # Get launchable tasks (check dependencies for wave > 1)
        if wave_num > 1:
            launchable = self.check_dependencies(wave_num)
        else:
            launchable = wave_data["tasks"]

        if not launchable:
            print(f"No launchable tasks in wave {wave_num}.")
            return

        # Detect headless mode
        mode = self.headless_detector.detect()
        self.state["headless_mode"] = mode

        # Create tmux session
        tmux_name = self.tmux_mgr.create_session(
            f"finesse-{self.session}-w{wave_num}"
        )
        self.state["waves"][wave_key]["tmux_session"] = tmux_name
        self.state["waves"][wave_key]["status"] = "running"
        self.state["current_wave"] = wave_num

        is_first_pane = True
        for task in launchable:
            if self._shutdown:
                print("Shutdown requested. Skipping remaining tasks.")
                break

            task_name = task["name"]
            print(f"  Launching: {task_name}")

            # Create worktree
            worktree_path, branch = self.worktree_mgr.create(
                self.session, task_name, self.base_branch
            )
            self.state["waves"][wave_key]["workflows"][task_name].update({
                "status": "running",
                "worktree_path": worktree_path,
                "branch": branch,
                "started_at": datetime.now(timezone.utc).isoformat(),
            })

            # Set up state in worktree
            if not self.setup_worktree_state(worktree_path, task):
                print(f"  Failed to set up state for {task_name}. Skipping.")
                self.state["waves"][wave_key]["workflows"][task_name]["status"] = "failed"
                self.state["waves"][wave_key]["workflows"][task_name]["outcome"] = "setup_failed"
                continue

            # Read prompt for launch command
            prompt_file = task.get("prompt_file", "")
            if prompt_file and Path(prompt_file).is_file():
                prompt_text = Path(prompt_file).read_text().strip()
            else:
                prompt_text = f"Execute task: {task_name}"

            # Launch in tmux pane
            launch_cmd = self.headless_detector.get_launch_command(
                mode, prompt_text, worktree_path
            )
            self.tmux_mgr.add_pane(
                tmux_name, launch_cmd, pane_name=task_name,
                is_first=is_first_pane,
            )
            is_first_pane = False

        # Save state
        self.session_tracker.save(self.session, self.state)

        # Verify hooks mode on first use — fall back to wrapper if hooks aren't firing
        if mode == "hooks" and not self._shutdown:
            if not self._verify_hooks_mode(wave_num):
                print("  Hooks mode not responding. Falling back to wrapper mode...")
                mode = self.headless_detector.fallback_to_wrapper()
                self.state["headless_mode"] = mode
                self._relaunch_wave(wave_num, mode)

        print(f"\nWave {wave_num} launched. Attach with: tmux attach -t {self.state['waves'][wave_key].get('tmux_session', tmux_name)}")

    def _verify_hooks_mode(self, wave_num: int, timeout: int = 90) -> bool:
        """Verify hooks mode is working after launching a wave.

        Polls run-log.json files for stop_hook activity (iterations > 0 or
        an outcome). Returns True if any task shows activity within timeout.
        Returns True immediately on shutdown to avoid interference.
        """
        wave_key = str(wave_num)
        workflows = self.state["waves"][wave_key]["workflows"]

        start = time.monotonic()
        while time.monotonic() - start < timeout:
            if self._shutdown:
                return True

            for wf in workflows.values():
                worktree_path = wf.get("worktree_path")
                if not worktree_path:
                    continue
                run_log_path = Path(worktree_path) / ".finesse" / "run-log.json"
                if not run_log_path.is_file():
                    continue
                try:
                    rl = json.loads(run_log_path.read_text())
                    if rl.get("outcome"):
                        return True
                    if rl.get("iterations") and len(rl["iterations"]) > 0:
                        return True
                except (json.JSONDecodeError, OSError):
                    pass

            time.sleep(5)

        return False

    def _relaunch_wave(self, wave_num: int, mode: str):
        """Kill current tmux session for a wave and re-launch tasks in a new mode.

        Reuses existing worktrees — only the tmux session and launch commands change.
        """
        wave_key = str(wave_num)
        wave_data = self.state["waves"][wave_key]

        # Kill current tmux session
        old_tmux = wave_data.get("tmux_session")
        if old_tmux:
            self.tmux_mgr.kill_session(old_tmux)

        # Create new tmux session
        tmux_name = self.tmux_mgr.create_session(
            f"finesse-{self.session}-w{wave_num}"
        )
        wave_data["tmux_session"] = tmux_name

        is_first_pane = True
        for task_name, wf in wave_data["workflows"].items():
            if self._shutdown:
                break
            if wf.get("status") != "running":
                continue

            worktree_path = wf.get("worktree_path")
            if not worktree_path:
                continue

            # Read prompt for launch command
            prompt_file = wf.get("prompt_file", "")
            if prompt_file and Path(prompt_file).is_file():
                prompt_text = Path(prompt_file).read_text().strip()
            else:
                prompt_text = f"Execute task: {task_name}"

            launch_cmd = self.headless_detector.get_launch_command(
                mode, prompt_text, worktree_path
            )
            self.tmux_mgr.add_pane(
                tmux_name, launch_cmd, pane_name=task_name,
                is_first=is_first_pane,
            )
            is_first_pane = False

        self.session_tracker.save(self.session, self.state)

    def setup_worktree_state(self, worktree_path: str, task: dict) -> bool:
        """Set up finesse execution state files in a worktree.

        Returns True if setup succeeded, False otherwise.
        """
        prompt_file = task.get("prompt_file", "")
        promise_file = task.get("promise_file", "")
        max_iterations = task.get("max_iterations", 0)

        cmd = [
            sys.executable,
            str(PLUGIN_ROOT / "scripts" / "finesse_execute.py"),
        ]

        if prompt_file:
            abs_prompt = str(Path(prompt_file).resolve())
            cmd.extend(["--prompt-file", abs_prompt])

        if promise_file:
            abs_promise = str(Path(promise_file).resolve())
            cmd.extend(["--completion-promise-file", abs_promise])

        if max_iterations:
            cmd.extend(["--max-iterations", str(max_iterations)])

        # If no prompt file, provide a minimal inline prompt
        if not prompt_file:
            cmd.append(f"Execute task: {task.get('name', 'unknown')}")

        result = subprocess.run(
            cmd,
            cwd=worktree_path,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(
                f"  Error setting up state for {task.get('name', 'unknown')}: "
                f"{result.stderr.strip()}",
                file=sys.stderr,
            )
            return False
        return True

    def poll_wave(self, wave_num: int, poll_interval: int = None,
                  timeout: int = 14400) -> dict:
        """Poll workflows in a wave until all complete. Returns results dict.

        Args:
            wave_num: Wave number to poll.
            poll_interval: Seconds between polls (default: DEFAULT_POLL_INTERVAL).
            timeout: Maximum seconds to poll before giving up (default: 4 hours).
        """
        if poll_interval is None:
            poll_interval = DEFAULT_POLL_INTERVAL

        wave_key = str(wave_num)
        workflows = self.state["waves"][wave_key]["workflows"]
        start_time = time.monotonic()

        while True:
            if self._shutdown:
                break

            # Timeout check
            elapsed = time.monotonic() - start_time
            if elapsed > timeout:
                print(
                    f"  Polling timeout ({timeout}s) reached for wave {wave_num}.",
                    file=sys.stderr,
                )
                for task_name, wf in workflows.items():
                    if wf["outcome"] is None:
                        wf["outcome"] = "timeout"
                        wf["status"] = "failed"
                        wf["finished_at"] = datetime.now(timezone.utc).isoformat()
                break

            all_done = True
            for task_name, wf in workflows.items():
                if wf["outcome"] is not None:
                    continue

                # Read run-log.json from worktree
                worktree_path = wf.get("worktree_path")
                if not worktree_path:
                    continue

                # Check if worktree still exists
                if not Path(worktree_path).is_dir():
                    print(
                        f"  {task_name}: worktree deleted, marking as failed.",
                        file=sys.stderr,
                    )
                    wf["outcome"] = "worktree_deleted"
                    wf["status"] = "failed"
                    wf["finished_at"] = datetime.now(timezone.utc).isoformat()
                    continue

                run_log_path = Path(worktree_path) / ".finesse" / "run-log.json"
                if not run_log_path.is_file():
                    all_done = False
                    continue

                try:
                    run_log = json.loads(run_log_path.read_text())
                except (json.JSONDecodeError, OSError):
                    all_done = False
                    continue

                outcome = run_log.get("outcome")
                if outcome is not None:
                    wf["outcome"] = outcome
                    wf["finished_at"] = datetime.now(timezone.utc).isoformat()
                    wf["iteration"] = run_log.get("final_iteration", 0)
                    wf["status"] = "completed" if outcome == "completed" else "failed"
                    print(f"  {task_name}: {outcome} (iteration {wf['iteration']})")
                else:
                    all_done = False
                    # Update iteration count from live data
                    wf["iteration"] = len(run_log.get("iterations", []))

            self.session_tracker.save(self.session, self.state)

            if all_done:
                break

            time.sleep(poll_interval)

        return {
            name: {"outcome": wf["outcome"], "iteration": wf["iteration"]}
            for name, wf in workflows.items()
        }

    def reconcile_wave(self, wave_num: int) -> bool:
        """Merge completed workflow branches back into base. Returns True if all succeed."""
        wave_key = str(wave_num)
        workflows = self.state["waves"][wave_key]["workflows"]

        for task_name, wf in workflows.items():
            if wf.get("status") == "failed" or wf.get("status") == "skipped":
                continue
            if wf.get("outcome") != "completed":
                continue

            branch = wf.get("branch", f"finesse/{task_name}")
            print(f"  Merging {branch} into {self.base_branch}...")

            success, conflicts, diff = self.worktree_mgr.merge(branch, self.base_branch)
            if not success:
                print(f"  CONFLICT in {branch}:")
                if conflicts:
                    print(f"    Conflicted files:")
                    for f in conflicts.split("\n"):
                        print(f"      {f}")
                if diff:
                    diff_lines = diff.split("\n")
                    print(f"    Conflict diff (first 100 lines):")
                    for line in diff_lines[:100]:
                        print(f"      {line}")
                    if len(diff_lines) > 100:
                        print(f"      ... ({len(diff_lines) - 100} more lines)")
                wf["merge_status"] = "conflict"
                self.session_tracker.save(self.session, self.state)
                return False

            wf["merge_status"] = "merged"
            print(f"  Merged {branch} successfully.")

        self.session_tracker.save(self.session, self.state)
        return True

    def check_dependencies(self, wave_num: int) -> list:
        """Check task dependencies against prior wave results. Returns launchable tasks."""
        wave_data = None
        for w in self.graph_data["waves"]:
            if w["wave_num"] == wave_num:
                wave_data = w
                break

        if not wave_data:
            return []

        # Build set of completed tasks from prior waves
        completed_tasks = set()
        for wn in range(1, wave_num):
            wk = str(wn)
            if wk in self.state["waves"]:
                for name, wf in self.state["waves"][wk]["workflows"].items():
                    if wf.get("outcome") == "completed":
                        completed_tasks.add(name)

        launchable = []
        for task in wave_data["tasks"]:
            deps_str = task.get("dependencies", "none")
            if deps_str.lower() in ("none", "", "-"):
                launchable.append(task)
                continue

            deps = [d.strip() for d in deps_str.split(",")]
            failed_deps = [d for d in deps if d and d not in completed_tasks]
            if failed_deps:
                print(f"  Skipping {task['name']}: dependencies not met ({', '.join(failed_deps)})")
                wave_key = str(wave_num)
                if task["name"] in self.state["waves"][wave_key]["workflows"]:
                    self.state["waves"][wave_key]["workflows"][task["name"]]["status"] = "skipped"
                    self.state["waves"][wave_key]["workflows"][task["name"]]["outcome"] = "skipped"
            else:
                launchable.append(task)

        return launchable

    def stop(self):
        """Gracefully stop the session."""
        self._shutdown = True
        self.state["status"] = "stopped"
        self.state["finished_at"] = datetime.now(timezone.utc).isoformat()
        self.session_tracker.save(self.session, self.state)


# ---------------------------------------------------------------------------
# Subcommand handlers
# ---------------------------------------------------------------------------

def cmd_start(args):
    """Start wave execution for a session."""
    session = args.session_name
    graph_path = f"finesse-plans/{session}/execution-graph.md"

    if not Path(graph_path).is_file():
        print(
            f"Error: Execution graph not found: {graph_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    orchestrator = WaveOrchestrator(session, graph_path)

    if not orchestrator.dry_run():
        print("Aborted.")
        sys.exit(0)

    for wave_num in range(1, orchestrator.total_waves + 1):
        if orchestrator._shutdown:
            break

        print(f"\n--- Wave {wave_num} ---")
        orchestrator.run_wave(wave_num)

        print(f"\nPolling wave {wave_num}...")
        results = orchestrator.poll_wave(
            wave_num,
            poll_interval=args.poll_interval,
        )

        print(f"\nReconciling wave {wave_num}...")
        if not orchestrator.reconcile_wave(wave_num):
            print(
                f"\nMerge conflicts in wave {wave_num}. "
                f"Resolve manually and run: finesse-waves merge {session}"
            )
            break

    if not orchestrator._shutdown:
        orchestrator.state["status"] = "completed"
        orchestrator.state["finished_at"] = datetime.now(timezone.utc).isoformat()
        orchestrator.session_tracker.save(session, orchestrator.state)
        print("\nWave execution complete.")
    else:
        print("\nWave execution stopped by user.")


def cmd_status(args):
    """Show status of active wave sessions."""
    tracker = SessionTracker()
    active = tracker.list_active()

    if not active:
        print("No active wave sessions.")
        sys.exit(0)

    for state in active:
        session = state["session_name"]
        status = state["status"]
        current_wave = state["current_wave"]
        print(f"\n{session} [{status}] — wave {current_wave}")

        for wave_key, wave_data in state["waves"].items():
            wave_status = wave_data["status"]
            if wave_status in ("running", "completed", "partial"):
                print(f"  Wave {wave_key} ({wave_status}):")
                for task_name, wf in wave_data["workflows"].items():
                    wf_status = wf["status"]
                    iteration = wf.get("iteration", 0)
                    max_iters = wf.get("max_iterations", 0)
                    outcome = wf.get("outcome", "")

                    # Try reading live iteration from worktree run-log
                    worktree_path = wf.get("worktree_path")
                    if worktree_path and wf_status == "running":
                        run_log_path = Path(worktree_path) / ".finesse" / "run-log.json"
                        if run_log_path.is_file():
                            try:
                                rl = json.loads(run_log_path.read_text())
                                iteration = len(rl.get("iterations", []))
                                live_outcome = rl.get("outcome")
                                if live_outcome:
                                    outcome = live_outcome
                            except (json.JSONDecodeError, OSError):
                                pass

                    iter_str = f"iter {iteration}/{max_iters}" if max_iters else f"iter {iteration}"
                    outcome_str = f" -> {outcome}" if outcome else ""
                    print(f"    {task_name}: {wf_status} ({iter_str}){outcome_str}")


def cmd_attach(args):
    """Attach to tmux session for observation."""
    tracker = SessionTracker()
    state = tracker.load(args.session_name)
    current_wave = state["current_wave"]
    wave_key = str(current_wave)

    tmux_name = state["waves"].get(wave_key, {}).get("tmux_session")
    if not tmux_name:
        print(
            f"Error: No tmux session found for wave {current_wave}.",
            file=sys.stderr,
        )
        sys.exit(1)

    tmux_mgr = TmuxManager()
    if not tmux_mgr.session_exists(tmux_name):
        print(f"Error: tmux session '{tmux_name}' does not exist.", file=sys.stderr)
        sys.exit(1)

    tmux_mgr.attach(tmux_name)


def cmd_stop(args):
    """Gracefully stop a wave session."""
    orchestrator = WaveOrchestrator(args.session_name)
    orchestrator.stop()
    print(f"Session {args.session_name} stopped.")


def cmd_cleanup(args):
    """Remove worktrees and tmux sessions for a completed session."""
    session = args.session_name
    tracker = SessionTracker()
    state = tracker.load(session)

    tmux_mgr = TmuxManager()
    worktree_mgr = WorktreeManager()

    # Kill tmux sessions
    for wave_data in state["waves"].values():
        tmux_name = wave_data.get("tmux_session")
        if tmux_name:
            tmux_mgr.kill_session(tmux_name)

    # Kill any orphaned claude processes that survived tmux SIGHUP
    _kill_session_claude_processes(state)

    # Remove worktrees
    worktree_mgr.cleanup_session(session)

    # Remove session file
    Path(f"{SESSIONS_DIR}/{session}.json").unlink(missing_ok=True)
    print(f"Cleaned up session {session}.")


def cmd_merge(args):
    """Manually trigger merge reconciliation."""
    orchestrator = WaveOrchestrator(args.session_name)
    state = orchestrator.session_tracker.load(args.session_name)
    current_wave = state["current_wave"]

    if orchestrator.reconcile_wave(current_wave):
        print(f"Wave {current_wave} merged successfully.")
    else:
        print("Merge conflicts remain. Resolve and retry.")


# ---------------------------------------------------------------------------
# Main
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

    start_parser = subparsers.add_parser(
        "start", help="Start wave execution for a session"
    )
    start_parser.add_argument(
        "session_name", help="Session name (matches finesse-plans/<session>/)"
    )

    subparsers.add_parser(
        "status", help="Show status of active wave sessions"
    )

    attach_parser = subparsers.add_parser(
        "attach", help="Attach to tmux session for observation"
    )
    attach_parser.add_argument(
        "session_name", help="Session name to attach to"
    )

    stop_parser = subparsers.add_parser(
        "stop", help="Gracefully stop a wave session"
    )
    stop_parser.add_argument(
        "session_name", help="Session name to stop"
    )

    cleanup_parser = subparsers.add_parser(
        "cleanup", help="Remove worktrees and tmux sessions"
    )
    cleanup_parser.add_argument(
        "session_name", help="Session name to clean up"
    )

    merge_parser = subparsers.add_parser(
        "merge", help="Manually trigger merge reconciliation"
    )
    merge_parser.add_argument(
        "session_name", help="Session name to merge"
    )

    args = parser.parse_args()

    dispatch = {
        "start": cmd_start,
        "status": cmd_status,
        "attach": cmd_attach,
        "stop": cmd_stop,
        "cleanup": cmd_cleanup,
        "merge": cmd_merge,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
