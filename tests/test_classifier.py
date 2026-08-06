from models.job import Job
from utils.job_classifier import (
    JobClassifier,
)


classifier = JobClassifier()


TESTS = [
    (
        "ASIC Design Verification Engineer",
        "Santa Clara, CA",
    ),
    (
        "RTL Design Intern",
        "Austin, TX",
    ),
    (
        "Physical Design Engineer",
        "Toronto, ON, Canada",
    ),
    (
        "Graduate Hardware Engineer",
        "Cambridge, United Kingdom",
    ),
    (
        "Design Verification Engineer",
        "Munich, Germany",
    ),
]


for title, location in TESTS:

    job = Job(
        company="Test",
        title=title,
        url="",
        job_id="",
        location=location,
        country="",
        work_mode="Unknown",
        job_type="Unknown",
        experience_level="Unknown",
        ats_platform="Test",
        keywords=[],
        score=0,
    )

    classifier.classify(
        job
    )

    print(
        "-" * 60
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
        "Country:",
        job.country,
    )

    print(
        "Job type:",
        job.job_type,
    )