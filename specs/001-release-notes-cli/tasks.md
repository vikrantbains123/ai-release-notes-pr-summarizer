# Tasks: Release Notes & PR Summary Generation

**Input**: Design documents from `/specs/001-release-notes-cli/` (plan.md, spec.md, research.md, data-model.md, contracts/cli-interface.md, quickstart.md)

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-interface.md

**Tests**: NOT optional for this project — the project constitution's Principle I
(Test-First Development, NON-NEGOTIABLE) requires every task below to have its
test written and failing *before* the corresponding implementation task, with
GitHub/Anthropic calls mocked rather than live.

**Organization**: Tasks are grouped by user story (from spec.md) to enable
independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- File paths are exact, per plan.md's Project Structure

---

## Phase 1: Setup

**Purpose**: Project initialization

- [X] T001 Create project skeleton: `src/ai_release_notes/` package (with `__init__.py`) and `tests/{unit,integration,contract}/` directories, per plan.md's Project Structure
- [X] T002 Create `pyproject.toml`: package metadata, an `ai-release-notes` console-script entry point → `ai_release_notes.cli:main`, runtime dependencies (`anthropic`, `requests`, `python-dotenv` — per research.md), dev dependency (`pytest`)
- [X] T003 [P] Add `.env.example` at the repo root documenting `GITHUB_TOKEN` and `ANTHROPIC_API_KEY` (names only, no real values)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared modules and test infrastructure every user story depends on — Cost Transparency, header metadata (FR-011), and cross-run dedup (FR-016) apply to *every* run, not just one story, so they live here rather than in a single story's phase.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 [P] Create `tests/conftest.py` with shared pytest fixtures: a mocked `requests` session/response for GitHub calls and a mocked `anthropic.Anthropic` client — no test in the suite may make a live network call (constitution Principle I)
- [X] T005 [P] Unit test `config.py` in `tests/unit/test_config.py`: a missing `GITHUB_TOKEN`/`ANTHROPIC_API_KEY` raises an error naming the variable and stating it is "not set"; an invalid one (rejected by the API) raises an error naming the variable and stating it was "rejected" — distinct wording per case (FR-008); both present loads successfully — write first, confirm it fails
- [X] T006 Implement `config.py` in `src/ai_release_notes/config.py`: load `.env` via `python-dotenv`, read `GITHUB_TOKEN`/`ANTHROPIC_API_KEY` from the environment, raise the distinct missing-vs-invalid errors validated by T005, never log/expose the raw values beyond a masked partial (e.g. last 4 characters) if shown at all (FR-008, FR-009) — makes T005 pass
- [X] T007 [P] Unit test `window.py` in `tests/unit/test_window.py`, per data-model.md's Time Window rules: exactly one of a date range or a ref pair may be supplied; neither supplied resolves `kind = default` = last 1 month ending now (FR-015); `resolved_end` must be after `resolved_start` — write first, confirm it fails
- [X] T008 [P] Implement `window.py` in `src/ai_release_notes/window.py`: resolves a `TimeWindow` (`kind`: `dates`/`refs`/`default`) per data-model.md — makes T007 pass
- [X] T009 [P] Unit test `history.py` in `tests/unit/test_history.py`, per data-model.md's Summarization History rules: a PR `number` already present in `reported_pr_numbers` for a repo is excluded from a new candidate set (FR-016); new numbers are recorded after a successful run — write first, confirm it fails
- [X] T010 [P] Implement `history.py` in `src/ai_release_notes/history.py`: local JSON-backed Summarization History (`load`/`contains`/`record`) per data-model.md — makes T009 pass
- [X] T011 [P] Unit test `release_identity.py` in `tests/unit/test_release_identity.py`, per data-model.md: `version` is the sole matching key for identifying "the same release" — two identities with the same `version` but different `rc_branch`/`commit_sha` MUST be treated as the same release (FR-012); constructing a Release Identity without `version` or `release_name` raises (FR-019) — write first, confirm it fails
- [X] T012 [P] Implement `release_identity.py` in `src/ai_release_notes/release_identity.py`: takes `release_name`/`version`/`rc_branch` as explicit inputs (FR-019) and `commit_sha` auto-resolved from the Time Window's end reference, exposes the version-based matching key — makes T011 pass
- [X] T013 [P] Unit test `cost.py` in `tests/unit/test_cost.py`: given a mock Anthropic `usage` object, `compute_cost` returns an `estimated_cost_usd` rounded to 6 decimal places from the static pricing table, and a separate display-formatting function rounds it to 4 decimal places for the stdout summary; `record_usage` appends one well-formed line matching the schema in `logs/cost/runs/README.md` (FR-007, data-model.md); asserts the written `usage_log.jsonl` line never contains the raw `ANTHROPIC_API_KEY`/`GITHUB_TOKEN` value (FR-009) — write first, confirm it fails
- [X] T014 [P] Implement `cost.py` in `src/ai_release_notes/cost.py`: static per-model pricing table, `compute_cost(usage)` (6-decimal precision), a display-formatting helper (4-decimal rounding), `record_usage(path, record)` — makes T013 pass
- [X] T015 [P] Unit test `render.py` in `tests/unit/test_render.py`, per data-model.md's Generated Summary validation: every included Pull Request appears in exactly one of the customer-facing sections or the internal section — never both, never neither (SC-002); the rendered header shows all four Release Identity fields (FR-011) — write first, confirm it fails
- [X] T016 Implement `render.py` in `src/ai_release_notes/render.py`: renders a Generated Summary (header + customer-facing categories + de-emphasized "Other/Internal Changes" section) to Markdown — makes T015 pass; depends on T012
- [X] T017 Integration test the PR-fetch path of `github_client.py` in `tests/integration/test_github_client.py`, using the T004 mocked-`requests` fixture: fetching merged PRs within a resolved window returns objects with the fields required by data-model.md's Pull Request entity (FR-002); a PR with an empty/missing body is valid input, not an error; a window resolving to more than 300 PRs raises a clear, distinguishable error naming both the actual count found and the 300 cap, rather than truncating or paginating silently (FR-017); a simulated GitHub API error's message is scrubbed of the `Authorization` header value before it reaches the caller (FR-009) — write first, confirm it fails
- [X] T018 Implement the PR-fetch path of `github_client.py` in `src/ai_release_notes/github_client.py`: `fetch_merged_prs(repo, window)` against the GitHub REST API; checks the 300-PR cap (FR-017) before returning and raises (naming the actual count and the cap) before any Anthropic call is made; scrubs the `Authorization` header value from any propagated error message (FR-009) — makes T017 pass; depends on T006, T008

