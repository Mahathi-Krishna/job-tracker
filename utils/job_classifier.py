from __future__ import annotations

import re

from models.job import Job


class JobClassifier:
    """
    Lightweight rule-based classification.

    No ML models or external APIs are used.
    """

    EU_COUNTRIES = {
        "austria",
        "belgium",
        "bulgaria",
        "croatia",
        "cyprus",
        "czech republic",
        "czechia",
        "denmark",
        "estonia",
        "finland",
        "france",
        "germany",
        "greece",
        "hungary",
        "ireland",
        "italy",
        "latvia",
        "lithuania",
        "luxembourg",
        "malta",
        "netherlands",
        "poland",
        "portugal",
        "romania",
        "slovakia",
        "slovenia",
        "spain",
        "sweden",
    }

    US_STATE_CODES = {
        "al", "ak", "az", "ar", "ca", "co", "ct", "de",
        "fl", "ga", "hi", "id", "il", "in", "ia", "ks",
        "ky", "la", "me", "md", "ma", "mi", "mn", "ms",
        "mo", "mt", "ne", "nv", "nh", "nj", "nm", "ny",
        "nc", "nd", "oh", "ok", "or", "pa", "ri", "sc",
        "sd", "tn", "tx", "ut", "vt", "va", "wa", "wv",
        "wi", "wy", "dc",
    }

    CANADIAN_PROVINCES = {
        "alberta",
        "british columbia",
        "manitoba",
        "new brunswick",
        "newfoundland and labrador",
        "nova scotia",
        "ontario",
        "prince edward island",
        "quebec",
        "saskatchewan",
        "northwest territories",
        "nunavut",
        "yukon",
    }

    CANADIAN_PROVINCE_CODES = {
        "ab", "bc", "mb", "nb", "nl", "ns",
        "nt", "nu", "on", "pe", "qc", "sk", "yt",
    }

    UK_TERMS = {
        "united kingdom",
        "england",
        "scotland",
        "wales",
        "northern ireland",
    }

    @staticmethod
    def _normalize(text: str | None) -> str:

        if not text:
            return ""

        text = text.lower()

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    @staticmethod
    def _contains_phrase(
        text: str,
        phrase: str,
    ) -> bool:

        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(phrase.lower())
            + r"(?![a-z0-9])"
        )

        return bool(
            re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )
        )

    def classify_country(
        self,
        location: str,
    ) -> str:

        text = self._normalize(location)

        if not text:
            return "Unknown"

        # -------------------------
        # United States
        # -------------------------

        if (
            self._contains_phrase(
                text,
                "united states",
            )
            or self._contains_phrase(
                text,
                "usa",
            )
            or self._contains_phrase(
                text,
                "u.s.",
            )
        ):
            return "United States"

        # Workday often returns locations such as:
        #
        # US, CA, Santa Clara
        # US, TX, Austin

        if re.search(
            r"(^|[,/\s])us([,/\s]|$)",
            text,
            flags=re.IGNORECASE,
        ):
            return "United States"

        tokens = {
            token.lower()
            for token in re.findall(
                r"\b[a-zA-Z]{2}\b",
                location,
            )
        }

        if tokens & self.US_STATE_CODES:
            return "United States"

        # -------------------------
        # Canada
        # -------------------------

        if self._contains_phrase(
            text,
            "canada",
        ):
            return "Canada"

        if re.search(
            r"(^|[,/\s])can([,/\s]|$)",
            text,
            flags=re.IGNORECASE,
        ):
            return "Canada"

        for province in self.CANADIAN_PROVINCES:

            if self._contains_phrase(
                text,
                province,
            ):
                return "Canada"

        if tokens & self.CANADIAN_PROVINCE_CODES:
            return "Canada"

        # -------------------------
        # United Kingdom
        # -------------------------

        for term in self.UK_TERMS:

            if self._contains_phrase(
                text,
                term,
            ):
                return "United Kingdom"

        if re.search(
            r"(^|[,/\s])uk([,/\s]|$)",
            text,
            flags=re.IGNORECASE,
        ):
            return "United Kingdom"

        # -------------------------
        # European Union
        # -------------------------

        for country in self.EU_COUNTRIES:

            if self._contains_phrase(
                text,
                country,
            ):
                return "European Union"

        return "Unknown"

    def classify_work_mode(
        self,
        job: Job,
    ) -> str:

        text = self._normalize(
            " ".join(
                [
                    job.title or "",
                    job.location or "",
                    job.description or "",
                ]
            )
        )

        if self._contains_phrase(
            text,
            "hybrid",
        ):
            return "Hybrid"

        remote_terms = [
            "remote",
            "work from home",
            "work-from-home",
            "home based",
            "home-based",
        ]

        for term in remote_terms:

            if self._contains_phrase(
                text,
                term,
            ):
                return "Remote"

        onsite_terms = [
            "on-site",
            "onsite",
            "on site",
        ]

        for term in onsite_terms:

            if self._contains_phrase(
                text,
                term,
            ):
                return "On-site"

        return "Unknown"

    def classify_job_type(
        self,
        job: Job,
    ) -> str:

        text = self._normalize(
            " ".join(
                [
                    job.title or "",
                    job.job_type or "",
                    job.description or "",
                ]
            )
        )

        # Order matters.
        # Co-op should be checked before
        # generic full-time terms.

        coop_terms = [
            "co-op",
            "coop",
            "co op",
        ]

        for term in coop_terms:

            if self._contains_phrase(
                text,
                term,
            ):
                return "Co-op"

        internship_terms = [
            "internship",
            "intern",
            "summer intern",
        ]

        for term in internship_terms:

            if self._contains_phrase(
                text,
                term,
            ):
                return "Internship"

        new_grad_terms = [
            "new grad",
            "new graduate",
            "recent graduate",
            "graduate engineer",
            "university graduate",
        ]

        for term in new_grad_terms:

            if self._contains_phrase(
                text,
                term,
            ):
                return "New Grad"

        entry_terms = [
            "entry level",
            "entry-level",
            "early career",
            "junior engineer",
        ]

        for term in entry_terms:

            if self._contains_phrase(
                text,
                term,
            ):
                return "Entry Level"

        full_time_terms = [
            "full time",
            "full-time",
            "regular",
            "permanent",
        ]

        for term in full_time_terms:

            if self._contains_phrase(
                text,
                term,
            ):
                return "Full-time"

        return "Unknown"

    def classify(
        self,
        job: Job,
    ) -> Job:

        job.country = self.classify_country(
            job.location
        )

        job.work_mode = (
            self.classify_work_mode(job)
        )

        job.job_type = (
            self.classify_job_type(job)
        )

        return job