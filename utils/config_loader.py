from pathlib import Path

import yaml


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

CONFIG_DIR = (
    PROJECT_ROOT / "config"
)


class ConfigLoader:

    def __init__(self):

        self.config = {}

        self.companies = []

        self.keywords = []

        self.role_keywords = []
        self.ats_overrides = {}

    def load(self):

        self.config = self._load_yaml(
            CONFIG_DIR
            / "config.yml"
        )

        self.companies = self._load_list(
            CONFIG_DIR
            / "companies.txt"
        )

        self.keywords = self._load_list(
            CONFIG_DIR
            / "keywords.txt"
        )

        self.role_keywords = (
            self._load_list(
                CONFIG_DIR
                / "role_keywords.txt"
            )
        )

        overrides_path = (
            CONFIG_DIR
            / "ats_overrides.yml"
        )

        if overrides_path.exists():

            self.ats_overrides = (
                self._load_yaml(
                    overrides_path
                )
                or {}
            )

    @staticmethod
    def _load_yaml(
        path: Path,
    ):

        if not path.exists():

            raise FileNotFoundError(
                path
            )

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:

            return yaml.safe_load(
                file
            )

    @staticmethod
    def _load_list(
        path: Path,
    ):

        if not path.exists():

            raise FileNotFoundError(
                path
            )

        items = []

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:

            for line in file:

                line = line.strip()

                if not line:
                    continue

                if line.startswith("#"):
                    continue

                items.append(line)

        return items

    @property
    def companies_with_urls(
        self,
    ):

        companies = []

        for line in self.companies:

            parts = line.split(
                "|",
                maxsplit=1,
            )

            if len(parts) != 2:
                continue

            company = (
                parts[0].strip()
            )

            url = (
                parts[1].strip()
            )

            if not company or not url:
                continue

            companies.append(
                {
                    "company": company,
                    "url": url,
                }
            )

        return companies

    @property
    def interval_minutes(
        self,
    ):
        return self.config[
            "scheduler"
        ][
            "interval_minutes"
        ]

    @property
    def retention_days(
        self,
    ):
        return self.config[
            "database"
        ][
            "retention_days"
        ]

    @property
    def spreadsheet_name(
        self,
    ):
        return self.config[
            "google_sheets"
        ][
            "spreadsheet_name"
        ]

    @property
    def worksheet_name(
        self,
    ):
        return self.config[
            "google_sheets"
        ][
            "worksheet_name"
        ]

    @property
    def credentials_file(
        self,
    ):

        path = self.config[
            "google_sheets"
        ][
            "credentials_file"
        ]

        return str(
            PROJECT_ROOT / path
        )

    @property
    def countries(
        self,
    ):
        return self.config[
            "search"
        ][
            "countries"
        ]

    @property
    def job_types(
        self,
    ):
        return self.config[
            "search"
        ][
            "job_types"
        ]

    @property
    def experience_levels(
        self,
    ):
        return self.config[
            "search"
        ][
            "experience_levels"
        ]

    @property
    def work_modes(
        self,
    ):
        return self.config[
            "search"
        ][
            "work_modes"
        ]

    @property
    def minimum_score(
        self,
    ):
        return self.config[
            "matching"
        ][
            "minimum_score"
        ]

    @property
    def ats_cache_retention_days(
        self,
    ):
        return self.config.get(
            "ats_cache",
            {},
        ).get(
            "retention_days",
            7,
        )