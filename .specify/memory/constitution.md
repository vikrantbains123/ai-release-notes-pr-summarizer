<!--
Sync Impact Report
- Version change: (none) → 1.0.0 (initial ratification)
- Modified principles: n/a (first version)
- Added sections:
  - Core Principles: I. Test-First Development (NON-NEGOTIABLE), II. Cost
    Transparency, III. Simplicity & CLI-First, IV. Secrets Never Committed
  - Technology Constraints
  - Development Workflow
  - Governance
- Removed sections: n/a
- Deferred TODOs: none — all placeholders resolved
-->

# AI Release Notes & PR Summarizer Constitution

## Core Principles

### I. Test-First Development (NON-NEGOTIABLE)
Every feature or bug fix MUST have tests written before its implementation
code, following red-green-refactor: write the test, watch it fail, then
implement until it passes. A task is not "done" until its tests exist and
pass. Tests covering GitHub API or Anthropic API integration MUST run
against mocks/fakes, not live network calls, so the suite is deterministic
and runnable offline without consuming real API quota.

Rationale: This is a learning project — writing tests first forces
thinking through expected behavior before code, and keeps live API calls
(cost, rate limits, flakiness) out of the test suite entirely.

### II. Cost Transparency
Every call to the Anthropic API MUST report the tokens consumed (input and
output) and an estimated dollar cost, computed from the model's published
per-token pricing. Each CLI run MUST print a cost summary and append a
structured record to `logs/cost/runs/usage_log.jsonl`. No feature that
calls an LLM may ship without this reporting in place.

Rationale: Understanding the real cost of running the tool is a stated
goal of this project, not an afterthought — making it a hard requirement
prevents it from being deprioritized later.

### III. Simplicity & CLI-First
The tool MUST remain a single-purpose command-line program: one command,
one job — generate release notes / PR summaries for a given time window of
a GitHub repo. New capability MUST NOT be added speculatively; build only
what the current spec's requirements call for. No plugin systems and no
abstraction layers for hypothetical future providers (e.g. other VCS hosts
or LLMs) until a spec actually requires one.

Rationale: This is a solo, learning-oriented project — YAGNI keeps it
small enough to fully understand end to end, and keeps every abstraction
justified by an actual requirement instead of a guess about the future.

### IV. Secrets Never Committed
API tokens (`GITHUB_TOKEN`, `ANTHROPIC_API_KEY`) MUST be supplied via
environment variables or a local `.env` file that is git-ignored, never
hardcoded in source or committed. Generated logs, including
`logs/cost/runs/usage_log.jsonl`, MUST NOT contain raw secrets.

Rationale: This is a public GitHub repository — an accidentally committed
key is trivially scraped and abused within minutes of a push.

## Technology Constraints

- Python 3.11+, distributed as a CLI (no web service/API layer).
- GitHub REST API is the only supported data source for PRs/commits — no
  other VCS provider until a spec requires it (see Principle III).
- Anthropic Claude API is the only supported LLM provider — no other LLM
  provider until a spec requires it (see Principle III).
- Prefer the standard library and a small number of well-maintained
  dependencies over heavier frameworks.
- Configuration (tokens, model name, defaults) is supplied via environment
  variables / a git-ignored `.env` file — never via committed config files.

## Development Workflow

This project follows spec-driven development via GitHub Spec Kit:
`/speckit-constitution` → `/speckit-specify` → `/speckit-plan` →
`/speckit-tasks` → `/speckit-implement`. Every feature MUST have a written
spec and a task breakdown before implementation begins; implementation
work MUST trace back to a task.

Build decisions and narrative progress are recorded in
`logs/demo/DEMO_LOG.md` (for later demo material), and the cost of the
Claude Code sessions used to build this project is recorded in
`logs/cost/build/BUILD_LOG.md` at milestones. Neither log is a
governance document — they do not override this constitution — but
keeping them current is expected practice for this project.

## Governance

This constitution supersedes ad-hoc practices for this project. Any
deviation from a principle MUST be explicitly justified in the relevant
spec, plan, or PR description — silent deviation is not permitted.

**Amendment procedure**: edit this file directly, update the Sync Impact
Report at the top, and bump `CONSTITUTION_VERSION` per semantic
versioning: MAJOR for backward-incompatible principle removals or
redefinitions, MINOR for a new principle or materially expanded guidance,
PATCH for wording/clarification only. Update `LAST_AMENDED_DATE` to the
date of the change.

**Compliance review**: this is currently a single-maintainer project
(vikrantbains123), so compliance is self-reviewed against these
principles before each feature is considered complete, rather than via a
separate approval board. If the project gains additional contributors,
this section should be amended to add peer review.

**Version**: 1.0.0 | **Ratified**: 2026-09-12 | **Last Amended**: 2026-09-12
