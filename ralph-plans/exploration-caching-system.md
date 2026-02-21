You are iterating on the Finesse plugin at /workspace/plugins/finesse/. Before doing anything, check the current state: read the files listed below, run grep to verify what has and hasn't been changed, and determine which phases are complete vs. remaining.

The task is to add an exploration caching system that persists key codebase findings across finesse sessions. This involves: (1) defining a cache JSON schema in meta-prompting/SKILL.md, (2) adding cache orchestration instructions to finesse.md, (3) adding cache-aware notes to all 6 exploration phases in task-workflows/SKILL.md, (4) updating finesse-resume.md for cache awareness, (5) updating finesse-help.md documentation, (6) adding .finesse/ to .gitignore, and (7) bumping version to 0.6.0.

Files to check on cold start:
- /workspace/.gitignore
- /workspace/plugins/finesse/skills/meta-prompting/SKILL.md
- /workspace/plugins/finesse/commands/finesse.md
- /workspace/plugins/finesse/skills/task-workflows/SKILL.md
- /workspace/plugins/finesse/commands/finesse-resume.md
- /workspace/plugins/finesse/commands/finesse-help.md
- /workspace/plugins/finesse/.claude-plugin/plugin.json
- /workspace/.claude-plugin/marketplace.json
- /workspace/plugins/finesse/commands/finesse-version.md

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

## Requirements (in order)

Phase 1: Add `.finesse/` to `.gitignore`
  - Open `/workspace/.gitignore` (currently contains `.claude/` and `ralph-plans/`)
  - Add `.finesse/` as a new line
  - The file should have exactly 3 lines after this change
  Verify: `grep ".finesse/" .gitignore` returns a match

Phase 2: Define Exploration Cache Schema in `meta-prompting/SKILL.md`
  - Open `/workspace/plugins/finesse/skills/meta-prompting/SKILL.md`
  - Insert a new `## Exploration Cache Schema` section AFTER the `## Subagent Configuration` section (which ends around line 222 with "### No Subagent Instructions Selected") and BEFORE `## Multi-Workflow Output Format` (line 224)
  - The section must define:
    a) The JSON schema for `.finesse/exploration-cache.json`:
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
    b) The JSON schema for `.finesse/config.json`:
       ```json
       {
         "cache_enabled": true,
         "staleness_threshold": 50
       }
       ```
    c) Index key format: `<directory_scope>:<keyword>` (e.g., `src/auth:jwt-validation`)
    d) Staleness model: An entry is stale if any file in its `referenced_files` appears in `git diff --name-only <entry.commit_hash>..HEAD`. The baseline is stale if the diff since `baseline.commit_hash` exceeds `staleness_threshold` files.
    e) Merge rules: New entries with existing keys overwrite old entries. New entries with new keys are additive. Baseline is overwritten wholesale on full exploration. Stale entries are removed on cache load.
  - Do NOT modify any other section in this file
  Verify: `grep "Exploration Cache Schema" plugins/finesse/skills/meta-prompting/SKILL.md` returns a match AND `grep "Multi-Workflow Output Format" plugins/finesse/skills/meta-prompting/SKILL.md` still returns a match (neighbor section intact)