**Checkpoint**: Config, window resolution, dedup history, release identity, cost tracking, rendering, and PR-fetching all exist and are independently tested. User story work can now begin.

---

## Phase 3: User Story 1 - Generate release notes for a date range (Priority: P1) 🎯 MVP

**Goal**: Given a repo and a date range (or the default 1-month window), produce a customer-facing, categorized Markdown summary of merged PRs.

**Independent Test**: Run against a repository fixture with a known date range containing several merged PRs; confirm the output file's categorized content, the printed cost summary, and that a second run of the same range reports no new/duplicate PRs.

- [X] T019 [P] [US1] Integration test `summarizer.py` in `tests/integration/test_summarizer.py`, using the T004 mocked Anthropic client: a successful call returns customer/internal groupings consumable by `render.py` (FR-003, FR-003a); a failing/timing-out call retries up to 3 attempts total with exponential backoff starting at 2 seconds and doubling (2s, 4s), then raises a clear error with no partial result (FR-014) — write first, confirm it fails
- [X] T020 [US1] Implement `summarizer.py` in `src/ai_release_notes/summarizer.py`: builds the prompt from PR title/body/labels, calls the Anthropic client via a retry loop (3 attempts total, 2s/4s exponential backoff, per research.md and FR-014), returns customer-facing/internal groupings — makes T019 pass; depends on T014, T010 (dedup exclusion happens before this call, not after)
- [X] T021 [P] [US1] Contract test the base CLI in `tests/contract/test_cli_date_range.py`, per contracts/cli-interface.md: `--repo --since --until` exits 0, writes the output file, and prints a cost summary; a window with zero PRs exits 0 with the "no pull requests found" message and produces no misleading file (FR-006) — write first, confirm it fails
- [X] T022 [US1] Implement `cli.py`'s entry point and date-range flags in `src/ai_release_notes/cli.py`: argparse for `--repo`, `--since`/`--until`, `--output` (default `RELEASE_NOTES.md`), `--version`/`--release-name`/`--rc-branch` (all optional at this stage, since `--publish` doesn't exist yet); when `--version`/`--release-name` are omitted, auto-derive both from the resolved window via a new `window.derive_identity_string()` helper (FR-019); wires config → window → history-filter → github_client fetch → summarizer → render → file write → cost report (FR-004, FR-006, FR-007, FR-010) — makes T021 pass; depends on T006, T008, T010, T016, T018, T020
- [X] T023 [US1] Wire Summarization History recording into `cli.py`: after a successful run, record every included PR's number via `history.py` so it is excluded from future runs (FR-016, SC-008) — extends T022; depends on T010, T022

