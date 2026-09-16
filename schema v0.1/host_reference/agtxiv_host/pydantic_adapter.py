"""One real Pydantic AI request per durable host attempt (not run on import).

No model/provider is selected here; the application supplies an approved Model.
No function tools, shell, files, graph client, network-search capability or
cross-task message history are exposed. This is not an OS security sandbox.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib.metadata import version

from agtxiv_v3.contracts import ContractError, canonical, digest, parse
from pydantic_ai import Agent, StructuredDict, ToolOutput, capture_run_messages
from pydantic_ai.messages import ModelMessagesTypeAdapter, ToolCallPart
from pydantic_ai.models import Model
from pydantic_ai.usage import RunUsage, UsageLimits

from .contracts import Catalog
from .inputs import model_prompt
from .types import CallBudget, FrozenInputs, IntegrationRequired, ModelExchange, UnsafeInput


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


@dataclass(frozen=True)
class ModelDeps:
    visible_context_sha256: str


class PydanticAdapter:
    def __init__(self, model: Model, *, model_binding_sha256: str):
        if isinstance(model, str):
            raise UnsafeInput("Supply an explicitly configured, approved Model, not an inferred provider name")
        if version("pydantic-ai-slim") != "2.43.0" or version("pydantic") != "2.13.5":
            raise IntegrationRequired("SDK_VERSION_DIFFERS_FROM_REFERENCE_SELECTION")
        self.model = model
        # Trusted deployment binds provider, model, transport retry policy,
        # network/account policy and resolved package lock to this descriptor.
        self.model_binding_sha256 = model_binding_sha256

    async def generate(self, inputs: FrozenInputs, budget: CallBudget, catalog: Catalog) -> ModelExchange:
        catalog.assert_unchanged()
        prompt = model_prompt(inputs)
        submitted_bytes = (len(prompt.encode("utf-8")) + len(inputs.instructions) + len(inputs.output_schema))
        if submitted_bytes > budget.input_bytes:
            raise UnsafeInput("MODEL_CONTEXT_LIMIT: split into a new explicit Task, never silently truncate")
        task = parse(inputs.task_bytes)
        output = StructuredDict(parse(inputs.output_schema), name="AssignedDraft")
        agent = Agent(
            model=self.model, deps_type=ModelDeps,
            name="agtxiv_" + task["operation"].replace(".", "_"),
            instructions=inputs.instructions.decode("utf-8"),
            output_type=ToolOutput(output, name="submit_draft", max_retries=0),
            retries=0, tools=(), toolsets=(), capabilities=(),
            model_settings={"max_tokens": budget.output_tokens, "timeout": float(budget.seconds)},
        )
        # Do not export prompt/response contents through process-wide tracing.
        # An application-supplied instrumented Model still needs policy review.
        agent.instrument = False
        candidate = None
        checker_report = None

        @agent.output_validator
        async def validate(output_value: dict) -> dict:
            nonlocal candidate, checker_report
            # StructuredDict does NOT validate JSON Schema constraints itself.
            # Use the original checker and keep its exact original report.
            calls = [part for message in messages for part in message.parts
                     if isinstance(part, ToolCallPart) and part.tool_name == "submit_draft"]
            if len(calls) != 1 or not isinstance(calls[0].args, str):
                # Some providers expose only a parsed dict. Keep its SDK message
                # but do not pretend original JSON duplicate-key checks ran.
                raise UnsafeInput("EXACT_DRAFT_ARGUMENT_BYTES_UNAVAILABLE")
            candidate = calls[0].args.encode("utf-8")
            if len(candidate) > budget.output_bytes:
                raise UnsafeInput("DRAFT_BYTES_LIMIT")
            parsed = parse(candidate)  # Strict original-argument parse, including duplicate keys.
            if canonical(parsed) != canonical(output_value):
                raise UnsafeInput("SDK_OUTPUT_DIFFERS_FROM_ORIGINAL_ARGUMENTS")
            checker_report = catalog.check_draft(task, parsed)
            if not checker_report["shape_and_interface_passed"]:
                raise UnsafeInput("DRAFT_INTERFACE_REJECTED")
            return output_value

        usage = RunUsage()
        started = timestamp()
        state, error_code = "FAILED", None
        with capture_run_messages() as messages:
            try:
                async with asyncio.timeout(budget.seconds):
                    await agent.run(
                        prompt, deps=ModelDeps(digest(prompt.encode("utf-8"))),
                        usage=usage,
                        usage_limits=UsageLimits(request_limit=1, tool_calls_limit=0),
                        # No message_history, external tools, auto-dispatch or SDK retry.
                    )
                state = "DRAFT"
            except TimeoutError:
                state, error_code = "TIMEOUT", "MODEL_TIMEOUT_COST_MAY_BE_UNKNOWN"
            except asyncio.CancelledError:
                state, error_code = "CANCELLED", "MODEL_CANCELLED_COST_MAY_BE_UNKNOWN"
            except (UnsafeInput, ContractError):
                state, error_code = "INVALID", "DRAFT_OR_PIN_REJECTED"
            except Exception as error:
                state, error_code = "FAILED", type(error).__name__
        # SDK message serialization, NOT claimed to be original HTTP wire bytes.
        # Retain private messages on failures too. RuntimePort owns secure storage.
        message_bytes = ModelMessagesTypeAdapter.dump_json(messages)
        usage_bytes = canonical({
            "requests": usage.requests, "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "accounting_source": "SDK_OBSERVED_NOT_PROVIDER_BILLING",
            "actual_cost_units": None,
        })
        return ModelExchange(
            state, candidate, canonical(checker_report) if checker_report is not None else None,
            message_bytes, usage_bytes, started, timestamp(), error_code,
        )
