import json
import re
from typing import Any

from pydantic import ValidationError

from app.core.logging import logger
from app.inference.client import NebiusTokenFactoryClient
from app.inference.prompts.document_extraction_v1 import (
    EXTRACTION_SYSTEM_PROMPT,
    build_repair_user_prompt,
)
from app.inference.schemas import DocumentExtractionV1


class ExtractionParseError(Exception):
    """Raised when LLM output cannot be parsed into a valid DocumentExtractionV1 schema."""

    def __init__(self, message: str, raw_output: str = "", validation_error: Exception | None = None):
        super().__init__(message)
        self.message = message
        # Bounded snippet (max 200 chars) for diagnostics without leaking entire document
        self.raw_output_snippet = raw_output[:200] if raw_output else ""
        self.validation_error = validation_error


def clean_json_text(raw_text: str) -> str:
    """Strips reasoning models' <think> tags, markdown code blocks, and extraneous conversational filler."""
    if not raw_text:
        return ""

    # 1. Remove reasoning model chain-of-thought tokens (<think>...</think>)
    text = re.sub(r"(?s)<think>.*?</think>", "", raw_text).strip()

    # 2. Extract content from markdown code fences if present (```json ... ``` or ``` ... ```)
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence_match:
        text = fence_match.group(1).strip()

    # 3. If surrounding text remains, locate opening and closing JSON braces
    start_idx = text.find("{")
    end_idx = text.rfind("}")
    if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
        return ""

    text = text[start_idx : end_idx + 1]
    return text.strip()


def parse_extraction_output(raw_text: str) -> DocumentExtractionV1:
    """Parses and validates LLM completion output against DocumentExtractionV1 schema."""
    cleaned = clean_json_text(raw_text)
    if not cleaned:
        raise ExtractionParseError(
            message="LLM output is empty or contains no parseable JSON object",
            raw_output=raw_text,
        )

    try:
        data: dict[str, Any] = json.loads(cleaned)
    except json.JSONDecodeError as err:
        raise ExtractionParseError(
            message=f"Failed to decode JSON from LLM output: {err}",
            raw_output=raw_text,
            validation_error=err,
        ) from err

    try:
        return DocumentExtractionV1.model_validate(data)
    except ValidationError as err:
        raise ExtractionParseError(
            message=f"LLM output violates DocumentExtractionV1 schema: {err}",
            raw_output=raw_text,
            validation_error=err,
        ) from err


async def parse_with_repair(
    raw_text: str,
    client: NebiusTokenFactoryClient,
    model: str,
) -> DocumentExtractionV1:
    """Attempts defensive parsing; if malformed, triggers exactly one repair round-trip with the LLM."""
    try:
        return parse_extraction_output(raw_text)
    except ExtractionParseError as parse_err:
        logger.warning(
            "Initial document extraction output parsing failed. Triggering 1-shot repair request to model: %s",
            model,
            extra={"error_type": "extraction_parse_failure"},
        )

        repair_prompt = build_repair_user_prompt(
            invalid_output=parse_err.raw_output_snippet,
            error_message=str(parse_err),
        )

        messages = [
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": repair_prompt},
        ]

        repair_response = await client.chat_completion(
            messages=messages,
            model=model,
            temperature=0.0,
        )

        repaired_content = repair_response["choices"][0]["message"]["content"]
        # If repair attempt also fails, ExtractionParseError will propagate
        return parse_extraction_output(repaired_content)
