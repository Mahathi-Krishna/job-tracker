from datetime import (
    datetime,
    timezone,
)

from collectors.detector import (
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
from utils.config_loader import (
    ConfigLoader,
)
from utils.job_classifier import (
    JobClassifier,
)
from utils.logger import logger


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

    try:

        database.cleanup(
            config.retention_days
        )

        sheets = GoogleSheetsClient(
            config.credentials_file,
            config.spreadsheet_name,
            config.worksheet_name,
        )

        matcher = Matcher(
            keywords=config.keywords,
            role_keywords=config.role_keywords,
            minimum_score=config.minimum_score,
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
        total_jobs_added = 0

        for company_info in companies:

            company = (
                company_info[
                    "company"
                ]
            )

            career_url = (
                company_info[
                    "url"
                ]
            )

            logger.info(
                f"Checking {company}"
            )

            detection = (
                detector.detect(
                    career_url
                )
            )

            collector = (
                registry.get(
                    detection.ats
                )
            )

            if collector is None:

                logger.warning(
                    f"{company}: "
                    f"unsupported ATS "
                    f"{detection.ats}"
                )

                continue

            try:

                jobs = (
                    collector.collect(
                        company,
                        detection.url,
                    )
                )

            except Exception as exc:

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

                # ------------------------
                # Already written?
                # ------------------------

                if database.exists(job):
                    continue

                # ------------------------
                # Stage 1:
                # cheap title filter
                # ------------------------

                if not matcher.title_matches(
                    job
                ):
                    continue

                title_candidates += 1

                # ------------------------
                # Enrich only candidates
                # ------------------------

                if not job.description:

                    try:

                        job = (
                            collector.enrich(
                                job
                            )
                        )

                        enriched_jobs += 1

                    except Exception as exc:

                        logger.warning(
                            f"Could not enrich "
                            f"{company} | "
                            f"{job.title}: "
                            f"{exc}"
                        )

                # ------------------------
                # Classification
                # ------------------------

                classifier.classify(
                    job
                )

                # ------------------------
                # Country filter
                # ------------------------

                if (
                    job.country
                    not in config.countries
                ):

                    # Unknown is intentionally
                    # allowed through for now.
                    #
                    # Some ATS listings don't
                    # provide enough location
                    # information until detail
                    # parsing improves.

                    if (
                        job.country
                        != "Unknown"
                    ):
                        continue

                # ------------------------
                # Full matching
                # ------------------------

                if not matcher.is_match(
                    job
                ):
                    continue

                matched_jobs += 1

                # ------------------------
                # Timestamp
                # ------------------------

                job.date_found = (
                    datetime.now(
                        timezone.utc
                    ).isoformat()
                )

                # ------------------------
                # Sheets first
                # ------------------------

                try:

                    sheets.append_job(
                        job
                    )

                except Exception as exc:

                    logger.exception(
                        f"Sheet write failed: "
                        f"{company} | "
                        f"{job.title}: "
                        f"{exc}"
                    )

                    continue

                # ------------------------
                # Mark processed only
                # after Sheets succeeds
                # ------------------------

                database.insert(
                    job
                )

                total_jobs_added += 1

                logger.info(
                    f"Added: "
                    f"{company} | "
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
            f"Jobs matched: "
            f"{matched_jobs}"
        )

        logger.info(
            f"Jobs added: "
            f"{total_jobs_added}"
        )

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