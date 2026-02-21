You are iterating on the Finesse plugin at plugins/finesse/. Before doing anything:
1. Read plugins/finesse/.claude-plugin/plugin.json to check the current version
2. Read plugins/finesse/skills/task-workflows/SKILL.md and check if "Scope Analysis & Decomposition" sections exist
3. Read plugins/finesse/commands/finesse.md and check if "Multi-Workflow Branching" section exists
4. Read plugins/finesse/agents/ directory to check if task-decomposer.md exists
5. Determine what has been completed and what remains

## Requirements (in order)

Phase 1: Add Scope Analysis & Decomposition Framework to task-workflows/SKILL.md
  - Insert a new top-level section "## Scope Analysis & Decomposition Framework" between the "## Task Type Detection" section (around line 19) and the "## Feature Development Workflow (7 phases)" section (around line 36)
  - The framework section must define:
    a) Purpose: "After exploration reveals codebase context but before architecture/strategy design, analyze whether the task should be decomposed into multiple independent sub-workflows that each run as a separate ralph-loop."
    b) Decomposition triggers (when to propose splitting):
       - Estimated iteration count exceeds 25 (the ralph-loop ceiling)
       - Task touches more than 2 independent functional areas with no shared state
       - Task contains sub-tasks with no mutual dependencies
    c) When NOT to decompose:
       - Estimated iterations are within the task-type iteration range
       - All changes are tightly coupled (changing one requires changing all)
       - Task is inherently atomic (single root cause, single optimization target)
    d) Decomposition procedure:
       1. Launch code-architect in decomposition mode with exploration findings
       2. Launch task-decomposer to validate the proposal
       3. Present at UAT checkpoint
       4. User accepts, modifies, or overrides to single workflow
    e) Dependency analysis rules:
       - File-based: if sub-workflow A and B both modify the same file, they must be sequenced
       - Logical: if A's output is B's input, B depends on A
       - Parallel candidates: sub-workflows with zero file overlap and zero logical dependency
       - Wave assignment: build DAG, topological sort, assign waves (wave N = all nodes whose dependencies are in waves < N)
    f) Task-type-specific decomposition metrics table:
       | Task Type | Primary Metrics | Decomposition Signals |
       | Feature | code complexity (files touched), independent concerns, integration points | >8 files, >2 independent concerns, >18 estimated iterations |
       | Bugfix | triage effort (hypothesis count), multi-stage fixes, regression surface | >2 distinct root causes, fix spans >3 independent areas |
       | Refactor | scope breadth (modules), dependency chain depth, migration stages | >3 modules, chain >4 deep, >2 migration stages |
       | Testing | coverage breadth (areas), suite size, framework heterogeneity | >3 test areas, >25 test cases, >2 frameworks |
       | Performance | bottleneck count, scope breadth, measurement independence | >2 independent bottlenecks, optimizations in >3 areas |
       | Research | scoping breadth (topics), section count, investigation independence | >5 sections, >3 independent threads |
  - Insert a new "Scope Analysis & Decomposition [UAT]" phase into ALL 6 workflows. The exact insertion points and new phase counts:
    - Feature: insert between Phase 2 (Codebase Exploration) and current Phase 3 (Clarifying Questions). New phase becomes Phase 3. Old F3→F4, F4→F5, F5→F6, F6→F7, F7→F8. Heading updates to "## Feature Development Workflow (8 phases)"
    - Bugfix: insert between Phase 2 (Codebase Investigation) and current Phase 3 (Root Cause Analysis). New phase becomes Phase 3. Old B3→B4, B4→B5, B5→B6, B6→B7. Heading updates to "## Bug Fix Workflow (7 phases)"
    - Refactor: insert between Phase 2 (Current State Analysis) and current Phase 3 (Target State Design). New phase becomes Phase 3. Old R3→R4, R4→R5, R5→R6, R6→R7. Heading updates to "## Refactor/Chore Workflow (7 phases)"
    - Testing: insert between Phase 1 (Coverage Analysis) and current Phase 2 (Test Strategy). New phase becomes Phase 2. Old T2→T3, T3→T4, T4→T5, T5→T6. Heading updates to "## Testing Workflow (6 phases)"
    - Performance: insert between Phase 2 (Profiling & Analysis) and current Phase 3 (Optimization Strategy). New phase becomes Phase 3. Old P3→P4, P4→P5, P5→P6. Heading updates to "## Performance Optimization Workflow (6 phases)"
    - Research: insert between Phase 2 (Source Identification) and current Phase 3 (Research Plan). New phase becomes Phase 3. Old RE3→RE4, RE4→RE5, RE5→RE6, RE6→RE7, RE7→RE8. Heading updates to "## Research Workflow (8 phases)"
  - Each inserted phase must include:
    - **Goal**: "Determine whether this task should be decomposed into multiple independent ralph-loop sub-workflows."
    - **Code-architect launch**: "Launch 1 code-architect agent with decomposition focus, passing the exploration findings and task requirements. The architect evaluates the task-type-specific decomposition metrics from the framework section above."
    - **Task-decomposer launch**: "Launch 1 task-decomposer agent to validate the decomposition proposal."
    - **Branching**: "If architect recommends SINGLE_WORKFLOW: present the recommendation at UAT and proceed to the next phase as normal. If architect recommends DECOMPOSE: present proposed sub-workflows, dependency graph, and wave assignment at UAT."
    - **User override**: "If the user overrides to single workflow: warn about risks (high iteration count, broad scope) but respect the decision and proceed with single-workflow path."
    - **UAT presentation**: What was done (scope analysis), Key findings (decomposition decision, proposed sub-workflows if any), Impact on next phases (single vs multi-workflow path)
    - **Per-workflow customization**: Each workflow's phase should reference that workflow's specific decomposition metrics (e.g., Feature references code complexity and independent concerns, Bugfix references triage effort and multi-stage fixes)
  - Add a new section "## Multi-Workflow Execution (Decomposed Tasks)" after all 6 workflow definitions (before any closing content). This section must contain:
    a) "Shared phases: Discovery/Understanding, Exploration/Investigation, and Scope Analysis are shared across all sub-workflows. They run once and their outputs are included in every sub-workflow's prompt context."
    b) "Shared architecture: If the workflow includes an Architecture Design phase (Feature), architecture decisions are shared. The architect designs the overall system; decomposition determines which pieces each sub-workflow builds."
    c) "Per-sub-workflow phases: Only Plan Construction and Validation run independently for each sub-workflow. Each gets its own prompt, promise, and plan files."
    d) "Clarifying Questions: Run once with awareness of all sub-workflows. Questions may be sub-workflow-specific but are asked in a single batch."
    e) "Validation: Each sub-workflow's prompt is validated independently by all 5 standard validation agents."
    f) "Presentation: All sub-workflows are presented together with the execution graph. The user accepts or rejects the entire decomposition as a unit."
  - Add a note to each workflow's Plan Construction phase (the existing phase that builds the ralph-loop prompt): "If this workflow was decomposed during Scope Analysis, run Plan Construction independently for each sub-workflow. Each sub-workflow gets its own prompt scoped to its concern and files, sharing the exploration context gathered earlier. See the Multi-Workflow Execution section above."
  Verify: Run `grep -c "Scope Analysis" plugins/finesse/skills/task-workflows/SKILL.md` — should return at least 7 (1 framework section + 6 per-workflow phases). Run `grep "8 phases" plugins/finesse/skills/task-workflows/SKILL.md` — should return 2 matches (Feature and Research). Run `grep "7 phases" plugins/finesse/skills/task-workflows/SKILL.md` — should return 2 matches (Bugfix and Refactor). Run `grep "6 phases" plugins/finesse/skills/task-workflows/SKILL.md` — should return 2 matches (Testing and Performance). Run `grep "Multi-Workflow Execution" plugins/finesse/skills/task-workflows/SKILL.md` — should return at least 1 match.

