from abc import ABC
from abc import abstractmethod

from models.job import Job


class BaseCollector(ABC):

    @abstractmethod
    def collect(self, company: str, career_url: str) -> list[Job]:
        """
        Collect jobs for a company.

        Returns a list of Job objects.
        """
        raise NotImplementedError