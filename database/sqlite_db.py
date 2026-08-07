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

    def __init__(
        self,
    ):

        DB_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.conn = sqlite3.connect(
            DB_PATH,
            timeout=10,
        )

        #
        # WAL is reliable and prevents
        # unnecessary full-database writes.
        #

        self.conn.execute(
            "PRAGMA journal_mode=WAL"
        )

        self.conn.execute(
            "PRAGMA synchronous=NORMAL"
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

        if job.url.strip():

            canonical = "|".join(
                [
                    job.company
                    .strip()
                    .casefold(),

                    job.url
                    .strip()
                    .rstrip("/")
                    .casefold(),
                ]
            )

        else:

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
            self.generate_hash(
                job
            )
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

    def insert_many(
        self,
        jobs: list[Job],
    ) -> None:

        if not jobs:
            return

        rows = []

        now = datetime.now(
            timezone.utc
        ).isoformat(
            timespec="seconds"
        )

        for job in jobs:

            rows.append(
                (
                    self.generate_hash(
                        job
                    ),
                    job.job_id,
                    job.company,
                    job.title,
                    job.location,
                    job.url,
                    job.date_found
                    or now,
                )
            )

        self.conn.executemany(
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
            rows,
        )

        self.conn.commit()

    def insert(
        self,
        job: Job,
    ) -> None:

        self.insert_many(
            [job]
        )

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

        deleted = max(
            cursor.rowcount,
            0,
        )

        self.conn.commit()

        return deleted

    def checkpoint(
        self,
    ) -> None:

        #
        # Keep the WAL side file from
        # growing indefinitely.
        #

        self.conn.execute(
            "PRAGMA wal_checkpoint(TRUNCATE)"
        )

    def close(
        self,
    ) -> None:

        self.checkpoint()

        self.conn.close()