Phase 2: Extend code-architect.md with Decomposition Mode
  - Add a new "## Decomposition Mode" section at the END of plugins/finesse/agents/code-architect.md (after the existing ## Rules section, at the very bottom of the file)
  - The section must define:
    a) When activated: "Your task prompt may specify decomposition mode instead of a design focus. In this mode, your job is to analyze whether the task should be split into multiple independent ralph-loop runs."
    b) Input: task description and type, codebase exploration findings, task-type-specific decomposition metrics from task-workflows skill
    c) Analysis steps: (1) Estimate scope — count files, independent areas, integration points. (2) Identify boundaries — find natural seams. (3) Check independence — can each sub-task be built/tested independently? (4) Map dependencies — file-based and logical. (5) Estimate iterations per sub-task.
    d) Output format — "Decomposition Recommendation": either SINGLE_WORKFLOW with 1-sentence rationale, or DECOMPOSE with full structure below
    e) Sub-Workflows (if DECOMPOSE): for each, provide: Name (kebab-case), Type (usually same as parent), Scope (files/dirs), Description (1-2 sentences), Estimated iterations, Dependencies (names of other sub-workflows or "none")
    f) Dependency Graph: list sub-workflows grouped into waves with reasoning (file-based vs logical)
    g) Override Warnings: flag any sub-workflow with >25 estimated iterations
    h) Rules: prefer 2-4 sub-workflows, each independently verifiable, no splitting tightly coupled changes, no file overlap between parallel sub-workflows, analysis only (don't modify any files)
  Verify: Run `grep -c "Decomposition Mode" plugins/finesse/agents/code-architect.md` — should return at least 1. Run `grep "SINGLE_WORKFLOW" plugins/finesse/agents/code-architect.md` — should match. Run `grep "DECOMPOSE" plugins/finesse/agents/code-architect.md` — should match.

Phase 3: Create task-decomposer.md validation agent
  - Create new file at plugins/finesse/agents/task-decomposer.md
  - Must have YAML frontmatter with description field following existing validator pattern, e.g.:
    ---
    description: "Validates that a proposed task decomposition has proper sub-workflow boundaries, correct dependencies, reasonable scope, and no file conflicts"
    ---
  - Title: "# Task Decomposer"
  - Opening: "You will receive a proposed task decomposition in your task prompt. Your sole focus is whether the decomposition is structurally sound and will produce valid, independent ralph-loop runs."
  - Must check these 6 things (use "## What to Check" with numbered subsections):
    1. Sub-workflow independence: Can each be built/tested independently? If tightly coupled: FAIL.
    2. File scope conflicts: Does every modified file appear in exactly one sub-workflow? If overlap without dependency: FAIL.
    3. Dependency graph validity: Is the graph a DAG? Are waves consistent with deps? If cycles: FAIL.
    4. Iteration estimates: Each ≤25? Total reasonable? If any exceeds 25: NEEDS_REWORK.
    5. Completeness: Does the union cover the full original task? If gaps: FAIL.
    6. Granularity: Not over-decomposed (>6 sub-workflows)? Not trivially small (<5 iterations)? If over-decomposed: NEEDS_REWORK.
  - Must use PASS / FAIL / NEEDS_REWORK verdict vocabulary (matching existing validators in prompt-validation/SKILL.md)
  - Output format section with: VERDICT line, ISSUES section, FILE CONFLICTS section, DEPENDENCY ISSUES section, SUGGESTIONS section
  - Verdict rules: FAIL for structural problems (file conflicts, cycles, gaps, tight coupling). NEEDS_REWORK for minor issues (over-decomposition, borderline estimates). PASS when sound.
  Verify: File exists at plugins/finesse/agents/task-decomposer.md. Run `grep "VERDICT" plugins/finesse/agents/task-decomposer.md` — should match. Run `grep "independence" plugins/finesse/agents/task-decomposer.md` — should match. Run `grep -i "file.*conflict\|file.*scope" plugins/finesse/agents/task-decomposer.md` — should match. Run `grep "dependency" plugins/finesse/agents/task-decomposer.md` — should match. Run `grep "iteration" plugins/finesse/agents/task-decomposer.md` — should match. Run `grep "completeness" plugins/finesse/agents/task-decomposer.md` — should match. Run `grep "granularity" plugins/finesse/agents/task-decomposer.md` — should match.

Phase 4: Update meta-prompting/SKILL.md with multi-workflow output format
  - Add "## Multi-Workflow Output Format" section AFTER the existing "## File Output Format" section (which ends around line 101) in plugins/finesse/skills/meta-prompting/SKILL.md
  - The section must define:
    a) Directory structure:
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
    b) Session naming: kebab-case derived from original task description
    c) Sub-task naming: kebab-case from decomposition proposal names
    d) Execution graph format: overview section (original task, sub-workflow count, wave count, total estimated iterations), wave structure tables (name, type, est. iterations, scope/dependencies), dependency rationale section, per-wave commands section with full ralph-loop command for each task
    e) Per-sub-workflow prompt rules: (1) each prompt.md must be fully self-contained (valid as $(cat ...) argument), (2) must include its own cold start paragraph specific to its scope, (3) must reference only files in its scope, (4) must include own verification commands/guardrails/completion criteria, (5) wave 2+ prompts can reference wave 1 outputs as existing state but must NOT assume they will be built
    f) The 10 Mandatory Attributes apply to EACH sub-workflow prompt individually
    g) Single-workflow backward compatibility: when decomposition does not occur, use the existing flat format (ralph-plans/<name>.md, <name>-promise.txt, <name>-plan.md)
  - Update attribute #9 (Conservative Iteration Limit, around line 49-50) to reference decomposition: change from "decompose it into separate sequential ralph runs" to "it should have been decomposed during the Scope Analysis phase. If you reach plan construction with an estimate over 25, revisit scope analysis."
  Verify: Run `grep -c "Multi-Workflow Output Format" plugins/finesse/skills/meta-prompting/SKILL.md` — should return at least 1. Run `grep "execution-graph" plugins/finesse/skills/meta-prompting/SKILL.md` — should match. Run `grep "per-sub-workflow\|sub-workflow prompt" plugins/finesse/skills/meta-prompting/SKILL.md` — should match. Run `grep "Scope Analysis" plugins/finesse/skills/meta-prompting/SKILL.md` — should match (in updated attribute #9).

Phase 5: Update prompt-validation/SKILL.md with multi-workflow validation
  - Add "### Multi-Workflow Validation" section AFTER the existing "### Step 1: Launch All Validators in Parallel" section in plugins/finesse/skills/prompt-validation/SKILL.md
  - The section must define:
    a) Per-sub-workflow validation: launch all 5 validators on each sub-workflow's prompt independently. Sequential per sub-workflow (to manage context), not all at once.
    b) Cross-sub-workflow checks: after individual validation, verify (1) no file scope overlaps between parallel sub-workflow prompts, (2) wave 2+ sub-workflows correctly assume wave 1 outputs as existing state
    c) Verdict aggregation: all sub-workflow prompts must pass all 5 validators. A FAIL on one blocks the entire plan.
    d) Refinement budget: applies per sub-workflow independently. Each can use up to --max-refinements cycles.
  - Update the "### Post-Acceptance" section (around lines 63-73) to add a multi-workflow path:
    "Multi-workflow acceptance:
    1. Create ralph-plans/<session-name>/ directory
    2. For each wave N, create ralph-plans/<session-name>/wave-<N>/
    3. For each sub-workflow, create its directory and write prompt.md, promise.txt, plan.md
    4. Write ralph-plans/<session-name>/execution-graph.md
    5. Output ralph-loop commands organized by wave"
  Verify: Run `grep -c "Multi-Workflow Validation" plugins/finesse/skills/prompt-validation/SKILL.md` — should return at least 1. Run `grep "per-sub-workflow\|sub-workflow" plugins/finesse/skills/prompt-validation/SKILL.md` — should match. Run `grep "cross-sub-workflow\|file scope overlap" plugins/finesse/skills/prompt-validation/SKILL.md` — should match.

