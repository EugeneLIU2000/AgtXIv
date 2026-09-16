"""Host-only types. Never use these models to regenerate the business schemas."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

Hash = Annotated[str, Field(pattern=r"^sha256:[0-9a-f]{64}$", min_length=71, max_length=71)]
Key = Annotated[str, Field(min_length=1, max_length=128)]


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class WorkBinding(FrozenModel):
    """Approved host template identity, NOT a new model-authored FollowUp field."""
    plan_id: Key
    template_id: Key
    template_sha256: Hash
    purpose_id: Key
    policy_sha256: Hash
    model_binding_sha256: Hash
    specification_sha256: Hash


class Assignment(FrozenModel):
    task_bytes: bytes
    task_sha256: Hash
    binding: WorkBinding


class CallBudget(FrozenModel):
    """One reserved attempt; persistent parent accounting belongs to RuntimePort."""
    seconds: Annotated[int, Field(ge=1, le=3600)]
    input_bytes: Annotated[int, Field(ge=1, le=8 * 1024 * 1024)]
    output_bytes: Annotated[int, Field(ge=1, le=8 * 1024 * 1024)]
    output_tokens: Annotated[int, Field(ge=1, le=65536)]
    reserved_cost_units: Annotated[int, Field(ge=1)]


class Lease(FrozenModel):
    task_id: Key
    attempt_id: Key
    execution_id: Key
    principal_id: str
    fencing_token: Annotated[int, Field(ge=1)]
    budget: CallBudget


class GateDecision(FrozenModel):
    state: Literal["ALLOW", "WAIT", "DENY"]
    reasons: tuple[str, ...]
    evidence_receipt_ids: tuple[str, ...]


class HostReply(FrozenModel):
    state: Literal["WAITING", "DRAFT_STAGED", "FAILED", "DEFERRED", "COMMIT_UNKNOWN", "DELIVERED"]
    task_id: str
    attempt_id: str | None = None
    result_bytes: bytes | None = None
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class TextArtifact:
    reference_bytes: bytes
    data: bytes


@dataclass(frozen=True)
class FrozenInputs:
    """Bytes are immutable; no database/client/credential enters model deps."""
    task_bytes: bytes
    instructions: bytes
    output_schema: bytes
    records: tuple[bytes, ...]
    artifacts: tuple[TextArtifact, ...]
    manifest_bytes: bytes
    prompt_bytes: bytes


@dataclass(frozen=True)
class ModelExchange:
    state: Literal["DRAFT", "INVALID", "FAILED", "TIMEOUT", "CANCELLED"]
    draft_bytes: bytes | None
    checker_report_bytes: bytes | None
    messages_bytes: bytes
    usage_bytes: bytes
    started_at: str
    finished_at: str
    error_code: str | None


class IntegrationRequired(RuntimeError):
    """An explicitly missing adapter; never a reason to manufacture success."""


class UnsafeInput(ValueError):
    pass
