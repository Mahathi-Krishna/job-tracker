from matcher.matcher import Matcher
from models.job import Job
from utils.config_loader import ConfigLoader


config = ConfigLoader()
config.load()


matcher = Matcher(
    keywords=config.keywords,
    role_keywords=config.role_keywords,
    minimum_score=config.minimum_score,
)


TITLES = [
    "ASIC Design Verification Engineer",
    "RTL Design Engineer",
    "Physical Design Engineer",
    "Accountant, Revenue",
    "Software Engineer",
    "UVM Verification Engineer",
    "Formal Verification Engineer",
    "DFT Engineer",
    "Digital Design Engineer",
    "Senior Physical Design Engineer",
    "Electrical Hardware Engineer",
    "Business Operations Internship/Co-op",
    "Silicon Engineering Internship/Co-op",
    "ASIC Hardware Engineer",
]


for title in TITLES:

    job = Job(
        company="Test",
        title=title,
        url="",
        job_id="",
        location="",
        country="",
        work_mode="Unknown",
        job_type="Unknown",
        experience_level="Unknown",
        ats_platform="Test",
        keywords=[],
        score=0,
    )

    title_candidate = (
        matcher.title_matches(
            job
        )
    )

    score = matcher.score(
        job
    )

    print(
        "-" * 60
    )

    print(
        "Title:",
        title
    )

    print(
        "Stage 1:",
        title_candidate
    )

    print(
        "Keywords:",
        job.keywords
    )

    print(
        "Score:",
        score
    )

    print(
        "Match:",
        score
        >= config.minimum_score
    )