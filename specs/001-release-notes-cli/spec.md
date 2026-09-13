# Feature Specification: Release Notes & PR Summary Generation

**Feature Branch**: `001-release-notes-cli`

**Created**: 2026-09-12

**Status**: Draft

**Input**: User description: "Build a Python CLI tool that generates AI-written release notes and PR summaries for a GitHub repository over a given time window. Core behavior: user specifies a target GitHub repo and a time window (dates or ref range); the tool fetches merged pull requests in that window (title, number, author, labels, body, merge date, linked issues); the PR data is sent to an AI service to generate a structured, categorized summary; output is written to a local Markdown file (path configurable); an optional flag also creates/updates a draft GitHub Release with the same content; configuration (tokens/keys) comes from environment variables, never hardcoded; every AI call reports tokens used and estimated cost; this is a single-purpose CLI tool with no web UI and no multi-provider abstraction in v1."

## Clarifications

### Session 2026-09-12

- Q: When the tool re-runs for a window that already has a published release, how should it recognize *that specific release* as the one to check, rather than creating a duplicate or updating the wrong one? → A: Match by release version/tag; the generated document's header must also show the release name, version, RC (release-candidate) branch name, and the commit tag/SHA it was generated from.
- Q: For a given release, once its notes have already been captured/published, should a subsequent run update them? → A: No — the release notes are immutable once they exist for a given release; a re-run MUST NOT regenerate or republish them.
- Q: When the tool skips because notes already exist for the target release, what should the user see? → A: A clear message that notes already exist for that release and nothing was changed (not a silent skip, and not a hard failure requiring an override flag).
- Q: When the AI summarization call fails or times out partway through a run, what should happen? → A: Retry a small, fixed number of times with backoff; if still failing, abort the run with a clear error and produce no partial or misleading output.
- Q: What should the tool do when the user doesn't specify a window? → A: Default to the last 1 month. (Also volunteered: a pull request already included in a previous summary must never be reported again in a later one, even on overlapping windows.)
- Q: Is there a maximum number of pull requests the tool must handle within a single window? → A: Assume a reasonable soft cap for v1 (e.g. a few hundred PRs); if exceeded, report a clear error rather than silently truncating or batching across multiple AI calls.

### Session 2026-09-12 (pre-implementation checklist follow-up)

- Q: FR-014 said "a small, fixed number of times with backoff" without a number — what exactly? → A: Up to 2 retries (3 attempts total), with exponential backoff starting at 2 seconds and doubling each attempt (2s, then 4s).
- Q: Does FR-012's "MUST NOT regenerate... notes" apply to the local file as well as the published release? → A: No — it applies only to the published release. The local file is regenerated on every run regardless of whether a release already exists for that version; only the publish step is skipped.
- Q: What happens if the local file is written successfully but the subsequent publish step then fails (e.g. a network error while creating the release)? → A: The already-written local file is left in place as valid output (it is complete and correct, not partial); the run still exits with an error clearly stating that generation succeeded but publishing failed, and no partial/corrupt release is created.

### Session 2026-09-12 (pre-implementation checklist, full review)

- Q: Does a DRAFT release for a version/tag count as "already exists" for FR-012's immutability check, or only a fully published release? → A: Any release state (draft or published) counts — a re-run must not touch a matching release regardless of its draft/published state.
- Q: How are the Release Identity's 4 fields (release name, version, RC branch, commit SHA) populated — only `version` had a clear source before? → A: `--version` and `--release-name` are required CLI flags whenever `--publish` is used; `--rc-branch` is an optional flag (may be omitted); `commit_sha` is always auto-resolved from the window's end reference/commit, never user-supplied.
- Q: Should a missing credential's error message differ from an invalid one's? → A: Yes — each names the specific variable and states which of the two problems it is (e.g. "GITHUB_TOKEN is not set" vs. "GITHUB_TOKEN was rejected by GitHub").
- Q: Does FR-009's "MUST NOT expose credentials" cover a masked/partial display (e.g. showing only the last 4 characters), or only full raw values? → A: A masked partial representation is explicitly not considered exposure; only the full usable secret value is prohibited.
- Q: Who maintains the hardcoded Anthropic pricing table, and is staleness detection in scope? → A: Manually maintained by the developer; no automated staleness detection in v1 — an accepted limitation, not a gap to build around.
- Q: What precision/rounding applies to `estimated_cost_usd`? → A: Stored with 6 decimal places of precision in the usage log; displayed to the user rounded to 4 decimal places.
- Q: Is it acceptable for the local file's exact wording to differ between two runs of the same release (AI output isn't perfectly deterministic), given the published release itself must stay immutable? → A: Yes — accepted behavior; only the published release (FR-012) carries an immutability guarantee, not the local file's exact content.
- Q: Is supplying only one of `--from-ref`/`--to-ref` (not both) addressed as clearly as supplying both a date range and a ref pair? → A: Yes — also a usage error (exit code 2), same category.
- Q: When the PR-volume cap (FR-017) is exceeded, does the error report the actual count found? → A: Yes — the error names both the actual count and the cap (e.g. "found 412 pull requests, which exceeds the 300 supported per window").

