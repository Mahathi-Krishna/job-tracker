from urllib.parse import urlparse


class ATSDetector:
    """
    Detect an ATS from a direct careers/ATS URL.

    Network-based detection will be added separately.
    """

    @staticmethod
    def detect(url: str) -> str:

        if not url:
            return "unknown"

        parsed = urlparse(url)

        hostname = parsed.netloc.lower()

        if (
            "greenhouse.io" in hostname
            or "greenhouse.com" in hostname
        ):
            return "greenhouse"

        if (
            "lever.co" in hostname
            or "jobs.lever.co" in hostname
        ):
            return "lever"

        if "myworkdayjobs.com" in hostname:
            return "workday"

        if "ashbyhq.com" in hostname:
            return "ashby"

        if "smartrecruiters.com" in hostname:
            return "smartrecruiters"

        if "icims.com" in hostname:
            return "icims"

        if (
            "oraclecloud.com" in hostname
            or "oracle.com" in hostname
        ):
            return "oracle"

        if "successfactors" in hostname:
            return "successfactors"

        return "generic"