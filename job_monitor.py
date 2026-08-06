from datetime import datetime

from database.sqlite_db import JobDatabase
from matcher.matcher import Matcher
from sheets.google_sheets import GoogleSheetsClient
from utils.config_loader import ConfigLoader
from utils.logger import logger


def main():

    logger.info("Starting Job Monitor")

    config = ConfigLoader()
    config.load()

    database = JobDatabase()

    database.cleanup(config.retention_days)

    sheets = GoogleSheetsClient(
        config.credentials_file,
        config.spreadsheet_name,
        config.worksheet_name,
    )

    matcher = Matcher(
        config.keywords,
        config.minimum_score,
    )

    logger.info("Configuration loaded")

    logger.info(
        f"Companies configured: {len(config.companies)}"
    )

    logger.info(
        f"Keywords configured: {len(config.keywords)}"
    )

    logger.info("Phase 1 initialized successfully.")

    #
    # Phase 2 starts here.
    #
    # Collectors will return Job objects.
    #
    # for job in jobs:
    #
    #     if not database.exists(job):
    #
    #         if matcher.is_match(job):
    #
    #             job.date_found = datetime.utcnow().isoformat()
    #
    #             sheets.append_job(job)
    #
    #             database.insert(job)
    #

    database.close()

    logger.info("Finished")


if __name__ == "__main__":
    main()