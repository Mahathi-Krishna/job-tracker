from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

LOCK_PATH = (
    PROJECT_ROOT
    / "data"
    / "job_monitor.lock"
)


class RunLock:

    def __init__(
        self,
    ):

        self.acquired = False

        LOCK_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def acquire(
        self,
    ) -> bool:

        try:

            descriptor = os.open(
                LOCK_PATH,
                os.O_CREAT
                | os.O_EXCL
                | os.O_WRONLY,
            )

        except FileExistsError:

            if self._is_stale():

                try:
                    LOCK_PATH.unlink()
                except OSError:
                    return False

                return self.acquire()

            return False

        with os.fdopen(
            descriptor,
            "w",
            encoding="utf-8",
        ) as file:

            file.write(
                str(
                    os.getpid()
                )
            )

        self.acquired = True

        return True

    @staticmethod
    def _is_stale(
        max_age_seconds: int = 3600,
    ) -> bool:

        try:

            age = (
                __import__("time").time()
                - LOCK_PATH.stat().st_mtime
            )

            return (
                age > max_age_seconds
            )

        except OSError:

            return True

    def release(
        self,
    ) -> None:

        if not self.acquired:
            return

        try:

            LOCK_PATH.unlink(
                missing_ok=True
            )

        finally:

            self.acquired = False

    def __enter__(
        self,
    ):

        if not self.acquire():

            raise RuntimeError(
                "Another Job Monitor "
                "instance is already running."
            )

        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):

        self.release()