from collectors.detector import (
    ATSDetectionResult,
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


def resolve_company(
    company: str,
    configured_url: str,
    config: ConfigLoader,
    cache: ATSCache,
    detector: ATSDetector,
) -> ATSDetectionResult:

    override = (
        config.ats_overrides.get(
            company
        )
    )

    if override:

        ats = (
            override.get(
                "ats",
                ""
            )
            .strip()
            .lower()
        )

        url = (
            override.get(
                "url",
                configured_url,
            )
            .strip()
        )

        if ats:

            return ATSDetectionResult(
                ats=ats,
                url=url,
                detected_by="override",
            )

    cached = cache.get(
        company,
        configured_url,
    )

    if cached:

        return ATSDetectionResult(
            ats=cached["ats"],
            url=cached["url"],
            detected_by="cache",
        )

    detection = detector.detect(
        configured_url
    )

    cache.set(
        company=company,
        configured_url=(
            configured_url
        ),
        ats=detection.ats,
        detected_url=(
            detection.url
        ),
        detected_by=(
            detection.detected_by
        ),
    )

    return detection


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


try:

    print(
        "=" * 100
    )

    print(
        f"{'Company':<25}"
        f"{'ATS':<18}"
        f"{'Status':<15}"
        f"{'Detection':<15}"
        f"Resolved URL"
    )

    print(
        "=" * 100
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

        result = resolve_company(
            company=company,
            configured_url=(
                configured_url
            ),
            config=config,
            cache=cache,
            detector=detector,
        )

        collector = registry.get(
            result.ats
        )

        if collector:

            status = "SUPPORTED"
            supported += 1

        else:

            status = "UNSUPPORTED"
            unsupported += 1

        print(
            f"{company:<25}"
            f"{result.ats:<18}"
            f"{status:<15}"
            f"{result.detected_by:<15}"
            f"{result.url}"
        )

    print(
        "=" * 100
    )

    print(
        f"Supported   : "
        f"{supported}"
    )

    print(
        f"Unsupported : "
        f"{unsupported}"
    )

finally:

    detector.close()