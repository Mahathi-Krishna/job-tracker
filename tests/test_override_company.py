from collectors.registry import CollectorRegistry
from utils.config_loader import ConfigLoader


COMPANY = "Silicon Labs"


config = ConfigLoader()
config.load()

override = config.ats_overrides.get(
    COMPANY
)

if not override:
    raise RuntimeError(
        f"No override for {COMPANY}"
    )


ats = override["ats"]
url = override["url"]

registry = CollectorRegistry()

collector = registry.get(
    ats
)

if collector is None:
    raise RuntimeError(
        f"No collector for {ats}"
    )


jobs = collector.collect(
    COMPANY,
    url,
)


print(
    f"Company: {COMPANY}"
)

print(
    f"ATS: {ats}"
)

print(
    f"Jobs: {len(jobs)}"
)


for job in jobs[:10]:

    print("-" * 60)

    print(job.job_id)
    print(job.title)
    print(job.location)
    print(job.url)