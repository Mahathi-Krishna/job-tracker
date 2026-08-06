from models.job import Job


class Matcher:

    def __init__(self, keywords, minimum_score):

        self.keywords = [k.lower() for k in keywords]

        self.minimum_score = minimum_score

    def score(self, job: Job):

        text = " ".join(
            [
                job.title,
                job.description or "",
            ]
        ).lower()

        matched = []

        score = 0

        for keyword in self.keywords:

            if keyword in text:

                matched.append(keyword)

                score += 10

        score = min(score, 100)

        job.score = score

        job.keywords = matched

        return score

    def is_match(self, job: Job):

        return self.score(job) >= self.minimum_score