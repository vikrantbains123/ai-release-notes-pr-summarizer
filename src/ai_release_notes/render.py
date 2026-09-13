"""Generated Summary: renders categorized pull requests + a Release Identity
header into a customer-facing Markdown document (FR-003, FR-003a, FR-004,
FR-011).

Also defines PullRequest -- the Pull Request entity -- since render.py is
built before github_client.py (the module that will fetch real PRs) and
both need the same shape.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from ai_release_notes.release_identity import ReleaseIdentity


class ValidationError(Exception):
    """Raised when a Generated Summary violates an invariant (e.g. a PR
    placed in more than one section)."""


@dataclass
class PullRequest:
    number: int
    title: str
    author: str
    labels: List[str]
    body: Optional[str]
    merged_at: datetime
    linked_issues: List[str] = field(default_factory=list)


@dataclass
class GeneratedSummary:
    header: ReleaseIdentity
    customer_sections: Dict[str, List[PullRequest]]
    internal_section: List[PullRequest]
    generated_at: datetime


def validate_no_duplicate_placement(summary: GeneratedSummary) -> None:
    seen: Dict[int, str] = {}
    for category, prs in summary.customer_sections.items():
        for pr in prs:
            if pr.number in seen:
                raise ValidationError(
                    f"PR #{pr.number} appears in both '{seen[pr.number]}' and '{category}'"
                )
            seen[pr.number] = category
    for pr in summary.internal_section:
        if pr.number in seen:
            raise ValidationError(
                f"PR #{pr.number} appears in both '{seen[pr.number]}' and the internal section"
            )
        seen[pr.number] = "internal"


def render_summary(summary: GeneratedSummary) -> str:
    validate_no_duplicate_placement(summary)

    header = summary.header
    lines = [f"# {header.release_name}", ""]
    lines.append(f"**Version**: {header.version}")
    if header.rc_branch:
        lines.append(f"**RC Branch**: {header.rc_branch}")
    lines.append(f"**Commit**: {header.commit_sha}")
    lines.append("")

    for category, prs in summary.customer_sections.items():
        if not prs:
            continue
        lines.append(f"## {category}")
        lines.append("")
        for pr in prs:
            lines.append(f"- {pr.title} (#{pr.number})")
        lines.append("")

    if summary.internal_section:
        lines.append("## Other/Internal Changes")
        lines.append("")
        for pr in summary.internal_section:
            lines.append(f"- {pr.title} (#{pr.number})")
        lines.append("")

    return "\n".join(lines)
