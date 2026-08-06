from datetime import datetime, timezone

from collectors.detector import ATSDetector
from collectors.registry import CollectorRegistry
from database.sqlite_db import JobDatabase
from matcher.matcher import Matcher
from sheets.google_sheets import GoogleSheetsClient
from utils.config_loader import ConfigLoader
from utils.logger import logger


def main():

    logger.info("=" * 60)
    logger.info("Starting Job Monitor")

    config = ConfigLoader()
    config.load()

    database = JobDatabase()

    detector = ATSDetector()

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
            config.keywords,
            config.minimum_score,
        )

        registry = CollectorRegistry()

        companies = (
            config.companies_with_urls
        )

        logger.info(
            f"Companies configured: "
            f"{len(companies)}"
        )

        logger.info(
            f"Keywords configured: "
            f"{len(config.keywords)}"
        )

        logger.info(
            "Collectors available: "
            + ", ".join(
                registry.supported_platforms()
            )
        )

        total_jobs_found = 0
        total_jobs_added = 0
        companies_checked = 0
        companies_skipped = 0

        for company_info in companies:

            company = (
                company_info["company"]
            )

            career_url = (
                company_info["url"]
            )

            logger.info(
                f"Discovering ATS: {company}"
            )

            detection = detector.detect(
                career_url
            )

            logger.info(
                f"{company}: "
                f"ATS={detection.ats}, "
                f"detected_by="
                f"{detection.detected_by}"
            )

            collector = registry.get(
                detection.ats
            )

            if collector is None:

                companies_skipped += 1

                logger.warning(
                    f"Skipping {company}: "
                    f"unsupported ATS "
                    f"'{detection.ats}'"
                )

                continue

            try:

                jobs = collector.collect(
                    company,
                    detection.url,
                )

            except Exception as exc:

                companies_skipped += 1

                logger.exception(
                    f"{company} collection "
                    f"failed: {exc}"
                )

                continue

            companies_checked += 1

            total_jobs_found += len(jobs)

            logger.info(
                f"{company}: "
                f"{len(jobs)} jobs returned"
            )

            for job in jobs:

                if database.exists(job):
                    continue

                if not matcher.is_match(job):
                    continue

                job.date_found = (
                    datetime.now(
                        timezone.utc
                    ).isoformat()
                )

                try:

                    sheets.append_job(job)

                except Exception as exc:

                    logger.exception(
                        "Google Sheets write "
                        f"failed for "
                        f"{company} / "
                        f"{job.title}: {exc}"
                    )

                    #
                    # Do NOT insert it into SQLite.
                    #
                    # This ensures the job will be
                    # attempted again next run.
                    #

                    continue

                database.insert(job)

                total_jobs_added += 1

                logger.info(
                    f"Added: "
                    f"{job.company} | "
                    f"{job.title}"
                )

        logger.info("-" * 60)

        logger.info(
            f"Companies checked: "
            f"{companies_checked}"
        )

        logger.info(
            f"Companies skipped: "
            f"{companies_skipped}"
        )

        logger.info(
            f"Jobs found: "
            f"{total_jobs_found}"
        )

        logger.info(
            f"Jobs added: "
            f"{total_jobs_added}"
        )

    finally:

        detector.close()
        database.close()

        logger.info("Finished")
        logger.info("=" * 60)


if __name__ == "__main__":
    main()