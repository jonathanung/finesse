---
description: "Task-type-specific planning workflows for Finesse — defines phases for features, bug fixes, chores, testing, performance, and research work"
---

# Task Workflows

After detecting the task type, follow the corresponding workflow below. Every workflow ends with plan construction, validation, pre-flight, and presentation. The phases before that differ by task type.

---

## UAT Checkpoints

Phases marked with `[UAT]` require a User Acceptance Testing checkpoint as defined in the main command (`finesse.md`). When you complete a `[UAT]` phase, follow the UAT Checkpoint Procedure before proceeding to the next phase.

If the user has elected to fast-forward UAT (by selecting "Accept and skip remaining UAT" at any checkpoint), skip the checkpoint and proceed directly. Discovery/Understanding phase confirmations are never affected by fast-forward.

---

## Task Type Detection

Classify the user's task into one of these types based on their description:

| Type | Signals |
|---|---|
| **feature** | "Add", "build", "create", "implement", "new", introduces new functionality |
| **bugfix** | "Fix", "broken", "not working", "error", "crash", "wrong", "regression" |
| **refactor** | "Refactor", "clean up", "reorganize", "restructure", "improve code", "tech debt" |
| **testing** | "Add tests", "test coverage", "write tests", "validate", "QA" |
| **performance** | "Slow", "optimize", "performance", "speed up", "bottleneck", "latency" |
| **research** | "Research", "investigate", "compare", "evaluate", "analyze", "study", "survey", "document", "explore options", "understand", "assessment", "trade-offs", "pros and cons", "spike", "feasibility" |

If ambiguous, ask the user. Do not guess.

---

## Scope Analysis & Decomposition Framework

After exploration reveals codebase context but before architecture/strategy design, analyze whether the task should be decomposed into multiple independent sub-workflows that each run as a separate ralph-loop.

### Decomposition Triggers

Propose splitting when ANY of these apply:
- Estimated iteration count exceeds 25 (the ralph-loop ceiling)
- Task touches more than 2 independent functional areas with no shared state
- Task contains sub-tasks with no mutual dependencies

### When NOT to Decompose

Do NOT decompose when:
- Estimated iterations are within the task-type iteration range
- All changes are tightly coupled (changing one requires changing all)
- Task is inherently atomic (single root cause, single optimization target)

### Decomposition Procedure

1. Launch 1 **code-architect** agent in decomposition mode with exploration findings and task requirements. The architect evaluates the task-type-specific decomposition metrics below.
2. Launch 1 **task-decomposer** agent to validate the decomposition proposal.
3. Present at UAT checkpoint.
4. User accepts, modifies, or overrides to single workflow.

### Dependency Analysis Rules

- **File-based**: If sub-workflow A and B both modify the same file, they must be sequenced
- **Logical**: If A's output is B's input, B depends on A
- **Parallel candidates**: Sub-workflows with zero file overlap and zero logical dependency
- **Wave assignment**: Build DAG, topological sort, assign waves (wave N = all nodes whose dependencies are in waves < N)

### Task-Type-Specific Decomposition Metrics

| Task Type | Primary Metrics | Decomposition Signals |
|---|---|---|
| Feature | code complexity (files touched), independent concerns, integration points | >8 files, >2 independent concerns, >18 estimated iterations |
| Bugfix | triage effort (hypothesis count), multi-stage fixes, regression surface | >2 distinct root causes, fix spans >3 independent areas |
| Refactor | scope breadth (modules), dependency chain depth, migration stages | >3 modules, chain >4 deep, >2 migration stages |
| Testing | coverage breadth (areas), suite size, framework heterogeneity | >3 test areas, >25 test cases, >2 frameworks |
| Performance | bottleneck count, scope breadth, measurement independence | >2 independent bottlenecks, optimizations in >3 areas |
| Research | scoping breadth (topics), section count, investigation independence | >5 sections, >3 independent threads |

---

