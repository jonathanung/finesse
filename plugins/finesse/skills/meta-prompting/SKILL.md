---
description: "Guide for constructing high-quality ralph-loop prompts that converge instead of thrashing"
---

# Ralph-Loop Prompt Construction

When drafting a ralph-loop prompt via Finesse, follow these rules. A ralph-loop prompt is NOT a conversation — it's a specification for an autonomous agent that re-reads it from scratch on every iteration with zero memory.

## The 10 Mandatory Attributes

Every prompt you produce MUST have all 10. If any are missing, the validation agents will reject it.

### 1. Binary Completion Criteria
Every requirement must be checkable by running a command. If the agent can't programmatically verify success, it can't know when to stop.
- YES: "All tests pass", "Coverage > 80%", "No linter errors", "API returns 200 for GET /users"
- NO: "Code is clean", "Make it good", "Properly structured"

### 2. Explicit Completion Signal
The prompt must state exactly what to output and when:
"Output `<promise>COMPLETE</promise>` when ALL of the following are true: [list]."
Never leave this implicit.

### 3. Self-Diagnosing Failure Instructions
The agent WILL get stuck. The prompt must say what to do when stuck:
"If stuck on the same error for 3+ attempts, step back, read the error trace fully, and try an alternative approach. If blocked for N+ iterations, document what's blocking progress and output `<promise>BLOCKED</promise>`."

### 4. Ordered Phases
"Build auth, then products, then cart" gives clear progression. A flat list of 20 unordered requirements is ambiguous about what to tackle next when the agent has no memory of what it was planning.

### 5. Verification Commands Baked In
Don't assume the agent will figure out how to check its work:
"After each change, run `npm test` and `npm run lint`. If either fails, fix before moving on."

### 6. Guardrails Against Failure Modes
Explicit "Do NOT" rules based on known pitfalls:
- "Do NOT rewrite files from scratch. Make targeted edits."
- "Do NOT delete existing tests to make the suite pass."
- "Read the actual error message before attempting a fix."
- "Do NOT add unnecessary abstractions or extra files."

Note: Git commit and push rules are configured per-plan during Plan Construction — see Git Configuration Rules section below.

### 7. Scoped Context
Tell the agent which files matter and which to leave alone:
"The relevant files are `src/api/`, `src/models/`, and `tests/api/`. Do not modify anything in `src/ui/`."

### 8. Cold Start Paragraph
Since the agent re-reads the prompt fresh each iteration:
"You are iterating on [project]. Check the current state of tests and code before doing anything. Determine what has already been completed and what remains."

### 9. Conservative Iteration Limit
If the task can't converge in 25 iterations, it should have been decomposed during the Scope Analysis phase. If you reach plan construction with an estimate over 25, revisit scope analysis. Refer to the iteration count table in the **task-workflows** skill for specific guidance by task type and scope.

### 10. Zero Ambiguity About "Done"
No room for the agent to convince itself it's done when it isn't. Include: "Do not output the completion promise unless every criterion is met. Do not lie even if you think you should exit."

## Template

```
You are iterating on [PROJECT]. Before doing anything, check the current
state: run tests, read recent git log, identify what's done vs remaining.

[If subagent instructions opted in: include ## Subagent Instructions section here. See Subagent Configuration section.]

## Requirements (in order)
Phase 1: [specific deliverable]
  - [verifiable criterion]
  - [verifiable criterion]
  Verify: [exact command to run]
  [If subagent eligible: include [Subagent opportunity] annotation here. See Subagent Configuration section.]

Phase 2: [specific deliverable]
  - [verifiable criterion]
  - [verifiable criterion]
  Verify: [exact command to run]
  [If subagent eligible: include [Subagent opportunity] annotation here. See Subagent Configuration section.]

## Rules
- Run [test command] after every change. Fix failures before moving on.
- Do NOT rewrite files from scratch. Make targeted edits.
- Do NOT delete existing tests to make a suite pass.
- [Git rules — include checkpoint and push rules based on user's git configuration. See Git Configuration Rules section.]
- Do NOT add unnecessary abstractions or extra files.
- Only modify files in [scoped directories].
- Read actual error messages before attempting fixes.
- If stuck on the same error for 3+ attempts, try an alternative approach.
- If unable to make progress after [N] iterations, document blockers and
  output <promise>BLOCKED</promise>.

## Completion
When ALL phases are complete and ALL verification commands pass cleanly,
output <promise>[EXACT_TEXT]</promise>. This must be unequivocally true.
Do not output the completion promise unless every criterion is met.
```

## File Output Format

When the plan is accepted, the prompt you construct is written to `ralph-plans/<name>.md` as a **prompt-only file**. This means:

