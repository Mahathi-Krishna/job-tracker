from collectors.ashby import (
    AshbyCollector,
)
from collectors.generic_html import (
    GenericHTMLCollector,
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
from collectors.synopsys import (
    SynopsysCollector,
)
from collectors.arm import (
    ArmCollector,
)
from collectors.amd import (
    AMDCollector,
)

class CollectorRegistry:

    def __init__(
        self,
    ):

        self.collectors = {
            "ashby":
                AshbyCollector(),

            "generic":
                GenericHTMLCollector(),

            "greenhouse":
                GreenhouseCollector(),

            "lever":
                LeverCollector(),

            "smartrecruiters":
                SmartRecruitersCollector(),

            "workday":
                WorkdayCollector(),

            "synopsys":
                SynopsysCollector(),

            "arm":
                ArmCollector(),
            
            "amd":
                AMDCollector(),
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