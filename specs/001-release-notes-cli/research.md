# Phase 0 Research: Release Notes & PR Summary Generation

No `NEEDS CLARIFICATION` markers remain in Technical Context — the project
constitution already fixed language, hosting platform, and AI provider. The
research below resolves the concrete implementation-pattern decisions needed
before design (Phase 1), one per unknown/technology choice.

## GitHub API access

**Decision**: Use the `requests` library against the GitHub REST API
directly (pulls, releases endpoints), not the `PyGithub` SDK.

**Rationale**: `PyGithub` wraps the API in an ORM-like object model with far
more surface area than this tool needs (one read path: merged PRs in a
window; one write path: create/check a release). `requests` keeps the
dependency footprint and the abstraction to exactly what FR-002/FR-011/FR-012
require, in line with the Simplicity & CLI-First principle.

**Alternatives considered**: `PyGithub` (rejected — heavier abstraction than
needed); GitHub's official GraphQL API (rejected — REST's `/pulls` and
`/releases` endpoints are sufficient and simpler to mock in tests than a
GraphQL query/response shape).

## Anthropic API access

**Decision**: Use the official `anthropic` Python SDK.

**Rationale**: It owns the request/response contract (including the
`usage.input_tokens`/`usage.output_tokens` fields Cost Transparency depends
on) and its retry/timeout semantics, which a hand-rolled `requests` client
would have to reimplement. This is the one dependency with no reasonable
stdlib alternative.

**Alternatives considered**: Raw `requests` calls against the Anthropic HTTP
API (rejected — would re-implement what the SDK already provides, with no
simplicity benefit since the SDK is officially maintained).

## CLI argument parsing

**Decision**: Stdlib `argparse`.

**Rationale**: The CLI is one command with a handful of flags (repo, window
inputs, output path, publish flag) — well within what `argparse` handles
cleanly. Avoids adding Click/Typer as a dependency for a surface this small.

**Alternatives considered**: `click` / `typer` (rejected — nicer ergonomics
for larger CLIs with subcommands, but this tool has neither; would violate
Simplicity & CLI-First without a corresponding benefit).

## Retry/backoff for AI call failures (FR-014)

**Decision**: A small hand-written retry loop inside `summarizer.py` — 3
attempts total, exponential backoff starting at 2 seconds and doubling each
attempt (2s, then 4s) — not a dependency like `tenacity`.

**Rationale**: The requirement (FR-014) is narrow and now fully quantified —
retry a failed/timed-out call up to 2 additional times with a short, fixed
backoff schedule, then abort cleanly. A ~15-line loop covers this without
adding a dependency whose generality (arbitrary retry policies, decorators,
jitter strategies) this tool doesn't need.

**Alternatives considered**: `tenacity` (rejected — general-purpose retry
library, more configurability than FR-014 requires).

## Summarization History storage (FR-016, dedup across runs)

**Decision**: A local JSON file (e.g. `.ai-release-notes/history.json`) keyed
by repository, storing the set of pull request numbers already included in a
previously generated summary.

**Rationale**: Simplest structure that satisfies FR-016 (never report a PR
twice) without a database, consistent with the constitution's Storage
constraint (files only). A flat JSON set is trivial to read, update
atomically, and unit-test.

**Alternatives considered**: Deriving "already covered" purely from the
previous window's end date (rejected — doesn't hold up if windows are
requested out of order or overlap irregularly; an explicit record is more
robust and directly testable against FR-016/SC-008).

## Release Identity matching (FR-011, FR-012, FR-013)

**Decision**: Before publishing, `github_client.py` lists the repository's
releases (via the list-releases endpoint, which includes drafts) and checks
client-side for one whose tag matches the resolved Release Identity's
version — rather than using the tag-specific "get release by tag" endpoint,
which does not reliably return draft releases (a draft may not yet have its
tag fully attached until published). If a match of *any* state (draft or
published) is found, publishing is skipped and FR-013's message is
reported; the local Markdown file is still written either way (immutability
applies to the *published release*, not local output — see spec
Clarifications).

**Rationale**: FR-012 (per the pre-implementation checklist review) treats a
matching draft as "already existing," same as a published release — so the
matching check must actually see drafts, which the tag-specific lookup
endpoint doesn't reliably do. Listing releases and filtering client-side by
`version` is a small extra step but is the only approach that satisfies the
requirement as written.

**Alternatives considered**: Embedding a hidden marker in the release body
to detect prior publication (rejected — GitHub's own tag uniqueness already
gives us this for free, so a marker would be redundant).

## Cost calculation (FR-007, Cost Transparency)

**Decision**: A small static pricing table in `cost.py` (per-model
input/output cost per token), populated from Anthropic's published pricing
for the model(s) this tool supports, combined with the `usage` field on each
API response to compute `estimated_cost_usd`.

**Rationale**: Directly satisfies FR-007 and the constitution's Cost
Transparency principle using only data the SDK already returns; no external
pricing lookup/service call needed. Per spec Assumptions, the table is
maintained manually by the developer (no automated staleness detection in
v1) and `estimated_cost_usd` is computed and stored at 6 decimal places of
precision (data-model.md), displayed to the user rounded to 4.

**Alternatives considered**: Calling an external pricing API at runtime
(rejected — adds a network dependency and failure mode for a number that
changes rarely enough to hardcode and update on release).

## Configuration loading

**Decision**: `python-dotenv` to load a local `.env` file into the process
environment on startup; `config.py` reads `GITHUB_TOKEN` / `ANTHROPIC_API_KEY`
/ defaults from `os.environ` afterward.

**Rationale**: Small, single-purpose, widely-used dependency that keeps
`.env` support (constitution Secrets Never Committed) simple without hand-
rolling a parser.

**Alternatives considered**: Requiring users to `export` variables manually
with no `.env` support (rejected — worse day-to-day ergonomics for a
personal tool, and `.env` is already git-ignored by the project's `.gitignore`).

## Test mocking strategy (constitution Principle I)

**Decision**: `unittest.mock` (stdlib) to stub `requests` calls in
`github_client.py` tests and the `anthropic` client in `summarizer.py` tests;
no live network calls anywhere in the suite.

**Rationale**: Satisfies the constitution's requirement directly with no
added dependency; `pytest` fixtures wrap the mock setup for reuse across
test modules.

**Alternatives considered**: `responses` / `pytest-mock` (rejected — small
convenience wrappers around what `unittest.mock` already does; not
justified for this project's size per Simplicity & CLI-First).
