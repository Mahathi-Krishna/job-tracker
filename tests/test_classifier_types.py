from models.job import Job
from utils.job_classifier import (
    JobClassifier,
)


classifier = JobClassifier()


job = Job(
    company="Test",
    title=(
        "Design Verification Engineer"
    ),
    url=(
        "https://example.com/job/123"
    ),
    job_id="123",
    location="Austin, TX",
    country="",
    work_mode="Unknown",

    #
    # Simulate structured ATS data.
    #

    job_type={
        "id": "full_time",
        "label": "Full-time",
    },

    experience_level="Unknown",
    ats_platform="Test",
    keywords=[],
    score=0,
    description=(
        "ASIC design verification "
        "using SystemVerilog and UVM."
    ),
)


classifier.classify(
    job
)


print(
    "Country:",
    job.country,
)

print(
    "Work Mode:",
    job.work_mode,
)

print(
    "Job Type:",
    job.job_type,
)

print(
    "Experience:",
    job.experience_level,
)