Phase 6: Update finesse.md orchestrator
  This phase modifies plugins/finesse/commands/finesse.md. Each sub-item below is a specific edit:

  6a) Update allowed-tools in YAML frontmatter (line 4):
      Change: "Bash(mkdir -p ralph-plans/*)", "Write(ralph-plans/*)"
      To: "Bash(mkdir -p ralph-plans/*)", "Bash(mkdir -p ralph-plans/**/*)", "Write(ralph-plans/*)", "Write(ralph-plans/**/*)"
      This allows creating nested wave/task directories.

  6b) Update Workflow Quick Reference (lines 51-63):
      Update each workflow summary to include the new Scope Analysis phase. The new summaries:
      - Feature: "F1 Discovery (deep) → F2 Codebase Exploration [UAT] → F3 Scope Analysis [UAT] → F4 Clarifying Questions → F5 Architecture Design [UAT] → F6 Plan Construction [UAT] → Validate → Present"
      - Bug Fix: "B1 Bug Understanding (deep) → B2 Codebase Investigation [UAT] → B3 Scope Analysis [UAT] → B4 Root Cause Analysis [UAT] → B5 Fix Strategy [UAT] → Plan → Validate → Present"
      - Refactor: "R1 Scope Definition (deep) → R2 Current State Analysis [UAT] → R3 Scope Analysis [UAT] → R4 Target State Design [UAT] → R5 Migration Strategy [UAT] → Plan → Validate → Present"
      - Testing: "T1 Coverage Analysis [UAT] → T2 Scope Analysis [UAT] → T3 Test Strategy [UAT] → T4 Clarifying Questions → Plan → Validate → Present"
      - Performance: "P1 Problem Definition (deep) → P2 Profiling & Analysis [UAT] → P3 Scope Analysis [UAT] → P4 Optimization Strategy [UAT] → Plan → Validate → Present"
      - Research: "RE1 Goal Definition (deep) → RE2 Source Identification [UAT] → RE3 Scope Analysis [UAT] → RE4 Research Plan & Questions [UAT] → RE5 Investigation Strategy [UAT] → Plan → Validate → Present"

  6c) Add "## Multi-Workflow Branching" section AFTER the "## UAT Checkpoint Procedure" section and BEFORE the "## Common Final Phases (all task types)" section. Content:
      "After the Scope Analysis & Decomposition phase, the workflow branches:
      ### Single Workflow Path
      If decomposition was not warranted (code-architect recommended SINGLE_WORKFLOW and user accepted): Continue with the remaining phases as a single linear workflow. Output format: flat ralph-plans/<name>.md, <name>-promise.txt, <name>-plan.md (unchanged from v0.2.0).
      ### Multi-Workflow Path
      If decomposition was accepted:
      1. Shared context: Exploration/investigation findings from earlier phases are shared across ALL sub-workflows. Do NOT re-explore for each.
      2. Per-sub-workflow phases: Starting from the phase after scope analysis, run remaining workflow phases independently for each sub-workflow. Each gets its own clarifying questions (if applicable), architecture/strategy, plan construction, and UAT checkpoints (unless fast-forwarded).
      3. Processing order: Process sub-workflows in wave order (Wave 1 first, then Wave 2). Within a wave, process sequentially to avoid overwhelming the user with parallel UAT.
      4. Output format: Multi-workflow session directory structure (see meta-prompting skill for details).
      5. Execution graph: Generate execution-graph.md showing wave structure, dependencies, and recommended execution order."

  6d) Update "### Plan Construction" in Common Final Phases section to add:
      "### Multi-Workflow Plan Construction
      When the Scope Analysis phase resulted in an accepted decomposition:
      1. Shared context: Exploration findings and architecture decisions from earlier phases apply to ALL sub-workflows. Do not re-explore or re-design.
      2. Per-sub-workflow loop: For each sub-workflow in wave order, construct a ralph-loop prompt using the meta-prompting skill template, scoped to that sub-workflow's concern and files. The cold start paragraph must reference the shared architecture context. Include cross-sub-workflow guardrails: 'Do NOT modify files outside this sub-workflow's scope: [list].'
      3. Each sub-workflow prompt gets its own iteration count recommendation.
      4. Execution graph: Build an execution-graph.md documenting wave order, dependencies, and run instructions."

  6e) Update "### Validation" in Common Final Phases to add:
      "In multi-workflow mode, validate EACH sub-workflow's plan independently with all 5 validators. A FAIL on any sub-workflow blocks presentation of the entire decomposition."

  6f) Add multi-workflow User Decision section (after the existing single-workflow "If ACCEPTED" block):
      "**If ACCEPTED (multi-workflow):**
      1. Create ralph-plans/<session-name>/ directory
      2. For each wave and task, create directories and write three files:
         - ralph-plans/<session-name>/wave-<N>/<task-name>/prompt.md — sub-workflow prompt text ONLY
         - ralph-plans/<session-name>/wave-<N>/<task-name>/promise.txt — sub-workflow completion promise ONLY
         - ralph-plans/<session-name>/wave-<N>/<task-name>/plan.md — sub-workflow metadata
      3. Write ralph-plans/<session-name>/execution-graph.md with wave structure, dependency rationale, and per-task commands
      4. Output ALL commands grouped by wave:
         ## Wave 1 (run in parallel)
         /ralph-loop:ralph-loop $(cat ralph-plans/<session>/wave-1/<task-1>/prompt.md) --completion-promise '$(cat ralph-plans/<session>/wave-1/<task-1>/promise.txt)' --max-iterations=<N>
         ## Wave 2 (run after Wave 1 completes)
         /ralph-loop:ralph-loop $(cat ralph-plans/<session>/wave-2/<task>/prompt.md) --completion-promise '$(cat ralph-plans/<session>/wave-2/<task>/promise.txt)' --max-iterations=<N>
      5. Single-workflow output uses the existing flat format (unchanged)."

  6g) Update Agent Launch Guidance section to add two subsections:
      "### Task Decomposer Agent
      When the Scope Analysis phase produces a DECOMPOSE recommendation and the user accepts:
      - Launch the task-decomposer agent to validate the decomposition structure
      - Pass the full decomposition (sub-workflows, scopes, dependencies, estimates)
      - If FAIL: fix the decomposition and re-present at the UAT checkpoint
      - If NEEDS_REWORK: fix if within refinement budget

      ### Code Architect in Decomposition Mode
      When launching code-architect for scope analysis (not architecture design):
      - Set the mode to 'decomposition' in the task prompt
      - Pass the exploration findings, task type, and task requirements
      - The architect returns either SINGLE_WORKFLOW or DECOMPOSE with sub-workflow structure"

  6h) Update Critical Rules section to add:
      "- When decomposition is accepted, run plan construction and validation PER sub-workflow. Exploration and architecture are shared and NOT re-run.
      - Multi-workflow output uses the wave/task directory structure. Single-workflow output keeps the flat ralph-plans/<name>.* format. NEVER mix the two formats.
      - Each sub-workflow prompt must be fully self-contained — include all relevant shared context inline. Sub-workflow prompts are read via $(cat ...) and have no access to sibling files.
      - The execution-graph.md file is for human reference. The user decides whether to run sub-workflows in parallel.
      - When the user overrides decomposition, warn about consequences but respect the override."

  6i) Update Context Compaction Handling section's working file structure list to add:
      "Decomposition results (if multi-workflow): sub-workflow names, types, scopes, dependencies, wave assignments"

  Verify: Run `grep -c "Multi-Workflow" plugins/finesse/commands/finesse.md` — should return at least 5. Run `grep "Scope Analysis" plugins/finesse/commands/finesse.md` — should match at least 6 times (once per workflow in quick reference). Run `grep "task-decomposer" plugins/finesse/commands/finesse.md` — should match. Run `grep "execution-graph" plugins/finesse/commands/finesse.md` — should match. Run `grep "wave-1\|wave-2\|Wave 1\|Wave 2" plugins/finesse/commands/finesse.md` — should match.

