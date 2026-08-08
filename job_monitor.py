from utils.title_filter import (
    TitleFilter,
)

from __future__ import annotations

import time
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
from utils.ats_cache import ATSCache
from utils.config_loader import (
    ConfigLoader,
)
from utils.dry_run_reporter import (
    DryRunReporter,
)
from utils.job_classifier import (
    JobClassifier,
)
from utils.job_validator import (
    JobValidator,
)
from utils.logger import logger
from utils.run_lock import RunLock


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


def run_monitor() -> None:

    started = time.monotonic()

    config = ConfigLoader()
    config.load()

    logger.info(
        "=" * 60
    )

    logger.info(
        "Starting Job Monitor"
    )

    logger.info(
        "Mode: "
        + (
            "DRY RUN"
            if config.dry_run
            else "PRODUCTION"
        )
    )

    database = JobDatabase()

    detector = ATSDetector()

    classifier = JobClassifier()

    cache = ATSCache(
        retention_days=(
            config
            .ats_cache_retention_days
        )
    )

    reporter = DryRunReporter(
        limit=(
            config
            .dry_run_report_limit
        )
    )

    pending_jobs = []

    pending_hashes = set()

    try:

        deleted = database.cleanup(
            config.retention_days
        )

        if deleted:

            logger.info(
                "Database cleanup: "
                f"{deleted} expired "
                "records removed"
            )

        #
        # We still connect to Sheets during
        # a dry run.
        #
        # Reasons:
        #   1. Verify credentials.
        #   2. Exclude jobs already present
        #      in the permanent tracker.
        #
        # We simply don't WRITE to it.
        #

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

        #
        # Give high-volume collectors a
        # lightweight title pre-filter.
        #

        title_filter = TitleFilter(
            keywords=(
                config.keywords
            ),
            role_keywords=(
                config.role_keywords
            ),
        )


        workday_collector = (
            registry.get(
                "workday"
            )
        )


        if (
            workday_collector
            is not None
            and hasattr(
                workday_collector,
                "set_title_filter",
            )
        ):

            workday_collector.set_title_filter(
                title_filter
            )

        companies = (
            config.companies_with_urls
        )

        stats = {
            "companies": 0,
            "failed_companies": 0,
            "listings": 0,
            "invalid": 0,
            "local_duplicates": 0,
            "sheet_duplicates": 0,
            "run_duplicates": 0,
            "title_candidates": 0,
            "enriched": 0,
            "location_filtered": 0,
            "experience_filtered": 0,
            "job_type_filtered": 0,
            "score_filtered": 0,
            "matched": 0,
        }

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

                continue

            logger.info(
                f"Checking {company} "
                f"({detection.ats})"
            )

            try:

                jobs = (
                    collector.collect(
                        company,
                        detection.url,
                    )
                )

            except Exception as exc:

                stats[
                    "failed_companies"
                ] += 1

                logger.warning(
                    f"{company}: "
                    f"collection failed: "
                    f"{exc}"
                )

                continue

            stats[
                "companies"
            ] += 1

            stats[
                "listings"
            ] += len(
                jobs
            )

            for job in jobs:

                if not (
                    JobValidator.is_valid(
                        job
                    )
                ):

                    stats[
                        "invalid"
                    ] += 1

                    continue

                job_hash = (
                    database.generate_hash(
                        job
                    )
                )

                if (
                    job_hash
                    in pending_hashes
                ):

                    stats[
                        "run_duplicates"
                    ] += 1

                    continue

                if database.exists(
                    job
                ):

                    stats[
                        "local_duplicates"
                    ] += 1

                    continue

                if sheets.contains_job(
                    job
                ):

                    stats[
                        "sheet_duplicates"
                    ] += 1

                    continue

                #
                # Stage 1:
                # title only.
                #

                if not (
                    matcher.title_matches(
                        job
                    )
                ):

                    continue

                stats[
                    "title_candidates"
                ] += 1

                #
                # Only candidate jobs get
                # potentially expensive
                # detail requests.
                #

                if not job.description:

                    try:

                        job = (
                            collector.enrich(
                                job
                            )
                        )

                        stats[
                            "enriched"
                        ] += 1

                    except Exception as exc:

                        logger.warning(
                            "Enrichment failed: "
                            f"{company} | "
                            f"{job.title} | "
                            f"{exc}"
                        )

                classifier.classify(
                    job
                )

                #
                # Country filtering.
                #
                # Unknown remains allowed
                # because some ATSs don't
                # expose enough location data.
                #

                if (
                    job.country
                    not in config.countries
                    and job.country
                    != "Unknown"
                ):

                    stats[
                        "location_filtered"
                    ] += 1

                    continue

                if (
                    job.experience_level
                    not in
                    config.experience_levels
                ):

                    stats[
                        "experience_filtered"
                    ] += 1

                    continue

                if (
                    job.job_type
                    not in
                    config.job_types
                ):

                    stats[
                        "job_type_filtered"
                    ] += 1

                    continue

                if not matcher.is_match(
                    job
                ):

                    stats[
                        "score_filtered"
                    ] += 1

                    continue

                job.date_found = (
                    datetime.now(
                        timezone.utc
                    ).isoformat(
                        timespec="seconds"
                    )
                )

                pending_hashes.add(
                    job_hash
                )

                pending_jobs.append(
                    job
                )

                stats[
                    "matched"
                ] += 1

                if config.dry_run:

                    reporter.add(
                        job
                    )

        #
        # ============================
        # Output
        # ============================
        #

        if config.dry_run:

            report_path = (
                reporter.write()
            )

            logger.info(
                "DRY RUN: no jobs were "
                "written to Google Sheets "
                "or SQLite."
            )

            logger.info(
                "Dry-run report: "
                f"{report_path}"
            )

        elif pending_jobs:

            logger.info(
                "Writing "
                f"{len(pending_jobs)} "
                "new jobs to Google Sheets"
            )

            #
            # Sheets first.
            #
            # If this fails, SQLite remains
            # untouched so the jobs can be
            # retried next run.
            #

            sheets.append_jobs(
                pending_jobs
            )

            database.insert_many(
                pending_jobs
            )

        elapsed = (
            time.monotonic()
            - started
        )

        logger.info(
            "-" * 60
        )

        logger.info(
            f"Companies checked: "
            f"{stats['companies']}"
        )

        logger.info(
            f"Company failures: "
            f"{stats['failed_companies']}"
        )

        logger.info(
            f"Listings examined: "
            f"{stats['listings']}"
        )

        logger.info(
            f"Invalid listings: "
            f"{stats['invalid']}"
        )

        logger.info(
            f"SQLite duplicates: "
            f"{stats['local_duplicates']}"
        )

        logger.info(
            f"Sheet duplicates: "
            f"{stats['sheet_duplicates']}"
        )

        logger.info(
            f"Run duplicates: "
            f"{stats['run_duplicates']}"
        )

        logger.info(
            f"Title candidates: "
            f"{stats['title_candidates']}"
        )

        logger.info(
            f"Descriptions fetched: "
            f"{stats['enriched']}"
        )

        logger.info(
            f"Location filtered: "
            f"{stats['location_filtered']}"
        )

        logger.info(
            f"Experience filtered: "
            f"{stats['experience_filtered']}"
        )

        logger.info(
            f"Job-type filtered: "
            f"{stats['job_type_filtered']}"
        )

        logger.info(
            f"Score filtered: "
            f"{stats['score_filtered']}"
        )

        logger.info(
            f"Matched/new jobs: "
            f"{stats['matched']}"
        )

        logger.info(
            f"Runtime: "
            f"{elapsed:.1f} seconds"
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


def main() -> None:

    lock = RunLock()

    if not lock.acquire():

        logger.info(
            "Another Job Monitor run "
            "is already active. Exiting."
        )

        return

    try:

        run_monitor()

    except Exception:

        logger.exception(
            "Job Monitor terminated "
            "with an unexpected error"
        )

        raise

    finally:

        lock.release()


if __name__ == "__main__":
    main()