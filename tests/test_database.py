from datetime import (
    datetime,
    timezone,
)

from database.sqlite_db import (
    JobDatabase,
)
from models.job import Job


database = JobDatabase()


job = Job(
    company="TEST COMPANY",
    title="Test RTL Engineer",
    url=(
        "https://example.com/"
        "jobs/test-123"
    ),
    job_id="TEST-123",
    location="Austin, TX",
    country="United States",
    work_mode="Unknown",
    job_type="Full-time",
    experience_level="Unknown",
    ats_platform="Test",
    keywords=["RTL"],
    score=100,
    date_found=(
        datetime.now(
            timezone.utc
        ).isoformat(
            timespec="seconds"
        )
    ),
)


print(
    "Exists before:",
    database.exists(job),
)


database.insert(job)


print(
    "Exists after:",
    database.exists(job),
)


database.cleanup(
    retention_days=30
)


database.close()