## Shared Phase Templates

These templates define common patterns used across multiple workflows. Each task-type workflow references these and provides only its unique customization.

### Exploration Phase Template

Every exploration/investigation phase follows this pattern:

1. **Cache check**: Follow Exploration Cache loading procedure in finesse.md. On cache hit, launch 1 focused agent with cached context. On cache miss, proceed with full exploration.
2. **Launch agents**: Launch the task-type-specified number of code-explorer agents with the task-specific prompts listed in each workflow.
3. **Read files**: After agents return, read all essential files identified. Build deep understanding before proceeding.
4. **Cache save**: Follow Cache Saving procedure in finesse.md to persist findings to `.finesse/exploration-cache.json`.

### Scope Analysis Phase Template [UAT]

**Goal**: Determine whether the task should be decomposed into multiple independent ralph-loop sub-workflows.

1. Launch 1 **code-architect** agent in decomposition mode with exploration findings and task requirements. Pass the task-type-specific metrics from the Decomposition Metrics table above.
2. Launch 1 **task-decomposer** agent to validate the proposal.
3. **Branching**: If SINGLE_WORKFLOW → present at UAT and proceed. If DECOMPOSE → present sub-workflows, dependency graph, and wave assignment at UAT.
4. **User override**: Warn about risks (high iteration count, broad scope) but respect the decision.

**UAT topics**: decomposition decision, sub-workflows (if any), dependency graph, impact on remaining phases

### Plan Construction Phase Template

1. If decomposed during Scope Analysis, run Plan Construction independently per sub-workflow (see Multi-Workflow Execution section).
2. Build a complete ralph-loop prompt per the meta-prompting skill template with the task-type-specific content (cold start, phases, guardrails) listed in each workflow.
3. **Subagent analysis**: After git configuration, analyze phases for subagent eligibility per meta-prompting skill heuristics. Ask user via Subagent Configuration Prompt in finesse.md.
4. **Context budget**: Compute estimate per Context Budget Estimation Procedure in finesse.md. If critical (>80%), trigger re-route.
5. Determine `--max-iterations` with reasoning using the task-type-specific iteration ranges listed in each workflow.

---

## Feature Development Workflow (8 phases)

### Phase 1: Discovery (deep)

**Goal**: Understand what needs to be built — thoroughly.

- Clarify the feature request if vague
- Ask what problem it solves
- Identify constraints and requirements
- Probe for edge cases: What happens when this fails? What about empty states? Concurrent access?
- Ask about the user's mental model: How do they envision this working from the user's perspective?
- Ask about constraints they haven't mentioned: Performance requirements? Accessibility? Backward compatibility?
- If the user's description is short or vague, ask at least 3 clarifying questions before summarizing
- Summarize understanding and confirm with user

Do NOT proceed until the user confirms your understanding is correct. This is NOT a UAT checkpoint — Discovery requires iterative back-and-forth until alignment is achieved.

### Phase 2: Codebase Exploration [UAT]

**Goal**: Understand relevant existing code and patterns.

Follow the Exploration Phase Template. Launch 2-3 **code-explorer** agents:
- Agent 1: "Find features similar to [feature] in this codebase. Trace their implementation end-to-end. Return entry points, execution flow, key components, and essential files."
- Agent 2: "Map the architecture and abstractions in [relevant area]. Identify patterns, conventions, file organization, and dependencies."
- Agent 3 (if applicable): "Analyze the current implementation of [related feature]. How does it handle [relevant concern like auth, data flow, error handling]?"

**UAT topics**: similar features found, architecture patterns and conventions, key files and responsibilities

### Phase 3: Scope Analysis & Decomposition [UAT]

Follow the Scope Analysis Phase Template using **feature** metrics.

### Phase 4: Clarifying Questions

**Goal**: Fill every gap before designing.

Based on codebase exploration, identify underspecified aspects:
- Edge cases
- Error handling expectations
- Integration points with existing code
- Backward compatibility requirements
- Performance requirements
- Data model implications
- UI/UX expectations (if applicable)

