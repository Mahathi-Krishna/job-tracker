from utils.job_validator import (
    JobValidator,
)
from datetime import (
    datetime,
    timezone,
)
from collectors.detector import (
    ATSDetectionResult,
    ATSDetector,
)
from collectors.registry import (
    CollectorRegistry,
)
from database.sqlite_db import (
    JobDatabase,
)
from matcher.matcher import Matcher
from sheets.google_sheets import (
    GoogleSheetsClient,
)
from utils.ats_cache import (
    ATSCache,
)
from utils.config_loader import (
    ConfigLoader,
)
from utils.job_classifier import (
    JobClassifier,
)
from utils.logger import logger


def get_detection(
    company: str,
    configured_url: str,
    detector: ATSDetector,
    cache: ATSCache,
    overrides: dict,
) -> ATSDetectionResult:

    override = overrides.get(
        company
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


def main():

    logger.info(
        "=" * 60
    )

    logger.info(
        "Starting Job Monitor"
    )

    config = ConfigLoader()
    config.load()

    database = JobDatabase()

    detector = ATSDetector()

    classifier = JobClassifier()

    cache = ATSCache(
        retention_days=(
            config
            .ats_cache_retention_days
        )
    )

    pending_jobs = []

    try:

        deleted = database.cleanup(
            config.retention_days
        )

        if deleted:

            logger.info(
                f"Database cleanup: "
                f"{deleted} old records "
                f"removed"
            )

        sheets = GoogleSheetsClient(
            config.credentials_file,
            config.spreadsheet_name,
            config.worksheet_name,
        )

        matcher = Matcher(
            keywords=(
                config.keywords
            ),
            role_keywords=(
                config.role_keywords
            ),
            minimum_score=(
                config.minimum_score
            ),
        )

        registry = (
            CollectorRegistry()
        )

        companies = (
            config.companies_with_urls
        )

        logger.info(
            f"Companies configured: "
            f"{len(companies)}"
        )

        total_jobs_found = 0
        title_candidates = 0
        enriched_jobs = 0
        matched_jobs = 0

        filtered_location = 0
        filtered_experience = 0
        filtered_job_type = 0

        unsupported_companies = 0
        failed_companies = 0

        for company_info in companies:

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

            detection = get_detection(
                company=company,
                configured_url=(
                    configured_url
                ),
                detector=detector,
                cache=cache,
                overrides=(
                    config.ats_overrides
                ),
            )

            collector = (
                registry.get(
                    detection.ats
                )
            )

            if collector is None:

                unsupported_companies += 1

                logger.info(
                    f"{company}: "
                    f"unsupported ATS "
                    f"'{detection.ats}'"
                )

                continue

            logger.info(
                f"Checking {company} "
                f"({detection.ats}, "
                f"{detection.detected_by})"
            )

            try:

                jobs = (
                    collector.collect(
                        company,
                        detection.url,
                    )
                )

            except Exception as exc:

                failed_companies += 1

                logger.exception(
                    f"{company}: "
                    f"collection failed: "
                    f"{exc}"
                )

                continue

            total_jobs_found += len(
                jobs
            )

            logger.info(
                f"{company}: "
                f"{len(jobs)} listings"
            )

            for job in jobs:
                #
                # Basic sanity validation before
                # any matching or enrichment work.
                #
                if not JobValidator.is_valid(
                    job
                ):
                    continue

                if database.exists(
                    job
                ):
                    continue
                
        # ------------------------------
        # One Sheets operation
        # ------------------------------

        if pending_jobs:

            logger.info(
                f"Writing "
                f"{len(pending_jobs)} "
                f"jobs to Google Sheets"
            )

            sheets.append_jobs(
                pending_jobs
            )

            # Only record jobs locally
            # after Sheets succeeds.

            for job in pending_jobs:

                database.insert(
                    job
                )

                logger.info(
                    f"Added: "
                    f"{job.company} | "
                    f"{job.title}"
                )

        logger.info(
            "-" * 60
        )

        logger.info(
            f"Listings found: "
            f"{total_jobs_found}"
        )

        logger.info(
            f"Title candidates: "
            f"{title_candidates}"
        )

        logger.info(
            f"Jobs enriched: "
            f"{enriched_jobs}"
        )

        logger.info(
            f"Location filtered: "
            f"{filtered_location}"
        )

        logger.info(
            f"Experience filtered: "
            f"{filtered_experience}"
        )

        logger.info(
            f"Job-type filtered: "
            f"{filtered_job_type}"
        )

        logger.info(
            f"Jobs matched: "
            f"{matched_jobs}"
        )

        logger.info(
            f"Jobs added: "
            f"{len(pending_jobs)}"
        )

        logger.info(
            f"Unsupported companies: "
            f"{unsupported_companies}"
        )

        logger.info(
            f"Failed companies: "
            f"{failed_companies}"
        )

    except Exception:

        logger.exception(
            "Job Monitor terminated "
            "with an unexpected error"
        )

        raise

    finally:

        detector.close()

        database.close()

        logger.info(
            "Finished"
        )

        logger.info(
            "=" * 60
        )


if __name__ == "__main__":
    main()