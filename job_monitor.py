from datetime import datetime

from collectors.registry import CollectorRegistry
from collectors.detector import ATSDetector
from database.sqlite_db import JobDatabase
from matcher.matcher import Matcher
from sheets.google_sheets import GoogleSheetsClient
from utils.config_loader import ConfigLoader
from utils.logger import logger


def main():

    logger.info("=" * 60)
    logger.info("Starting Job Monitor")

    # ----------------------------
    # Load Configuration
    # ----------------------------

    config = ConfigLoader()
    config.load()

    logger.info("Configuration loaded.")

    # ----------------------------
    # Initialize Database
    # ----------------------------

    database = JobDatabase()

    database.cleanup(config.retention_days)

    # ----------------------------
    # Google Sheets
    # ----------------------------

    sheets = GoogleSheetsClient(
        config.credentials_file,
        config.spreadsheet_name,
        config.worksheet_name,
    )

    # ----------------------------
    # Matcher
    # ----------------------------

    matcher = Matcher(
        config.keywords,
        config.minimum_score,
    )

    # ----------------------------
    # Collector Registry
    # ----------------------------

    registry = CollectorRegistry()
    companies = config.companies_with_urls

    logger.info(f"Companies configured : {len(config.companies)}")
    logger.info(f"Keywords configured  : {len(config.keywords)}")
    logger.info(f"Companies configured : {len(companies)}")

    total_jobs_found = 0
    total_jobs_added = 0

    for company_info in companies:

        company = company_info["company"]
        career_url = company_info["url"]

        ats = ATSDetector.detect(career_url)

        collector = registry.get(ats)

        if collector is None:

            logger.warning(
                f"No collector implemented for ATS '{ats}' ({company})"
            )

            continue

        logger.info(f"Checking {company} ({ats})")

        try:

            jobs = collector.collect(
                company,
                career_url,
            )

        except Exception as ex:

            logger.exception(f"{company} failed: {ex}")
            continue

        logger.info(f"Found {len(jobs)} jobs")

        total_jobs_found += len(jobs)

        for job in jobs:

            if database.exists(job):
                continue

            if not matcher.is_match(job):
                continue

            job.date_found = datetime.utcnow().isoformat()

            sheets.append_job(job)

            database.insert(job)

            total_jobs_added += 1

            logger.info(f"Added: {job.company} | {job.title}")

    database.close()

    logger.info("-" * 60)
    logger.info(f"Jobs Found : {total_jobs_found}")
    logger.info(f"Jobs Added : {total_jobs_added}")
    logger.info("Finished")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()