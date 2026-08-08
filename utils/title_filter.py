from __future__ import annotations

import re


class TitleFilter:
    """
    Lightweight title-only relevance filter.

    Used by high-volume collectors to discard
    obviously irrelevant listings before creating
    full Job objects.

    This is only a pre-filter. Final relevance is
    still decided by Matcher.
    """

    def __init__(
        self,
        keywords: list[str],
        role_keywords: list[str],
    ):

        combined = (
            role_keywords
            + keywords
        )

        self.patterns = []

        seen = set()

        for keyword in combined:

            keyword = keyword.strip()

            if not keyword:
                continue

            normalized = (
                keyword.casefold()
            )

            if normalized in seen:
                continue

            seen.add(
                normalized
            )

            escaped = re.escape(
                keyword
            )

            pattern = re.compile(
                r"(?<![A-Za-z0-9])"
                + escaped
                + r"(?![A-Za-z0-9])",
                flags=re.IGNORECASE,
            )

            self.patterns.append(
                pattern
            )

    def matches(
        self,
        title: str,
    ) -> bool:

        if not title:
            return False

        return any(
            pattern.search(
                title
            )
            for pattern
            in self.patterns
        )