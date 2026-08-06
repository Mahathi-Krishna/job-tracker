from collectors.lever import LeverCollector


collector = LeverCollector()

jobs = collector.collect(
    "Test Company",
    "https://jobs.lever.co/example",
)

print(f"Jobs returned: {len(jobs)}")

for job in jobs[:5]:

    print("-" * 60)

    print(job.job_id)
    print(job.title)
    print(job.location)
    print(job.url)