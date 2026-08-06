from __future__ import annotations

from abc import ABC, abstractmethod

from models.job import Job


class BaseCollector(ABC):

    @abstractmethod
    def collect(
        self,
        company: str,
        career_url: str,
    ) -> list[Job]:
        """
        Retrieve lightweight job listings.
        """
        raise NotImplementedError

    def enrich(
        self,
        job: Job,
    ) -> Job:
        """
        Optionally retrieve additional details.

        Collectors that already include descriptions
        can simply inherit this implementation.
        """

        return job