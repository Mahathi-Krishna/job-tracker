from models.job import Job
from utils.job_classifier import (
    JobClassifier,
)


classifier = JobClassifier()


TESTS = [
    (
        "Bengaluru, KA, in",
        "in",
    ),
    (
        "Catania, it",
        "it",
    ),
    (
        "Kodaira, jp",
        "jp",
    ),
    (
        "Istanbul, tr",
        "tr",
    ),
    (
        "San Jose, CA, us",
        "us",
    ),
]


for location, code in TESTS:

    job = Job(
        company="Test",
        title=(
            "Physical Design Engineer"
        ),
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

    job.metadata[
        "country_code"
    ] = code

    classifier.classify(
        job
    )

    print(
        location,
        "->",
        job.country,
    )