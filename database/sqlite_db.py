from __future__ import annotations

import hashlib
import sqlite3
from datetime import (
    datetime,
    timedelta,
    timezone,
)
from pathlib import Path

from models.job import Job


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

DB_PATH = (
    PROJECT_ROOT
    / "database"
    / "jobs.db"
)


class JobDatabase:

    def __init__(self):

        DB_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.conn = sqlite3.connect(
            DB_PATH,
            timeout=10,
        )

        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                job_hash TEXT PRIMARY KEY,
                job_id TEXT,
                company TEXT NOT NULL,
                title TEXT NOT NULL,
                location TEXT,
                url TEXT NOT NULL,
                first_seen TEXT NOT NULL
            )
            """
        )

        self.conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_jobs_first_seen
            ON jobs(first_seen)
            """
        )

        self.conn.commit()

    @staticmethod
    def generate_hash(
        job: Job,
    ) -> str:

        #
        # URL is normally the most stable
        # identifier available across ATSs.
        #
        # Including company prevents accidental
        # collisions between employers.
        #

        canonical = "|".join(
            [
                job.company
                .strip()
                .casefold(),

                job.url
                .strip()
                .casefold(),
            ]
        )

        # If the URL is unavailable, fall
        # back to identifying fields.

        if not job.url.strip():

            canonical = "|".join(
                [
                    job.company
                    .strip()
                    .casefold(),

                    job.job_id
                    .strip()
                    .casefold(),

                    job.title
                    .strip()
                    .casefold(),

                    job.location
                    .strip()
                    .casefold(),
                ]
            )

        return hashlib.sha256(
            canonical.encode(
                "utf-8"
            )
        ).hexdigest()

    def exists(
        self,
        job: Job,
    ) -> bool:

        job_hash = (
            self.generate_hash(job)
        )

        cursor = self.conn.execute(
            """
            SELECT 1
            FROM jobs
            WHERE job_hash = ?
            LIMIT 1
            """,
            (job_hash,),
        )

        return (
            cursor.fetchone()
            is not None
        )

    def insert(
        self,
        job: Job,
    ) -> None:

        job_hash = (
            self.generate_hash(job)
        )

        first_seen = (
            job.date_found
            or datetime.now(
                timezone.utc
            ).isoformat()
        )

        self.conn.execute(
            """
            INSERT OR IGNORE INTO jobs (
                job_hash,
                job_id,
                company,
                title,
                location,
                url,
                first_seen
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_hash,
                job.job_id,
                job.company,
                job.title,
                job.location,
                job.url,
                first_seen,
            ),
        )

        self.conn.commit()

    def cleanup(
        self,
        retention_days: int,
    ) -> int:

        cutoff = (
            datetime.now(
                timezone.utc
            )
            - timedelta(
                days=retention_days
            )
        ).isoformat()

        cursor = self.conn.execute(
            """
            DELETE FROM jobs
            WHERE first_seen < ?
            """,
            (cutoff,),
        )

        deleted = (
            cursor.rowcount
            if cursor.rowcount > 0
            else 0
        )

        self.conn.commit()

        # Ask SQLite to reuse deleted pages.
        # We deliberately don't VACUUM every
        # 10 minutes because VACUUM performs
        # unnecessary disk work.

        return deleted

    def close(
        self,
    ) -> None:

        self.conn.close()