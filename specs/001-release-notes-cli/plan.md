# Implementation Plan: Release Notes & PR Summary Generation

**Branch**: `001-release-notes-cli` | **Date**: 2026-09-12 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-release-notes-cli/spec.md`

## Summary

A single-purpose Python CLI that, given a target GitHub repository and a time
window (dates, ref pair, or defaulted to the last month), fetches merged pull
requests, sends them to the Anthropic Claude API to produce a customer-facing,
categorized summary (with internal/technical changes set apart), writes it to
a local Markdown file, and optionally publishes it once — immutably — as a
GitHub Release identified by version/tag. Every Claude API call reports token
usage and estimated cost. Technical approach: a small set of focused modules
(GitHub client, window resolution, summarization history, Claude
summarization, cost tracking, rendering) behind a thin `argparse` CLI, with
the GitHub and Anthropic clients mocked in all tests per the constitution's
Test-First principle.

## Technical Context

**Language/Version**: Python 3.11+ (per constitution Technology Constraints)

**Primary Dependencies**: `anthropic` (official Claude SDK — no reasonable
stdlib alternative for the API contract/streaming/retry semantics),
`requests` (GitHub REST API calls — lighter than PyGithub, no ORM-style
abstraction we don't need), `python-dotenv` (loads `.env` into the
environment). Deliberately excludes a CLI framework (e.g. Click/Typer) in
favor of stdlib `argparse`, and excludes a retry-library dependency (e.g.
tenacity) in favor of a small hand-written retry loop — both per the
Simplicity & CLI-First principle. See `research.md`.

**Storage**: Local files only — the generated Markdown summary, the
Summarization History record (which PRs have already been reported), and the
cost usage log (`logs/cost/runs/usage_log.jsonl`). No database.

**Testing**: `pytest`, with `unittest.mock` for stubbing the GitHub and
Anthropic HTTP calls (no live network calls in the test suite, no added
mocking-library dependency — per constitution Principle I).

**Target Platform**: Cross-platform CLI — anywhere Python 3.11+ runs
(macOS/Linux/Windows); no OS-specific APIs.

**Project Type**: Single project — command-line tool (Option 1 structure).

**Performance Goals**: Not a high-throughput system — this is a manually
invoked, single-run tool. A typical run (tens of PRs, one Claude call)
completing in well under a minute is sufficient; no server-style throughput
target applies.

**Constraints**: Requires network access to GitHub and the Anthropic API at
runtime (per spec Assumptions) — not offline-capable. No hard memory/latency
budget beyond "usable interactively for a single maintainer."

**Scale/Scope**: Single repository, single time window, single user per run.
Soft cap of 300 pull requests per window (FR-017); exceeding it is a
reported error, not silent truncation or multi-call batching.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|---|---|---|
| I. Test-First Development (NON-NEGOTIABLE) | Every module planned below has a corresponding test target; GitHub/Anthropic clients are mocked, not called live, in tests | PASS — structure below separates `github_client.py`/`summarizer.py` (thin I/O wrappers) from logic that can be unit-tested against fakes |
| II. Cost Transparency | Every Anthropic call's token usage + estimated cost must be captured and reported/logged | PASS — dedicated `cost.py` module owns this; no Anthropic call site is allowed to bypass it (enforced at task level) |
| III. Simplicity & CLI-First | Single command, no plugin system, no multi-provider abstraction, dependencies justified individually | PASS — dependency list above is minimal and each entry is justified; no abstraction layer for hypothetical non-GitHub/non-Claude providers |
| IV. Secrets Never Committed | Tokens via env vars/`.env` only, never logged | PASS — `config.py` is the only module that reads credentials; `cost.py`/log writers never receive raw credential values |

No violations to justify — Complexity Tracking table is empty.

**Post-Design Re-check** (after Phase 1 — data-model.md, contracts/,
quickstart.md): still PASS on all four gates. `cost.py` is the single
owner of Usage Record creation (data-model.md), `config.py` is the single
reader of credentials (contracts/cli-interface.md's Configuration
contract), and no entity or module introduces a second provider or a
plugin surface. No new violations introduced by the design artifacts.

## Project Structure

### Documentation (this feature)

```text
specs/001-release-notes-cli/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── cli-interface.md
└── tasks.md             # Phase 2 output (/speckit-tasks command — NOT created here)
```

### Source Code (repository root)

```text
src/
└── ai_release_notes/
    ├── __init__.py
    ├── cli.py                # argparse entry point; wires modules together
    ├── config.py             # env/.env loading: GITHUB_TOKEN, ANTHROPIC_API_KEY, defaults
    ├── window.py              # resolves the Time Window: dates, ref pair, or default 1 month
    ├── github_client.py      # GitHub REST calls: fetch merged PRs, check/publish releases
    ├── release_identity.py   # Release Identity: name/version/RC branch/commit SHA + matching
    ├── history.py            # Summarization History: tracks already-reported PR numbers
    ├── summarizer.py         # builds the prompt, calls Anthropic, retry/backoff (FR-014)
    ├── cost.py                # Usage Record: token usage → estimated cost; writes usage_log.jsonl
    └── render.py              # renders categorized PR data + header into the Markdown document

tests/
├── unit/           # window, release_identity, history, cost, render — pure logic, no I/O mocks needed
├── integration/    # github_client, summarizer — against mocked HTTP/Anthropic responses
└── contract/       # cli.py argument/flag contract, exit codes, file-output contract
```

**Structure Decision**: Single project (Option 1) — this is one CLI tool with
no separate frontend/backend or mobile component, matching the constitution's
Simplicity & CLI-First principle. Each module above maps to one Key Entity or
responsibility from the spec, keeping logic (testable without I/O) separate
from thin I/O wrappers (`github_client.py`, `summarizer.py`) that get mocked
in tests.

## Complexity Tracking

*No entries — Constitution Check has no violations to justify.*