Present ALL questions in an organized list. **Wait for answers before proceeding.**

### Phase 5: Architecture Design [UAT]

**Goal**: Design multiple implementation approaches.

Launch 2-3 **code-architect** agents in parallel, each with a different focus:
- Agent 1 (Minimal Changes): "Design an implementation using the smallest changes, maximum code reuse. Context: [codebase findings + clarified requirements]"
- Agent 2 (Clean Architecture): "Design an implementation prioritizing maintainability, clean abstractions, and testability. Context: [same]"
- Agent 3 (Pragmatic Balance): "Design an implementation balancing speed and quality, fitting existing patterns. Context: [same]"

**UAT topics**: each approach with architecture decisions, trade-offs, and verification strategy; your recommendation with reasoning

Note: When the user selects "Accept" at this checkpoint, ask which approach they are accepting (or if they accept your recommendation). When they select "Provide feedback" or "Make specific changes", the feedback may target a specific approach or request an entirely different direction.

### Phase 6: Plan Construction [UAT]

Follow the Plan Construction Phase Template. Task-specific content:
- **Cold start**: check current state of files and patterns discovered during exploration
- **Phases**: ordered matching the architecture's build sequence with verification commands
- **Guardrails**: task-specific based on the chosen architecture
- **Iteration range**: Simple (1-2 files): 8-12, Medium (3-5 files): 12-18, Complex (6+ files): 18-25

**UAT topics**: complete prompt with cold start, phases, verification, guardrails, completion criteria; recommended iterations with reasoning

### Phase 7: Validation

Launch all 6 validation agents in parallel on the drafted plan. Refine per severity tier rules in the prompt-validation skill.

After validation passes, run pre-flight checks per the "Pre-flight Validation" section of finesse.md Common Final Phases. Collect warnings for presentation.

### Phase 8: Presentation

Present the validated plan. On acceptance, save to `finesse-plans/` and output the command.

---

## Bug Fix Workflow (7 phases)

### Phase 1: Bug Understanding (deep)

**Goal**: Fully understand the bug before touching code.

Gather from the user:
- What's the expected behavior?
- What's the actual behavior?
- Steps to reproduce
- When did it start? (recent change, always broken, intermittent?)
- Error messages, stack traces, logs (if available)
- Which environments? (dev, staging, prod)
- Has anything changed recently that might have caused this?
- Is this blocking other work or users?

If the user provides sparse information, ask explicitly for missing details. Do NOT proceed with partial understanding.

Do NOT proceed until you have a clear reproduction path. This is NOT a UAT checkpoint — Bug Understanding requires iterative back-and-forth until the reproduction path is clear.

### Phase 2: Codebase Investigation [UAT]

**Goal**: Trace the bug through the code.

Follow the Exploration Phase Template. Launch 2 **code-explorer** agents:
- Agent 1: "Trace the execution path for [the failing operation]. Start from [entry point] and follow through to where [the failure occurs]. Identify every file and function in the chain."
- Agent 2: "Search for recent changes to [affected area]. Check git history for files related to [the bug]. Find any related tests that might be passing incorrectly."

After agents return, map the exact code path where the bug occurs.

**UAT topics**: exact code path where bug occurs, relevant files and functions, recent changes, related tests

### Phase 3: Scope Analysis & Decomposition [UAT]

Follow the Scope Analysis Phase Template using **bugfix** metrics.

### Phase 4: Root Cause Analysis [UAT]

**Goal**: Identify the actual root cause, not just symptoms.

Based on investigation:
- Present your hypothesis for the root cause with evidence
- Identify whether this is a logic error, data issue, race condition, missing edge case, etc.
- Check if there are related bugs (same root cause could affect other paths)

If multiple possible causes, present them ranked by likelihood.

**UAT topics**: root cause hypothesis with evidence, error type, related bugs sharing the same root cause