Phase 7: Update finesse-help.md
  This phase modifies plugins/finesse/commands/finesse-help.md. Each sub-item:

  7a) Update the workflow table (lines 15-22) to include Scope Analysis in each row:
      | **Feature** | Discovery (deep) → Codebase Exploration [UAT] → Scope Analysis [UAT] → Clarifying Questions → Architecture Design [UAT] → Plan Construction [UAT] → Validate → Present |
      | **Bug Fix** | Bug Understanding (deep) → Codebase Investigation [UAT] → Scope Analysis [UAT] → Root Cause Analysis [UAT] → Fix Strategy [UAT] → Plan → Validate → Present |
      | **Refactor** | Scope Definition (deep) → Current State Analysis [UAT] → Scope Analysis [UAT] → Target State Design [UAT] → Migration Strategy [UAT] → Plan → Validate → Present |
      | **Testing** | Coverage Analysis [UAT] → Scope Analysis [UAT] → Test Strategy [UAT] → Clarifying Questions → Plan → Validate → Present |
      | **Performance** | Problem Definition (deep) → Profiling & Analysis [UAT] → Scope Analysis [UAT] → Optimization Strategy [UAT] → Plan → Validate → Present |
      | **Research** | Goal Definition (deep) → Source Identification [UAT] → Scope Analysis [UAT] → Research Plan [UAT] → Investigation Strategy [UAT] → Plan → Validate → Present |

  7b) Add task-decomposer to the Planning Agents table (after code-architect, around line 84):
      | task-decomposer | Validates decomposition proposals: sub-workflow scoping, dependencies, wave grouping, coverage |
      Also update code-architect description to:
      | code-architect | Designs implementation approaches with trade-offs; proposes task decomposition |

  7c) Update the "What Happens" numbered list (lines 53-65) to add a new step 2 (shifting subsequent numbers):
      "2. **Scope analysis** — For large tasks, Finesse may propose splitting into multiple sub-workflows that can run in parallel"

  7d) Add a "## Multi-Workflow Output" section BEFORE the "## Plan Rejection" section (around line 107). Content:
      "## Multi-Workflow Output
      For large tasks, Finesse may decompose the work into multiple ralph-loop runs organized into execution waves:
      - **Wave 1**: Independent sub-tasks that can run in parallel
      - **Wave 2+**: Sub-tasks that depend on earlier waves completing
      Output goes to ralph-plans/<session>/wave-N/<task>/ instead of the flat format. An execution-graph.md shows the dependency structure and all commands.
      Single-workflow tasks still use the flat ralph-plans/<name>.md format."

  7e) Update the "## Output" section (lines 95-105) to note: "For multi-workflow tasks, files are organized under ralph-plans/<session-name>/ with wave/task subdirectories. See Multi-Workflow Output below."

  Verify: Run `grep -c "Scope Analysis" plugins/finesse/commands/finesse-help.md` — should return at least 6 (one per workflow in table). Run `grep "task-decomposer" plugins/finesse/commands/finesse-help.md` — should match. Run `grep "Multi-Workflow Output" plugins/finesse/commands/finesse-help.md` — should match. Run `grep "Scope analysis" plugins/finesse/commands/finesse-help.md` — should match (in What Happens list).

