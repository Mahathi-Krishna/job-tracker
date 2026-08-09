import time

from collectors.workday import (
    WorkdayCollector,
)


QUALCOMM_URL = (
    "https://qualcomm.wd12."
    "myworkdayjobs.com/External"
)


collector = WorkdayCollector()

#
# IMPORTANT:
# Do NOT install the TitleFilter here.
# We want the raw Workday inventory.
#


print(
    "Testing raw Qualcomm "
    "Workday inventory..."
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
    "Raw jobs returned:",
    len(jobs),
)

print(
    "Collection time:",
    f"{elapsed:.1f} seconds",
)

print("=" * 70)
print()


for job in jobs[:50]:

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