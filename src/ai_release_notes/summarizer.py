"""Builds the prompt, calls Anthropic, retry/backoff (FR-003, FR-003a,
FR-014).
"""
import json
import time
from datetime import datetime
from typing import Callable, List, Tuple

from ai_release_notes.release_identity import ReleaseIdentity
from ai_release_notes.render import GeneratedSummary, PullRequest

DEFAULT_MODEL = "claude-sonnet-5"
MAX_ATTEMPTS = 3
INITIAL_BACKOFF_SECONDS = 2

CUSTOMER_CATEGORIES = ["Features", "Improvements", "Fixes"]
INTERNAL_LABEL = "Internal"


class SummarizerError(Exception):
    """Raised when the AI summarization call still fails after retries."""


def _build_prompt(pull_requests: List[PullRequest]) -> str:
    pr_lines = []
    for pr in pull_requests:
        labels = ", ".join(pr.labels) if pr.labels else "(none)"
        pr_lines.append(
            f"- #{pr.number}: {pr.title}\n"
            f"  Labels: {labels}\n"
            f"  Description: {pr.body or '(no description)'}"
        )

    return (
        "You are generating customer-facing release notes. For each pull "
        "request below, classify it into exactly one of these categories: "
        f"{', '.join(CUSTOMER_CATEGORIES)} (if it has customer-visible "
        f"impact), or '{INTERNAL_LABEL}' (if it is a purely internal/"
        "technical change such as a refactor, dependency bump, or CI "
        "change, with no customer-visible impact).\n\n"
        "Pull requests:\n" + "\n".join(pr_lines) + "\n\n"
        "Respond with ONLY a JSON object mapping each PR number (as a "
        f"string) to one of: {', '.join(CUSTOMER_CATEGORIES + [INTERNAL_LABEL])}. "
        'Example: {"101": "Features", "102": "Internal"}'
    )


def _parse_categorization(text: str) -> dict:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return {}


def summarize(
    pull_requests: List[PullRequest],
    header: ReleaseIdentity,
    generated_at: datetime,
    client,
    model: str = DEFAULT_MODEL,
    sleep_func: Callable[[float], None] = time.sleep,
) -> Tuple[GeneratedSummary, int, int]:
    last_error: Exception = SummarizerError("no attempts made")
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=2048,
                messages=[{"role": "user", "content": _build_prompt(pull_requests)}],
            )
            break
        except Exception as exc:  # noqa: BLE001 -- any failure is retryable
            last_error = exc
            if attempt < MAX_ATTEMPTS:
                sleep_func(INITIAL_BACKOFF_SECONDS * (2 ** (attempt - 1)))
    else:
        raise SummarizerError(
            f"AI summarization failed after {MAX_ATTEMPTS} attempts: {last_error}"
        ) from last_error

    categorization = _parse_categorization(response.content[0].text)

    customer_sections = {category: [] for category in CUSTOMER_CATEGORIES}
    internal_section: List[PullRequest] = []

    for pr in pull_requests:
        category = categorization.get(str(pr.number))
        if category in customer_sections:
            customer_sections[category].append(pr)
        else:
            # Unrecognized/missing category (including a hallucinated or
            # omitted PR number) defaults to internal -- never dropped.
            internal_section.append(pr)

    summary = GeneratedSummary(
        header=header,
        customer_sections=customer_sections,
        internal_section=internal_section,
        generated_at=generated_at,
    )
    return summary, response.usage.input_tokens, response.usage.output_tokens
