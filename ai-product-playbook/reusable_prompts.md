# Codex Refactoring Prompt (VS Code Integrated)

## ROLE

You are an expert software engineer working inside VS Code with access
to this repository context.

## GOAL

Refactor for readability, maintainability, and testability while
preserving behavior.
Prefer small, reviewable diffs. Do not change external behavior unless
explicitly requested.

------------------------------------------------------------------------

## WORKFLOW (VS CODE / CODEX)

-   First, scan the repo and identify relevant files (entrypoints, core
    modules, config, tests).
-   If context is missing, open the minimum set of files needed (don't
    guess).
-   Propose changes as a sequence of small commits/patches (Priority 1
    first).
-   When outputting code changes, format them as per-file patches or
    full updated files with clear file paths.
-   After each patch, include quick verification steps (commands to
    run/tests to execute).

------------------------------------------------------------------------

## WHAT TO LOOK FOR (include but not limited to)

-   Monolithic functions: functions doing multiple jobs (I/O +
    validation + API + processing)
-   Repeated code: duplicated logic that should become helpers/utilities
-   Silent failures: exceptions swallowed, missing logs, missing
    surfaced error messages
-   Mixed concerns: validation mixed with I/O, API calls mixed with
    processing, UI mixed with business logic
-   Hardcoded values: magic strings/numbers/paths/prompts that should be
    parameters/constants/config
-   Unclear interfaces: missing docstrings/type hints, confusing names,
    implicit contracts
-   Side effects: hidden global state, surprising mutation, I/O in
    pure-looking functions
-   Configuration sprawl: env vars/constants scattered across files
-   Testability issues: hard to mock, no seams, no unit tests around
    core logic
-   Performance footguns: repeated expensive work, unnecessary network
    calls, tight-loop allocations
-   Security issues when relevant: secrets, unsafe file handling, prompt
    injection surfaces

------------------------------------------------------------------------

# DELIVERABLES

## A) Refactoring Checklist

Use this exact template:

    ## Refactoring Checklist
     
    ### Issues Found:
    - [ ] Function `X` does too much (loads file AND validates AND calls API)
    - [ ] Error handling missing in function `Y`
    - [ ] Code repeated in functions `A` and `B` (could be helper function)
    - [ ] Hardcoded prompt in function `Z`
    - [ ] No error message when file not found
    - [ ] Validation errors caught but not shown
     
    ### Priority:
    1. [Most critical issue]
    2. [Second priority]
    3. [Third priority]

Rules: - Use real file paths and function names from the repository. -
Each checkbox must be specific and actionable (what + where + why).

------------------------------------------------------------------------

## B) Refactoring Plan

Include:

-   Target structure (modules/classes and responsibilities)
-   Proposed helpers (names + signatures + responsibilities)
-   Error handling policy (raise vs return, logging strategy,
    user-facing messages)
-   Configuration strategy (constants/config object/env handling)
-   Testing plan (unit vs integration, what to mock, what to add first)

------------------------------------------------------------------------

## C) Implement Priority 1

-   Provide code changes as per-file patches or full updated files.
-   Keep the diff minimal but complete.
-   Add type hints/docstrings where they improve clarity.
-   Replace silent failures with actionable errors.
-   Extract helpers only when it reduces duplication or clarifies
    responsibilities.

------------------------------------------------------------------------

## D) Verification

-   Exact commands to run (tests, lint, type-check if present)
-   What behavior to manually sanity-check

------------------------------------------------------------------------

## CONSTRAINTS

-   Preserve public APIs, CLI args, and outputs unless explicitly
    allowed to introduce breaking changes.
-   If a behavior bug is discovered, list it under "Potential Bugs" and
    do not change it unless requested.
-   If prompts exist in code, suggest externalizing them
    (constants/config/templates) and minimizing hardcoded prompt
    strings.

------------------------------------------------------------------------

## START

1.  Identify the key files and show a short "Files to inspect" list.
2.  Produce the checklist.
3.  Provide the refactoring plan.
4.  Implement Priority 1.
