#!/usr/bin/env python3
"""
Finesse Execute Validator - Validates the execution layer components.

Runs structural checks and functional tests against:
  - finesse_execute.py (setup script)
  - stop_hook.py (stop hook)
  - hooks.json (hook registration)
  - Command definitions (finesse-execute.md, cancel-finesse-execute.md)

Exit codes:
  0 = all checks pass
  1 = one or more checks failed
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# Resolve plugin root relative to this script
SCRIPT_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = SCRIPT_DIR.parent
SCRIPTS_DIR = PLUGIN_ROOT / "scripts"
HOOKS_DIR = PLUGIN_ROOT / "hooks"
COMMANDS_DIR = PLUGIN_ROOT / "commands"

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
WARN = "\033[33mWARN\033[0m"

results = []


def record(name: str, passed: bool, detail: str = ""):
    status = "PASS" if passed else "FAIL"
    results.append({"name": name, "passed": passed, "detail": detail})
    icon = PASS if passed else FAIL
    msg = f"  {icon}  {name}"
    if detail and not passed:
        msg += f"\n         {detail}"
    print(msg)


def record_warn(name: str, detail: str = ""):
    results.append({"name": name, "passed": True, "detail": detail, "warn": True})
    print(f"  {WARN}  {name}")
    if detail:
        print(f"         {detail}")


# ─── Structural Checks ───────────────────────────────────────────────────────


def check_files_exist():
    """Verify all required files are present."""
    required = {
        "scripts/finesse_execute.py": SCRIPTS_DIR / "finesse_execute.py",
        "hooks/stop_hook.py": HOOKS_DIR / "stop_hook.py",
        "hooks/hooks.json": HOOKS_DIR / "hooks.json",
        "commands/finesse:finesse-execute.md": COMMANDS_DIR / "finesse-execute.md",
        "commands/cancel-finesse-execute.md": COMMANDS_DIR
        / "cancel-finesse-execute.md",
    }
    for label, path in required.items():
        record(f"File exists: {label}", path.is_file(), f"Missing: {path}")


def check_python_compiles():
    """Verify Python files compile without syntax errors."""
    py_files = [
        SCRIPTS_DIR / "finesse_execute.py",
        HOOKS_DIR / "stop_hook.py",
    ]
    for pf in py_files:
        if not pf.is_file():
            record(f"Compiles: {pf.name}", False, "File not found")
            continue
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(pf)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            record(f"Compiles: {pf.name}", result.returncode == 0, result.stderr)
        except subprocess.TimeoutExpired:
            record(f"Compiles: {pf.name}", False, "Timeout")


def check_hooks_json():
    """Validate hooks.json structure."""
    hooks_file = HOOKS_DIR / "hooks.json"
    if not hooks_file.is_file():
        record("hooks.json: valid JSON", False, "File not found")
        return

    try:
        data = json.loads(hooks_file.read_text())
    except json.JSONDecodeError as e:
        record("hooks.json: valid JSON", False, str(e))
        return

    record("hooks.json: valid JSON", True)

    # Check required structure
    has_hooks = "hooks" in data
    record("hooks.json: has 'hooks' key", has_hooks)

    if has_hooks:
        has_stop = "Stop" in data["hooks"]
        record("hooks.json: has 'Stop' hook", has_stop)

        if has_stop:
            stop_hooks = data["hooks"]["Stop"]
            has_command = (
                len(stop_hooks) > 0
                and "hooks" in stop_hooks[0]
                and len(stop_hooks[0]["hooks"]) > 0
                and "command" in stop_hooks[0]["hooks"][0]
            )
            record("hooks.json: Stop hook has command", has_command)

            if has_command:
                cmd = stop_hooks[0]["hooks"][0]["command"]
                uses_python = "python3" in cmd and "stop_hook.py" in cmd
                record(
                    "hooks.json: Stop command references stop_hook.py",
                    uses_python,
                    f"Got: {cmd}",
                )


def check_command_frontmatter():
    """Validate command markdown files have correct YAML frontmatter."""
    commands = {
        "finesse-execute.md": {
            "required_keys": ["description", "argument-hint", "allowed-tools"],
            "must_contain_tool": "finesse_execute.py",
        },
        "cancel-finesse-execute.md": {
            "required_keys": ["description", "allowed-tools"],
            "must_contain_tool": "loop-state.md",
        },
    }

    for filename, checks in commands.items():
        path = COMMANDS_DIR / filename
        if not path.is_file():
            record(f"Command {filename}: frontmatter", False, "File not found")
            continue

        content = path.read_text()

        # Check starts with ---
        has_frontmatter = content.startswith("---")
        record(f"Command {filename}: has frontmatter", has_frontmatter)

        if not has_frontmatter:
            continue

        # Extract frontmatter
        parts = content.split("---", 2)
        if len(parts) < 3:
            record(f"Command {filename}: frontmatter closes", False, "No closing ---")
            continue

        fm = parts[1]

        for key in checks["required_keys"]:
            has_key = f"{key}:" in fm
            record(f"Command {filename}: has '{key}'", has_key)

        tool_ref = checks["must_contain_tool"]
        has_tool_ref = tool_ref in content
        record(f"Command {filename}: references '{tool_ref}'", has_tool_ref)


def check_no_external_deps():
    """Verify Python scripts only use stdlib modules."""
    allowed_top_level = {
        "argparse",
        "json",
        "os",
        "re",
        "subprocess",
        "sys",
        "tempfile",
        "datetime",
        "pathlib",
    }
    # Also allow from-imports of submodules
    allowed_from = {
        "datetime": {"datetime", "timezone"},
        "pathlib": {"Path"},
    }

    py_files = [
        SCRIPTS_DIR / "finesse_execute.py",
        HOOKS_DIR / "stop_hook.py",
    ]

    for pf in py_files:
        if not pf.is_file():
            continue

        content = pf.read_text()
        imports = re.findall(r"^(?:import|from)\s+(\w+)", content, re.MULTILINE)
        non_stdlib = [i for i in imports if i not in allowed_top_level]
        record(
            f"No external deps: {pf.name}",
            len(non_stdlib) == 0,
            f"Non-stdlib imports: {non_stdlib}" if non_stdlib else "",
        )


def check_state_file_path_consistency():
    """Verify setup and hook agree on state file path."""
    setup = (SCRIPTS_DIR / "finesse_execute.py").read_text()
    hook = (HOOKS_DIR / "stop_hook.py").read_text()

    setup_match = re.search(r'STATE_FILE\s*=\s*"(.+?)"', setup)
    hook_match = re.search(r'STATE_FILE\s*=\s*"(.+?)"', hook)

    if not setup_match or not hook_match:
        record(
            "State file path consistent",
            False,
            "Could not find STATE_FILE in one or both scripts",
        )
        return

    setup_path = setup_match.group(1)
    hook_path = hook_match.group(1)
    record(
        "State file path consistent",
        setup_path == hook_path,
        f"Setup: {setup_path}, Hook: {hook_path}",
    )


def check_run_log_path_consistency():
    """Verify setup and hook agree on run log path."""
    setup = (SCRIPTS_DIR / "finesse_execute.py").read_text()
    hook = (HOOKS_DIR / "stop_hook.py").read_text()

    setup_match = re.search(r'RUN_LOG\s*=\s*"(.+?)"', setup)
    hook_match = re.search(r'RUN_LOG\s*=\s*"(.+?)"', hook)

    if not setup_match or not hook_match:
        record(
            "Run log path consistent",
            False,
            "Could not find RUN_LOG in one or both scripts",
        )
        return

    setup_path = setup_match.group(1)
    hook_path = hook_match.group(1)
    record(
        "Run log path consistent",
        setup_path == hook_path,
        f"Setup: {setup_path}, Hook: {hook_path}",
    )


# ─── Functional Tests ────────────────────────────────────────────────────────


def run_in_tmpdir(func):
    """Decorator to run a test in a temporary directory with a git repo."""
    def wrapper():
        original_dir = os.getcwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            try:
                # Init git repo
                subprocess.run(
                    ["git", "init", "-q"],
                    capture_output=True,
                    timeout=5,
                )
                subprocess.run(
                    ["git", "config", "user.email", "test@test.com"],
                    capture_output=True,
                    timeout=5,
                )
                subprocess.run(
                    ["git", "config", "user.name", "Test"],
                    capture_output=True,
                    timeout=5,
                )
                subprocess.run(
                    ["git", "commit", "--allow-empty", "-m", "init", "-q"],
                    capture_output=True,
                    timeout=5,
                )
                func(tmpdir)
            finally:
                os.chdir(original_dir)

    return wrapper


@run_in_tmpdir
def test_setup_creates_state_file(tmpdir):
    """Setup script creates .finesse/loop-state.md with correct structure."""
    # Create plan files
    os.makedirs("finesse-plans", exist_ok=True)
    Path("finesse-plans/test-plan.md").write_text("Do the thing\n")
    Path("finesse-plans/test-plan-promise.txt").write_text("DONE\n")

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS_DIR / "finesse_execute.py"),
            "--prompt-file",
            "finesse-plans/test-plan.md",
            "--completion-promise-file",
            "finesse-plans/test-plan-promise.txt",
            "--max-iterations",
            "10",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )

    record(
        "Func: setup exits 0",
        result.returncode == 0,
        result.stderr if result.returncode != 0 else "",
    )

    state_exists = Path(".finesse/loop-state.md").is_file()
    record("Func: setup creates state file", state_exists)

    if state_exists:
        content = Path(".finesse/loop-state.md").read_text()
        has_frontmatter = content.startswith("---")
        record("Func: state file has frontmatter", has_frontmatter)

        has_iteration = "iteration: 1" in content
        record("Func: state file starts at iteration 1", has_iteration)

        has_max = "max_iterations: 10" in content
        record("Func: state file has max_iterations", has_max)

        has_promise = '"DONE"' in content
        record("Func: state file has completion promise", has_promise)

        has_prompt = "Do the thing" in content
        record("Func: state file contains prompt text", has_prompt)

        has_plan_name = 'plan_name: "test-plan"' in content
        record("Func: state file has plan name", has_plan_name)

    log_exists = Path(".finesse/run-log.json").is_file()
    record("Func: setup creates run-log.json", log_exists)

    if log_exists:
        try:
            log = json.loads(Path(".finesse/run-log.json").read_text())
            record("Func: run-log is valid JSON", True)

            has_version = log.get("version") == 1
            record("Func: run-log version is 1", has_version)

            has_git = bool(log.get("pre_execution", {}).get("git_hash"))
            record("Func: run-log captured git hash", has_git)

            is_pending = log.get("outcome") is None
            record("Func: run-log outcome is null (pending)", is_pending)

            empty_iters = log.get("iterations") == []
            record("Func: run-log iterations is empty array", empty_iters)
        except json.JSONDecodeError:
            record("Func: run-log is valid JSON", False, "Parse error")


@run_in_tmpdir
def test_setup_rejects_double_start(tmpdir):
    """Setup script refuses to start if a loop is already active."""
    os.makedirs(".finesse", exist_ok=True)
    Path(".finesse/loop-state.md").write_text("---\nactive: true\n---\nold prompt\n")

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS_DIR / "finesse_execute.py"),
            "New task",
            "--max-iterations",
            "5",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )

    record(
        "Func: setup rejects double start",
        result.returncode != 0,
        f"Expected non-zero exit, got {result.returncode}",
    )


@run_in_tmpdir
def test_setup_rejects_empty_prompt(tmpdir):
    """Setup script fails when no prompt is provided."""
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS_DIR / "finesse_execute.py"),
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )

    record(
        "Func: setup rejects empty prompt",
        result.returncode != 0,
        f"Expected non-zero exit, got {result.returncode}",
    )


@run_in_tmpdir
def test_setup_rejects_missing_file(tmpdir):
    """Setup script fails when --prompt-file points to nonexistent file."""
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS_DIR / "finesse_execute.py"),
            "--prompt-file",
            "nonexistent.md",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )

    record(
        "Func: setup rejects missing prompt file",
        result.returncode != 0,
        f"Expected non-zero exit, got {result.returncode}",
    )


@run_in_tmpdir
def test_setup_inline_prompt(tmpdir):
    """Setup script accepts inline prompt text."""
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS_DIR / "finesse_execute.py"),
            "Fix", "the", "auth", "bug",
            "--max-iterations",
            "5",
            "--completion-promise",
            "FIXED",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )

    record(
        "Func: inline prompt accepted",
        result.returncode == 0,
        result.stderr if result.returncode != 0 else "",
    )

    if Path(".finesse/loop-state.md").is_file():
        content = Path(".finesse/loop-state.md").read_text()
        has_prompt = "Fix the auth bug" in content
        record("Func: inline prompt in state file", has_prompt)


@run_in_tmpdir
def test_hook_continues_on_no_promise(tmpdir):
    """Stop hook blocks exit and increments iteration when no promise match."""
    # Create state file at iteration 3
    os.makedirs(".finesse", exist_ok=True)
    Path(".finesse/loop-state.md").write_text(
        '---\nactive: true\niteration: 3\nmax_iterations: 10\n'
        'completion_promise: "DONE"\nstarted_at: "2025-01-01T00:00:00Z"\n'
        'prompt_source: "inline"\npromise_source: "inline"\n'
        'plan_name: "test"\n---\n\nDo the thing\n'
    )
    Path(".finesse/run-log.json").write_text(
        json.dumps(
            {
                "version": 1,
                "plan_name": "test",
                "prompt_source": "inline",
                "promise_source": "inline",
                "max_iterations": 10,
                "completion_promise": "DONE",
                "started_at": "2025-01-01T00:00:00+00:00",
                "finished_at": None,
                "final_iteration": None,
                "outcome": None,
                "pre_execution": {"git_hash": "abc123", "git_dirty": False},
                "iterations": [],
            }
        )
    )

    # Create transcript without promise
    transcript = Path(tmpdir) / "transcript.jsonl"
    transcript.write_text(
        '{"role":"assistant","message":{"content":[{"type":"text","text":"Working on it..."}]}}\n'
    )

    hook_input = json.dumps({"transcript_path": str(transcript)})

    result = subprocess.run(
        [sys.executable, str(HOOKS_DIR / "stop_hook.py")],
        input=hook_input,
        capture_output=True,
        text=True,
        timeout=10,
    )

    record(
        "Func: hook exits 0 on continue",
        result.returncode == 0,
        result.stderr,
    )

    try:
        output = json.loads(result.stdout)
        record(
            "Func: hook returns 'block' decision",
            output.get("decision") == "block",
            f"Got: {output.get('decision')}",
        )
        record(
            "Func: hook re-feeds prompt",
            "Do the thing" in output.get("reason", ""),
            f"Got reason: {output.get('reason', '')[:50]}",
        )
        record(
            "Func: hook system msg has iteration 4",
            "iteration 4" in output.get("systemMessage", ""),
            f"Got: {output.get('systemMessage', '')}",
        )
    except json.JSONDecodeError:
        record("Func: hook returns valid JSON", False, f"Got: {result.stdout[:100]}")

    # Check state file updated
    if Path(".finesse/loop-state.md").is_file():
        content = Path(".finesse/loop-state.md").read_text()
        record("Func: iteration incremented to 4", "iteration: 4" in content)

    # Check telemetry
    if Path(".finesse/run-log.json").is_file():
        log = json.loads(Path(".finesse/run-log.json").read_text())
        has_entry = len(log.get("iterations", [])) == 1
        record("Func: telemetry has 1 iteration entry", has_entry)
        if has_entry:
            entry = log["iterations"][0]
            record(
                "Func: telemetry entry outcome is 'continue'",
                entry.get("outcome") == "continue",
            )


@run_in_tmpdir
def test_hook_detects_promise(tmpdir):
    """Stop hook allows exit when promise is matched."""
    os.makedirs(".finesse", exist_ok=True)
    Path(".finesse/loop-state.md").write_text(
        '---\nactive: true\niteration: 5\nmax_iterations: 10\n'
        'completion_promise: "ALL TESTS PASS"\nstarted_at: "2025-01-01T00:00:00Z"\n'
        'prompt_source: "inline"\npromise_source: "inline"\n'
        'plan_name: "test"\n---\n\nFix the tests\n'
    )
    Path(".finesse/run-log.json").write_text(
        json.dumps(
            {
                "version": 1,
                "plan_name": "test",
                "prompt_source": "inline",
                "promise_source": "inline",
                "max_iterations": 10,
                "completion_promise": "ALL TESTS PASS",
                "started_at": "2025-01-01T00:00:00+00:00",
                "finished_at": None,
                "final_iteration": None,
                "outcome": None,
                "pre_execution": {"git_hash": "abc123", "git_dirty": False},
                "iterations": [],
            }
        )
    )

    transcript = Path(tmpdir) / "transcript.jsonl"
    transcript.write_text(
        '{"role":"assistant","message":{"content":[{"type":"text","text":"Fixed! <promise>ALL TESTS PASS</promise>"}]}}\n'
    )

    hook_input = json.dumps({"transcript_path": str(transcript)})

    result = subprocess.run(
        [sys.executable, str(HOOKS_DIR / "stop_hook.py")],
        input=hook_input,
        capture_output=True,
        text=True,
        timeout=10,
    )

    record("Func: hook exits 0 on promise match", result.returncode == 0)

    # Should NOT output block JSON (empty stdout or non-block)
    has_no_block = "block" not in result.stdout
    record("Func: hook does not block on promise match", has_no_block)

    # State file should be removed
    state_removed = not Path(".finesse/loop-state.md").is_file()
    record("Func: state file removed on completion", state_removed)

    # Telemetry should mark completion
    if Path(".finesse/run-log.json").is_file():
        log = json.loads(Path(".finesse/run-log.json").read_text())
        record(
            "Func: telemetry outcome is 'completed'",
            log.get("outcome") == "completed",
        )
        record(
            "Func: telemetry final_iteration is 5",
            log.get("final_iteration") == 5,
        )
        record(
            "Func: telemetry finished_at is set",
            log.get("finished_at") is not None,
        )


@run_in_tmpdir
def test_hook_stops_at_max_iterations(tmpdir):
    """Stop hook allows exit when max iterations reached."""
    os.makedirs(".finesse", exist_ok=True)
    Path(".finesse/loop-state.md").write_text(
        '---\nactive: true\niteration: 10\nmax_iterations: 10\n'
        'completion_promise: "DONE"\nstarted_at: "2025-01-01T00:00:00Z"\n'
        'prompt_source: "inline"\npromise_source: "inline"\n'
        'plan_name: "test"\n---\n\nDo the thing\n'
    )
    Path(".finesse/run-log.json").write_text(
        json.dumps(
            {
                "version": 1,
                "plan_name": "test",
                "iterations": [],
                "finished_at": None,
                "final_iteration": None,
                "outcome": None,
            }
        )
    )

    transcript = Path(tmpdir) / "transcript.jsonl"
    transcript.write_text(
        '{"role":"assistant","message":{"content":[{"type":"text","text":"Still working..."}]}}\n'
    )

    hook_input = json.dumps({"transcript_path": str(transcript)})

    result = subprocess.run(
        [sys.executable, str(HOOKS_DIR / "stop_hook.py")],
        input=hook_input,
        capture_output=True,
        text=True,
        timeout=10,
    )

    record("Func: hook exits 0 at max iterations", result.returncode == 0)

    has_no_block = "block" not in result.stdout
    record("Func: hook does not block at max iterations", has_no_block)

    state_removed = not Path(".finesse/loop-state.md").is_file()
    record("Func: state file removed at max iterations", state_removed)

    if Path(".finesse/run-log.json").is_file():
        log = json.loads(Path(".finesse/run-log.json").read_text())
        record(
            "Func: telemetry outcome is 'max_iterations'",
            log.get("outcome") == "max_iterations",
        )


@run_in_tmpdir
def test_hook_noop_when_no_state(tmpdir):
    """Stop hook is a no-op when no state file exists."""
    result = subprocess.run(
        [sys.executable, str(HOOKS_DIR / "stop_hook.py")],
        input="{}",
        capture_output=True,
        text=True,
        timeout=10,
    )

    record("Func: hook exits 0 with no state file", result.returncode == 0)
    record(
        "Func: hook outputs nothing with no state file",
        result.stdout.strip() == "",
        f"Got: {result.stdout[:50]}" if result.stdout.strip() else "",
    )


# ─── Runner ──────────────────────────────────────────────────────────────────


def main():
    print("")
    print("Finesse Execute - Validation Suite")
    print("=" * 50)

    print("")
    print("Structural Checks")
    print("-" * 50)
    check_files_exist()
    check_python_compiles()
    check_hooks_json()
    check_command_frontmatter()
    check_no_external_deps()
    check_state_file_path_consistency()
    check_run_log_path_consistency()

    print("")
    print("Functional Tests")
    print("-" * 50)
    test_setup_creates_state_file()
    test_setup_rejects_double_start()
    test_setup_rejects_empty_prompt()
    test_setup_rejects_missing_file()
    test_setup_inline_prompt()
    test_hook_continues_on_no_promise()
    test_hook_detects_promise()
    test_hook_stops_at_max_iterations()
    test_hook_noop_when_no_state()

    # Summary
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed
    warnings = sum(1 for r in results if r.get("warn"))

    print("")
    print("=" * 50)
    if failed == 0:
        print(f"{PASS}  All {total} checks passed.")
    else:
        print(f"{FAIL}  {failed}/{total} checks failed.")

    if warnings > 0:
        print(f"{WARN}  {warnings} warnings.")

    print("")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()