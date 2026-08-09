from collectors.workday import (
    WorkdayCollector,
)


collector = WorkdayCollector()


base_url = (
    "https://micron.wd1."
    "myworkdayjobs.com"
)

site = "External"

external_path = (
    "/job/Richardson-TX/"
    "Senior-Engineer---HBM-"
    "Design-for-Test--DFT-_"
    "JR102419-1"
)


normalized_path = (
    external_path
    if external_path.startswith("/")
    else "/" + external_path
)


public_url = (
    f"{base_url}/"
    f"{site}"
    f"{normalized_path}"
)


expected = (
    "https://micron.wd1."
    "myworkdayjobs.com/"
    "External/job/"
    "Richardson-TX/"
    "Senior-Engineer---HBM-"
    "Design-for-Test--DFT-_"
    "JR102419-1"
)


print(
    "Generated:"
)

print(
    public_url
)

print()

print(
    "Expected:"
)

print(
    expected
)

print()

print(
    "Match:",
    public_url == expected,
)