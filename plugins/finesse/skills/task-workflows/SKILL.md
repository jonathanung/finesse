---
description: "Task-type-specific planning workflows for Finesse — defines phases for features, bug fixes, chores, testing, performance, and research work"
---

# Task Workflows

After detecting the task type, follow the corresponding workflow below. Every workflow ends with plan construction, validation, and presentation. The phases before that differ by task type.

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

## Feature Development Workflow (7 phases)

### Phase 1: Discovery

**Goal**: Understand what needs to be built.

- Clarify the feature request if vague
- Ask what problem it solves
- Identify constraints and requirements
- Summarize understanding and confirm with user

Do NOT proceed until the user confirms your understanding is correct.

### Phase 2: Codebase Exploration

**Goal**: Understand relevant existing code and patterns.

Launch 2-3 **code-explorer** agents in parallel via Task tool. Each explores a different aspect:
- Agent 1: "Find features similar to [feature] in this codebase. Trace their implementation end-to-end. Return entry points, execution flow, key components, and essential files."
- Agent 2: "Map the architecture and abstractions in [relevant area]. Identify patterns, conventions, file organization, and dependencies."
- Agent 3 (if applicable): "Analyze the current implementation of [related feature]. How does it handle [relevant concern like auth, data flow, error handling]?"

After agents return, READ all essential files they identified. Build deep understanding before proceeding.

Present a summary of findings to the user:
- Similar features found and how they're implemented
- Architecture patterns and conventions
- Key files and their responsibilities

### Phase 3: Clarifying Questions

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

### Phase 4: Architecture Design

**Goal**: Design multiple implementation approaches.

Launch 2-3 **code-architect** agents in parallel, each with a different focus:
- Agent 1 (Minimal Changes): "Design an implementation using the smallest changes, maximum code reuse. Context: [codebase findings + clarified requirements]"
- Agent 2 (Clean Architecture): "Design an implementation prioritizing maintainability, clean abstractions, and testability. Context: [same]"
- Agent 3 (Pragmatic Balance): "Design an implementation balancing speed and quality, fitting existing patterns. Context: [same]"

Present all approaches with trade-offs. Form and state your recommendation with reasoning. Ask which approach the user prefers.

### Phase 5: Plan Construction

**Goal**: Build the ralph-loop prompt from the chosen architecture.

Using the chosen approach, construct a complete ralph-loop prompt following the template in the meta-prompting skill. The prompt must include:
- Cold start paragraph referencing the specific files and patterns discovered
- Ordered phases matching the architecture's build sequence
- Verification commands for each phase (discovered during exploration)
- Scope constraints (files to modify, files to leave alone)
- Task-specific guardrails based on the architecture
- Completion criteria derived from the requirements

Determine ralph-loop `--max-iterations` with reasoning:
- Simple feature (1-2 files): 8-12
- Medium feature (3-5 files): 12-18
- Complex feature (6+ files): 18-25

### Phase 6: Validation

Launch all 5 validation agents in parallel on the drafted plan. Refine until all pass. (See prompt-validation skill.)

### Phase 7: Presentation

Present the validated plan. On acceptance, save to `ralph-plans/` and output the command.

---

## Bug Fix Workflow (6 phases)

### Phase 1: Bug Understanding

**Goal**: Fully understand the bug before touching code.

Gather from the user:
- What's the expected behavior?
- What's the actual behavior?
- Steps to reproduce
- When did it start? (recent change, always broken, intermittent?)
- Error messages, stack traces, logs (if available)
- Which environments? (dev, staging, prod)

Do NOT proceed until you have a clear reproduction path.

### Phase 2: Codebase Investigation

**Goal**: Trace the bug through the code.

Launch 2 **code-explorer** agents in parallel:
- Agent 1: "Trace the execution path for [the failing operation]. Start from [entry point] and follow through to where [the failure occurs]. Identify every file and function in the chain."
- Agent 2: "Search for recent changes to [affected area]. Check git history for files related to [the bug]. Find any related tests that might be passing incorrectly."

After agents return, read all identified files. Map the exact code path where the bug occurs.

### Phase 3: Root Cause Analysis

**Goal**: Identify the actual root cause, not just symptoms.

Based on investigation:
- Present your hypothesis for the root cause with evidence
- Identify whether this is a logic error, data issue, race condition, missing edge case, etc.
- Check if there are related bugs (same root cause could affect other paths)
- Ask the user to confirm the hypothesis makes sense

If multiple possible causes, present them ranked by likelihood.

### Phase 4: Fix Strategy

**Goal**: Design the fix with regression prevention.

- Design the minimal fix for the root cause
- Identify what tests need to be added to prevent regression
- Identify what existing tests might need updating
- Check for related code that might have the same bug

Present the strategy to the user. Confirm before building the prompt.

### Phase 5: Plan Construction

