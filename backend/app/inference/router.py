from enum import StrEnum

from app.core.config import settings
from app.inference.client import InferenceError


class Tier(StrEnum):
    """Reasoning and capacity tiers for NVIDIA Nemotron models."""

    NANO = "nano"
    SUPER = "super"
    ULTRA = "ultra"


class TaskType(StrEnum):
    """Distinct AI task workflows defined across the ClaimGuard platform."""

    DOCUMENT_EXTRACTION = "document_extraction"


class UnsupportedTaskError(InferenceError):
    """Raised when an unrecognized task or tier cannot be mapped to a model."""

    def __init__(self, task: str):
        super().__init__(
            message=f"Inference task '{task}' has no configured model tier mapping.",
            status_code=400,
        )
        self.task = task


class ModelRouter:
    """Deterministic task-to-tier and tier-to-model resolver for Nemotron models on Nebius."""

    def __init__(self):
        # Phase 2 wires exclusively DOCUMENT_EXTRACTION -> NANO
        self._task_map: dict[TaskType, Tier] = {
            TaskType.DOCUMENT_EXTRACTION: Tier.NANO,
        }

    def resolve_tier(self, task: TaskType | str) -> Tier:
        """Resolves an AI workflow task to its designated capacity tier."""
        if isinstance(task, str):
            try:
                task = TaskType(task)
            except ValueError:
                raise UnsupportedTaskError(str(task)) from None

        tier = self._task_map.get(task)
        if not tier:
            raise UnsupportedTaskError(task.value)
        return tier

    def resolve_model(self, target: Tier | TaskType | str) -> str:
        """Resolves a Tier, TaskType, or string name to the active model identifier."""
        # 1. If target is string matching a Tier or TaskType
        if isinstance(target, str):
            try:
                target = Tier(target.lower())
            except ValueError:
                try:
                    target = TaskType(target.lower())
                except ValueError:
                    raise UnsupportedTaskError(target) from None

        # 2. If target is TaskType, resolve to its Tier first
        if isinstance(target, TaskType):
            target = self.resolve_tier(target)

        # 3. Map Tier to configured model ID from settings
        if target == Tier.NANO:
            return settings.NEMOTRON_NANO_MODEL
        if target == Tier.SUPER:
            return settings.NEMOTRON_SUPER_MODEL
        if target == Tier.ULTRA:
            return settings.NEMOTRON_ULTRA_MODEL

        raise UnsupportedTaskError(str(target))


model_router = ModelRouter()
