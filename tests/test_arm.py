import time

from collectors.arm import (
    ArmCollector,
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


collector = ArmCollector()

collector.set_title_filter(
    title_filter
)


started = time.monotonic()


jobs = collector.collect(
    "Arm",
    (
        "https://careers.arm.com/"
        "en/search-jobs"
    ),
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
        "URL:",
        job.url,
    )