Phase 8: Version bump to v0.3.0
  - Edit plugins/finesse/.claude-plugin/plugin.json: change "version": "0.2.0" to "version": "0.3.0"
  - Edit .claude-plugin/marketplace.json (at REPO ROOT, not under plugins/): change "0.2.0" to "0.3.0" in the finesse plugin entry
  - Edit plugins/finesse/commands/finesse-version.md: change "**Finesse v0.2.0**" to "**Finesse v0.3.0**"
  Verify: Run `grep '"0.3.0"' plugins/finesse/.claude-plugin/plugin.json` — should match. Run `grep '"0.3.0"' .claude-plugin/marketplace.json` — should match. Run `grep "v0.3.0" plugins/finesse/commands/finesse-version.md` — should match.

## Rules
- ONLY modify the following 10 files (no others):
  - plugins/finesse/skills/task-workflows/SKILL.md
  - plugins/finesse/agents/code-architect.md
  - plugins/finesse/agents/task-decomposer.md (CREATE)
  - plugins/finesse/skills/meta-prompting/SKILL.md
  - plugins/finesse/skills/prompt-validation/SKILL.md
  - plugins/finesse/commands/finesse.md
  - plugins/finesse/commands/finesse-help.md
  - plugins/finesse/commands/finesse-version.md
  - plugins/finesse/.claude-plugin/plugin.json
  - .claude-plugin/marketplace.json (at repo root)
