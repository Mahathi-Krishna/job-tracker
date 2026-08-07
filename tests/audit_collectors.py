from collectors.detector import (
    ATSDetectionResult,
    ATSDetector,
)
from collectors.registry import (
    CollectorRegistry,
)
from utils.ats_cache import ATSCache
from utils.config_loader import (
    ConfigLoader,
)


def resolve(
    company,
    configured_url,
    config,
    cache,
    detector,
):

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

    result = detector.detect(
        configured_url
    )

    cache.set(
        company=company,
        configured_url=(
            configured_url
        ),
        ats=result.ats,
        detected_url=result.url,
        detected_by=(
            result.detected_by
        ),
    )

    return result


config = ConfigLoader()
config.load()

detector = ATSDetector()

registry = CollectorRegistry()

cache = ATSCache(
    retention_days=(
        config.ats_cache_retention_days
    )
)


working = 0
failed = 0
unsupported = 0


try:

    print(
        "=" * 110
    )

    print(
        f"{'Company':<25}"
        f"{'ATS':<20}"
        f"{'Result':<15}"
        f"{'Jobs':<10}"
        f"Resolved URL"
    )

    print(
        "=" * 110
    )

    for company_info in (
        config.companies_with_urls
    ):

        company = (
            company_info["company"]
        )

        configured_url = (
            company_info["url"]
        )

        result = resolve(
            company,
            configured_url,
            config,
            cache,
            detector,
        )

        collector = registry.get(
            result.ats
        )

        if collector is None:

            unsupported += 1

            print(
                f"{company:<25}"
                f"{result.ats:<20}"
                f"{'UNSUPPORTED':<15}"
                f"{'-':<10}"
                f"{result.url}"
            )

            continue

        try:

            jobs = collector.collect(
                company,
                result.url,
            )

        except Exception as exc:

            failed += 1

            exception_name = (
                type(exc).__name__
            )

            message = str(exc)

            if "404" in message:
                failure_type = "BAD_URL"

            elif "400" in message:
                failure_type = "BAD_REQUEST"

            elif "403" in message:
                failure_type = "BLOCKED"

            elif "429" in message:
                failure_type = "RATE_LIMIT"

            elif (
                "timeout" in message.lower()
            ):
                failure_type = "TIMEOUT"

            elif isinstance(
                exc,
                ValueError,
            ):
                failure_type = "BAD_CONFIG"

            else:
                failure_type = exception_name

            error = (
                f"{failure_type}: "
                f"{message[:70]}"
            )

            print(
                f"{company:<25}"
                f"{result.ats:<20}"
                f"{'FAILED':<15}"
                f"{'-':<10}"
                f"{error}"
            )

            continue

        working += 1

        print(
            f"{company:<25}"
            f"{result.ats:<20}"
            f"{'WORKING':<15}"
            f"{len(jobs):<10}"
            f"{result.url}"
        )

    print(
        "=" * 110
    )

    print(
        f"Working     : {working}"
    )

    print(
        f"Failed      : {failed}"
    )

    print(
        f"Unsupported : {unsupported}"
    )

finally:

    detector.close()