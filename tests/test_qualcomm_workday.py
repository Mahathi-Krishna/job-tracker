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


QUALCOMM_URL = (
    "https://qualcomm.wd12."
    "myworkdayjobs.com/External"
)


print(
    "Testing Qualcomm Workday backend..."
)


started = time.monotonic()


jobs = collector.collect(
    "Qualcomm",
    QUALCOMM_URL,
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
    "Collection time:",
    f"{elapsed:.1f} seconds",
)

print("=" * 70)
print()


for job in jobs[:30]:

    print("-" * 70)

    print(
        "ID:",
        job.job_id,
    )

    print(
        "Title:",
        job.title,
    )

    print(
        "Location:",
        job.location,
    )

    print(
        "Posted:",
        job.date_posted,
    )

    print(
        "URL:",
        job.url,
    )