### Session 2026-09-12 (post-/speckit-analyze remediation)

- Q: FR-017's cap was still "a reasonable soft cap... e.g. a few hundred" with no exact number, and had zero tasks behind it — what's the actual number? → A: 300 pull requests.
- Q: FR-009 was scoped only to "any file it generates" — does the no-credential-exposure guarantee also cover stdout/stderr, as contracts/cli-interface.md already assumed? → A: Yes — widened to cover stdout/stderr output as well.

### Session 2026-09-13 (implementation-time gap: header vs. FR-019)

- Q: FR-011 requires a header on *every* generated document, but FR-019 only requires `--version`/`--release-name` when `--publish` is used — what populates the header on a plain run where neither was supplied? → A: Auto-derive `version` (and `release_name`, defaulting to the same value) from the resolved window — e.g. `2026-08-01_to_2026-08-31` for a date range, `v1.2.0_to_v1.3.0` for a ref pair — so a local-only run never requires typing `--version`/`--release-name`. `--rc-branch` stays blank unless supplied. Explicit `--version`/`--release-name`, when given, always take precedence over the auto-derived default, publish or not.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate release notes for a date range (Priority: P1)

As a repository maintainer, I want to generate a customer-facing, plain-language summary of pull requests merged into my repository over a specific date range, so I can produce release notes without manually reading through every pull request or rewriting engineering-speak into something my customers can understand.

**Why this priority**: This is the core value proposition and the minimum viable product — without it, nothing else in this feature matters.

**Independent Test**: Can be fully tested by running the tool against a repository with a known start/end date range containing several merged pull requests, and confirming a local summary file is produced covering exactly the pull requests merged in that window.

**Acceptance Scenarios**:

1. **Given** a valid repository and a start/end date range containing several merged pull requests, **When** the user runs the tool, **Then** a local file is produced containing a categorized, human-readable summary of those pull requests.
2. **Given** a date range with zero merged pull requests, **When** the user runs the tool, **Then** the tool clearly reports that no pull requests were found in that window and does not produce a misleading or empty-looking summary.

---

### User Story 2 - Generate notes between two release points (Priority: P2)

As a repository maintainer, I want to specify two reference points (e.g. the previous release and the current state) instead of calendar dates, so the generated notes align with how I actually cut releases.

**Why this priority**: A common real-world release workflow and high value, but the date-range capability in User Story 1 already delivers a usable product on its own.

**Independent Test**: Can be fully tested by running the tool with two reference points instead of dates and confirming the same categorized summary is produced for pull requests merged between them.

**Acceptance Scenarios**:

1. **Given** two valid reference points where the second comes after the first, **When** the user runs the tool, **Then** a summary is generated for pull requests merged in between them.
2. **Given** a reference point that does not exist in the repository, **When** the user runs the tool, **Then** the tool reports a clear error identifying the invalid reference rather than failing unclearly.

---

### User Story 3 - Publish the summary as a release (Priority: P3)

As a repository maintainer, I want to optionally publish the generated summary directly as a release on the repository, so I don't have to manually copy the output somewhere else — and I want that publication to be a one-time, immutable event per release rather than something that can be silently overwritten on a later run.

**Why this priority**: A convenience layer on top of the core generation capability; the core value is already delivered without it.

**Independent Test**: Can be fully tested by running the tool with the publish option enabled against a repository with releases enabled, confirming a release is created containing the generated content and its identifying header, then running it again for the same release and confirming it is left untouched.

**Acceptance Scenarios**:

1. **Given** a successfully generated summary, the publish option enabled, and no release notes previously published for this release, **When** the run completes, **Then** a release is created on the target repository containing that summary, with a header showing the release name, version, RC branch name, and commit tag/SHA.
2. **Given** release notes already exist for the target release (matched by version/tag), **When** the user runs the tool again with the publish option enabled, **Then** the system does not regenerate or republish the notes, and clearly reports that notes already exist for that release and nothing was changed.
3. **Given** the publish option is not provided, **When** the run completes, **Then** no release is created or modified — output remains local only.

---

### Edge Cases

