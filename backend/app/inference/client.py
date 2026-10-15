import asyncio
import random
import time
from typing import Any

import httpx
from pydantic import SecretStr

from app.core.config import settings
from app.core.logging import logger


class InferenceError(Exception):
    """Base exception for all inference and LLM client operations."""

    def __init__(self, message: str, status_code: int | None = None, details: Any | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


class InferenceDisabledError(InferenceError):
    """Raised when inference execution is requested but INFERENCE_ENABLED is False."""

    def __init__(self, message: str = "Inference is disabled in application configuration"):
        super().__init__(message=message, status_code=503)


class RetryableInferenceError(InferenceError):
    """Temporary failure (e.g. rate limit 429, 5xx server error, timeout) eligible for retry."""


class FinalInferenceError(InferenceError):
    """Non-retryable client failure (e.g. 400 Bad Request, 401 Unauthorized, 422 Unprocessable)."""


class InferenceTimeoutError(RetryableInferenceError):
    """Timeout during communication with inference service."""


class NebiusTokenFactoryClient:
    """Production-grade asynchronous client for Nebius Token Factory with retries, backoff, and concurrency control."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: SecretStr | str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        max_concurrency: int | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.base_url = (base_url or settings.NEBIUS_BASE_URL).rstrip("/")
        self._api_key = api_key or settings.NEBIUS_API_KEY
        self.timeout = timeout or settings.LLM_TIMEOUT_SECONDS
        self.max_retries = max_retries if max_retries is not None else settings.LLM_MAX_RETRIES
        self.max_concurrency = max_concurrency or settings.LLM_MAX_CONCURRENCY
        self._transport = transport
        self._semaphore = asyncio.Semaphore(self.max_concurrency)

    @property
    def api_key(self) -> str | None:
        if self._api_key is None:
            return None
        if isinstance(self._api_key, SecretStr):
            return self._api_key.get_secret_value()
        return str(self._api_key)

    def _get_headers(self) -> dict[str, str]:
        key = self.api_key
        if not key:
            raise FinalInferenceError(
                "Nebius API key is not configured. Set NEBIUS_API_KEY in environment or .env.",
                status_code=401,
            )
        return {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _calculate_backoff(self, attempt: int, response: httpx.Response | None = None) -> float:
        """Calculates backoff delay, honoring Retry-After headers when provided by the server."""
        if response is not None and response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    return max(float(retry_after), 0.5)
                except ValueError:
                    pass

        base_delay = 1.0
        max_delay = 15.0
        delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
        jitter = random.uniform(0.0, 0.5 * delay)
        return delay + jitter

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str,
        response_format: dict[str, Any] | None = None,
        extra_body: dict[str, Any] | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Executes chat completion with bounded retries, jittered backoff, and concurrency gating."""
        if not settings.INFERENCE_ENABLED:
            raise InferenceDisabledError()

        headers = self._get_headers()
        url = f"{self.base_url}/chat/completions"

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if response_format is not None:
            payload["response_format"] = response_format
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if extra_body:
            payload.update(extra_body)

        last_error: Exception | None = None

        async with self._semaphore:
            for attempt in range(1, self.max_retries + 1):
                start_time = time.monotonic()
                try:
                    async with httpx.AsyncClient(
                        timeout=self.timeout,
                        transport=self._transport,
                    ) as client:
                        response = await client.post(url, headers=headers, json=payload)

                    latency_ms = (time.monotonic() - start_time) * 1000

                    # 1. Success (200 OK)
                    if response.status_code == 200:
                        data = response.json()
                        usage = data.get("usage", {})
                        logger.info(
                            "Nebius inference completion successful: model=%s, latency_ms=%.1f, prompt_tokens=%s, completion_tokens=%s",
                            model,
                            latency_ms,
                            usage.get("prompt_tokens", 0),
                            usage.get("completion_tokens", 0),
                            extra={
                                "model": model,
                                "latency_ms": latency_ms,
                                "prompt_tokens": usage.get("prompt_tokens", 0),
                                "completion_tokens": usage.get("completion_tokens", 0),
                            },
                        )
                        return data

                    # 2. Rate limited (429) or Server error (5xx) -> eligible for retry
                    if response.status_code == 429 or response.status_code >= 500:
                        delay = self._calculate_backoff(attempt, response)
                        logger.warning(
                            "Nebius inference retryable status %s (attempt %s/%s). Retrying in %.2fs: %s",
                            response.status_code,
                            attempt,
                            self.max_retries,
                            delay,
                            response.text,
                        )
                        last_error = RetryableInferenceError(
                            f"Nebius service returned status {response.status_code}: {response.text}",
                            status_code=response.status_code,
                        )
                        if attempt < self.max_retries:
                            await asyncio.sleep(delay)
                            continue
                        raise last_error

                    # 3. Client error (4xx other than 429) -> immediate non-retryable failure
                    logger.error(
                        "Nebius inference fatal client error status %s: %s",
                        response.status_code,
                        response.text,
                    )
                    raise FinalInferenceError(
                        f"Nebius client request rejected with status {response.status_code}: {response.text}",
                        status_code=response.status_code,
                    )

                except (httpx.TimeoutException, httpx.NetworkError) as net_err:
                    latency_ms = (time.monotonic() - start_time) * 1000
                    delay = self._calculate_backoff(attempt)
                    logger.warning(
                        "Nebius network/timeout error (attempt %s/%s). Retrying in %.2fs: %s",
                        attempt,
                        self.max_retries,
                        delay,
                        net_err,
                    )
                    last_error = (
                        InferenceTimeoutError(
                            f"Nebius inference timed out after {self.timeout}s: {net_err}"
                        )
                        if isinstance(net_err, httpx.TimeoutException)
                        else RetryableInferenceError(f"Nebius connection error: {net_err}")
                    )
                    if attempt < self.max_retries:
                        await asyncio.sleep(delay)
                        continue
                    raise last_error from net_err

        raise last_error or InferenceError("Inference failed without specific exception")


inference_client = NebiusTokenFactoryClient()
