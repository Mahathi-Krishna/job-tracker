from __future__ import annotations

import re

from models.job import Job


class Matcher:
    """
    Lightweight role-aware job matcher.

    Role keywords describe job families:
        Physical Design
        RTL Design
        Design Verification
        DFT
        etc.

    General keywords describe relevant
    technologies and skills:
        UVM
        SystemVerilog
        Verilog
        PrimeTime
        Innovus
        etc.
    """

    STRONG_ROLE_SCORE = 70

    SUPPORTING_TITLE_SCORE = 15

    SUPPORTING_DESCRIPTION_SCORE = 5

    MAX_SUPPORTING_TITLE_SCORE = 30

    MAX_SUPPORTING_DESCRIPTION_SCORE = 20

    def __init__(
        self,
        keywords: list[str],
        role_keywords: list[str],
        minimum_score: int,
    ):

        self.keywords = self._deduplicate(
            keywords
        )

        self.role_keywords = (
            self._deduplicate(
                role_keywords
            )
        )

        self.minimum_score = (
            minimum_score
        )

        self.keyword_patterns = {
            keyword:
                self._compile_keyword(
                    keyword
                )
            for keyword
            in self.keywords
        }

        self.role_patterns = {
            keyword:
                self._compile_keyword(
                    keyword
                )
            for keyword
            in self.role_keywords
        }

    @staticmethod
    def _deduplicate(
        values: list[str],
    ) -> list[str]:

        result = []

        seen = set()

        for value in values:

            value = value.strip()

            if not value:
                continue

            key = value.casefold()

            if key in seen:
                continue

            seen.add(key)

            result.append(value)

        return result

    @staticmethod
    def _compile_keyword(
        keyword: str,
    ) -> re.Pattern:

        escaped = re.escape(
            keyword.strip()
        )

        return re.compile(
            r"(?<![A-Za-z0-9])"
            + escaped
            + r"(?![A-Za-z0-9])",
            flags=re.IGNORECASE,
        )

    @staticmethod
    def _find_matches(
        text: str,
        patterns: dict[
            str,
            re.Pattern,
        ],
    ) -> list[str]:

        if not text:
            return []

        return [
            keyword
            for keyword, pattern
            in patterns.items()
            if pattern.search(text)
        ]

    def find_keywords(
        self,
        text: str,
    ) -> list[str]:

        return self._find_matches(
            text,
            self.keyword_patterns,
        )

    def find_roles(
        self,
        text: str,
    ) -> list[str]:

        return self._find_matches(
            text,
            self.role_patterns,
        )

    def title_matches(
        self,
        job: Job,
    ) -> bool:
        """
        Stage 1 screening.

        Accept a title when:

        1. It directly matches a configured
           role phrase; OR

        2. It contains at least two relevant
           supporting keywords.

        The second condition catches titles
        such as:
            UVM Verification Engineer
        even if the exact phrase isn't in
        role_keywords.txt.
        """

        role_matches = (
            self.find_roles(
                job.title
            )
        )

        if role_matches:
            return True

        supporting = (
            self.find_keywords(
                job.title
            )
        )

        return len(
            supporting
        ) >= 2

    def score(
        self,
        job: Job,
    ) -> int:

        title = (
            job.title
            or ""
        )

        description = (
            job.description
            or ""
        )

        # -------------------------
        # Strong role matches
        # -------------------------

        title_roles = (
            self.find_roles(
                title
            )
        )

        # -------------------------
        # Supporting keywords
        # -------------------------

        title_keywords = (
            self.find_keywords(
                title
            )
        )

        description_keywords = (
            self.find_keywords(
                description
            )
        )

        # -------------------------
        # Score
        # -------------------------

        score = 0

        if title_roles:

            score += (
                self.STRONG_ROLE_SCORE
            )

        # Don't reward the same phrase
        # twice merely because it exists
        # in role_keywords and keywords.

        role_names = {
            value.casefold()
            for value
            in title_roles
        }

        supporting_title = [
            keyword
            for keyword
            in title_keywords
            if keyword.casefold()
            not in role_names
        ]

        title_bonus = min(
            len(supporting_title)
            * self.SUPPORTING_TITLE_SCORE,
            self.MAX_SUPPORTING_TITLE_SCORE,
        )

        score += title_bonus

        title_keyword_names = {
            value.casefold()
            for value
            in title_keywords
        }

        description_only = [
            keyword
            for keyword
            in description_keywords
            if keyword.casefold()
            not in title_keyword_names
        ]

        description_bonus = min(
            len(description_only)
            * self.SUPPORTING_DESCRIPTION_SCORE,
            self.MAX_SUPPORTING_DESCRIPTION_SCORE,
        )

        score += description_bonus

        # -------------------------
        # Fallback:
        #
        # Some titles don't exactly
        # match role_keywords but have
        # multiple strong terms.
        #
        # Example:
        # UVM Verification Engineer
        # -------------------------

        if (
            not title_roles
            and len(title_keywords) >= 2
        ):

            score = max(
                score,
                65,
            )

        job.score = min(
            score,
            100,
        )

        # -------------------------
        # Spreadsheet keywords
        # -------------------------

        combined = (
            title_roles
            + title_keywords
            + description_keywords
        )

        job.keywords = (
            self._deduplicate(
                combined
            )
        )

        return job.score

    def is_match(
        self,
        job: Job,
    ) -> bool:

        score = self.score(
            job
        )

        return (
            score
            >= self.minimum_score
        )