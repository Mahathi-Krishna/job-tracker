from collectors.ashby import (
    AshbyCollector,
)
from collectors.greenhouse import (
    GreenhouseCollector,
)
from collectors.lever import (
    LeverCollector,
)
from collectors.smartrecruiters import (
    SmartRecruitersCollector,
)
from collectors.workday import (
    WorkdayCollector,
)


class CollectorRegistry:

    def __init__(
        self,
    ):

        self.collectors = {
            "ashby":
                AshbyCollector(),

            "greenhouse":
                GreenhouseCollector(),

            "lever":
                LeverCollector(),

            "smartrecruiters":
                SmartRecruitersCollector(),

            "workday":
                WorkdayCollector(),
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