- What happens when a merged pull request has no description/body text at all?
- How does the system behave when a very large number of pull requests fall inside one window (e.g. hundreds)?
- What happens when the user lacks sufficient access to the target repository, or a required credential is missing or invalid?
- How does the system behave when the underlying AI summarization call fails or times out mid-run? Resolved: it retries a small, fixed number of times with backoff, then aborts the run cleanly with no partial or misleading output if still failing (see Clarifications, FR-014).
- What happens when the same release is run twice with publishing enabled? Resolved: the tool detects existing notes for that release (matched by version/tag) and skips regeneration, clearly reporting that nothing changed (see Clarifications, FR-012, FR-013).
- What happens to a pull request that is purely internal/technical (e.g. a refactor, dependency bump, or CI change) with no customer-visible impact? (See Assumptions.)
- What happens when a pull request falls inside the specified window but was already included in an earlier summary? Resolved: it is excluded from the new summary (see Clarifications, FR-016).
- What happens when the number of pull requests in a window exceeds the supported cap? Resolved: the system reports a clear error rather than truncating or silently batching (see Clarifications, FR-017).
- What happens if the local file is written successfully but the subsequent publish step fails? Resolved: the local file is left in place as valid output, and the run exits with an error clearly distinguishing "generation succeeded, publishing failed" (see Clarifications, FR-018).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST allow a user to specify a target repository and either an explicit start/end date range or a pair of reference points to define the window to summarize.
- **FR-002**: The system MUST retrieve all pull requests merged within the specified window, including at minimum: title, identifying number, author, associated labels, description text, and merge timestamp.
- **FR-003**: The system MUST generate a customer-facing summary written in plain, non-technical language — describing the customer-visible impact or benefit of each change rather than internal implementation detail — categorized into groups such as new features, improvements, and fixes.
- **FR-003a**: The system MUST place pull requests with no customer-visible impact (e.g. refactors, dependency bumps, CI/tooling changes) into a separate, clearly de-emphasized section (e.g. "Other/Internal Changes") rather than mixing them into the customer-facing categories or omitting them outright.
- **FR-004**: The system MUST write the generated summary to a local, human-readable file by default, without requiring any additional user action beyond running the tool.
- **FR-005**: The system MUST support an explicit opt-in action to also publish the generated summary as a release on the source repository, and MUST NOT publish anything unless this opt-in is given.
- **FR-006**: The system MUST clearly report to the user when no pull requests are found in the specified window, rather than producing an empty or misleading summary.
- **FR-007**: The system MUST report, after each run, how much of the underlying AI service was consumed and its estimated monetary cost.
- **FR-008**: The system MUST fail with a clear, actionable error message when required access credentials are missing or invalid, rather than failing silently or with a raw/technical error. The message MUST name the specific credential involved and MUST distinguish "not set" from "rejected/invalid" (e.g. "GITHUB_TOKEN is not set" vs. "GITHUB_TOKEN was rejected by GitHub").
- **FR-009**: The system MUST NOT persist or expose access credentials in any file it generates (summaries, logs, or otherwise), or in its stdout/stderr output. A masked, partial representation (e.g. showing only the last 4 characters) is not considered exposure; only the full, usable secret value is prohibited.
- **FR-010**: The system MUST allow the user to configure the target repository and the destination file path rather than these being hardcoded.
- **FR-011**: The system MUST identify each release by its version/tag, and MUST include, in every generated document, a header showing the release name, version, RC (release-candidate) branch name, and the commit tag/SHA the notes were generated from.
- **FR-012**: The system MUST treat a *published* release's notes as immutable per release: once a release exists for a target version/tag — in any state, draft or published — the system MUST NOT create or modify a release for that version/tag on a subsequent run. This immutability applies only to the published release — the local file (FR-004) is regenerated on every run regardless of whether a matching release already exists.
- **FR-019**: The system MUST require the user to explicitly supply `--version` and `--release-name` whenever `--publish` is used (no silent defaults for either); `--rc-branch` is optional and may be omitted. When `--publish` is not used and `--version`/`--release-name` are not supplied, the system MUST auto-derive both from the resolved Time Window (e.g. `2026-08-01_to_2026-08-31` for a date range, `v1.2.0_to_v1.3.0` for a ref pair) so FR-011's header requirement is always satisfiable without requiring these flags for a local-only run; an explicitly supplied `--version`/`--release-name` always takes precedence over the auto-derived value. The commit SHA in the Release Identity header (FR-011) MUST always be auto-resolved from the window's end reference/commit, never user-supplied.
- **FR-013**: When skipping publication because a release already exists for the target version/tag (FR-012), the system MUST clearly report to the user that notes already exist for that release and that no release was created or modified.
- **FR-014**: The system MUST retry a failed or timed-out AI summarization call up to 2 additional times (3 attempts total), with exponential backoff starting at 2 seconds and doubling each attempt, before giving up; if it is still failing after retries, the system MUST abort the run with a clear error and MUST NOT produce partial or misleading local file or release content.
- **FR-018**: If the local file (FR-004) is written successfully but a subsequent `--publish` attempt then fails (e.g. a network, permission, or API error while creating the release), the system MUST leave the already-written local file in place as valid output, MUST NOT create a partial or corrupt release, and MUST exit with a clear error distinguishing "generation succeeded, publishing failed" from a full run failure.
- **FR-015**: The system MUST default the time window to the last 1 month when the user does not explicitly specify a date range or reference points.
- **FR-016**: The system MUST exclude, from a newly generated summary, any pull request that was already included in a previously generated summary for this repository — a pull request is reported at most once across separate runs, even when windows overlap.
- **FR-017**: The system MUST support up to 300 pull requests within a single window; if that cap is exceeded, the system MUST report a clear error naming both the actual pull request count found and the 300 cap, rather than silently truncating the results or splitting the request across multiple AI calls.

