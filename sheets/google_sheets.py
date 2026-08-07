from __future__ import annotations

from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

from models.job import Job

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

HEADERS = [
    "Date Found",
    "Company",
    "Job Title",
    "Job ID",
    "Location",
    "Country",
    "Work Mode",
    "Job Type",
    "Experience Level",
    "ATS Platform",
    "Matching Keywords",
    "Match Score",
    "Posting URL",
    "Date Posted",
    "Status",
]


class GoogleSheetsClient:

    URL_COLUMN = 13
    JOB_ID_COLUMN = 4

    def __init__(
        self,
        credentials_file: str,
        spreadsheet_name: str,
        worksheet_name: str,
    ):

        credentials_path = Path(
            credentials_file
        )

        if not credentials_path.exists():
            raise FileNotFoundError(
                "Google credentials file "
                f"not found: {credentials_path}"
            )

        credentials = (
            Credentials.from_service_account_file(
                str(credentials_path),
                scopes=SCOPES,
            )
        )

        client = gspread.authorize(
            credentials
        )

        spreadsheet = client.open(
            spreadsheet_name
        )

        self.sheet = spreadsheet.worksheet(
            worksheet_name
        )

        self._initialize_header()

        self.known_urls: set[str] = set()

        self.known_job_keys: set[
            tuple[str, str]
        ] = set()

        self._load_existing_jobs()

    def _initialize_header(
        self,
    ) -> None:

        existing = self.sheet.row_values(
            1
        )

        if not existing:

            self.sheet.append_row(
                HEADERS,
                value_input_option="RAW",
            )

            return

        if existing != HEADERS:

            raise ValueError(
                "Google Sheet header does "
                "not match Job Monitor schema.\n\n"
                f"Expected:\n{HEADERS}\n\n"
                f"Found:\n{existing}"
            )

    @staticmethod
    def _normalize_url(
        url: str,
    ) -> str:

        return (
            url.strip()
            .rstrip("/")
            .casefold()
        )

    @staticmethod
    def _normalize_value(
        value: str,
    ) -> str:

        return (
            value.strip()
            .casefold()
        )

    def _load_existing_jobs(
        self,
    ) -> None:
        """
        Read only the columns needed for
        long-term spreadsheet deduplication.

        The spreadsheet is the permanent
        record; SQLite only keeps 30 days.
        """

        urls = self.sheet.col_values(
            self.URL_COLUMN
        )

        job_ids = self.sheet.col_values(
            self.JOB_ID_COLUMN
        )

        companies = self.sheet.col_values(
            2
        )

        # Skip header rows.

        for url in urls[1:]:

            if url.strip():

                self.known_urls.add(
                    self._normalize_url(
                        url
                    )
                )

        row_count = max(
            len(job_ids),
            len(companies),
        )

        for index in range(
            1,
            row_count,
        ):

            company = (
                companies[index]
                if index < len(companies)
                else ""
            )

            job_id = (
                job_ids[index]
                if index < len(job_ids)
                else ""
            )

            if (
                company.strip()
                and job_id.strip()
            ):

                self.known_job_keys.add(
                    (
                        self._normalize_value(
                            company
                        ),
                        self._normalize_value(
                            job_id
                        ),
                    )
                )

    def contains_job(
        self,
        job: Job,
    ) -> bool:

        if job.url.strip():

            normalized_url = (
                self._normalize_url(
                    job.url
                )
            )

            if (
                normalized_url
                in self.known_urls
            ):
                return True

        if (
            job.company.strip()
            and job.job_id.strip()
        ):

            key = (
                self._normalize_value(
                    job.company
                ),
                self._normalize_value(
                    job.job_id
                ),
            )

            if key in self.known_job_keys:
                return True

        return False

    def append_jobs(
        self,
        jobs: list[Job],
    ) -> None:

        if not jobs:
            return

        rows = [
            job.to_row()
            for job in jobs
        ]

        self.sheet.append_rows(
            rows,
            value_input_option="RAW",
        )

        # Update in-memory deduplication
        # immediately after successful write.

        for job in jobs:

            if job.url.strip():

                self.known_urls.add(
                    self._normalize_url(
                        job.url
                    )
                )

            if (
                job.company.strip()
                and job.job_id.strip()
            ):

                self.known_job_keys.add(
                    (
                        self._normalize_value(
                            job.company
                        ),
                        self._normalize_value(
                            job.job_id
                        ),
                    )
                )

    def append_job(
        self,
        job: Job,
    ) -> None:

        self.append_jobs(
            [job]
        )