- The file must contain ONLY the prompt text — no metadata, no YAML frontmatter, no markdown headers describing the plan
- The file starts directly with the cold start paragraph (e.g., "You are iterating on...")
- The file is referenced via `$(cat ralph-plans/<name>.md)` in the ralph-loop command
- Metadata (task type, context, approach, rationale) goes in a separate `ralph-plans/<name>-plan.md` file
- The completion promise text goes in `ralph-plans/<name>-promise.txt`

Keep this in mind when constructing the prompt: everything you write using the template above becomes the content of the prompt-only file. Do not mix in non-prompt content.

Write every prompt like a QA spec for a contractor you cannot talk to until the job is done. Every ambiguity is a potential infinite loop.

## Git Configuration Rules

During Plan Construction, the user is always prompted about git usage. Based on their answers, include the following rules in the prompt's `## Rules` section.

### No checkpointing selected

```
- Do NOT make git commits.
- Do NOT push to remote repositories.
```

### Checkpointing enabled, no push

The checkpoint rule varies by the user's chosen granularity:

**After each phase:**
```
- After completing each phase and verifying it passes, create a git commit with a descriptive message referencing the completed phase.
- Do NOT push to remote repositories.
```

**After each change:**
```
- After each logical unit of work, create a git commit with a descriptive message describing the change.
- Do NOT push to remote repositories.
```

**Custom:**
Use the user's verbatim description as the checkpoint rule, plus:
```
- Do NOT push to remote repositories.
```

### Checkpointing enabled + push

The checkpoint rule (same granularity variants as above) plus a push rule instead of the prohibition:

**After each phase:**
```
- After completing each phase and verifying it passes, create a git commit with a descriptive message referencing the completed phase.
- Push commits to the remote repository after committing.
```

**After each change:**
```
- After each logical unit of work, create a git commit with a descriptive message describing the change.
- Push commits to the remote repository after committing.
```

**Custom:**
Use the user's verbatim description as the checkpoint rule, plus:
```
- Push commits to the remote repository after committing.
```

## Subagent Configuration

During Plan Construction, the user is optionally offered subagent instructions for phases where parallel execution would improve efficiency. Based on the user's choice, include or omit the following sections in the generated prompt.

### Subagent Eligibility Heuristics

1. **Independent subtasks**: Phase contains work on separate file sets with no shared writes. Recommended subagent type: `general-purpose`.
2. **Parallel verification**: Phase's verification commands can run alongside next phase's work without gating it. Recommended subagent type: `Bash`.
3. **Exploration benefit**: Phase touches unfamiliar code that benefits from dedicated investigation. Recommended subagent type: `Explore`.

A phase is subagent-eligible if it matches at least one heuristic.

### Subagent Section Format

When the user opts in to subagent instructions, include the following section in the generated prompt after the cold start paragraph and before `## Requirements`:

```
## Subagent Instructions

You may use the Task tool to spawn subagents for parallel work. Follow these guidelines:

### Available Subagent Types

- **Bash**: Run test suites, linting, and verification commands in parallel with continued work.
- **Explore**: Investigate unfamiliar code, research patterns, and trace execution flows.
- **general-purpose**: Perform file modifications on independent, non-overlapping file sets.

### Guardrails

- Run at most 2 concurrent subagents at a time.
- Subagents must NOT make git commits or push to remote repositories.
- Subagents must NOT modify files outside their assigned scope.
- Wait for all subagent results before marking a phase complete.
- If a subagent fails, retry once. If it fails again, do the work yourself.
- Provide clear, scoped instructions when spawning a subagent — include specific file paths and expected outcomes.
```

### Per-Phase Annotation Format

For each subagent-eligible phase, add an annotation on a new line after the phase's `Verify:` line, indented to match the phase content. Use this format:

```
[Subagent opportunity]: <description of what to parallelize>, using <subagent_type> subagent. <why it's safe>.
```

Example:

```
Phase 2: Implement authentication endpoint
  - Add JWT validation middleware to src/middleware/auth.ts
  - Create /api/auth route handler in src/routes/auth.ts
  Verify: npm test -- --grep "auth"
  [Subagent opportunity]: Spawn a Bash subagent to run the full test suite while beginning Phase 3. Phase 3 modifies different files (src/routes/users.ts) so there is no write conflict.
```

### No Subagent Instructions Selected

If the user declines subagent instructions, omit the `## Subagent Instructions` section and all `[Subagent opportunity]` annotations entirely. The prompt is generated without any subagent content.

## Exploration Cache Schema

Finesse persists codebase exploration findings across sessions using a JSON cache stored at `.finesse/exploration-cache.json`. This section defines the schema, staleness model, and merge rules that all cache operations reference.