### Key Entities *(include if feature involves data)*

- **Pull Request**: A merged unit of work in the source repository — title, number, author, labels, description, merge date, and (where available) linked issue references. The primary input to the summary.
- **Time Window**: The period being summarized, expressed either as a calendar date range or as a pair of reference points, defaulting to the last 1 month when not specified; determines which pull requests are candidates for inclusion.
- **Summarization History**: A record of which pull requests have already been included in a previously generated summary for the repository, used to ensure a pull request is never reported more than once across separate runs (FR-016).
- **Generated Summary**: The AI-produced output — a customer-facing, plain-language, categorized document derived from the pull requests in the window, with internal/technical changes set apart in their own de-emphasized section, and headed by the release's Release Identity. Exists as a local file and, optionally, as a published release.
- **Release Identity**: The release name, version/tag, RC branch name, and commit tag/SHA that together identify a specific release. Release name, version, and RC branch are explicit user-supplied inputs (FR-019); commit SHA is always auto-resolved. Used both to detect whether notes already exist for that release, in any release state — draft or published (FR-012) — and as header metadata in the generated document (FR-011).
- **Usage Record**: A record of AI-service consumption and estimated cost for a single run, used for cost transparency.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can produce a categorized summary of a repository's changes for a given time window in a single run, without manually reading individual pull requests.
- **SC-002**: For a window with merged pull requests, the generated summary reflects all of those pull requests — none omitted, none fabricated — when spot-checked against the source list.
- **SC-003**: A user can determine the estimated cost of a run immediately after it completes, without consulting an external billing dashboard.
- **SC-004**: A user who runs the tool with missing or invalid access credentials understands what went wrong and how to fix it without reading source code.
- **SC-005**: Publishing a summary as a release is always a distinct, explicit opt-in step beyond generating it locally — it never happens by accident.
- **SC-006**: A customer with no engineering background can read the main body of a generated summary and understand what changed for them, without encountering unexplained technical jargon or internal implementation detail.
- **SC-007**: A run that ultimately fails due to an AI service error never leaves behind a partial or misleading local file or published release.
- **SC-008**: Across multiple runs with overlapping windows, no pull request ever appears in more than one generated summary.

## Assumptions

- The target repository is hosted on GitHub, and the user has sufficient access (read access for pull request data; write/release access only when choosing to publish).
- "Merged pull requests" is the unit of change being summarized for v1 — direct commits not associated with a pull request are out of scope.
- A single default category set is sufficient for v1: customer-facing categories (e.g. Features, Improvements, Fixes) written in plain language, plus one de-emphasized "Other/Internal Changes" category for pull requests with no customer-visible impact. Fully custom, user-defined categories are out of scope.
- Classifying a pull request as customer-facing vs. internal/technical, and rewriting its description into plain language, is done by the AI summarization step itself (from the PR's title/body/labels) — no separate manual tagging step is required from the maintainer.
- This is a local, single-user tool for v1 — no multi-user/team collaboration features, no hosted service.
- Network access to GitHub and the AI service is available at runtime.
- The Anthropic pricing table used to compute `estimated_cost_usd` is maintained manually by the developer and may become stale between Anthropic pricing changes; automated staleness detection is out of scope for v1.
- The local file's exact generated wording may differ between separate runs for the same release, since AI-generated content is not perfectly deterministic; only the *published* release (FR-012) carries an immutability guarantee — the local file does not.
