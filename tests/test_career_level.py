from models.job import Job
from utils.config_loader import ConfigLoader
from utils.job_classifier import JobClassifier


config = ConfigLoader()
config.load()

classifier = JobClassifier()


TITLES = [
    "Physical Design Engineer",
    "Senior Physical Design Engineer",
    "Staff RTL Design Engineer",
    "Principal Design Verification Engineer",
    "RTL Design Intern",
    "New Grad ASIC Design Engineer",
    "Entry-Level Verification Engineer",
    "DFT Engineer",
]


for title in TITLES:

    job = Job(
        company="Test",
        title=title,
        url="",
        job_id="",
        location="Austin, TX",
        country="",
        work_mode="Unknown",
        job_type="Unknown",
        experience_level="Unknown",
        ats_platform="Test",
        keywords=[],
        score=0,
    )

    classifier.classify(job)

    allowed = (
        job.experience_level
        in config.experience_levels
    )

    print("-" * 60)
    print(title)
    print("Job Type:", job.job_type)
    print("Experience:", job.experience_level)
    print("Allowed:", allowed)