from sheets.google_sheets import (
    GoogleSheetsClient,
)
from utils.config_loader import (
    ConfigLoader,
)


config = ConfigLoader()
config.load()


print(
    "Connecting to Google Sheets..."
)


client = GoogleSheetsClient(
    config.credentials_file,
    config.spreadsheet_name,
    config.worksheet_name,
)


print(
    "Connection successful."
)

print(
    "Spreadsheet:",
    config.spreadsheet_name,
)

print(
    "Worksheet:",
    config.worksheet_name,
)

print(
    "Existing posting URLs:",
    len(
        client.known_urls
    ),
)

print(
    "Existing company/job-ID pairs:",
    len(
        client.known_job_keys
    ),
)