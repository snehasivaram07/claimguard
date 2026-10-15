import asyncio

import httpx
import pytest

from app.core.config import settings
from app.inference.client import (
    FinalInferenceError,
    InferenceDisabledError,
    NebiusTokenFactoryClient,
    RetryableInferenceError,
)
from app.inference.router import TaskType, Tier, UnsupportedTaskError, model_router


@pytest.fixture
def enable_inference(monkeypatch):
    monkeypatch.setattr(settings, "INFERENCE_ENABLED", True)
    monkeypatch.setattr(settings, "NEBIUS_API_KEY", "test_mock_token_12345")


@pytest.mark.asyncio
async def test_client_disabled_raises_inference_disabled_error(monkeypatch):
    monkeypatch.setattr(settings, "INFERENCE_ENABLED", False)
    client = NebiusTokenFactoryClient(api_key="mock_key")
    with pytest.raises(InferenceDisabledError):
        await client.chat_completion(
            messages=[{"role": "user", "content": "hi"}],
            model="nvidia/nemotron-3-nano",
        )


@pytest.mark.asyncio
@pytest.mark.usefixtures("enable_inference")
async def test_client_successful_chat_completion():
    def mock_handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer test_mock_token_12345"
        return httpx.Response(
            status_code=200,
            json={
                "id": "chatcmpl-mock-123",
                "object": "chat.completion",
                "model": "nvidia/nemotron-3-nano",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": '{"status": "ok"}'},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 15,
                    "completion_tokens": 8,
                    "total_tokens": 23,
                },
            },
        )

    transport = httpx.MockTransport(mock_handler)
    client = NebiusTokenFactoryClient(
        api_key="test_mock_token_12345",
        transport=transport,
    )

    resp = await client.chat_completion(
        messages=[{"role": "user", "content": "hello"}],
        model="nvidia/nemotron-3-nano",
        response_format={"type": "json_object"},
    )
    assert resp["id"] == "chatcmpl-mock-123"
    assert resp["choices"][0]["message"]["content"] == '{"status": "ok"}'
    assert resp["usage"]["total_tokens"] == 23


@pytest.mark.asyncio
@pytest.mark.usefixtures("enable_inference")
async def test_client_retries_on_429_and_recovers():
    attempts = 0

    def mock_handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(
                status_code=429,
                headers={"Retry-After": "0.01"},
                json={"error": {"message": "Rate limit exceeded"}},
            )
        return httpx.Response(
            status_code=200,
            json={
                "id": "chatcmpl-recovered",
                "choices": [{"message": {"role": "assistant", "content": "recovered"}}],
                "usage": {"total_tokens": 10},
            },
        )

    transport = httpx.MockTransport(mock_handler)
    client = NebiusTokenFactoryClient(
        api_key="test_mock_token_12345",
        max_retries=3,
        transport=transport,
    )

    res = await client.chat_completion(
        messages=[{"role": "user", "content": "test"}],
        model="nvidia/nemotron-3-nano",
    )
    assert res["id"] == "chatcmpl-recovered"
    assert attempts == 2


@pytest.mark.asyncio
@pytest.mark.usefixtures("enable_inference")
async def test_client_retries_on_503_and_exhausts_retries():
    attempts = 0

    def mock_handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(
            status_code=503,
            text="Service Temporarily Unavailable",
        )

    transport = httpx.MockTransport(mock_handler)
    client = NebiusTokenFactoryClient(
        api_key="test_mock_token_12345",
        max_retries=2,
        transport=transport,
    )

    with pytest.raises(RetryableInferenceError) as exc_info:
        await client.chat_completion(
            messages=[{"role": "user", "content": "test"}],
            model="nvidia/nemotron-3-nano",
        )
    assert attempts == 2
    assert "status 503" in str(exc_info.value)


@pytest.mark.asyncio
@pytest.mark.usefixtures("enable_inference")
async def test_client_fails_fast_on_401_unauthorized_without_retrying():
    attempts = 0

    def mock_handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(
            status_code=401,
            json={"error": {"message": "Invalid API key"}},
        )

    transport = httpx.MockTransport(mock_handler)
    client = NebiusTokenFactoryClient(
        api_key="bad_token",
        max_retries=3,
        transport=transport,
    )

    with pytest.raises(FinalInferenceError) as exc_info:
        await client.chat_completion(
            messages=[{"role": "user", "content": "test"}],
            model="nvidia/nemotron-3-nano",
        )
    assert attempts == 1  # Strictly 1 attempt (no retries on 401)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
@pytest.mark.usefixtures("enable_inference")
async def test_client_concurrency_semaphore_limits_in_flight():
    in_flight = 0
    max_in_flight_seen = 0

    async def mock_handler(_request: httpx.Request) -> httpx.Response:
        nonlocal in_flight, max_in_flight_seen
        in_flight += 1
        if in_flight > max_in_flight_seen:
            max_in_flight_seen = in_flight
        await asyncio.sleep(0.05)
        in_flight -= 1
        return httpx.Response(
            status_code=200,
            json={
                "id": "chatcmpl-concurrent",
                "choices": [{"message": {"role": "assistant", "content": "done"}}],
            },
        )

    transport = httpx.MockTransport(mock_handler)
    client = NebiusTokenFactoryClient(
        api_key="test_mock_token_12345",
        max_concurrency=2,
        transport=transport,
    )

    tasks = [
        client.chat_completion([{"role": "user", "content": "hi"}], "nvidia/nemotron-3-nano")
        for _ in range(5)
    ]
    await asyncio.gather(*tasks)
    assert max_in_flight_seen <= 2


def test_model_router_resolutions():
    # 1. Workflow task resolution
    nano_model = model_router.resolve_model(TaskType.DOCUMENT_EXTRACTION)
    assert nano_model == settings.NEMOTRON_NANO_MODEL

    # 2. Tier resolution
    assert model_router.resolve_model(Tier.NANO) == settings.NEMOTRON_NANO_MODEL
    assert model_router.resolve_model(Tier.SUPER) == settings.NEMOTRON_SUPER_MODEL
    assert model_router.resolve_model(Tier.ULTRA) == settings.NEMOTRON_ULTRA_MODEL

    # 3. String tier resolution
    assert model_router.resolve_model("nano") == settings.NEMOTRON_NANO_MODEL
    assert model_router.resolve_model("super") == settings.NEMOTRON_SUPER_MODEL
    assert model_router.resolve_model("ultra") == settings.NEMOTRON_ULTRA_MODEL

    # 4. Unknown task raises UnsupportedTaskError
    with pytest.raises(UnsupportedTaskError):
        model_router.resolve_model("unknown_hypothetical_workflow")
