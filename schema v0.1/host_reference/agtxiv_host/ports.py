"""Required integration contracts. Protocols here are NOT working backends.

In particular, RuntimePort must own the business/runtime/outbox transaction.
Calling LocalStore.ingest followed by a separate runtime commit is NOT a valid
implementation. No permissive in-memory 'production' substitute is supplied.
"""
from __future__ import annotations

from typing import Protocol

from .types import Assignment, FrozenInputs, GateDecision, Lease, ModelExchange


class ExactReader(Protocol):
    def record(self, exact_ref: dict, *, max_bytes: int) -> bytes:
        """Return the authorized, exact version's stored JSON bytes, never latest."""
        ...

    def artifact(self, exact_ref: dict, *, max_bytes: int) -> bytes:
        """Bound reads before allocation; return authorized original bytes.
        path_hint grants no filesystem access. Oversize input must be refused.
        """
        ...


class EvidenceGate(Protocol):
    async def before_attempt(self, assignment: Assignment, task: dict) -> GateDecision:
        """Authenticate caller/executor, approve template+purpose+model binding;
        verify prerequisites from actual committed state (DELIVERY != EVIDENCE),
        exclusions, full producer closure, source visibility and remaining budget.
        Blind review requires a separately audited neutral context. A trace ID or
        caller-supplied principal string is NOT proof of independent identity.
        """
        ...

    async def before_inputs(self, assignment: Assignment, inputs: FrozenInputs) -> GateDecision:
        """Inspect exact rendered model context before reservation/send: source
        permissions, neutral blind brief, record envelopes, attachments and all
        instructions, including prompt_bytes exactly as sent to the SDK. Reject
        leaked target/producer metadata, not just bad refs.
        A generic Dependency Injection container is not a visibility attestation.
        """
        ...

    async def before_delivery(
        self, assignment: Assignment, lease: Lease, inputs: FrozenInputs,
        exchange: ModelExchange, checker_report: dict,
    ) -> GateDecision:
        """Judge purpose-specific delivery completeness, not just output families.
        Recheck actual inputs, mandatory target coverage and relevant evidence.
        Empty Delta drafts with prose gaps may be stored, not silently accepted
        as a complete comparison. Returning ALLOW is not scientific admission.
        Receipt IDs must allow RuntimePort to recheck gate freshness at commit.
        """
        ...


class RuntimePort(Protocol):
    async def record_waiting(self, assignment: Assignment, reasons: tuple[str, ...]) -> None:
        """Persist fixed pending Task + missing inputs, without a fake attempt.
        Must not reset parent budget or permit same task ID with changed bytes.
        """
        ...

    async def claim(
        self, assignment: Assignment, inputs: FrozenInputs,
        prerequisite_decision: GateDecision, *, work_key: str,
    ) -> Lease:
        """Atomically persist immutable Task/input manifest, recheck gate versions,
        reserve PARENT plan budget and acquire fenced lease. Reject duplicate
        task IDs with different bytes, expired/denied evidence and exhausted or
        cancelled work. Template+purpose distinguish otherwise identical work.
        work_key is a conservative deduplication index, not reusable scientific
        approval. Recheck prerequisites on every admission, including cache hits.
        Host-controlled caps include transport retries and one model request.
        No network/file downloads inside this transaction.
        """
        ...

    async def assert_current(self, lease: Lease) -> None:
        """Check task cancellation, budget, holder, fencing token and deadline."""
        ...

    async def stage(self, lease: Lease, exchange: ModelExchange) -> None:
        """Durably retain success/invalid/partial messages and actual usage.
        Reconcile actual cost against reserved parent units. Unknown cost keeps
        its reservation and blocks automatic retry; never silently record zero.
        Immutable bytes/attempt, fenced writes, no formal Result/admission yet.
        """
        ...

    async def close_attempt(self, lease: Lease, state: str, reasons: tuple[str, ...]) -> None:
        """Persist WAITING/FAILED/DEFERRED/DRAFT_STAGED transition and actual event.
        Losing a lease must not overwrite its new owner. A crash after request
        send but before stage leaves an uncertain attempt: reconcile first,
        never repeat a possibly billed call under the old attempt identifier.
        """
        ...

    async def deliver_atomic(
        self, assignment: Assignment, lease: Lease, inputs: FrozenInputs,
        exchange: ModelExchange, decision: GateDecision,
    ) -> bytes:
        """Assemble allowed envelopes from frozen draft, validate FULL records
        and RecordSet/byte closure, then commit records/artifacts/Result/events/
        outbox in ONE transaction owned here. Preserve original draft and all
        declared mathematical payload fields; only documented identity fields
        may be assembled from independent host evidence. Recheck lease, policy
        and decision receipt versions in the transaction. Allocate stable output
        IDs across retries. Return the actual committed Result JSON bytes.
        On uncertain commit, resolve by task+attempt identity, never regenerate.
        IntegrationRequired is permitted ONLY before any side effect; after
        writes begin, raise an ordinary error and require commit reconciliation.
        """
        ...


class GraphPort(Protocol):
    async def query_between_tasks(self, request_bytes: bytes, authorization: object) -> bytes:
        """graph-service/1.0 query; fixed batch/ACL/budget, no arbitrary Cypher.
        Hydration and next-Task creation are host work, never a live model tool.
        """
        ...


class ArchivePort(Protocol):
    async def publish_sealed(self, message_bytes: bytes, authorization: object) -> bytes:
        """Fixed sealed bytes only; remote readback before publication receipt.
        Independent of graph readiness, outside the candidate transaction.
        """
        ...


class ProgramPort(Protocol):
    async def execute(self, task_bytes: bytes, request_bytes: bytes, lease: Lease) -> bytes:
        """Utility: exact Task/request binding + actual restricted program.
        No model decides command strings; diagnostics do not become execution.
        """
        ...
