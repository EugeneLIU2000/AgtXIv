"""Explicit bridge to existing offline checkers, without changing their schemas.

Construction/check calls are runtime work, not performed by importing this file.
The loaded repository is trusted executable code; model input cannot choose it.
"""
from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from pathlib import Path

from agtxiv_v3.contracts import canonical, digest, parse
from referencing import Resource

from .types import IntegrationRequired, UnsafeInput


@dataclass(frozen=True)
class Binding:
    directory: str
    kind: str
    schema_file: str
    checker_file: str = "check_interfaces.py"
    documents: tuple[str, ...] = ("AGENT.md",)


AF_DOCS = ("AGENT.md", "INTERFACE.md", "LAMPORT.md", "LEAN4.md", "REVIEW.md", "ENVIRONMENT.md", "CONFORMANCE.md")
BINDINGS = {
    "paper.extract": Binding("Paper Agent", "paper", "extraction-draft.schema.json",
                             "check_output.py", ("AGENT.md", "INTERFACE.md", "CONFORMANCE.md")),
    "proof.expand": Binding("Autoformalization Agent", "proof", "proof-draft.schema.json", documents=AF_DOCS),
    "formalization.generate": Binding("Autoformalization Agent", "lean", "lean-draft.schema.json", documents=AF_DOCS),
    "dependency.search": Binding("Dependency Agent", "search", "search-draft.schema.json"),
    "planner.propose": Binding("Planner Agent", "propose", "propose-draft.schema.json"),
    "delta.compare": Binding("Delta Agent", "delta", "delta-draft.schema.json"),
    "reader.explain": Binding("Reader Agent", "explanation", "explanation-draft.schema.json"),
    **{f"review.{kind}": Binding("Review Agent", kind, f"{kind}-draft.schema.json")
       for kind in ("scope", "argument", "reuse", "backtranslate", "alignment", "scientific", "audit", "admission")},
}


def load_trusted(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise IntegrationRequired("Checker cannot be loaded: " + path.name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Catalog:
    def __init__(self, repository: Path):
        self.repository = repository.resolve()
        self.directory = self.repository / "schema v0.1"
        self.overlay = load_trusted(self.directory / "validate.py", "host_overlay_contracts")
        self.contracts = self.overlay.Contracts(self.directory)
        self._checkers: dict[str, object] = {}
        self._initial_pins = self.pins()

    def pins(self) -> dict[str, str]:
        # Keep examples/reports/PENDING_TESTS out of executable specification pins.
        paths = set((self.repository / "schema v0.0").glob("*.json"))
        paths.update((self.directory / "schemas").glob("*.json"))
        paths.update(self.directory / name for name in (
            "validate.py", "agents.json", "compatibility.lock.json",
            "AGENT-CONTRACTS.md", "SCHEDULING.md", "STORAGE.md", "GRAPH-INTERFACE.md"))
        paths.update((self.repository / "src/agtxiv_v3").glob("*.py"))
        paths.add(self.repository / "src/agtxiv_v2/contracts/canonical.py")
        paths.update(Path(__file__).resolve().parent.glob("*.py"))
        paths.add(Path(__file__).resolve().parents[1] / "pyproject.toml")
        for binding in BINDINGS.values():
            base = self.directory / binding.directory
            paths.update(base.glob("*.schema.json"))
            paths.update(base / name for name in (*binding.documents, binding.schema_file, binding.checker_file))
        return {str(path.relative_to(self.repository)): digest(path.read_bytes())
                for path in sorted(paths)}

    @property
    def specification_hash(self) -> str:
        return digest(canonical(self._initial_pins))

    @property
    def specification_files(self) -> dict[str, str]:
        return dict(self._initial_pins)

    def assert_unchanged(self) -> None:
        if self.pins() != self._initial_pins:
            raise UnsafeInput("SPECIFICATION_CHANGED: create a new pinned attempt")

    def binding(self, operation: str) -> Binding:
        if operation not in BINDINGS:
            raise IntegrationRequired("No model adapter for " + operation + "; Utility requires ProgramPort")
        return BINDINGS[operation]

    def checker(self, operation: str):
        if operation not in self._checkers:
            binding = self.binding(operation)
            module = load_trusted(self.directory / binding.directory / binding.checker_file,
                                  "host_checker_" + operation.replace(".", "_"))
            self._checkers[operation] = (module.OutputChecker() if binding.kind == "paper"
                                         else module.InterfaceChecker())
        return self._checkers[operation]

    def check_draft(self, task: dict, draft: dict) -> dict:
        self.assert_unchanged()
        binding = self.binding(task["operation"])
        checker = self.checker(task["operation"])
        if binding.kind == "paper":
            original = checker.check_draft(draft, task)
            passed = original["error_count"] == 0
        else:
            original = checker.check(binding.kind, draft, task, require_task=True)
            passed = original["checks_passed"] is True
        # Preserve each checker's actual scope; never collapse it to "verified".
        return {"shape_and_interface_passed": passed, "original_report": original}

    def instructions(self, operation: str) -> bytes:
        binding = self.binding(operation)
        paths = [self.directory / "AGENT-CONTRACTS.md"]
        paths.extend(self.directory / binding.directory / name for name in binding.documents)
        text = "\n\n".join(f"DOCUMENT {path.name}\n{path.read_text(encoding='utf-8')}" for path in paths)
        return text.encode("utf-8")

    def provider_schema(self, operation: str) -> bytes:
        """Bounded inlining, only for provider transport; original validator wins.

        Cyclic/dynamic references are refused rather than weakening constraints.
        Provider support for the resulting schema still requires separate tests.
        """
        binding = self.binding(operation)
        schema = parse((self.directory / binding.directory / binding.schema_file).read_bytes())
        registry = self.contracts.registry.with_resource(schema["$id"], Resource.from_contents(schema))
        visited_nodes = 0

        def expand(node, resolver, depth=0):
            nonlocal visited_nodes
            visited_nodes += 1
            if depth > 80 or visited_nodes > 100000:
                raise IntegrationRequired("PROVIDER_SCHEMA_EXPANSION_LIMIT")
            if isinstance(node, list):
                return [expand(item, resolver, depth + 1) for item in node]
            if not isinstance(node, dict):
                return node
            if "$dynamicRef" in node or "$recursiveRef" in node:
                raise IntegrationRequired("DYNAMIC_SCHEMA_REQUIRES_DEDICATED_ADAPTER")
            if "$ref" in node:
                resolved = resolver.lookup(node["$ref"])
                target = expand(resolved.contents, resolved.resolver, depth + 1)
                siblings = {k: v for k, v in node.items() if k != "$ref"}
                return {"allOf": [target, expand(siblings, resolver, depth + 1)]} if siblings else target
            return {k: expand(v, resolver, depth + 1) for k, v in node.items()
                    if k not in {"$schema", "$id", "$defs"}}

        raw = canonical(expand(schema, registry.resolver(base_uri=schema["$id"])))
        if len(raw) > 2 * 1024 * 1024:
            raise IntegrationRequired("PROVIDER_SCHEMA_BYTES_LIMIT")
        return raw
