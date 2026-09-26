# ai-release-notes-pr-summarizer

A CLI tool that generates AI-written, customer-facing release notes and PR
summaries for a GitHub repository over a given date range or ref range,
using the Claude API.

Point it at a repo and a window of time (or two git refs), and it will:

- Fetch every merged pull request in that window
- Ask Claude to summarize them into plain-language categories (Features,
  Improvements, Fixes, and a de-emphasized "Other/Internal Changes" section)
- Write the result to a local Markdown file
- Report tokens used and estimated cost
- Remember which PRs it already summarized, so re-running with an
  overlapping window won't duplicate entries

## Features

- **Flexible windows** — select PRs by date range (`--since` / `--until`)
  or by git ref range (`--from-ref` / `--to-ref`); defaults to the last
  month if nothing is specified
- **Release identity header** — each summary is stamped with a release
  name, version, resolved commit SHA, and optional RC branch name
- **Deduplication across runs** — a local history file tracks which PR
  numbers have already been summarized so overlapping windows don't
  produce repeat entries
- **Cost visibility** — every run prints input/output token counts and an
  estimated USD cost, and logs usage for later review
- **Retry with backoff** — transient Claude API failures are retried
  automatically

## Requirements

- Python 3.11+
- A GitHub personal access token with read access to the target repo
- An Anthropic API key

## Installation

```bash
git clone https://github.com/vikrantbains123/ai-release-notes-pr-summarizer.git
cd ai-release-notes-pr-summarizer
pip install -e .
```

This installs the `ai-release-notes` command via the `pyproject.toml`
entry point.

## Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

```dotenv
# GitHub personal access token — needs read access to the target repo.
GITHUB_TOKEN=

# Anthropic API key, used to generate the release notes/PR summaries.
ANTHROPIC_API_KEY=
```

`.env` is git-ignored — never commit real credentials.

## Usage

```bash
ai-release-notes --repo owner/name [options]
```

| Flag | Description |
| --- | --- |
| `--repo` | **Required.** Target repository, as `owner/name`. |
| `--since` | Start date (`YYYY-MM-DD`). Used with `--until`. |
| `--until` | End date (`YYYY-MM-DD`). Used with `--since`. |
| `--from-ref` | Start git ref (branch, tag, or SHA). Used with `--to-ref` instead of dates. |
| `--to-ref` | End git ref. Used with `--from-ref`. |
| `--output` | Path to write the generated Markdown file. Defaults to `RELEASE_NOTES.md`. |
| `--version` | Version label for the release identity header. Auto-derived from the window if omitted. |
| `--release-name` | Release name for the header. Defaults to `--version` if omitted. |
| `--rc-branch` | Optional release-candidate branch name to include in the header. |

### Examples

Summarize everything merged in August 2026:

```bash
ai-release-notes --repo my-org/my-repo --since 2026-08-01 --until 2026-08-31
```

Summarize everything merged between two tags, with an explicit version and
custom output path:

```bash
ai-release-notes --repo my-org/my-repo \
  --from-ref v1.2.0 --to-ref v1.3.0 \
  --version 1.3.0 --output CHANGELOG_1.3.0.md
```

If no window is given, the tool defaults to the last one month.

## Output

Running the tool writes a Markdown file (default `RELEASE_NOTES.md`)
containing the release identity header followed by categorized,
plain-language summaries of the merged PRs in that window. It also prints
a line like:

```
Tokens used: 4213 input / 812 output — Est. cost: $0.03
```

Usage is additionally logged under `logs/` for later cost review, and
already-summarized PR numbers are recorded so future runs won't repeat
them.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT — see [LICENSE](LICENSE).