- Do NOT touch README.md or any other file not listed above.
- Make targeted edits using the Edit tool. Do NOT rewrite entire files from scratch. Exception: Phase 3 creates a new file (task-decomposer.md) using the Write tool.
- Read actual file contents before making any edit. Never edit blind.
- Read actual error messages and verification command output before attempting fixes. Diagnose from output, do not guess.
- After inserting a new phase, verify its position by reading the surrounding phases. The phase must appear in the correct logical order within the workflow.
- After adding a phase, update the phase count in the workflow heading (e.g., "7 phases" → "8 phases"). Verify with grep.
- When renumbering phases, verify that EVERY phase label is sequential with no gaps and no duplicates. Read the entire workflow section after editing to confirm.
- All phase numbers must be consistent across three files: task-workflows/SKILL.md, finesse.md workflow quick reference, and finesse-help.md workflow table. If you change a phase number in one file, verify the other two match.
- The task-decomposer agent MUST use the same verdict vocabulary as existing validators: PASS, FAIL, or NEEDS_REWORK. Model its structure on the existing validators (e.g., clarity-checker.md, scope-safety-reviewer.md).
- Multi-workflow output: ralph-plans/<session>/wave-N/<task>/prompt.md|promise.txt|plan.md. Single-workflow: unchanged flat ralph-plans/<name>.md format. Never mix formats.
- The code-architect's Decomposition Mode must be clearly separated from its existing 3-focus design mode. Do NOT merge them.
- After editing the markdown table in finesse-help.md, verify pipe characters are aligned and the table renders correctly.
- Do NOT push to remote repositories.
- Do NOT add unnecessary abstractions, extra files, or helper utilities.
- Do NOT delete or reorder existing phases unless renumbering due to the new insertion.
- If stuck on the same error for 3+ attempts, try an alternative approach.
- If unable to make progress after 5 iterations, document blockers and output <promise>BLOCKED</promise>.

