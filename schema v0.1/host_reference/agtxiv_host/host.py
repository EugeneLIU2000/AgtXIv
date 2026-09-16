"""Deterministic host orchestration around one model attempt.

No `host Agent`, recursive agent.run, self-granted tools or background loop.
Application-provided durable/security ports are mandatory; see ports.py.
"""
from __future__ import annotations

from agtxiv_v3.contracts import digest, parse

from .contracts import Catalog
from .inputs import freeze
from .policy import delivery_families, dispatch_key, guard_draft
from .ports import EvidenceGate, ExactReader, RuntimePort
from .pydantic_adapter import PydanticAdapter
from .types import Assignment, GateDecision, HostReply, IntegrationRequired, UnsafeInput


def attested(decision: GateDecision) -> GateDecision:
    # Nonempty IDs are only a necessary condition; the runtime must resolve
    # actual authenticated, version-bound receipts. Strings are not identity.
    if decision.state == "ALLOW" and (not decision.evidence_receipt_ids
                                     or any(not item.strip() for item in decision.evidence_receipt_ids)):
        return GateDecision(state="DENY", reasons=("GATE_RECEIPTS_REQUIRED",), evidence_receipt_ids=())
    return decision


class Host:
    def __init__(self, *, catalog: Catalog, reader: ExactReader, gate: EvidenceGate,
                 runtime: RuntimePort, model: PydanticAdapter):
        self.catalog, self.reader, self.gate = catalog, reader, gate
        self.runtime, self.model = runtime, model

    async def model_once(self, assignment: Assignment) -> HostReply:
        # Parsing/checking a Task never creates an execution identity or budget.
        if digest(assignment.task_bytes) != assignment.task_sha256:
            raise UnsafeInput("TASK_RAW_HASH_MISMATCH")
        task = parse(assignment.task_bytes)
        self.catalog.contracts.task(task)
        task_id = task["task_id"]
        self.catalog.binding(task["operation"])
        if assignment.binding.model_binding_sha256 != self.model.model_binding_sha256:
            raise UnsafeInput("MODEL_BINDING_MISMATCH")
        decision = attested(await self.gate.before_attempt(assignment, task))
        if decision.state != "ALLOW":
            await self.runtime.record_waiting(assignment, decision.reasons)
            return HostReply(state="WAITING", task_id=task_id, reasons=decision.reasons)
        try:
            inputs = freeze(assignment, self.catalog, self.reader)
        except (IntegrationRequired, UnsafeInput) as error:
            reasons = (str(error),)
            await self.runtime.record_waiting(assignment, reasons)
            return HostReply(state="WAITING", task_id=task_id, reasons=reasons)
        visibility = attested(await self.gate.before_inputs(assignment, inputs))
        if visibility.state != "ALLOW":
            await self.runtime.record_waiting(assignment, visibility.reasons)
            return HostReply(state="WAITING", task_id=task_id, reasons=visibility.reasons)
        # claim must bind BOTH actual gate receipts, including the exact context.
        decision = decision.model_copy(update={
            "evidence_receipt_ids": decision.evidence_receipt_ids + visibility.evidence_receipt_ids,
        })
        lease = await self.runtime.claim(assignment, inputs, decision,
                                         work_key=dispatch_key(assignment, task))
        if lease.task_id != task_id or lease.principal_id in task["exclusions"]:
            raise UnsafeInput("LEASE_TASK_OR_EXECUTOR_MISMATCH")
        if (lease.budget.seconds > task["limits"]["max_seconds"]
                or lease.budget.reserved_cost_units > task["limits"]["max_cost_units"]):
            raise UnsafeInput("LEASE_BUDGET_ESCALATION")
        await self.runtime.assert_current(lease)
        try:
            exchange = await self.model.generate(inputs, lease.budget, self.catalog)
        except (IntegrationRequired, UnsafeInput) as error:
            # Failure before request submission; no fictional model Result.
            reasons = (str(error),)
            await self.runtime.close_attempt(lease, "WAITING", reasons)
            return HostReply(state="WAITING", task_id=task_id, attempt_id=lease.attempt_id, reasons=reasons)
        # stage must be durable before admission/assembly or a second model call.
        # A stage storage failure propagates: recovery reconciles this attempt.
        await self.runtime.stage(lease, exchange)
        if exchange.state != "DRAFT" or exchange.draft_bytes is None:
            state = "DEFERRED" if exchange.state in {"TIMEOUT", "CANCELLED"} else "FAILED"
            reasons = (exchange.error_code or "NO_ACCEPTABLE_DRAFT",)
            await self.runtime.close_attempt(lease, state, reasons)
            return HostReply(state=state, task_id=task_id, attempt_id=lease.attempt_id, reasons=reasons)
        try:
            self.catalog.assert_unchanged()
            report = self.catalog.check_draft(task, parse(exchange.draft_bytes))
            draft = parse(exchange.draft_bytes)
            reasons = (() if report["shape_and_interface_passed"] else ("POST_RUN_INTERFACE_REJECTED",))
            if not reasons:
                reasons = guard_draft(task, draft) + delivery_families(task, draft)
        except (IntegrationRequired, UnsafeInput) as error:
            reasons = (str(error),)
        if reasons:
            # Diagnostic/partial drafts are kept, not promoted into full delivery.
            await self.runtime.close_attempt(lease, "DRAFT_STAGED", reasons)
            return HostReply(state="DRAFT_STAGED", task_id=task_id, attempt_id=lease.attempt_id, reasons=reasons)
        approval = attested(await self.gate.before_delivery(assignment, lease, inputs, exchange, report))
        if approval.state != "ALLOW":
            await self.runtime.close_attempt(lease, "DRAFT_STAGED", approval.reasons)
            return HostReply(state="DRAFT_STAGED", task_id=task_id,
                             attempt_id=lease.attempt_id, reasons=approval.reasons)
        await self.runtime.assert_current(lease)
        try:
            result_bytes = await self.runtime.deliver_atomic(assignment, lease, inputs, exchange, approval)
            result = parse(result_bytes)
            self.catalog.contracts.result(task, result)
            if (result["attempt_id"] != lease.attempt_id
                    or result["execution"]["execution_id"] != lease.execution_id
                    or result["execution"]["principal_id"] != lease.principal_id
                    or result["outcome"] != "DELIVERED"):
                raise UnsafeInput("COMMIT_RECEIPT_BINDING_MISMATCH")
        except IntegrationRequired as error:
            reasons = (str(error),)
            await self.runtime.close_attempt(lease, "DRAFT_STAGED", reasons)
            return HostReply(state="DRAFT_STAGED", task_id=task_id, attempt_id=lease.attempt_id, reasons=reasons)
        except Exception:
            # Never overwrite a possibly committed result with FAILED or retry
            # the model. Reconcile exact attempt identity through RuntimePort.
            return HostReply(state="COMMIT_UNKNOWN", task_id=task_id, attempt_id=lease.attempt_id,
                             reasons=("RECONCILE_COMMIT_BEFORE_RETRY",))
        return HostReply(state="DELIVERED", task_id=task_id, attempt_id=lease.attempt_id,
                         result_bytes=result_bytes)