**Checkpoint**: User Story 1 (the MVP) is fully functional and independently testable.

---

## Phase 4: User Story 2 - Generate notes between two release points (Priority: P2)

**Goal**: Same categorized output, scoped by a ref/tag pair instead of dates.

**Independent Test**: Run with two valid refs against a repository fixture and confirm the same summary shape as the date-range path; run with a nonexistent ref and confirm a clear, identifiable error.

- [X] T024 [P] [US2] Integration test ref resolution in `tests/integration/test_github_client.py`: a valid ref pair resolves to commit dates; an invalid ref raises a clear, identifiable error (spec User Story 2, Acceptance Scenario 2) — write first, confirm it fails
- [X] T025 [US2] Implement ref resolution in `github_client.py`: `resolve_ref(repo, ref)` → commit/date, feeding `window.py`'s `refs` kind — makes T024 pass; depends on T018
- [X] T026 [P] [US2] Contract test ref-pair flags in `tests/contract/test_cli_ref_range.py`, per contracts/cli-interface.md: `--from-ref --to-ref` produces the same output shape as the date-range path; supplying both date and ref options together is a usage error (exit code 2); supplying only one of `--from-ref`/`--to-ref` is likewise a usage error (exit code 2) — write first, confirm it fails
- [X] T027 [US2] Extend `cli.py` with `--from-ref`/`--to-ref` flags, the mutual-exclusivity check against `--since`/`--until`, and validation that both ref flags are given together or neither — makes T026 pass; depends on T022, T025

**Checkpoint**: User Stories 1 and 2 both independently functional.

---

## Phase 5: User Story 3 - Publish the summary as a release (Priority: P3)

**Goal**: An opt-in `--publish` flag creates the release exactly once per release identity; a second run leaves it untouched.

**Independent Test**: Run with `--publish` against a repository fixture with no existing release for that version — confirm a release is created with the correct header. Run the identical command again — confirm the release is left unchanged and the tool clearly reports notes already exist.

