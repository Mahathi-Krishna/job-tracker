from pathlib import Path

from collectors.detector import ATSDetector
from collectors.registry import CollectorRegistry
from utils.ats_cache import ATSCache
from utils.config_loader import ConfigLoader


ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

PRIORITY_FILE = (
    ROOT
    / "config"
    / "coverage_priority.txt"
)

REPORT_FILE = (
    ROOT
    / "data"
    / "coverage_report.txt"
)


def load_priority():

    if not PRIORITY_FILE.exists():
        return set()

    return {
        line.strip()
        for line
        in PRIORITY_FILE.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
        and not line.startswith("#")
    }


config = ConfigLoader()
config.load()

priority = load_priority()

detector = ATSDetector()

registry = CollectorRegistry()

cache = ATSCache(
    config.ats_cache_retention_days
)


lines = []

lines.append(
    "JOB MONITOR COVERAGE REPORT"
)

lines.append(
    "=" * 80
)


try:

    for item in (
        config.companies_with_urls
    ):

        company = item["company"]

        configured_url = item["url"]

        override = (
            config.ats_overrides.get(
                company
            )
        )

        if override:

            ats = override.get(
                "ats",
                "generic",
            )

            resolved_url = (
                override.get(
                    "url",
                    configured_url,
                )
            )

            method = "override"

        else:

            cached = cache.get(
                company,
                configured_url,
            )

            if cached:

                ats = cached["ats"]

                resolved_url = (
                    cached["url"]
                )

                method = "cache"

            else:

                result = detector.detect(
                    configured_url
                )

                ats = result.ats

                resolved_url = (
                    result.url
                )

                method = (
                    result.detected_by
                )

        collector = registry.get(
            ats
        )

        supported = (
            collector is not None
        )

        priority_mark = (
            "*"
            if company in priority
            else " "
        )

        lines.append(
            f"{priority_mark} "
            f"{company:<25} "
            f"{ats:<18} "
            f"{'SUPPORTED' if supported else 'UNSUPPORTED':<12} "
            f"{method:<10} "
            f"{resolved_url}"
        )

finally:

    detector.close()


REPORT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

REPORT_FILE.write_text(
    "\n".join(lines),
    encoding="utf-8",
)


print(
    f"Coverage report written to:"
)

print(
    REPORT_FILE
)