## Completion
When ALL phases are complete and ALL verification commands pass cleanly, output <promise>FINESSE_V030_COMPLETE</promise>. This must be unequivocally true.

The verification commands in each phase are NECESSARY but NOT SUFFICIENT. You must also visually confirm each criterion below is fully satisfied before outputting the promise.

Do not output the completion promise unless EVERY criterion below is met:
1. plugins/finesse/.claude-plugin/plugin.json contains "version": "0.3.0"
2. .claude-plugin/marketplace.json contains version "0.3.0" for finesse
3. plugins/finesse/commands/finesse-version.md contains "v0.3.0"
4. plugins/finesse/skills/task-workflows/SKILL.md contains "Scope Analysis & Decomposition Framework" section with decomposition triggers, metrics table, and dependency analysis rules. All 6 workflows have the new Scope Analysis phase. Expected phase counts: Feature=8, Bugfix=7, Refactor=7, Testing=6, Performance=6, Research=8. Phase numbers are sequential with no gaps.
5. plugins/finesse/agents/code-architect.md contains "Decomposition Mode" section with SINGLE_WORKFLOW and DECOMPOSE output formats, sub-workflow structure, dependency graph, and wave assignment
6. plugins/finesse/agents/task-decomposer.md exists with YAML frontmatter, PASS/FAIL/NEEDS_REWORK verdict format, and checks for: sub-workflow independence, file scope conflicts, dependency graph validity, iteration estimates, completeness, and granularity
7. plugins/finesse/skills/meta-prompting/SKILL.md contains "Multi-Workflow Output Format" section with directory structure specification, execution graph format, per-sub-workflow prompt rules, and backward compatibility note. Attribute #9 references Scope Analysis phase.
8. plugins/finesse/skills/prompt-validation/SKILL.md contains "Multi-Workflow Validation" section with per-sub-workflow validation, cross-sub-workflow checks, and updated post-acceptance for multi-workflow directory creation
9. plugins/finesse/commands/finesse.md contains: (a) updated workflow quick reference with Scope Analysis in all 6 workflows, (b) "Multi-Workflow Branching" section, (c) multi-workflow Plan Construction and Validation guidance, (d) multi-workflow User Decision section with wave/task output format, (e) task-decomposer and code-architect decomposition mode in Agent Launch Guidance, (f) multi-workflow critical rules
10. plugins/finesse/commands/finesse-help.md contains: (a) Scope Analysis in all 6 workflow table rows, (b) task-decomposer in agents table, (c) "Scope analysis" step in What Happens list, (d) "Multi-Workflow Output" section
11. Phase numbers are consistent across task-workflows/SKILL.md, finesse.md quick reference, and finesse-help.md workflow table

Before outputting the promise, run ALL verification commands from all 8 phases in sequence and confirm every single one passes.
