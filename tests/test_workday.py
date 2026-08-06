from collectors.workday import WorkdayCollector


collector = WorkdayCollector()

jobs = collector.collect(
    "NVIDIA",
    (
        "https://nvidia.wd5.myworkdayjobs.com/"
        "NVIDIAExternalCareerSite"
    ),
)

print(
    f"Jobs returned: {len(jobs)}"
)

for job in jobs[:10]:

    print("-" * 60)

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