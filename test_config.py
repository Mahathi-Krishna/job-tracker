from utils.config_loader import ConfigLoader

config = ConfigLoader()
config.load()

print("=" * 50)
print("Companies:", len(config.companies))
print("Keywords:", len(config.keywords))
print("Countries:", config.countries)
print("Spreadsheet:", config.spreadsheet_name)
print("Worksheet:", config.worksheet_name)
print("Interval:", config.interval_minutes)