Phase 3: Add Exploration Cache orchestration to `finesse.md`
  - Open `/workspace/plugins/finesse/commands/finesse.md`
  - Change A — Update `allowed-tools` (line 4) to add: `Bash(mkdir -p .finesse)`, `Write(.finesse/*)`, `Bash(git rev-parse HEAD)`, `Bash(git diff --name-only *)`
  - Change B — Insert a new `## Exploration Cache` section AFTER `## Agent Launch Guidance` (ends around line 308 with the Task Decomposer subsection) and BEFORE the `---` separator and `## Critical Rules` (line 311). The section must contain:

    ### Cache Structure
    Brief reference to the schema defined in meta-prompting/SKILL.md's Exploration Cache Schema section.

    ### Cache Loading (Before Exploration)
    At the START of every exploration phase (F2, B2, R2, T1, P2, RE2), BEFORE launching code-explorer agents:
    1. Check if `.finesse/exploration-cache.json` exists using Read. If not, skip to full exploration (cache miss).
    2. Read `.finesse/config.json` if it exists. If `cache_enabled` is false, skip to full exploration. Otherwise get `staleness_threshold` (default 50).
    3. Read the cache file.
    4. Run `git diff --name-only <baseline.commit_hash>..HEAD` and count changed files.
    5. If count >= threshold: cache miss — proceed with full exploration.
    6. If count < threshold: cache hit —
       a. Prune stale entries: for each entry, check if any `referenced_files` appear in the diff output. Remove stale entries.
       b. Load surviving baseline + entries whose `keywords` or `directory_scope` match the current task.
       c. Launch 1 code-explorer agent (instead of 2-3) with: "The following baseline context is already known: [baseline]. The following area-specific findings are cached: [matching entries]. Focus your exploration on [task-specific area] and any gaps not covered by cached context. Do NOT re-discover general patterns already provided."

    ### Cache Saving (After Exploration)
    At the END of every exploration phase, AFTER exploration results are gathered and synthesis is complete, BEFORE the UAT checkpoint:
    1. Create `.finesse/` if it does not exist: `mkdir -p .finesse`
    2. Get current commit hash: `git rev-parse HEAD`
    3. Extract findings into cache structure:
       - If no baseline exists or this was a cache miss: extract global findings as `baseline` (patterns, conventions, framework, directory structure). Set `baseline.commit_hash` and `baseline.last_confirmed`.
       - Extract task-specific findings as new entries with: `keywords` from task description and architecture patterns found; `directory_scope` from primary directories explored; `referenced_files` from all files read during exploration; `summary` as 1-2 sentence description.
    4. Merge new entries with existing cache (do not overwrite unrelated entries).
    5. Write updated cache to `.finesse/exploration-cache.json`.

    ### Cache Configuration
    An optional `.finesse/config.json` file with `cache_enabled` (boolean, default true) and `staleness_threshold` (integer, default 50). If absent, defaults are used. User may create or edit this file manually.

    ### Cache Presentation at UAT
    When cache is used, the exploration phase UAT checkpoint MUST include:
    - A note: "**Cache status**: Loaded baseline + N matching entries. M stale entries pruned."
    - The loaded baseline context
    - New task-specific findings from the lighter exploration
    - Any gaps where cache may be insufficient

  - Change C — In `## Agent Launch Guidance > ### Code Explorer Agents` (line 284), add a paragraph: "**Cache-aware launching**: Before launching code-explorer agents, check the exploration cache as described in the Exploration Cache section. On cache hit, launch 1 focused agent with cached context. On cache miss, launch agents as described above."

  - Change D — In `## Critical Rules` (line 311), add two rules:
    - "The `.finesse/` directory is for Finesse runtime cache and configuration. It is gitignored. Cache operations are best-effort — if reading or writing the cache fails (malformed JSON, missing git commit, etc.), continue the planning session without the cache. Do NOT block exploration on cache failures."
    - "When exploration uses cached context, ALWAYS disclose this at the UAT checkpoint. Never silently skip exploration."

  - Do NOT modify any section not listed above. Preserve all existing content exactly.
  Verify: `grep "Exploration Cache" plugins/finesse/commands/finesse.md` returns matches AND `grep "Write(.finesse" plugins/finesse/commands/finesse.md` returns a match AND `grep "Critical Rules" plugins/finesse/commands/finesse.md` still returns a match AND `grep "Context Compaction" plugins/finesse/commands/finesse.md` still returns a match

