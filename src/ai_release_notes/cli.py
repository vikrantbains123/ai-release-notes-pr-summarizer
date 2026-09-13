"""CLI entry point. Wires config -> window -> history-filter ->
github_client fetch -> summarizer -> render -> file write -> cost report
(FR-001, FR-004, FR-006, FR-007, FR-010, FR-019).
"""
import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import anthropic

from ai_release_notes import cost as cost_module
from ai_release_notes import history as history_module
from ai_release_notes import window as window_module
from ai_release_notes.config import CredentialError, load_config
from ai_release_notes.github_client import (
    GitHubClientError,
    InvalidRefError,
    fetch_merged_prs,
    get_default_branch_head_sha,
    resolve_ref,
)
from ai_release_notes.release_identity import ReleaseIdentityError, build_release_identity
from ai_release_notes.render import render_summary
from ai_release_notes.summarizer import DEFAULT_MODEL, SummarizerError, summarize
from ai_release_notes.window import WindowError, WindowKind


def _parse_date(value: str):
    return datetime.strptime(value, "%Y-%m-%d").date()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ai-release-notes")
    parser.add_argument("--repo", required=True, help="owner/name of the target GitHub repository")
    parser.add_argument("--since", type=_parse_date)
    parser.add_argument("--until", type=_parse_date)
    parser.add_argument("--from-ref", dest="from_ref", default=None)
    parser.add_argument("--to-ref", dest="to_ref", default=None)
    parser.add_argument("--output", default="RELEASE_NOTES.md")
    parser.add_argument("--version", dest="version", default=None)
    parser.add_argument("--release-name", dest="release_name", default=None)
    parser.add_argument("--rc-branch", dest="rc_branch", default=None)
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config()
    except CredentialError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    try:
        window = window_module.resolve_window(
            since=args.since, until=args.until, from_ref=args.from_ref, to_ref=args.to_ref
        )
    except WindowError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    ref_commit_sha = None
    if window.kind == WindowKind.REFS:
        try:
            _, from_committed_at = resolve_ref(args.repo, window.start_ref, config.github_token)
            ref_commit_sha, to_committed_at = resolve_ref(args.repo, window.end_ref, config.github_token)
            window = window_module.apply_resolved_refs(
                window, resolved_start=from_committed_at, resolved_end=to_committed_at
            )
        except InvalidRefError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        except WindowError as exc:
            print(str(exc), file=sys.stderr)
            return 1

    try:
        all_prs = fetch_merged_prs(args.repo, window, config.github_token)
    except GitHubClientError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    history_path = history_module.DEFAULT_HISTORY_PATH
    history = history_module.load(args.repo, path=history_path)
    prs = [pr for pr in all_prs if not history_module.contains(history, pr.number)]

    if not prs:
        print("No pull requests found in this window.")
        return 0

    if ref_commit_sha is not None:
        # Ref-based window: the header's commit SHA is the --to-ref's own
        # commit, already resolved above.
        commit_sha = ref_commit_sha
    else:
        try:
            commit_sha = get_default_branch_head_sha(args.repo, config.github_token)
        except GitHubClientError as exc:
            print(str(exc), file=sys.stderr)
            return 1

    version = args.version or window_module.derive_identity_string(window)
    release_name = args.release_name or version

    try:
        header = build_release_identity(
            release_name=release_name,
            version=version,
            commit_sha=commit_sha,
            rc_branch=args.rc_branch,
        )
    except ReleaseIdentityError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    client = anthropic.Anthropic(api_key=config.anthropic_api_key)
    try:
        summary, input_tokens, output_tokens = summarize(
            pull_requests=prs,
            header=header,
            generated_at=datetime.now(timezone.utc),
            client=client,
        )
    except SummarizerError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    Path(args.output).write_text(render_summary(summary))

    estimated_cost = cost_module.compute_cost(DEFAULT_MODEL, input_tokens, output_tokens)
    print(
        f"Tokens used: {input_tokens} input / {output_tokens} output — "
        f"Est. cost: {cost_module.format_cost_for_display(estimated_cost)}"
    )
    cost_module.record_usage(
        cost_module.UsageRecord(
            timestamp=datetime.now(timezone.utc),
            repo=args.repo,
            since=window.resolved_start.date().isoformat(),
            until=window.resolved_end.date().isoformat(),
            model=DEFAULT_MODEL,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=estimated_cost,
        )
    )

    history_module.record(history, [pr.number for pr in prs], path=history_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
