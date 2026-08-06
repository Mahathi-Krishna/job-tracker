from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from models.job import Job

DB_PATH = Path("database/jobs.db")


class JobDatabase:
    def __init__(self):

        DB_PATH.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(DB_PATH)

        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (

                job_hash TEXT PRIMARY KEY,

                job_id TEXT,

                company TEXT,

                title TEXT,

                location TEXT,

                url TEXT,

                first_seen TEXT

            )
            """
        )

        self.conn.commit()

    @staticmethod
    def generate_hash(job: Job) -> str:

        text = "|".join(
            [
                job.company.strip().lower(),
                job.title.strip().lower(),
                job.location.strip().lower(),
                job.url.strip().lower(),
            ]
        )

        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def exists(self, job: Job) -> bool:

        job_hash = self.generate_hash(job)

        cursor = self.conn.execute(
            "SELECT 1 FROM jobs WHERE job_hash=?",
            (job_hash,),
        )

        return cursor.fetchone() is not None

    def insert(self, job: Job):

        job_hash = self.generate_hash(job)

        self.conn.execute(
            """
            INSERT OR IGNORE INTO jobs
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_hash,
                job.job_id,
                job.company,
                job.title,
                job.location,
                job.url,
                job.date_found,
            ),
        )

        self.conn.commit()

    def cleanup(self, retention_days: int):

        cutoff = (
            datetime.utcnow() - timedelta(days=retention_days)
        ).isoformat()

        self.conn.execute(
            """
            DELETE FROM jobs
            WHERE first_seen < ?
            """,
            (cutoff,),
        )

        self.conn.commit()

    def close(self):
        self.conn.close()