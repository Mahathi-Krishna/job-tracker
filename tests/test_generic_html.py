from collectors.generic_html import (
    GenericHTMLCollector,
)


TEST_SITES = [
    (
        "Apple",
        "https://www.apple.com/careers/us/",
    ),
    (
        "OpenAI",
        "https://openai.com/careers/",
    ),
    (
        "Synopsys",
        "https://careers.synopsys.com/",
    ),
    (
        "TSMC",
        "https://careers.tsmc.com/en_US/careers",
    ),
]


collector = (
    GenericHTMLCollector()
)


for company, url in TEST_SITES:

    print(
        "=" * 80
    )

    print(company)

    try:

        jobs = collector.collect(
            company,
            url,
        )

    except Exception as exc:

        print(
            "FAILED:",
            exc,
        )

        continue

    print(
        "Jobs:",
        len(jobs)
    )

    for job in jobs[:10]:

        print(
            "-",
            job.title,
        )

        print(
            " ",
            job.url,
        )