### Phase 5: Fix Strategy [UAT]

**Goal**: Design the fix with regression prevention.

- Design the minimal fix for the root cause
- Identify what tests need to be added to prevent regression
- Identify what existing tests might need updating
- Check for related code that might have the same bug

**UAT topics**: minimal fix, regression tests to add, existing tests to update, related code to check

### Phase 6: Plan Construction

Follow the Plan Construction Phase Template. Task-specific content:
- **Cold start**: check if the bug is still present before fixing
- **Phases**: Phase 1: Fix root cause → Phase 2: Add regression tests → Phase 3: Verify no breakage
- **Guardrails**: "Do NOT fix symptoms — fix the root cause", "Do NOT modify unrelated code", "Verify the original reproduction case passes"
- **Iteration range**: Simple (one file, clear cause): 5-8, Medium (multi-file, clear cause): 8-12, Complex (unclear cause, multiple files): 12-18

### Phase 7: Validation + Presentation

Validate, run pre-flight checks, and present. Same as feature workflow phases 7-8.

---

## Refactor/Chore Workflow (7 phases)

### Phase 1: Scope Definition (deep)

**Goal**: Define exactly what's being refactored and why.

Clarify with the user:
- What code needs refactoring?
- Why? (tech debt, readability, performance, new pattern adoption)
- What's the target end state?
- What must NOT change? (external behavior, APIs, interfaces)
- What's the acceptable risk level?

If the user describes the refactor vaguely (e.g., "clean up the auth module"), ask: What specifically is wrong with it today? What does "clean" look like? What would success look like?

This is NOT a UAT checkpoint — Scope Definition requires iterative back-and-forth until the scope is clearly defined.

### Phase 2: Current State Analysis [UAT]

**Goal**: Map what exists before changing it.

Follow the Exploration Phase Template. Launch 1-2 **code-explorer** agents:
- Agent 1: "Map the current architecture of [area to refactor]. Identify all files, dependencies, callers, and tests. List everything that would break if this code changed."
- Agent 2 (if large scope): "Find all usages of [thing being refactored] across the codebase. Include imports, type references, and indirect dependencies."

After agents return, build a dependency map.

**UAT topics**: all files involved, dependency map, callers, existing tests, breakage risks

### Phase 3: Scope Analysis & Decomposition [UAT]

Follow the Scope Analysis Phase Template using **refactor** metrics.

### Phase 4: Target State Design [UAT]

**Goal**: Define the end state concretely.

- Present the target architecture with specific file changes
- Show how dependencies will be updated
- Identify breaking changes and migration path
- If adopting a new pattern, show examples of the pattern from the codebase (or propose one)

**UAT topics**: target architecture, file changes, dependency updates, breaking changes, migration path

### Phase 5: Migration Strategy [UAT]

**Goal**: Plan the safest path from current to target state.

Design an incremental migration that:
- Never leaves the codebase in a broken state between phases
- Has verification at each step
- Can be partially reverted if something goes wrong
- Updates callers before removing old interfaces

**UAT topics**: migration phases in order, verification at each step, revert strategy, caller update plan

### Phase 6: Plan Construction

Follow the Plan Construction Phase Template. Task-specific content:
- **Cold start**: check what's already been migrated
- **Phases**: ordered by dependency (inner layers first, callers last), each independently verifiable
- **Guardrails**: "Do NOT change external behavior", "Do NOT skip updating callers", "Run full test suite after each phase", "Make targeted edits, not file rewrites"
- **Completion**: all tests pass, no references to old pattern remain
- **Iteration range**: Small (1-3 files): 5-8, Medium (4-8 files): 10-15, Large (9+ files): 15-22

### Phase 7: Validation + Presentation

Validate, run pre-flight checks, and present.

---

## Testing Workflow (6 phases)

### Phase 1: Coverage Analysis [UAT]

**Goal**: Understand what's tested and what isn't.

