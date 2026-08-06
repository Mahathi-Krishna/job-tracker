from collectors.detector import ATSDetector


URLS = [
    (
        "NVIDIA",
        "https://nvidia.wd5.myworkdayjobs.com/"
        "NVIDIAExternalCareerSite",
    ),
    (
        "SpaceX",
        "https://boards.greenhouse.io/spacex",
    ),
    (
        "Apple",
        "https://jobs.apple.com",
    ),
    (
        "OpenAI",
        "https://openai.com/careers",
    ),
]


detector = ATSDetector()


try:

    for company, url in URLS:

        result = detector.detect(url)

        print("-" * 60)

        print(
            "Company:",
            company,
        )

        print(
            "ATS:",
            result.ats,
        )

        print(
            "Method:",
            result.detected_by,
        )

        print(
            "URL:",
            result.url,
        )

finally:

    detector.close()