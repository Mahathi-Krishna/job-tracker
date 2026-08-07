from __future__ import annotations

import re

from models.job import Job


class JobClassifier:
    """
    Lightweight rule-based job classifier.

    Classifies:
      - country
      - work mode
      - employment type
      - experience level

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

    SENIOR_TERMS = {
        "senior",
        "sr",
        "sr.",
        "staff",
        "principal",
        "lead",
        "manager",
        "director",
        "distinguished",
        "fellow",
        "architect",
    }

    ENTRY_TERMS = {
        "entry level",
        "entry-level",
        "early career",
        "junior",
        "junior engineer",
    }

    NEW_GRAD_TERMS = {
        "new grad",
        "new graduate",
        "recent graduate",
        "university graduate",
        "graduate engineer",
        "graduate hardware engineer",
    }

    @staticmethod
    def _normalize(
        text,
    ) -> str:

        if text is None:
            return ""

        if isinstance(
            text,
            str,
        ):

            value = text

        elif isinstance(
            text,
            dict,
        ):

            #
            # Prefer meaningful textual
            # values from structured ATS data.
            #

            parts = []

            for key in (
                "label",
                "name",
                "value",
                "text",
                "id",
            ):

                candidate = (
                    text.get(key)
                )

                if isinstance(
                    candidate,
                    str,
                ) and candidate.strip():

                    parts.append(
                        candidate
                    )

            value = " ".join(
                parts
            )

        elif isinstance(
            text,
            (
                list,
                tuple,
                set,
            ),
        ):

            value = " ".join(
                str(item)
                for item in text
                if item is not None
            )

        else:

            value = str(
                text
            )

        return re.sub(
            r"\s+",
            " ",
            value.lower(),
        ).strip()
    
    @staticmethod
    def _contains_phrase(
        text: str,
        phrase: str,
    ) -> bool:

        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(
                phrase.lower()
            )
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

        text = self._normalize(
            location
        )

        if not text:
            return "Unknown"

        if any(
            self._contains_phrase(
                text,
                term,
            )
            for term in (
                "united states",
                "usa",
                "u.s.",
            )
        ):
            return "United States"

        if re.search(
            r"(^|[,/\s])us([,/\s]|$)",
            text,
            flags=re.IGNORECASE,
        ):
            return "United States"

        tokens = {
            token.lower()
            for token in re.findall(
                r"\b[A-Za-z]{2}\b",
                location,
            )
        }

        if (
            tokens
            & self.US_STATE_CODES
        ):
            return "United States"

        if self._contains_phrase(
            text,
            "canada",
        ):
            return "Canada"

        for province in (
            self.CANADIAN_PROVINCES
        ):

            if self._contains_phrase(
                text,
                province,
            ):
                return "Canada"

        if (
            tokens
            & self.CANADIAN_PROVINCE_CODES
        ):
            return "Canada"

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

        text = " ".join(
            [
                self._normalize(
                    job.title
                ),
                self._normalize(
                    job.location
                ),
                self._normalize(
                    job.description
                ),
            ]
        )

        if self._contains_phrase(
            text,
            "hybrid",
        ):
            return "Hybrid"

        for term in (
            "remote",
            "work from home",
            "work-from-home",
            "home based",
            "home-based",
        ):

            if self._contains_phrase(
                text,
                term,
            ):
                return "Remote"

        for term in (
            "on-site",
            "onsite",
            "on site",
        ):

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
        """
        Employment type only.

        Career level is handled separately.
        """

        text = " ".join(
            [
                self._normalize(
                    job.title
                ),
                self._normalize(
                    job.job_type
                ),
                self._normalize(
                    job.description
                ),
            ]
        )

        for term in (
            "co-op",
            "coop",
            "co op",
        ):

            if self._contains_phrase(
                text,
                term,
            ):
                return "Co-op"

        for term in (
            "internship",
            "intern",
            "summer intern",
        ):

            if self._contains_phrase(
                text,
                term,
            ):
                return "Internship"

        for term in (
            "full-time",
            "full time",
            "regular full time",
            "regular full-time",
            "permanent",
        ):

            if self._contains_phrase(
                text,
                term,
            ):
                return "Full-time"

        return "Unknown"

    def classify_experience_level(
        self,
        job: Job,
    ) -> str:

        title = self._normalize(
            job.title
        )

        text = " ".join(
            [
                self._normalize(
                    job.title
                ),
                self._normalize(
                    job.description
                ),
            ]
        )

        # Seniority in the title is strong
        # evidence and takes precedence.

        for term in self.SENIOR_TERMS:

            if self._contains_phrase(
                title,
                term,
            ):
                return "Senior"

        for term in self.NEW_GRAD_TERMS:

            if self._contains_phrase(
                text,
                term,
            ):
                return "New Grad"

        for term in self.ENTRY_TERMS:

            if self._contains_phrase(
                text,
                term,
            ):
                return "Entry Level"

        if any(
            self._contains_phrase(
                title,
                term,
            )
            for term in (
                "intern",
                "internship",
                "co-op",
                "coop",
            )
        ):
            return "Student"

        return "Unknown"

    def classify(
        self,
        job: Job,
    ) -> Job:

        job.country = (
            self.classify_country(
                job.location
            )
        )

        job.work_mode = (
            self.classify_work_mode(
                job
            )
        )

        job.job_type = (
            self.classify_job_type(
                job
            )
        )

        job.experience_level = (
            self.classify_experience_level(
                job
            )
        )

        return job