from __future__ import annotations

import time
from typing import Any

import requests


class HttpClient:
    """
    Lightweight shared HTTP client.

    Retries only transient failures:
      - connection errors
      - timeouts
      - HTTP 429
      - HTTP 5xx

    Permanent client errors such as 400/403/404 are not retried.
    """

    RETRYABLE_STATUS_CODES = {
        429,
        500,
        502,
        503,
        504,
    }

    def __init__(
        self,
        timeout: int = 20,
        retries: int = 3,
        backoff_seconds: float = 1.0,
    ):
        self.timeout = timeout
        self.retries = retries
        self.backoff_seconds = backoff_seconds

        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/127.0 Safari/537.36"
                ),
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )

    def request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> requests.Response:

        timeout = kwargs.pop(
            "timeout",
            self.timeout,
        )

        last_exception = None

        for attempt in range(1, self.retries + 1):

            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    timeout=timeout,
                    **kwargs,
                )

            except (
                requests.Timeout,
                requests.ConnectionError,
            ) as exc:

                last_exception = exc

                if attempt == self.retries:
                    raise

                self._wait(attempt)
                continue

            if (
                response.status_code
                not in self.RETRYABLE_STATUS_CODES
            ):
                response.raise_for_status()
                return response

            if attempt == self.retries:
                response.raise_for_status()

            self._wait(attempt)

        if last_exception:
            raise last_exception

        raise RuntimeError(
            f"Request failed unexpectedly: {url}"
        )

    def get(
        self,
        url: str,
        **kwargs: Any,
    ) -> requests.Response:

        return self.request(
            "GET",
            url,
            **kwargs,
        )

    def post(
        self,
        url: str,
        **kwargs: Any,
    ) -> requests.Response:

        return self.request(
            "POST",
            url,
            **kwargs,
        )

    def _wait(self, attempt: int) -> None:

        delay = min(
            self.backoff_seconds * (2 ** (attempt - 1)),
            5,
        )

        time.sleep(delay)

    def close(self) -> None:
        self.session.close()