Follow the Exploration Phase Template. Launch 1-2 **code-explorer** agents:
- Agent 1: "Find all test files in this project. Identify the testing framework, test patterns, and conventions used. Map which source files have corresponding tests and which don't."
- Agent 2: "Analyze [area to test]. Identify all public functions, API endpoints, and user-facing behavior. Note edge cases, error paths, and boundary conditions."

Ask the user:
- What areas are highest priority for testing?
- What test types? (unit, integration, e2e)
- Any specific edge cases or scenarios to cover?
- What's the target coverage goal?

After gathering exploration results AND user answers, synthesize a coverage picture.

**UAT topics**: testing framework and conventions, coverage map, user's priority areas and coverage goals

### Phase 2: Scope Analysis & Decomposition [UAT]

Follow the Scope Analysis Phase Template using **testing** metrics.

### Phase 3: Test Strategy [UAT]

**Goal**: Prioritize what to test and how.

Based on exploration:
- List untested functions/paths ranked by risk
- Recommend test types for each area
- Identify shared test utilities or fixtures to create
- Map dependencies that need mocking/stubbing

**UAT topics**: untested paths ranked by risk, test types per area, shared utilities, mocking dependencies

### Phase 4: Clarifying Questions

**Goal**: Resolve testing-specific ambiguities.

- What should be mocked vs tested against real implementations?
- Are there test databases, fixtures, or seed data?
- What's the acceptable test runtime?
- Any flaky test patterns to avoid?

### Phase 5: Plan Construction

Follow the Plan Construction Phase Template. Task-specific content:
- **Cold start**: run existing test suite, check current coverage
- **Phases**: ordered by priority (critical paths first), each adds tests for one logical area
- **Guardrails**: "Do NOT modify source code to make tests pass", "Follow existing test patterns", "Test behavior not implementation", "Do NOT write tests that test the framework"
- **Iteration range**: Small (5-10 tests): 5-8, Medium (10-25 tests): 10-15, Large (25+ tests): 15-20

### Phase 6: Validation + Presentation

Validate, run pre-flight checks, and present.

---

## Performance Optimization Workflow (6 phases)

### Phase 1: Problem Definition (deep)

**Goal**: Define what's slow, how slow, and what's acceptable.

Clarify with the user:
- What's slow? (specific operation, endpoint, page load)
- How slow is it now? (measured or estimated)
- What's the target? (specific number: <200ms, <1s)
- How to measure? (benchmark command, profiling tool, load test)
- What trade-offs are acceptable? (memory vs speed, complexity vs performance)

Do not accept vague performance complaints. Insist on specifics: which operation, what latency, what is acceptable. This is NOT a UAT checkpoint — Problem Definition requires iterative back-and-forth until the performance target is concrete.

### Phase 2: Profiling & Analysis [UAT]

**Goal**: Find the actual bottleneck, don't guess.

Follow the Exploration Phase Template. Launch 1-2 **code-explorer** agents:
- Agent 1: "Trace the execution path of [slow operation]. Identify database queries, external API calls, loops, and data transformations. Flag anything that could be O(n²) or worse."
- Agent 2: "Find caching, indexing, and optimization patterns already used in this codebase. Identify if [slow area] is missing any of these."

**UAT topics**: identified bottlenecks with evidence, existing optimization patterns, what the slow area is missing

### Phase 3: Scope Analysis & Decomposition [UAT]

Follow the Scope Analysis Phase Template using **performance** metrics.

### Phase 4: Optimization Strategy [UAT]

**Goal**: Design the optimization with measurable targets.

- Present optimization approaches ranked by expected impact
- Each approach must have a measurable before/after verification
- Identify risks (correctness issues, cache invalidation complexity, etc.)

**UAT topics**: optimization approaches with expected impact, measurable verification for each, risks and trade-offs

### Phase 5: Plan Construction

