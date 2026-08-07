from collectors.detector import (
    ATSDetector,
)
from collectors.registry import (
    CollectorRegistry,
)
from utils.ats_cache import (
    ATSCache,
)
from utils.config_loader import (
    ConfigLoader,
)


config = ConfigLoader()
config.load()

detector = ATSDetector()

registry = CollectorRegistry()

cache = ATSCache(
    retention_days=(
        config.ats_cache_retention_days
    )
)


supported = 0
unsupported = 0
cached_count = 0


try:

    print(
        "=" * 90
    )

    print(
        f"{'Company':<25}"
        f"{'ATS':<18}"
        f"{'Status':<15}"
        f"{'Detection'}"
    )

    print(
        "=" * 90
    )

    for company_info in (
        config.companies_with_urls
    ):

        company = (
            company_info[
                "company"
            ]
        )

        configured_url = (
            company_info[
                "url"
            ]
        )

        cached = cache.get(
            company,
            configured_url,
        )

        if cached:

            ats = cached[
                "ats"
            ]

            detected_url = (
                cached["url"]
            )

            detected_by = (
                "cache"
            )

            cached_count += 1

        else:

            detection = (
                detector.detect(
                    configured_url
                )
            )

            ats = detection.ats

            detected_url = (
                detection.url
            )

            detected_by = (
                detection.detected_by
            )

            cache.set(
                company=company,
                configured_url=(
                    configured_url
                ),
                ats=ats,
                detected_url=(
                    detected_url
                ),
                detected_by=(
                    detected_by
                ),
            )

        collector = registry.get(
            ats
        )

        if collector:

            status = "SUPPORTED"

            supported += 1

        else:

            status = "UNSUPPORTED"

            unsupported += 1

        print(
            f"{company:<25}"
            f"{ats:<18}"
            f"{status:<15}"
            f"{detected_by}"
        )

    print(
        "=" * 90
    )

    print(
        f"Supported   : "
        f"{supported}"
    )

    print(
        f"Unsupported : "
        f"{unsupported}"
    )

    print(
        f"From cache  : "
        f"{cached_count}"
    )

finally:

    detector.close()