Phase 4: Add cache-aware notes to all 6 exploration phases in `task-workflows/SKILL.md`
  - Open `/workspace/plugins/finesse/skills/task-workflows/SKILL.md`
  - For EACH of the following 6 exploration phases, insert a cache preamble BEFORE the "Launch N **code-explorer** agents" line, and a cache save note AFTER the "After agents return, READ all essential files" line (or equivalent):

  1. Feature Phase 2 (line ~102): Before "Launch 2-3 **code-explorer** agents"
  2. Bugfix Phase 2 (line ~224): Before "Launch 2 **code-explorer** agents"
  3. Refactor Phase 2 (line ~330): Before "Launch 1-2 **code-explorer** agents"
  4. Testing Phase 1 (line ~419): Before "Launch 1-2 **code-explorer** agents"
  5. Performance Phase 2 (line ~522): Before "Launch 1-2 **code-explorer** agents"
  6. Research Phase 2 (line ~609): Before "Launch 2-3 **code-explorer** agents"

  The cache preamble for each phase (identical text):
  ```
  **Exploration cache**: Before launching exploration agents, follow the Exploration Cache procedure in finesse.md. On cache hit, load cached baseline and matching entries as context, then launch 1 focused code-explorer agent for the task-specific area not already covered. On cache miss, proceed with the full exploration below.
  ```

  The cache save note for each phase (identical text, inserted after agent return/read step):
  ```
  **Cache update**: After gathering and synthesizing exploration results, follow the Cache Saving procedure in finesse.md to persist findings to `.finesse/exploration-cache.json`.
  ```

  - Do NOT modify any other content in this file
  Verify: `grep -c "Exploration cache" plugins/finesse/skills/task-workflows/SKILL.md` returns exactly 6 AND `grep -c "Cache update" plugins/finesse/skills/task-workflows/SKILL.md` returns exactly 6
  [Subagent opportunity]: After completing all 6 insertions, spawn a Bash subagent to run the verification grep commands while beginning Phase 5. Phase 5 modifies a different file (finesse-resume.md) so there is no write conflict.

Phase 5: Update `finesse-resume.md` for cache awareness
  - Open `/workspace/plugins/finesse/commands/finesse-resume.md`
  - Change A — Update `allowed-tools` (line 4) to match finesse.md's updated list exactly (add: `Bash(mkdir -p .finesse)`, `Write(.finesse/*)`, `Bash(git rev-parse HEAD)`, `Bash(git diff --name-only *)`)
  - Change B — Add an `### Exploration Cache` subsection in the Workflow Continuation section (after the instruction to follow task-workflows phases). Content:
    ```
    ### Exploration Cache

    When resuming a session that will re-enter an exploration phase (F2, B2, R2, T1, P2, RE2), follow the Exploration Cache loading procedure from the main finesse command: check `.finesse/exploration-cache.json`, prune stale entries, and decide between cache-hit (lighter exploration) or cache-miss (full exploration) based on the staleness threshold.

    After exploration completes, save findings to the cache following the Cache Saving procedure from the main finesse command.

    Cache operations are best-effort — if the cache is missing or malformed, proceed with full exploration.
    ```
  - Do NOT modify any other content
  Verify: `grep "Exploration Cache" plugins/finesse/commands/finesse-resume.md` returns a match AND the allowed-tools line in finesse-resume.md contains `Write(.finesse/*)` (verify with `grep "Write(.finesse" plugins/finesse/commands/finesse-resume.md`)

Phase 6: Update `finesse-help.md` documentation
  - Open `/workspace/plugins/finesse/commands/finesse-help.md`
  - Change A — In the "## What Happens" section, update step 3 (line ~70) to mention caching. Change "Features get codebase exploration + 3 architecture approaches" to "Features get codebase exploration (with cache for faster repeat sessions) + 3 architecture approaches"
  - Change B — Insert a new `## Exploration Cache` section AFTER `## Resuming Sessions` (ends around line 152) and BEFORE `## When to Use Finesse` (line 154). Content:
    ```
    ## Exploration Cache

    Finesse caches codebase exploration findings in `.finesse/exploration-cache.json` to speed up repeat planning sessions:

    - **Cache hit**: If fewer than 50 files changed since last cache, Finesse loads cached findings and runs a lighter, task-specific exploration
    - **Cache miss**: If many files changed or no cache exists, full exploration runs as normal
    - **Staleness**: Cache entries referencing files that changed since last session are automatically pruned
    - **Configuration**: Override the threshold in `.finesse/config.json` (default: 50 files)
    - **Location**: `.finesse/` is gitignored — cache is local to your machine
    - **Reset**: Delete `.finesse/exploration-cache.json` to force full re-exploration
    ```
  - Do NOT modify any other content
  Verify: `grep "Exploration Cache" plugins/finesse/commands/finesse-help.md` returns a match AND `grep "When to Use Finesse" plugins/finesse/commands/finesse-help.md` still returns a match

