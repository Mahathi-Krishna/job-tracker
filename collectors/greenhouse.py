import requests

from collectors.base import BaseCollector


class GreenhouseCollector(BaseCollector):

    BASE_URL = "https://boards-api.greenhouse.io/v1/boards/{identifier}/jobs"

    def collect(self, company, identifier):

        url = self.BASE_URL.format(identifier=identifier)

        response = requests.get(url, timeout=20)

        response.raise_for_status()

        data = response.json()

        jobs = []

        #
        # We'll transform the JSON into Job objects
        # in the next step.
        #

        return jobs