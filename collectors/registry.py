from collectors.greenhouse import GreenhouseCollector
from collectors.lever import LeverCollector
from collectors.workday import WorkdayCollector


class CollectorRegistry:
    """
    Registry of implemented ATS collectors.
    """

    def __init__(self):

        self.collectors = {
            "greenhouse": GreenhouseCollector(),
            "lever": LeverCollector(),
            "workday": WorkdayCollector(),
        }

    def get(
        self,
        ats: str,
    ):

        if not ats:
            return None

        return self.collectors.get(
            ats.strip().lower()
        )

    def supported_platforms(
        self,
    ) -> list[str]:

        return sorted(
            self.collectors.keys()
        )