Phase 7: Version bump to v0.6.0
  - Change version from "0.5.0" to "0.6.0" in exactly 3 files:
    a. `/workspace/plugins/finesse/.claude-plugin/plugin.json` — update `"version": "0.5.0"` to `"version": "0.6.0"`
    b. `/workspace/.claude-plugin/marketplace.json` — update the finesse version entry from `"0.5.0"` to `"0.6.0"` (note: this file is at the workspace root under `.claude-plugin/`, NOT under `plugins/finesse/`)
    c. `/workspace/plugins/finesse/commands/finesse-version.md` — update `Finesse v0.5.0` to `Finesse v0.6.0`
  Verify: `grep '"0.6.0"' plugins/finesse/.claude-plugin/plugin.json` AND `grep '0.6.0' .claude-plugin/marketplace.json` AND `grep "v0.6.0" plugins/finesse/commands/finesse-version.md` all return matches

## Rules
- Run verification commands after every phase. Fix failures before moving on.
- Do NOT make git commits.
- Do NOT push to remote repositories.
- Do NOT rewrite files from scratch. Make targeted edits using the Edit tool.
- Do NOT delete existing tests to make a suite pass.
- Do NOT add unnecessary abstractions or extra files.
- Only modify files explicitly listed in the phases above:
  - `.gitignore`
  - `plugins/finesse/skills/meta-prompting/SKILL.md`
  - `plugins/finesse/commands/finesse.md`
  - `plugins/finesse/skills/task-workflows/SKILL.md`
  - `plugins/finesse/commands/finesse-resume.md`
  - `plugins/finesse/commands/finesse-help.md`
  - `plugins/finesse/.claude-plugin/plugin.json`
  - `.claude-plugin/marketplace.json`
  - `plugins/finesse/commands/finesse-version.md`
- Do NOT modify any agent files (`plugins/finesse/agents/*.md`).
- Do NOT modify `plugins/finesse/skills/prompt-validation/SKILL.md`.
- Do NOT create any new files (the `.finesse/` directory and its JSON files are runtime artifacts created by the LLM during finesse sessions, not by this implementation).
- Read actual error messages before attempting fixes.
- If an Edit tool call fails (e.g., old_string not found), read the target file to find the actual current text before retrying. Do NOT guess what the file contains.
- When verification commands fail, read the full output to identify WHICH specific check failed before attempting a fix.
- When inserting the 6 cache notes in task-workflows/SKILL.md, read the file to identify all 6 insertion points, then perform all 6 insertions. After all insertions, re-read the file to confirm all 6 are present with identical text.
- When inserting new sections, preserve ALL surrounding content exactly. Verify neighbor sections still exist after each insertion.
- The 6 cache notes in task-workflows/SKILL.md must use IDENTICAL text across all 6 exploration phases.
- The allowed-tools in finesse-resume.md must EXACTLY match finesse.md's allowed-tools after update.
- If stuck on the same error for 3+ attempts, try an alternative approach (e.g., different insertion strategy, smaller edits).
- If unable to make progress after 5 iterations, document blockers and output <promise>BLOCKED</promise>.

## Completion
When ALL phases are complete and ALL verification commands pass cleanly, output <promise>Exploration caching system added to Finesse v0.6.0</promise>. This must be unequivocally true — every verification grep must pass. Do not output the completion promise unless every criterion is met.