### Cache File Schema (`.finesse/exploration-cache.json`)

```json
{
  "version": 1,
  "baseline": {
    "commit_hash": "<git rev-parse HEAD when baseline was last confirmed>",
    "last_confirmed": "<ISO 8601 timestamp>",
    "file_structure_patterns": ["<pattern descriptions>"],
    "test_framework": "<framework name and conventions>",
    "naming_conventions": ["<convention descriptions>"],
    "architecture_style": "<description>",
    "key_directories": {
      "<directory_path>": "<responsibility description>"
    }
  },
  "entries": {
    "<directory_scope>:<keyword>": {
      "summary": "<1-2 sentence finding>",
      "referenced_files": ["<file paths this finding depends on>"],
      "keywords": ["<searchable keywords>"],
      "directory_scope": "<primary directory this entry covers>",
      "last_confirmed": "<ISO 8601 timestamp>",
      "commit_hash": "<git commit hash when entry was confirmed>"
    }
  }
}
```

### Configuration File Schema (`.finesse/config.json`)

```json
{
  "cache_enabled": true,
  "staleness_threshold": 50
}
```

### Index Key Format

Cache entry keys use the format `<directory_scope>:<keyword>` (e.g., `src/auth:jwt-validation`, `lib/models:active-record-patterns`). The directory scope is the primary directory the finding covers, and the keyword is a descriptive tag for the finding.

### Staleness Model

An entry is **stale** if any file in its `referenced_files` list appears in `git diff --name-only <entry.commit_hash>..HEAD`. Stale entries are removed during cache loading before any cached context is used.

The **baseline** is stale if the diff since `baseline.commit_hash` exceeds the `staleness_threshold` number of files (default: 50). A stale baseline triggers a full cache miss — the entire cache is discarded and full exploration runs.

### Merge Rules

- New entries with existing keys **overwrite** old entries.
- New entries with new keys are **additive** (appended to the cache).
- The baseline is **overwritten wholesale** on full exploration (cache miss).
- Stale entries are **removed** on cache load, before any merge occurs.

## Multi-Workflow Output Format

When a task is decomposed into multiple sub-workflows during Scope Analysis, the output uses a nested directory structure instead of the flat format.

### Directory Structure

```
ralph-plans/<session-name>/
  execution-graph.md
  wave-1/
    <sub-task-name>/
      prompt.md
      promise.txt
      plan.md
  wave-2/
    <sub-task-name>/
      prompt.md
      promise.txt
      plan.md
```

### Naming Conventions

- **Session name**: kebab-case derived from original task description (e.g., `build-todo-api-with-auth`)
- **Sub-task name**: kebab-case from decomposition proposal names (e.g., `auth-endpoints`, `todo-crud`)

### Execution Graph Format

The `execution-graph.md` file contains:

**Overview section:**
- Original task description
- Number of sub-workflows
- Number of waves
- Total estimated iterations across all sub-workflows

**Wave structure tables** — for each wave:

| Name | Type | Est. Iterations | Scope | Dependencies |
|---|---|---|---|---|
| sub-task-name | feature | 12 | src/auth/, tests/auth/ | none |

**Dependency rationale section:**
For each dependency, explain whether it is file-based or logical and why.

**Per-wave commands section:**
Full ralph-loop command for each sub-task:
```
## Wave 1 (run in parallel)
/ralph-loop:ralph-loop $(cat ralph-plans/<session>/wave-1/<task>/prompt.md) --completion-promise "$(cat ralph-plans/<session>/wave-1/<task>/promise.txt)" --max-iterations=<N>

## Wave 2 (run after Wave 1 completes)
/ralph-loop:ralph-loop $(cat ralph-plans/<session>/wave-2/<task>/prompt.md) --completion-promise "$(cat ralph-plans/<session>/wave-2/<task>/promise.txt)" --max-iterations=<N>
```

### Per-Sub-Workflow Prompt Rules

1. Each `prompt.md` must be fully self-contained (valid as a `$(cat ...)` argument)
2. Must include its own cold start paragraph specific to its scope
3. Must reference only files in its scope
4. Must include its own verification commands, guardrails, and completion criteria
5. Wave 2+ prompts can reference wave 1 outputs as existing state but must NOT assume they will be built

### Mandatory Attributes Per Sub-Workflow

The 10 Mandatory Attributes apply to EACH sub-workflow prompt individually. Every sub-workflow prompt must independently satisfy all 10 attributes.

### Single-Workflow Backward Compatibility

When decomposition does not occur, use the existing flat format:
- `ralph-plans/<name>.md` — prompt text only
- `ralph-plans/<name>-promise.txt` — promise text only
- `ralph-plans/<name>-plan.md` — metadata

Never mix the flat and nested formats.
