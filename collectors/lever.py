import requests

from collectors.base import BaseCollector


class LeverCollector(BaseCollector):

    BASE_URL = "https://api.lever.co/v0/postings/{identifier}"

    def collect(self, company, identifier):

        response = requests.get(
            self.BASE_URL.format(identifier=identifier),
            timeout=20,
        )

        response.raise_for_status()

        return []