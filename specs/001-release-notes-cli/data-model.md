# Phase 1 Data Model: Release Notes & PR Summary Generation

Entities below are drawn from spec.md's Key Entities section, with fields and
validation rules derived from the Functional Requirements. This is a local,
file-based tool — nothing here is a database schema; each entity maps to an
in-memory structure and, where noted, a serialized on-disk form.

## Pull Request

Represents one merged pull request retrieved from GitHub (FR-002).

| Field | Type | Notes |
|---|---|---|
| `number` | int | Unique within a repository; used as the dedup key against Summarization History (FR-016) |
| `title` | str | |
| `author` | str | GitHub username |
| `labels` | list[str] | Used as input signal for customer-facing vs. internal classification (FR-003a) |
| `body` | str \| None | May be empty (see spec Edge Cases — no body is valid input, not an error) |
| `merged_at` | datetime | Must fall within the resolved Time Window to be included |
| `linked_issues` | list[str] | Best-effort; optional per spec |

**Validation**: `merged_at` MUST be non-null (only merged PRs are fetched, per
spec Assumptions — PRs without a merge timestamp are excluded at the fetch
boundary, not passed downstream).

## Time Window

Represents the period being summarized (FR-001, FR-015).

| Field | Type | Notes |
|---|---|---|
| `kind` | enum: `dates` \| `refs` \| `default` | Which input mode was used |
| `start` / `end` | date | Present when `kind == dates` |
| `start_ref` / `end_ref` | str | Present when `kind == refs`; resolved to commit dates via GitHub |
| `resolved_start` / `resolved_end` | datetime | Always populated after resolution, regardless of `kind` — the concrete boundary used to filter PRs |

**Validation**:
- Exactly one of (`dates`, `refs`) may be supplied by the user; if neither,
  `kind` MUST resolve to `default` = last 1 month ending now (FR-015).
- `resolved_end` MUST be after `resolved_start`; an invalid/nonexistent ref
  MUST fail resolution with a clear error (spec User Story 2, Acceptance
  Scenario 2).

## Release Identity

Identifies a specific release for header metadata and re-run detection
(FR-011, FR-012, FR-013).

| Field | Type | Notes | Source |
|---|---|---|---|
| `release_name` | str | Human-readable name shown in the document header | Explicit user input `--release-name` (required when `--publish` is used); otherwise auto-derived from the resolved Time Window (FR-019) |
| `version` | str | The version/tag used as the matching key (FR-012) | Explicit user input `--version` (required when `--publish` is used); otherwise auto-derived from the resolved Time Window, e.g. `2026-08-01_to_2026-08-31` or `v1.2.0_to_v1.3.0` (FR-019) |
| `rc_branch` | str \| None | Release-candidate branch name, if applicable to how the window was specified | Explicit user input: `--rc-branch` (optional, may be omitted) |
| `commit_sha` | str | The commit the notes were generated from | Always auto-resolved, never user-supplied: for a `refs`-kind window, the resolved `end_ref`'s commit; for `dates`/`default`, the repository's current default-branch HEAD at run time (`github_client.get_default_branch_head_sha`) |

**Validation**:
- `version` is the sole identity/matching key — two runs with the same
  `version` refer to the same release for immutability purposes (FR-012),
  regardless of whether `rc_branch`/`commit_sha` differ.
- A release in *any* state (draft or published) matching `version` counts
  as "existing" for FR-012 — a draft is not treated as available to
  overwrite.
- `--version` and `--release-name` MUST be present when `--publish` is
  used; their absence in that case is a usage error, not a default-filled
  value.

## Generated Summary

The AI-produced output document (FR-003, FR-003a, FR-004).

| Field | Type | Notes |
|---|---|---|
| `header` | Release Identity | Rendered at the top of the document (FR-011) |
| `customer_sections` | dict[str, list[PullRequest]] | Keyed by customer-facing category (e.g. Features, Improvements, Fixes) |
| `internal_section` | list[PullRequest] | The de-emphasized "Other/Internal Changes" group (FR-003a) |
| `generated_at` | datetime | |

**Validation**: Every Pull Request included in the run's scope MUST appear in
exactly one of `customer_sections` or `internal_section` — never both, never
neither (spec SC-002: none omitted, none fabricated).

## Usage Record

One Anthropic API call's cost-transparency data (FR-007), appended to
`logs/cost/runs/usage_log.jsonl` per the format already documented in
[`logs/cost/runs/README.md`](../../logs/cost/runs/README.md).

| Field | Type | Notes |
|---|---|---|
| `timestamp` | datetime | |
| `repo` | str | |
| `since` / `until` | date | Resolved window boundaries |
| `model` | str | |
| `input_tokens` / `output_tokens` | int | From the Anthropic response's `usage` field |
| `estimated_cost_usd` | float | Computed via the static pricing table (see research.md); stored with 6 decimal places of precision |

**Validation**: `estimated_cost_usd` is stored at 6 decimal places of
precision in `usage_log.jsonl`; when printed to the user in the run's cost
summary, it is displayed rounded to 4 decimal places.

## Summarization History

Tracks which pull requests have already been reported, to satisfy FR-016 /
SC-008. Persisted as a small local JSON file, one per repository.

| Field | Type | Notes |
|---|---|---|
| `repo` | str | |
| `reported_pr_numbers` | set[int] | Every `Pull Request.number` ever included in a previously generated summary for this repo |
| `updated_at` | datetime | |

**Validation**: A Pull Request MUST be excluded from a new run's candidate
set if its `number` is already present in `reported_pr_numbers` for that
repo (FR-016) — checked before, not after, categorization.

## Relationships

```text
Time Window ──filters──> Pull Request (many)
Pull Request (many, minus Summarization History exclusions) ──input to──> Generated Summary
Release Identity ──identifies/headers──> Generated Summary
Generated Summary ──successful run──> Summarization History (adds reported PR numbers)
Each Anthropic call ──produces──> Usage Record
```
