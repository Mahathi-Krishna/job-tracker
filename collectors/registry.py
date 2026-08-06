from collectors.greenhouse import GreenhouseCollector
from collectors.lever import LeverCollector


class CollectorRegistry:

    def __init__(self):

        self.collectors = {
            "greenhouse": GreenhouseCollector(),
            "lever": LeverCollector(),
        }

    def get(self, ats: str):
        return self.collectors.get(ats)