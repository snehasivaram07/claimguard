import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.core.config import settings
from app.core.logging import logger


@dataclass
class GuardResult:
    """Result of passing untrusted document content through the guard layer."""

    sanitized_text: str
    wrapped_prompt_text: str
    has_injection_pattern: bool
    matched_rule: str | None = None
    truncated: bool = False


class BaseGuard(ABC):
    """Abstract interface for prompt injection defenses and boundary isolation."""

    @abstractmethod
    def sanitize_and_wrap(self, document_text: str) -> GuardResult:
        """Sanitizes untrusted text and wraps it in rigid data delimiters."""


class DefaultGuard(BaseGuard):
    """Zero-dependency default guard enforcing XML data boundaries and injection heuristics."""

    # Heuristic signatures for common prompt injection and system override attempts
    INJECTION_PATTERNS = [
        (r"(?i)\bignore\s+(all\s+)?(previous|prior|above)\s+instructions\b", "ignore_previous_instructions"),
        (r"(?i)\bsystem\s+prompt\s+override\b", "system_prompt_override"),
        (r"(?i)\bdisregard\s+(all\s+)?(prior|previous)\s+directives\b", "disregard_directives"),
        (r"(?i)\byou\s+are\s+now\s+(a|an)\b", "role_override"),
        (r"(?i)\bjailbreak\b", "jailbreak_keyword"),
        (r"(?i)\bdrop\s+all\s+tables\b", "sql_injection_heuristic"),
        (r"(?i)<script\b", "script_injection_heuristic"),
        (r"(?i)\bshow\s+me\s+your\s+(system\s+)?prompt\b", "prompt_leak_attempt"),
    ]

    def __init__(self, max_input_chars: int | None = None):
        self.max_input_chars = max_input_chars or settings.LLM_MAX_INPUT_CHARS

    def sanitize_and_wrap(self, document_text: str) -> GuardResult:
        """Prepares untrusted document text for safe LLM ingestion without leaking data in logs."""
        truncated = False
        text = document_text

        # 1. Enforce maximum input character bound
        if len(text) > self.max_input_chars:
            text = text[: self.max_input_chars]
            truncated = True

        # 2. Heuristic scan for prompt injection attempts
        has_injection = False
        matched_rule = None

        for pattern, rule_name in self.INJECTION_PATTERNS:
            if re.search(pattern, text):
                has_injection = True
                matched_rule = rule_name
                # Security logging: Log detection rule ONLY, never log document content or text!
                logger.warning(
                    "Prompt injection pattern detected in document text: rule=%s",
                    rule_name,
                    extra={"security_rule": rule_name, "injection_flag": True},
                )
                break

        # 3. Wrap in rigid XML data boundary declaring content as passive untrusted data
        wrapped_text = (
            "<untrusted_document_content>\n"
            f"{text}\n"
            "</untrusted_document_content>"
        )

        return GuardResult(
            sanitized_text=text,
            wrapped_prompt_text=wrapped_text,
            has_injection_pattern=has_injection,
            matched_rule=matched_rule,
            truncated=truncated,
        )


default_guard = DefaultGuard()
