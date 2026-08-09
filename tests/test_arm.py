import time

from collectors.arm import (
    ArmCollector,
)


collector = ArmCollector()


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


print(
    "Jobs returned:",
    len(jobs),
)

print(
    "Collection time:",
    f"{elapsed:.1f} seconds",
)

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