- [ ] T028 [P] [US3] Integration test release check/create in `tests/integration/test_github_client.py`: `find_release` lists releases and matches by `version` regardless of draft/published state (FR-012, per research.md's list-and-filter approach, since the tag-specific endpoint misses drafts); `--publish` against no existing match creates a release containing the rendered content; a matching existing release (draft or published) is left untouched (FR-012, FR-013); a `create_release` call that raises (network/permission/API error) propagates a distinguishable error rather than a generic exception (FR-018) — write first, confirm it fails
- [ ] T029 [US3] Implement release check/create in `github_client.py`: `find_release(repo, version)` (lists releases, filters client-side, matches any state) / `create_release(repo, release_identity, content)`, raising a distinguishable error type on failure so callers can tell "publish failed" apart from other errors (FR-018) — makes T028 pass; depends on T012, T018
- [ ] T030 [P] [US3] Contract test the `--publish` flag and its required options in `tests/contract/test_cli_publish.py`, per contracts/cli-interface.md: `--publish` without `--version`/`--release-name` is a usage error (exit 2, FR-019); `--publish` omitted → no release touched (FR-005); provided with both required flags + no existing release → release created with commit SHA auto-resolved (never user-supplied); provided + existing release (any state) → exit 0, clear "already exists" message, release left unchanged (FR-012, FR-013); provided + local file write succeeds but `create_release` fails → local file remains on disk, exit 1 with a message distinguishing "generation succeeded, publishing failed" (FR-018) — write first, confirm it fails
- [ ] T031 [US3] Extend `cli.py` with `--publish`, `--version`, `--release-name`, `--rc-branch` flags (validating `--version`/`--release-name` are present before any network call when `--publish` is given, FR-019), wiring `find_release` → `create_release` or skip-and-report, and catching a publish failure separately from generation failures so the already-written local file is never removed on a publish-only error (FR-018) — makes T030 pass; depends on T022, T029

**Checkpoint**: All three user stories independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validation and finishing touches across all stories

- [ ] T032 [P] Run quickstart.md's 5 scenarios manually end-to-end against a real (or sandbox) GitHub repository; record the `/cost` numbers observed in `logs/cost/build/BUILD_LOG.md` and confirm a matching entry appears in `logs/cost/runs/usage_log.jsonl`; specifically eyeball each generated summary against SC-006 (no unexplained jargon, readable by a non-technical customer)
- [ ] T033 [P] Replace the placeholder `README.md` with real usage docs: installation, `.env` setup, example commands for all three user stories
- [ ] T034 Run the full test suite and confirm zero live network calls occurred (constitution Principle I) and that every code path calling the Anthropic API also exercises `cost.py` (constitution Principle II)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories.
- **User Stories (Phase 3-5)**: All depend on Foundational completion. US1 has no dependency on US2/US3. US2 and US3 both extend `cli.py` from US1 (T022) but do not depend on each other's flags — either can be built first once Foundational + US1's `cli.py` skeleton exists.
- **Polish (Phase 6)**: Depends on all three user stories being complete.

### Within Each Phase

- Every test task MUST be written and confirmed failing before its paired implementation task (constitution Principle I) — this ordering is a real dependency, not just a suggestion, so implementation tasks are never marked `[P]` relative to their own test.
- Foundational modules with no cross-dependency (T005/T006, T007/T008, T009/T010, T011/T012, T013/T014) can be built in parallel with each other; `render.py` (T016) depends on `release_identity.py` (T012); `github_client.py`'s fetch path (T018) depends on `config.py` (T006) and `window.py` (T008).

### Parallel Opportunities

- All Setup [P] tasks (T003) can run alongside T001/T002 once those exist.
- The five independent Foundational test tasks (T005, T007, T009, T011, T013) can run in parallel; so can their implementations pairwise (T006/T008/T010/T012/T014 have no dependencies on each other, only on their own test).
- Once Foundational is complete, US2 (T024-T027) and US3 (T028-T031) can be built in parallel with each other — both only depend on Foundational + US1's `cli.py` skeleton (T022), not on each other.

---

## Parallel Example: Foundational Phase

```bash
# Launch the independent unit tests together:
Task: "Unit test config.py in tests/unit/test_config.py"
Task: "Unit test window.py in tests/unit/test_window.py"
Task: "Unit test history.py in tests/unit/test_history.py"
Task: "Unit test release_identity.py in tests/unit/test_release_identity.py"
Task: "Unit test cost.py in tests/unit/test_cost.py"
```

## Parallel Example: User Story 2 + User Story 3

```bash
# Once Foundational + T022 (US1's cli.py skeleton) are done, build both stories together:
Task: "Integration test ref resolution in tests/integration/test_github_client.py"     # US2
Task: "Integration test release check/create in tests/integration/test_github_client.py"  # US3
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Setup) and Phase 2 (Foundational) — all shared modules, fully tested.
2. Complete Phase 3 (User Story 1).
3. **STOP and VALIDATE**: run quickstart.md Scenarios 1, 2, and 5 by hand.
4. This is a usable tool at this point — date-range summaries with cost reporting and dedup.

### Incremental Delivery

1. Setup + Foundational → shared foundation ready, nothing user-facing yet.
2. Add User Story 1 → validate independently → usable MVP.
3. Add User Story 2 → validate independently (quickstart Scenario 3) → tag-range support.
4. Add User Story 3 → validate independently (quickstart Scenario 4, including the re-run/immutability check) → publishing support.
5. Polish (Phase 6) → docs, manual end-to-end pass, constitution compliance sweep.

Each story adds value without breaking the previous ones, and every module was already independently unit-tested in the Foundational phase before any story wired it together.