Build the ralph-loop prompt focused on:
- Cold start: check if the bug is still present before fixing
- Phase 1: Fix the root cause (specific files, specific changes)
- Phase 2: Add regression tests
- Phase 3: Verify fix doesn't break related functionality
- Verification: run test suite, specifically the failing case
- Guardrails: "Do NOT fix symptoms — fix the root cause", "Do NOT modify unrelated code", "Verify the original reproduction case passes"

Ralph-loop iterations:
- Simple bug (one file, clear cause): 5-8
- Medium bug (multi-file, clear cause): 8-12
- Complex bug (unclear cause, multiple files): 12-18

### Phase 6: Validation + Presentation

Validate and present. Same as feature workflow phases 6-7.

---

## Refactor/Chore Workflow (6 phases)

### Phase 1: Scope Definition

**Goal**: Define exactly what's being refactored and why.

Clarify with the user:
- What code needs refactoring?
- Why? (tech debt, readability, performance, new pattern adoption)
- What's the target end state?
- What must NOT change? (external behavior, APIs, interfaces)
- What's the acceptable risk level?

### Phase 2: Current State Analysis

**Goal**: Map what exists before changing it.

Launch 1-2 **code-explorer** agents:
- Agent 1: "Map the current architecture of [area to refactor]. Identify all files, dependencies, callers, and tests. List everything that would break if this code changed."
- Agent 2 (if large scope): "Find all usages of [thing being refactored] across the codebase. Include imports, type references, and indirect dependencies."

After agents return, read essential files. Build a dependency map.

### Phase 3: Target State Design

**Goal**: Define the end state concretely.

- Present the target architecture with specific file changes
- Show how dependencies will be updated
- Identify breaking changes and migration path
- If adopting a new pattern, show examples of the pattern from the codebase (or propose one)

Ask the user to confirm the target state.

### Phase 4: Migration Strategy

**Goal**: Plan the safest path from current to target state.

Design an incremental migration that:
- Never leaves the codebase in a broken state between phases
- Has verification at each step
- Can be partially reverted if something goes wrong
- Updates callers before removing old interfaces

Present the strategy. Confirm with user.

### Phase 5: Plan Construction

Build the ralph-loop prompt focused on:
- Cold start: check what's already been migrated
- Phases ordered by dependency (inner layers first, callers last)
- Each phase independently verifiable
- Guardrails: "Do NOT change external behavior", "Do NOT skip updating callers", "Run full test suite after each phase", "Make targeted edits, not file rewrites"
- Completion: all tests pass, no references to old pattern remain

Ralph-loop iterations:
- Small refactor (1-3 files): 5-8
- Medium refactor (4-8 files): 10-15
- Large refactor (9+ files): 15-22

### Phase 6: Validation + Presentation

Validate and present.

---

## Testing Workflow (5 phases)

### Phase 1: Coverage Analysis

**Goal**: Understand what's tested and what isn't.

Launch 1-2 **code-explorer** agents:
- Agent 1: "Find all test files in this project. Identify the testing framework, test patterns, and conventions used. Map which source files have corresponding tests and which don't."
- Agent 2: "Analyze [area to test]. Identify all public functions, API endpoints, and user-facing behavior. Note edge cases, error paths, and boundary conditions."

Ask the user:
- What areas are highest priority for testing?
- What test types? (unit, integration, e2e)
- Any specific edge cases or scenarios to cover?
- What's the target coverage goal?

### Phase 2: Test Strategy

**Goal**: Prioritize what to test and how.

Based on exploration:
- List untested functions/paths ranked by risk
- Recommend test types for each area
- Identify shared test utilities or fixtures to create
- Map dependencies that need mocking/stubbing

Present the strategy. Confirm with user.

### Phase 3: Clarifying Questions

**Goal**: Resolve testing-specific ambiguities.

- What should be mocked vs tested against real implementations?
- Are there test databases, fixtures, or seed data?
- What's the acceptable test runtime?
- Any flaky test patterns to avoid?

### Phase 4: Plan Construction

Build the ralph-loop prompt focused on:
- Cold start: run existing test suite, check current coverage
- Phases ordered by priority (critical paths first)
- Each phase adds tests for one logical area
- Verification: test suite passes, coverage increases
- Guardrails: "Do NOT modify source code to make tests pass", "Follow existing test patterns", "Test behavior not implementation", "Do NOT write tests that test the framework"

Ralph-loop iterations:
- Small test suite (5-10 tests): 5-8
- Medium test suite (10-25 tests): 10-15
- Large test suite (25+ tests): 15-20

### Phase 5: Validation + Presentation

Validate and present.

---

## Performance Optimization Workflow (5 phases)

### Phase 1: Problem Definition

**Goal**: Define what's slow, how slow, and what's acceptable.

Clarify with the user:
- What's slow? (specific operation, endpoint, page load)
- How slow is it now? (measured or estimated)
- What's the target? (specific number: <200ms, <1s)
- How to measure? (benchmark command, profiling tool, load test)
- What trade-offs are acceptable? (memory vs speed, complexity vs performance)

### Phase 2: Profiling & Analysis

**Goal**: Find the actual bottleneck, don't guess.

