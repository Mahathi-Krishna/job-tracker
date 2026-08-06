from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

from models.job import Job


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


class GoogleSheetsClient:

    def __init__(self, credentials_file, spreadsheet_name, worksheet_name):

        credentials = Credentials.from_service_account_file(
            Path(credentials_file),
            scopes=SCOPES,
        )

        client = gspread.authorize(credentials)

        self.sheet = (
            client.open(spreadsheet_name)
            .worksheet(worksheet_name)
        )

        self._initialize_header()

    def _initialize_header(self):

        header = self.sheet.row_values(1)

        if header:
            return

        self.sheet.append_row(
            [
                "Date Found",
                "Company",
                "Job Title",
                "Job ID",
                "Location",
                "Country",
                "Work Mode",
                "Job Type",
                "Experience",
                "ATS",
                "Keywords",
                "Score",
                "Posting URL",
                "Date Posted",
                "Status",
            ]
        )

    def append_job(self, job: Job):

        self.sheet.append_row(job.to_row())