Follow the Plan Construction Phase Template. Task-specific content:
- **Cold start**: run baseline benchmark, record numbers
- **Phases**: each optimizes one specific bottleneck with benchmark verification
- **Guardrails**: "Do NOT sacrifice correctness for speed", "Measure before and after every change", "If an optimization makes no measurable difference, revert it"
- **Completion**: benchmark meets target threshold
- **Iteration range**: Single bottleneck: 5-10, Multiple bottlenecks: 10-18, System-wide: 15-22

### Phase 6: Validation + Presentation

Validate, run pre-flight checks, and present.

---

## Research Workflow (8 phases)

### Phase 1: Research Goal Definition (deep)

**Goal**: Clarify what the research should answer and what the deliverable looks like.

Gather from the user:
- What is the research question or topic?
- What is the deliverable format? (comparison doc, architecture decision record, feasibility study, survey of approaches)
- What are the scope boundaries? (which parts of the codebase, which technologies, what's out of scope)
- How deep should the investigation go? (surface-level overview vs deep-dive analysis)
- Who is the audience? (team members, future self, stakeholders)
- Who will act on this research? What decision will it inform?

Push back on overly broad research questions. A good research question has a clear "done" state.

Do NOT proceed until the research question is specific enough to have a clear "done" state. This is NOT a UAT checkpoint — Goal Definition requires iterative back-and-forth until the research question is sharp.

### Phase 2: Source Identification [UAT]

**Goal**: Map codebase sources, architecture, and prior decisions related to the research topic.

Follow the Exploration Phase Template. Launch 2-3 **code-explorer** agents:
- Agent 1: "Find all code, configuration, and documentation related to [research topic]. Identify relevant files, patterns, and conventions. Return file paths and key excerpts."
- Agent 2: "Map the architecture and design decisions in [relevant area]. Identify how the current implementation works, what trade-offs were made, and where decisions are documented (comments, ADRs, READMEs)."
- Agent 3 (if applicable): "Search for prior art, alternative approaches, or related implementations in this codebase. Look for TODOs, FIXMEs, or comments referencing [topic]. Check git history for relevant discussions."

After agents return, build a source inventory before proceeding.

**UAT topics**: sources found and relevance, prior decisions discovered, gaps needing external research

### Phase 3: Scope Analysis & Decomposition [UAT]

Follow the Scope Analysis Phase Template using **research** metrics.

### Phase 4: Research Plan & Clarifying Questions [UAT]

**Goal**: Propose a research outline and resolve ambiguities before investigation begins.

Based on source identification, propose:
- A document outline with specific sections (e.g., "Background", "Approach A: ...", "Approach B: ...", "Comparison Matrix", "Recommendation")
- Expected length and depth per section
- What can be answered from the codebase vs what requires external knowledge

Present ALL clarifying questions:
- Should the research cover [specific subtopic]?
- How should trade-offs be weighted? (e.g., performance vs simplicity)
- Are there constraints or preferences that should bias the analysis?
- Is there a preferred format for the deliverable?

**Wait for the user to answer all clarifying questions.** Then incorporate their answers into the research plan.

**UAT topics**: finalized outline with sections, depth per section, codebase vs external knowledge split

### Phase 5: Investigation Strategy [UAT]

**Goal**: Define what to investigate for each section and how to verify findings.

For each section in the confirmed outline:
- What specific questions does this section answer?
- What evidence is needed? (code examples, benchmarks, documentation references)
- What commands or searches will surface the evidence?
- What rabbit holes should be avoided? (tangential topics, excessive depth on one area)

Key constraints:
- Max 2 investigation iterations per section — prevents deep-diving one topic endlessly
- Every claim must cite evidence: file:line, command output, or URL
- Read-only approach to source code — research must NOT modify any existing files

**UAT topics**: per-section investigation plan, rabbit holes to avoid, constraints

### Phase 6: Plan Construction

**Goal**: Build the ralph-loop prompt with research-specific adaptations.

Follow the Plan Construction Phase Template. Task-specific content:
- **Cold start**: check if the deliverable file exists, read it, determine what sections are complete vs remaining, resume from where the document left off
- **Phases**: one phase per document section, in outline order
- **Verification**: structural commands:
  - `grep -c "^## " <deliverable>` — section count matches outline
  - `wc -w <deliverable>` — minimum word count met
  - `grep -c "TODO\|PLACEHOLDER\|TBD" <deliverable>` — no placeholders remain
  - `grep -c "file:.*line\|\.rb:\|\.ts:\|\.py:\|http" <deliverable>` — evidence citations exist
  - Section existence checks via `grep "^## <Section Name>" <deliverable>`
- **Scope**: the ONLY file created or modified is the deliverable document — source code is strictly read-only
- **Guardrails**:
  - "Do NOT modify any source code files — the deliverable document is the only writable file"
  - "Every claim must cite evidence: file:line reference, command output, or URL"
  - "Do NOT spend more than 2 iterations on any single section — move on and mark incomplete sections with TODO"
  - "Do NOT add filler, preamble, or restating the research question — every sentence must add information"
  - "Do NOT go down rabbit holes — if a subtopic is tangential, note it as 'Out of Scope' and move on"
  - "Cross-reference prior sections when building on earlier findings"
- **Completion**: all sections present, no TODO/PLACEHOLDER/TBD, evidence citations in every substantive section, synthesis cross-references prior sections, minimum word count met
- **Iteration range**: Narrow (1-2 sections): 5-8, Medium (3-5 sections): 8-14, Broad (6+ sections): 14-20

### Phase 7: Validation

Launch all 6 validation agents in parallel on the drafted plan. Refine per severity tier rules in the prompt-validation skill.

After validation passes, run pre-flight checks per the "Pre-flight Validation" section of finesse.md Common Final Phases. Collect warnings for presentation.

### Phase 8: Presentation

Present the validated plan. On acceptance, save to `finesse-plans/` and output the command.

---

## Multi-Workflow Execution (Decomposed Tasks)

When the Scope Analysis phase results in an accepted decomposition, the remaining workflow phases operate differently:

**Shared phases**: Discovery/Understanding, Exploration/Investigation, and Scope Analysis are shared across all sub-workflows. They run once and their outputs are included in every sub-workflow's prompt context.

**Shared architecture**: If the workflow includes an Architecture Design phase (Feature), architecture decisions are shared. The architect designs the overall system; decomposition determines which pieces each sub-workflow builds.

**Per-sub-workflow phases**: Only Plan Construction and Validation run independently for each sub-workflow. Each gets its own prompt, promise, and plan files.

**Clarifying Questions**: Run once with awareness of all sub-workflows. Questions may be sub-workflow-specific but are asked in a single batch.

**Context budget**: Each sub-workflow gets its own context budget estimate (since each runs in its own context window). If any sub-workflow exceeds critical pressure (>80%), the re-route fires for that specific sub-workflow. An aggregate summary of all sub-workflow budgets is included in `execution-graph.md`.

**Validation**: Each sub-workflow's prompt is validated independently by all 6 standard validation agents.

**Presentation**: All sub-workflows are presented together with the execution graph. The user accepts or rejects the entire decomposition as a unit.

**Per-wave execution commands** — The `execution-graph.md` file includes ready-to-run commands for each sub-workflow:

```
## Wave 1 (run in parallel)
/finesse:finesse-execute --prompt-file finesse-plans/<session>/wave-1/<task>/prompt.md --completion-promise-file finesse-plans/<session>/wave-1/<task>/promise.txt --max-iterations <N>

## Wave 2 (run after Wave 1 completes)
/finesse:finesse-execute --prompt-file finesse-plans/<session>/wave-2/<task>/prompt.md --completion-promise-file finesse-plans/<session>/wave-2/<task>/promise.txt --max-iterations <N>
```
