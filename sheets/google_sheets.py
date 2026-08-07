from __future__ import annotations

from pathlib import Path

import gspread
from google.oauth2.service_account import (
    Credentials,
)

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
                f"not found: "
                f"{credentials_path}"
            )

        credentials = (
            Credentials
            .from_service_account_file(
                str(
                    credentials_path
                ),
                scopes=SCOPES,
            )
        )

        client = gspread.authorize(
            credentials
        )

        spreadsheet = client.open(
            spreadsheet_name
        )

        self.sheet = (
            spreadsheet.worksheet(
                worksheet_name
            )
        )

        self._initialize_header()

    def _initialize_header(
        self,
    ) -> None:

        existing = (
            self.sheet.row_values(1)
        )

        if not existing:

            self.sheet.append_row(
                HEADERS,
                value_input_option=(
                    "RAW"
                ),
            )

            return

        #
        # Don't silently overwrite an
        # existing spreadsheet layout.
        #

        if existing != HEADERS:

            raise ValueError(
                "Google Sheet header does "
                "not match the Job Monitor "
                "schema.\n\n"
                f"Expected:\n{HEADERS}\n\n"
                f"Found:\n{existing}"
            )

    def append_job(
        self,
        job: Job,
    ) -> None:

        self.append_jobs(
            [job]
        )

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