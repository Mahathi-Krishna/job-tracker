from collectors.workday import (
    WorkdayCollector,
)


TESTS = [
    (
        {
            "bulletFields": [
                "R55703"
            ]
        },
        (
            "/job/AUSTIN/"
            "DFT-Design-Engineer_R55703"
        ),
    ),
    (
        {
            "bulletFields": [
                "Posted 7 Days Ago"
            ]
        },
        (
            "/job/Santa-Clara-California-"
            "United-States/"
            "Intern---Design-Verification-"
            "Infrastructure-Engineer---"
            "Platform_R-101291-1"
        ),
    ),
    (
        {
            "bulletFields": []
        },
        (
            "/job/US-CA-Santa-Clara/"
            "ASIC-Verification-Engineer_"
            "JR2022280"
        ),
    ),
    (
        {
            "bulletFields": [
                "Posted Yesterday"
            ]
        },
        (
            "/job/Austin/"
            "Digital-Design-Engineer-I_"
            "20658-1"
        ),
    ),
]


for posting, path in TESTS:

    job_id = (
        WorkdayCollector
        ._extract_job_id(
            posting,
            path,
        )
    )

    print(
        path,
        "->",
        job_id,
    )