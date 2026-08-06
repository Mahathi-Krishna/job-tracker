from urllib.parse import urlparse


class ATSDetector:
    """
    Detect the ATS platform from a company's careers URL.
    """

    @staticmethod
    def detect(url: str) -> str:

        hostname = urlparse(url).netloc.lower()

        if "greenhouse" in hostname:
            return "greenhouse"

        if "lever" in hostname:
            return "lever"

        if "myworkdayjobs" in hostname:
            return "workday"

        if "smartrecruiters" in hostname:
            return "smartrecruiters"

        if "ashby" in hostname:
            return "ashby"

        if "icims" in hostname:
            return "icims"

        if "oracle" in hostname:
            return "oracle"

        if "successfactors" in hostname:
            return "successfactors"

        return "generic"