Launch 1-2 **code-explorer** agents:
- Agent 1: "Trace the execution path of [slow operation]. Identify database queries, external API calls, loops, and data transformations. Flag anything that could be O(n²) or worse."
- Agent 2: "Find caching, indexing, and optimization patterns already used in this codebase. Identify if [slow area] is missing any of these."

Present findings: where time is actually spent, not where you think it might be.

### Phase 3: Optimization Strategy

**Goal**: Design the optimization with measurable targets.

- Present optimization approaches ranked by expected impact
- Each approach must have a measurable before/after verification
- Identify risks (correctness issues, cache invalidation complexity, etc.)

Confirm approach with user.

### Phase 4: Plan Construction

Build the ralph-loop prompt focused on:
- Cold start: run baseline benchmark, record numbers
- Each phase optimizes one specific bottleneck
- Verification: run benchmark after each change, compare to baseline
- Guardrails: "Do NOT sacrifice correctness for speed", "Measure before and after every change", "If an optimization makes no measurable difference, revert it"
- Completion: benchmark meets target threshold

Ralph-loop iterations:
- Single bottleneck: 5-10
- Multiple bottlenecks: 10-18
- System-wide optimization: 15-22

### Phase 5: Validation + Presentation

Validate and present.

---

## Research Workflow (7 phases)

### Phase 1: Research Goal Definition

**Goal**: Clarify what the research should answer and what the deliverable looks like.

Gather from the user:
- What is the research question or topic?
- What is the deliverable format? (comparison doc, architecture decision record, feasibility study, survey of approaches)
- What are the scope boundaries? (which parts of the codebase, which technologies, what's out of scope)
- How deep should the investigation go? (surface-level overview vs deep-dive analysis)
- Who is the audience? (team members, future self, stakeholders)

Do NOT proceed until the research question is specific enough to have a clear "done" state.

### Phase 2: Source Identification

**Goal**: Map codebase sources, architecture, and prior decisions related to the research topic.

Launch 2-3 **code-explorer** agents in parallel:
- Agent 1: "Find all code, configuration, and documentation related to [research topic]. Identify relevant files, patterns, and conventions. Return file paths and key excerpts."
- Agent 2: "Map the architecture and design decisions in [relevant area]. Identify how the current implementation works, what trade-offs were made, and where decisions are documented (comments, ADRs, READMEs)."
- Agent 3 (if applicable): "Search for prior art, alternative approaches, or related implementations in this codebase. Look for TODOs, FIXMEs, or comments referencing [topic]. Check git history for relevant discussions."

After agents return, READ all identified files. Build a source inventory before proceeding.

Present a summary:
- Sources found and their relevance
- Prior decisions or context discovered
- Gaps where external research may be needed

### Phase 3: Research Plan & Clarifying Questions

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

**Wait for answers and outline confirmation before proceeding.**

### Phase 4: Investigation Strategy

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

Present the investigation strategy. Confirm with user.

### Phase 5: Plan Construction

**Goal**: Build the ralph-loop prompt with research-specific adaptations.

Build the ralph-loop prompt focused on:
- Cold start: check if the deliverable file exists, read it, determine what sections are complete vs remaining, resume from where the document left off
- Ordered phases: one phase per document section, in outline order
- Verification via structural commands:
  - `grep -c "^## " <deliverable>` — check section count matches outline
  - `wc -w <deliverable>` — check minimum word count is met
  - `grep -c "TODO\|PLACEHOLDER\|TBD" <deliverable>` — check no placeholders remain
  - `grep -c "file:.*line\|\.rb:\|\.ts:\|\.py:\|http" <deliverable>` — check evidence citations exist
  - Section existence checks via `grep "^## <Section Name>" <deliverable>`
- Scope constraints: the ONLY file created or modified is the deliverable document — source code is strictly read-only
- Research-specific guardrails:
  - "Do NOT modify any source code files — the deliverable document is the only writable file"
  - "Every claim must cite evidence: file:line reference, command output, or URL"
  - "Do NOT spend more than 2 iterations on any single section — move on and mark incomplete sections with TODO"
  - "Do NOT add filler, preamble, or restating the research question — every sentence must add information"
  - "Do NOT go down rabbit holes — if a subtopic is tangential, note it as 'Out of Scope' and move on"
  - "Cross-reference prior sections when building on earlier findings"
- Completion criteria:
  - All sections from the outline are present
  - No TODO, PLACEHOLDER, or TBD markers remain
  - Evidence citations present in every substantive section
  - Synthesis/recommendation section cross-references prior sections
  - Minimum word count met (defined during Phase 3)

Ralph-loop iterations:
- Narrow research (1-2 sections, single area): 5-8
- Medium research (3-5 sections, comparison): 8-14
- Broad research (6+ sections, comprehensive): 14-20

### Phase 6: Validation

Launch all 5 validation agents in parallel on the drafted plan. Refine until all pass. (See prompt-validation skill.)

### Phase 7: Presentation

Present the validated plan. On acceptance, save to `ralph-plans/` and output the command.
