import time

from collectors.workday import (
    WorkdayCollector,
)
from utils.config_loader import (
    ConfigLoader,
)
from utils.title_filter import (
    TitleFilter,
)


config = ConfigLoader()
config.load()


title_filter = TitleFilter(
    keywords=config.keywords,
    role_keywords=config.role_keywords,
)


collector = WorkdayCollector()

collector.set_title_filter(
    title_filter
)


url = (
    "https://nvidia.wd5."
    "myworkdayjobs.com/"
    "NVIDIAExternalCareerSite"
)


print(
    "Testing optimized NVIDIA "
    "Workday collection..."
)


started = time.monotonic()


jobs = collector.collect(
    "NVIDIA",
    url,
)


elapsed = (
    time.monotonic()
    - started
)


print()
print("=" * 70)

print(
    "Relevant title candidates:",
    len(jobs),
)

print(
    "Listing collection time:",
    f"{elapsed:.1f} seconds",
)

print("=" * 70)
print()

print(
    "First 30 candidates:"
)

print()


for job in jobs[:30]:

    print(
        "-",
        job.title,
        "|",
        job.location,
    )