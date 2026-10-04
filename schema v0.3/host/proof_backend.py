"""Source-bound model proof candidates, isolated Lean execution and term evidence.

The environment and root-search judgements are host inputs. This worker neither
accepts those judgements nor invents library-absence results. Its callbacks fit
scheduler.bottom_up_walk; model calls and proof reservations remain separate.
"""
from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
import re
import selectors
import subprocess
import time

from chunks import reference
from core import VERSION, canonical, digest, utcnow, write_json
from extension_migration import _check_context, _context, _lean_path
from lean import ALLOWED_AXIOMS
from library import load_index, retrieve_by_names, unknown_identifiers
from model import _frozen_source_payload, call_model
from pdf_proof_context import bound_pdf_proof_context
from premise_evidence import bind_premise_report
from clause_evidence import bind_clause_report, clause_binding_coverage
from clause_coverage import candidate_clause_status
from recursive_graph import _verified_json
from scheduler import FAILURE_KINDS, _statement_fingerprint


IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)*\Z")
MAX_LEAN_MEMORY_MB = 8192
# Conservative rejection, not a complete security boundary. The driver parses
# precisely one term and the OS sandbox restricts filesystem/network effects.
PROHIBITED = re.compile(r"\b(?:sorry|admit|axiom|unsafe|native_decide|run_tac|run_elab|run_cmd|"
                        r"initialize|elab|macro|syntax|set_option|attribute|import)\b|\bIO\.|#")
PROOF_SCHEMA = {"type": "object", "additionalProperties": False, "properties": {
    "clause_scope_protocol": {"const": "NODE_SOURCE_SPANS_V1"},
    "clause_report": {"type": "array", "minItems": 1, "items": {
        "type": "object", "additionalProperties": False,
        "properties": {
            "clause_id": {"type": "string", "minLength": 1},
            "pdf_region_indices": {"type": "array", "uniqueItems": True,
                "items": {"type": "integer", "minimum": 0}},
            "statement": {"type": "string", "minLength": 1},
            "source_role": {"enum": ["THEOREM_STATEMENT", "PROOF_USED", "GLOBAL_CONVENTION", "NOT_LOCATED"]},
            "source_evidence_description": {"type": "string"},
            "source_path": {"type": "string"}, "source_quote": {"type": "string"},
            "relation": {"enum": ["CANDIDATE_EQUIVALENT", "PARTIAL", "STRONGER", "WEAKER", "UNRESOLVED"]},
            "remaining_obligations": {"type": "array", "uniqueItems": True, "items": {"type": "string", "minLength": 1}}},
        "required": ["clause_id", "statement", "source_role", "source_evidence_description",
                     "source_path", "source_quote", "relation", "remaining_obligations", "pdf_region_indices"]}},
    "lean_type": {"type": "string", "minLength": 1},
    "lean_value": {"type": "string", "minLength": 1},
    "lamport_steps": {"type": "array", "minItems": 1, "items": {"type": "string"}},
    "alignment_notes": {"type": "array", "items": {"type": "string"}},
    "premise_report": {"type": "array", "items": {"type": "object", "additionalProperties": False,
        "properties": {
            "condition": {"type": "string", "minLength": 1},
            "lean_binder_or_structure_field": {"type": "string", "minLength": 1},
            "source_role": {"enum": ["THEOREM_STATEMENT", "PROOF_USED", "GLOBAL_CONVENTION", "NOT_LOCATED"]},
            "source_evidence_description": {"type": "string"},
            "source_path": {"type": "string"},
            "source_quote": {"type": "string"},
            "relation": {"enum": ["CANDIDATE_EQUIVALENT", "CANDIDATE_STRONGER", "CANDIDATE_WEAKER", "UNRESOLVED"]}},
        "required": ["condition", "lean_binder_or_structure_field", "source_role",
                     "source_evidence_description", "source_path", "source_quote", "relation"]}},
    "remaining_obligations": {"type": "array", "items": {"type": "string"}}},
    "required": ["lean_type", "lean_value", "lamport_steps", "alignment_notes", "remaining_obligations", "premise_report", "clause_report", "clause_scope_protocol"]}
# One probe per tactic: `first` does not catch recursion or heartbeat exhaustion.
TRIVIALITY_TACTICS = ("trivial", "rfl", "decide", "simp", "norm_num")
FAILURE_SCHEMA = {"type": "object", "additionalProperties": False, "properties": {
    "failure_kind": {"type": "string", "enum": sorted(FAILURE_KINDS)},
    "reason": {"type": "string"}, "confidence": {"type": "number", "minimum": 0, "maximum": 1}},
    "required": ["failure_kind", "reason", "confidence"]}


def _ident(value):
    if not isinstance(value, str) or not IDENT.fullmatch(value):
        raise ValueError("Lean identifier is not in the supported host identifier subset")
    return value


def _binary_reference(path):
    path = Path(path).resolve()
    h = hashlib.sha256()
    size = 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
            size += len(block)
    return {"path": str(path), "sha256": "sha256:" + h.hexdigest(), "byte_size": size}


def _object_inventory(paths):
    files = set()
    for path in paths:
        for pattern in ("*.olean*", "*.ir", "*.ir.sig"):
            files.update(p.resolve() for p in Path(path).rglob(pattern) if p.is_file())
    return [_binary_reference(path) for path in sorted(files)]


def _read_object_inventory(ref):
    # A full pinned mathlib/Physlib object inventory exceeds the deliberately
    # smaller candidate-JSON ceiling. It has its own explicit bounded format.
    path = Path(ref["path"])
    if path.stat().st_size > 64 * 1024 * 1024 or _binary_reference(path) != ref:
        raise ValueError("Base-object inventory exceeds its ceiling or changed")
    rows = json.loads(path.read_bytes())
    if not isinstance(rows, list) or len(rows) > 300000:
        raise ValueError("Malformed base-object inventory")
    return rows


def _run_lean(environment, source, directory, operation, *, timeout=180, output_object=None):
    """No package builds, shell, network, or writes outside the current attempt."""
    directory, source = Path(directory).resolve(), Path(source).resolve()
    if not source.is_relative_to(directory):
        raise ValueError("Lean source must be inside its isolated attempt directory")
    sandbox = Path("/usr/bin/sandbox-exec")
    if not sandbox.is_file():
        raise RuntimeError("LEAN_EXECUTION_SANDBOX_UNAVAILABLE")
    scratch = directory / "tmp"
    scratch.mkdir(exist_ok=True)
    objects = directory / "compiled"
    objects.mkdir(exist_ok=True)
    source_before = reference(source)
    # Standard macOS runtime services may be read; network and child processes
    # are denied, with exec allowed only for the pinned Lean executable itself.
    executable = str(Path(environment["executable"]).resolve())
    profile = ('(version 1) (deny default) (allow file-read*) (allow sysctl-read) '
               '(allow mach-lookup) (allow process-info*) '
               '(allow process-exec (literal ' + json.dumps(executable) + ')) '
               '(allow file-write* (subpath ' + json.dumps(str(objects)) + ') '
               '(subpath ' + json.dumps(str(scratch)) + '))\n')
    profile_path = directory / "lean.sb"
    profile_path.write_text(profile)
    command = [str(sandbox), "-f", str(profile_path), executable,
               "--root=" + str(directory), "-DautoImplicit=false", "-DmaxHeartbeats=800000", "-M", str(MAX_LEAN_MEMORY_MB)]
    if output_object is not None:
        output_object = Path(output_object).resolve()
        if not output_object.is_relative_to(objects):
            raise ValueError("Lean object output escaped attempt directory")
        command += ["-o", str(output_object)]
    command.append(str(source))
    started, tick = utcnow(), time.monotonic()
    process = subprocess.Popen(command, cwd=directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env={"PATH": "/usr/bin:/bin", "HOME": os.environ.get("HOME", str(directory)),
             "LANG": "en_US.UTF-8", "LEAN_PATH": environment["lean_path"], "TMPDIR": str(scratch)}, start_new_session=True)
    error, code, output_chunks, captured = None, None, {"STDOUT": [], "STDERR": []}, 0
    limit = 4 * 1024 * 1024
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ, "STDOUT")
            selector.register(process.stderr, selectors.EVENT_READ, "STDERR")
            while selector.get_map():
                if time.monotonic() - tick > timeout:
                    error = "TIMEOUT"
                    process.kill()
                    break
                for key, _ in selector.select(timeout=0.25):
                    chunk = os.read(key.fileobj.fileno(), 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    if captured + len(chunk) > limit:
                        output_chunks[key.data].append(chunk[:limit-captured])
                        captured = limit
                        error = "OUTPUT_BYTE_LIMIT_EXCEEDED"
                        process.kill()
                        break
                    output_chunks[key.data].append(chunk)
                    captured += len(chunk)
                if error:
                    break
        code = process.wait(timeout=5)
    except BaseException:
        process.kill()
        process.communicate()
        raise
    finally:
        process.stdout.close()
        process.stderr.close()
    log = b"".join(output_chunks["STDOUT"]) + b"\nSTDERR:\n" + b"".join(output_chunks["STDERR"])
    (directory / "lean.log").write_bytes(log)
    succeeded = code == 0 and error is None and reference(source) == source_before
    receipt = {"kind": "ProgramReceipt", "contract_version": VERSION, "engine_class": "HOST",
        "program": "agtxiv.proof-backend/0.3.0", "call": None,
        "outcome": "RECORDED" if succeeded else "FAILED",
        "operation": operation, "command": command, "cwd": str(directory),
        "started_at": started, "finished_at": utcnow(), "elapsed_seconds": round(time.monotonic()-tick, 6),
        "input_sha256": source_before["sha256"], "output_sha256": digest(log),
        "exit_code": code, "status": "SUCCEEDED" if succeeded else "FAILED", "log": str(directory / "lean.log"),
        "execution_context": {"source_unchanged": reference(source) == source_before,
            "max_output_bytes": limit, "captured_output_bytes": captured, "max_memory_megabytes": MAX_LEAN_MEMORY_MB,
            "sandbox_profile": reference(profile_path), "network_allowed": False,
            "dependency_builds_requested": False, "lean_path": environment["lean_path"]}}
    if error is not None:
        receipt["error"] = error
    write_json(directory / "lean-receipt.json", receipt)
    return receipt, log.decode("utf-8", errors="replace")


def _records(log, receipt, environment_sha):
    rows = []
    for line in log.splitlines():
        if not line.startswith("AGTXIV_AUDIT_JSON "):
            continue
        row = json.loads(line.removeprefix("AGTXIV_AUDIT_JSON "))
        row["forbidden_axioms"] = sorted(set(row["axioms"]) - ALLOWED_AXIOMS)
        row["kernel_checked"] = receipt["status"] == "SUCCEEDED" and not row["forbidden_axioms"]
        row["environment_sha256"] = environment_sha
        rows.append(row)
    return rows


def statement_triviality(environment, directory, declaration, imports, *, timeout=180):
    """Try small bounded tactics on the elaborated type; None when a probe did not elaborate."""
    directory = Path(directory).resolve()
    directory.mkdir()
    probes = {_ident(declaration) + "_trivial_" + str(number): tactic for number, tactic in enumerate(TRIVIALITY_TACTICS)}
    source = directory / "Triviality.lean"
    source.write_text("import AgtXIvProofRuntime\n" + "".join("import " + _ident(name) + "\n" for name in dict.fromkeys(imports)) +
        "open scoped BigOperators\n" + "".join("set_option maxHeartbeats 20000 in\ntheorem " + probe + " : type_of% @" +
        declaration + " := by\n  intros; " + tactic + "\n#agtxiv_audit " + probe + "\n" for probe, tactic in probes.items()))
    receipt, log = _run_lean(environment, source, directory, "lean.statement_triviality", timeout=timeout)
    axioms = {row["declaration"]: row["axioms"] for row in _records(log, receipt, environment["environment_sha256"])
              if row["declaration"] in probes}
    # Lean's error recovery fills a failed tactic block with sorryAx.
    proved = any("sorryAx" not in row for row in axioms.values())
    return {"statement_trivially_provable": True if proved else False if len(axioms) == len(probes) else None,
            "statement_triviality": {"lean_source": reference(source), "program_receipt": receipt}}


def freeze_environment(repo, directory, *, extension_layers, imports, declarations):
    """Actually audit selected libraries before allowing the model proof worker."""
    repo, directory = Path(repo).resolve(), Path(directory).resolve()
    if directory.exists() and any(directory.iterdir()):
        raise FileExistsError("Proof environment needs a fresh directory")
    directory.mkdir(parents=True, exist_ok=True)
    context = _context(repo, [Path(path) for path in extension_layers])
    library = repo.parent / "physlib"
    _check_context(context, library)
    imports, declarations = list(dict.fromkeys(map(_ident, imports))), list(dict.fromkeys(map(_ident, declarations)))
    if not imports or not declarations:
        raise ValueError("Library imports and concrete audit targets are required")
    observations = []
    for command in (["lake", "env", "which", "lean"], ["lake", "env", "printenv", "LEAN_PATH"]):
        p = subprocess.run(command, cwd=library, capture_output=True, text=True, timeout=60)
        observations.append({"command": command, "exit_code": p.returncode, "stdout": p.stdout, "stderr": p.stderr})
        if p.returncode:
            write_json(directory / "environment-observations.json", observations)
            raise RuntimeError("Common Lean runtime could not be resolved")
    # Lake's relative dependency paths are relative to its project directory.
    package_paths = [str((library / p).resolve()) if not Path(p).is_absolute() else p
                     for p in observations[1]["stdout"].strip().split(":") if p]
    prefix = subprocess.run([observations[0]["stdout"].strip(), "--print-prefix"],
                            capture_output=True, text=True, timeout=60, check=True).stdout.strip()
    standard_library = Path(prefix) / "lib/lean"
    if not standard_library.is_dir():
        raise ValueError("The actual Lean standard library directory is absent")
    package_paths.append(str(standard_library.resolve()))
    trusted_sources = []
    for name in ("EnvironmentAudit.lean", "GeneratedProofDriverV2.lean"):
        snapshot = directory / "trusted-runtime" / name
        snapshot.parent.mkdir(exist_ok=True)
        snapshot.write_bytes((repo / "schema v0.3/lean" / name).read_bytes())
        trusted_sources.append(reference(snapshot))
    environment = {"kind": "FrozenProofEnvironment", "context": context, "library_root": str(library),
        "imports": imports, "requested_declarations": declarations,
        "executable": observations[0]["stdout"].strip(),
        "lean_path": _lean_path(context, directory / "compiled") + ":" + ":".join(package_paths),
        "runtime_sources": trusted_sources,
        "prop_composition_protocol": "ACTUAL_VALUE_BINDER_ISDEFEQ_V2",
        "source_alignment_accepted": False, "cache_source_freshness": "FROZEN_LOCAL_OBJECTS_REUSED"}
    # Hash all readable Lean object variants on the effective search path. This
    # deliberately includes the standard library and transitive package caches;
    # a Git revision or a module's own object alone does not pin its imports.
    object_dirs = list(dict.fromkeys(environment["lean_path"].split(":")))
    environment["base_object_directories"] = [path for path in object_dirs if Path(path) != directory / "compiled"]
    inventory = _object_inventory(environment["base_object_directories"])
    environment["executable_artifact"] = _binary_reference(environment["executable"])
    environment["base_object_inventory"] = write_json(directory / "base-object-inventory.json", inventory)
    environment["environment_hash_scope"] = "PINNED_EXECUTABLE_ALL_BASE_OBJECT_BYTES_SEARCH_ORDER_TRUSTED_RUNTIME_SOURCE"
    environment["environment_sha256"] = digest(canonical(environment))
    runtime = directory / "AgtXIvProofRuntime.lean"
    bodies = []
    for ref in environment["runtime_sources"]:
        raw = Path(ref["path"]).read_text()
        bodies.append("\n".join(line for line in raw.splitlines() if not line.startswith("import ")))
    runtime.write_text("import Lean\n" + "\n".join(bodies))
    write_json(directory / "environment-observations.json", observations)
    receipt, _ = _run_lean(environment, runtime, directory, "lean.proof_runtime", output_object=directory / "compiled/AgtXIvProofRuntime.olean")
    if receipt["exit_code"] != 0:
        write_json(directory / "incomplete-environment.json", environment)
        raise RuntimeError("PROOF_RUNTIME_COMPILATION_FAILED")
    audit_dir = directory / "library-audit"
    audit_dir.mkdir()
    source = audit_dir / "LibraryAudit.lean"
    source.write_text("import AgtXIvProofRuntime\n" + "\n".join("import " + name for name in imports) +
                      "\n" + "\n".join("#agtxiv_audit " + name for name in declarations))
    receipt, log = _run_lean(environment, source, audit_dir, "lean.proof_library_audit")
    rows = _records(log, receipt, environment["environment_sha256"])
    write_json(audit_dir / "records.json", rows)
    if {row["declaration"] for row in rows} != set(declarations) or not all(row["kernel_checked"] for row in rows):
        raise RuntimeError("PROOF_LIBRARY_AUDIT_FAILED")
    _check_context(context, library)
    environment.update(runtime_object=reference(directory / "compiled/AgtXIvProofRuntime.olean"),
        runtime_artifacts=_object_inventory([directory]),
        library_records=reference(audit_dir / "records.json"), library_receipt=reference(audit_dir / "lean-receipt.json"))
    write_json(directory / "environment.json", environment)
    return environment


class ModelProofBackend:
    def __init__(self, ledger, environment_ref, paper_sources, output, *, library_index=None):
        self.ledger, self.output, self.library_index, self._indexes = ledger, Path(output).resolve(), library_index, {}
        self.environment = _verified_json(environment_ref)
        if ledger.plan["environment"]["lean_environment_sha256"] != self.environment["environment_sha256"]:
            raise ValueError("Proof worker environment differs from the frozen plan")
        self.library = _verified_json(self.environment["library_records"])
        self.paper_sources = paper_sources
        self.output.mkdir(parents=True, exist_ok=True)

    def _check_environment(self):
        env = self.environment
        _check_context(env["context"], Path(env["library_root"]))
        for ref in [*env["runtime_artifacts"], *env["runtime_sources"]]:
            if reference(Path(ref["path"])) != ref:
                raise ValueError("Frozen proof runtime changed")
        if _binary_reference(env["executable"]) != env["executable_artifact"]:
            raise ValueError("Pinned Lean executable changed")
        inventory = _read_object_inventory(env["base_object_inventory"])
        if _object_inventory(env["base_object_directories"]) != inventory:
            raise ValueError("Pinned transitive Lean object changed")

    def _source_context(self, node):
        paper_id = node.get("paper_id")
        entry = self.paper_sources.get(paper_id)
        if entry is None or not node.get("source_spans"):
            raise ValueError("Proof node has no retained source paper and span")
        if "pdf_run" in entry:
            context, images = bound_pdf_proof_context(node, entry)
            return [context], images
        paper = _verified_json(entry["extraction"])
        if paper["paper"]["id"] != paper_id:
            raise ValueError("Proof node and frozen paper identities differ")
        sources = _frozen_source_payload(paper, entry["directory"], source_directory=entry["directory"])
        lookup = {source["path"]: source for source in sources}
        for span in node["source_spans"]:
            source = lookup[span["path"]]
            raw = source["text"].encode("utf-8")
            start, end = span["byte_start"], span["byte_end"]
            if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(raw):
                raise ValueError("Proof source span has invalid byte boundaries")
            if (span["sha256"] != source["sha256"] or
                digest(raw[span["byte_start"]:span["byte_end"]]) != span["span_sha256"]):
                raise ValueError("Proof node source span differs from frozen bytes")
        return sources, []

    def _compile(self, node, candidate, directory, prerequisites, kind):
        self._check_environment()
        module = "Proof_" + digest(canonical({"node": node["id"], "directory": str(directory)}))[7:27]
        declaration = "AgtXIv.Generated." + module
        prior_modules, prior_paths, prior_records, parent_objects = [], [], {}, []
        for node_id, dependency in prerequisites.items():
            evidence = dependency.get("evidence") or dependency.get("explicit_premise")
            for object_ref in evidence["compiled_artifacts"] + evidence.get("parent_artifacts", []):
                if _binary_reference(object_ref["path"]) != object_ref:
                    raise ValueError("Upstream or transitive proof object changed")
                parent_objects.append(object_ref)
            prior_modules.append(_ident(evidence["module"]))
            # Include the transitive search paths recorded by its compilation.
            prior_paths.extend(evidence["object_search_paths"])
            prior_records[node_id] = evidence["audit_record"]
        paths = list(dict.fromkeys([str(directory / "compiled"), *prior_paths]))
        prop_protocol = self.environment.get("prop_composition_protocol") == "ACTUAL_VALUE_BINDER_ISDEFEQ_V2"
        prop_targets = [upstream["declaration"] for node_id, upstream in prior_records.items()
                        if prerequisites[node_id].get("dependency_kind") == "EXPLICIT_PROP_PREMISE"]
        prop_command = " against [" + ", ".join(map(_ident, prop_targets)) + "]" if prop_protocol else ""
        env = {**self.environment, "lean_path": ":".join(paths + [self.environment["lean_path"]])}
        source = directory / (module + ".lean")
        source.write_text("import AgtXIvProofRuntime\n" + "".join("import " + name + "\n" for name in dict.fromkeys(self.environment["imports"] + prior_modules)) +
            "open scoped BigOperators\n" +
            "#agtxiv_candidate " + declaration + " " + " ".join(json.dumps(value, ensure_ascii=False) for value in
                (kind, candidate["lean_type"], candidate["lean_value"])) + "\n#agtxiv_audit " + declaration +
                "\n#agtxiv_used_premises " + declaration + prop_command + "\n")
        receipt, log = _run_lean(env, source, directory, "lean.model_candidate",
            timeout=self.ledger.plan["limits"]["max_call_seconds"], output_object=directory / "compiled" / (module + ".olean"))
        self._check_environment()
        rows = _records(log, receipt, self.environment["environment_sha256"])
        write_json(directory / "audits.json", rows)
        valid = len(rows) == 1 and rows[0]["declaration"] == declaration and rows[0]["kernel_checked"] and rows[0]["kind"] == kind
        record = rows[0] if valid else None
        premise_rows = [json.loads(line.removeprefix("AGTXIV_USED_PREMISES_JSON ")) for line in log.splitlines()
                        if line.startswith("AGTXIV_USED_PREMISES_JSON ")]
        valid = valid and len(premise_rows) == 1 and premise_rows[0]["declaration"] == declaration
        if prop_protocol and valid:
            valid = (premise_rows[0].get("protocol") == "ACTUAL_VALUE_BINDER_ISDEFEQ_V2" and
                     premise_rows[0].get("checked_propositions") == prop_targets)
        result = {"kernel_checked": bool(valid), "program_receipt": receipt, "lean_source": reference(source),
            "lamport": reference(directory / "lamport.json"), "source_node_id": node["id"],
            "source_statement_sha256": _statement_fingerprint(node), "nonvacuity_witness": "NONE",
            "declaration_kind": kind, "declaration_bindings": [{"declaration": declaration}],
            "source_alignment_accepted": False, "promotion_allowed": False}
        if valid:
            artifacts = _object_inventory([directory])
            expected_names = {module + suffix for suffix in (".olean", ".olean.private", ".olean.server", ".ir", ".ir.sig")}
            if any(Path(row["path"]).parent != directory / "compiled" or Path(row["path"]).name not in expected_names for row in artifacts):
                raise ValueError("Candidate produced unexpected Lean objects")
            composition = []
            for node_id, upstream in prior_records.items():
                direct = upstream["declaration"] in record["term_constants"]
                premise = prerequisites[node_id].get("dependency_kind") == "EXPLICIT_PROP_PREMISE"
                # Never join value binders to statement binders by their names.
                used = [row for row in premise_rows[0]["used_prop_binders"]
                        if row.get("proof_body_uses_binder") is True and type(row.get("binder_index")) is int
                        and row["binder_index"] >= 0 and row.get("type_equality_method") ==
                        "LEAN_META_ISDEFEQ_ACTUAL_PROOF_VALUE_BINDER" and upstream["declaration"] in
                        row.get("definitionally_equal_propositions", [])] if premise and prop_protocol else []
                composition.append({"upstream_node_id": node_id, "downstream_node_id": node["id"],
                    "upstream_declaration": upstream["declaration"], "downstream_declaration": declaration,
                    "basis": ("LEAN_USED_PROP_BINDER" if used else "PROP_BINDER_TYPE_EQUIVALENCE_UNAVAILABLE") if premise else "LEAN_ELABORATED_TERM_CONSTANT",
                    "used_prop_binders": used,
                    "status": "COMPOSED" if (bool(used) if premise else direct) else "NOT_COMPOSED"})
            result.update(audit_record=record, module=module, object_search_paths=paths,
                compiled_object=reference(directory / "compiled" / (module + ".olean")),
                compiled_artifacts=artifacts,
                parent_artifacts=list({row["path"]: row for row in parent_objects}.values()),
                hypotheses=record["non_instance_prop_hypotheses"] + record["structure_prop_hypotheses"],
                forbidden_axioms=record["forbidden_axioms"], composition_witnesses=composition)
            if kind == "THEOREM":
                result.update(statement_triviality(env, directory / "triviality", declaration,
                    self.environment["imports"] + [module], timeout=self.ledger.plan["limits"]["max_call_seconds"]))
        return result, log

    def _library_context(self, node, earlier):
        """Index rows of a searched root's candidates and of names the last Lean run could not resolve."""
        audit = node.get("root_audit") if isinstance(node.get("root_audit"), dict) else {}
        ref = audit.get("index") or self.library_index
        if ref is None:
            return {}
        if ref["sha256"] not in self._indexes:
            index = load_index(ref)
            if index["environment_sha256"] != self.environment["environment_sha256"]:
                raise ValueError("Library index belongs to another proof environment")
            self._indexes[ref["sha256"]] = index["rows"], {row["name"]: row["type"] for row in index["rows"]}
        (rows, types), context = self._indexes[ref["sha256"]], {}
        if audit.get("candidates"):
            context["retrieved_library_candidates"] = [{"name": name, "type": types[name]} for name in audit["candidates"]]
        receipt = next((row["program_receipt"] for row in reversed(earlier) if row.get("program_receipt")), {})
        log = Path(receipt["log"]).read_bytes() if Path(receipt.get("log", "")).is_file() else b""
        names = unknown_identifiers(log.decode("utf-8", errors="replace"))
        if names and digest(log) == receipt["output_sha256"]:
            context["library_search_for_unknown_identifiers"] = {"unknown_identifiers": names, "candidates": {
                name: [{"name": row["name"], "type": row["type"]} for row in found]
                for name, found in retrieve_by_names(names, rows, 5).items()}}
        return context

    def _candidate(self, node, prerequisites, reservation, *, premise=False, failed_result=None):
        self._check_environment()
        directory = self.output / reservation["id"].replace(":", "-")
        directory.mkdir()
        prerequisite_manifest = write_json(directory / "prerequisites.json", prerequisites)
        previous = self.ledger.proof_attempt_history(node["id"], kind="PROOF")
        sources, images = self._source_context(node)
        earlier = [row.get("result") for row in previous if row.get("result")]
        payload = {"node": node, "full_frozen_sources": sources,
            "audited_library_declarations": self.library, "available_prerequisites": prerequisites,
            "earlier_attempts": earlier, "premise_only": premise, "failed_result": failed_result}
        retrieved = self._library_context(node, earlier)
        payload.update(retrieved)
        instruction = ("Render the source proposition as a Lean term of type Prop, without proving or weakening it. "
                       "Set lean_type to Prop and lean_value to that proposition, including its quantifiers. " if premise else
                       "Propose one faithful Lean statement and proof, each a single Lean term. "
                       "lean_type must include all binders; lean_value must prove precisely that type. "
                       "Use upstream declarations in the proof term when they are actual supports. ")
        instruction += ("Supply structured reasoning in lamport_steps. Do not assume the conclusion, strong duality, "
            "a representation certificate or an existence fact merely to make the proof easy. Preserve all original "
            "conditions and identify any restriction in alignment_notes. Do not use sorry, admit, new axioms, unsafe, "
            "IO, native_decide or custom elaborators. The host chooses names and imports. If a previous statement "
            "failed, do not silently weaken it. Library records are actual types, not accepted source alignment. "
            "In premise_report enumerate mathematical premises, including restrictions inside structures and typeclasses. "
            "Distinguish theorem-stated, proof-used and global source conditions; use NOT_LOCATED and an empty "
            "evidence description when no source basis is found. Describe file/section or PDF page and source wording "
            "when located. These are attributed descriptions, not verified source spans or accepted equivalence. "
            "For located UTF-8 sources also give source_path and a unique exact source_quote including TeX syntax. "
            "For NOT_LOCATED or PDF page evidence use empty source_path and source_quote; PDF descriptions remain unbound. "
            "An empty report means no premises were reported, not that completeness was verified. "
            "In clause_report enumerate the source node's separate conclusions, with local clause IDs. "
            "Compare each with the proposed Lean declaration, explicitly retaining omitted or partial clauses. "
            "Use clause_scope_protocol NODE_SOURCE_SPANS_V1: quotations must lie within the target node's "
            "source_spans. Other passages may provide proof context but do not cover its conclusion. "
            "Use the same exact-quotation/location rules as premise_report. "
            "For PDF clauses, select zero-based indices from the supplied context's page_regions in "
            "pdf_region_indices; do not invent regions or treat a full-page context image as a verified quote. "
            "Use an empty index list for text sources or NOT_LOCATED clauses. If none of the provided "
            "regions locates the clause, keep the list empty and state the missing location. "
            "A clause report is a candidate inventory, not certified completeness. "
            "For a definition report its defining content.\n")
        if retrieved:
            instruction += ("Retrieved library rows are lexical search results from the pinned index, not bindings "
                            "or evidence; use a declaration only if it elaborates here.\n")
        def validate(candidate):
            issues = []
            for field in ("lean_type", "lean_value"):
                if PROHIBITED.search(candidate[field]):
                    issues.append({"code": "UNSUPPORTED_LEAN_EFFECT_OR_PLACEHOLDER", "detail": field})
            if premise and candidate["lean_type"].strip() != "Prop":
                issues.append({"code": "PREMISE_MUST_HAVE_TYPE_PROP", "detail": "lean_type"})
            for index, item in enumerate(candidate["premise_report"]):
                located = item["source_role"] != "NOT_LOCATED"
                if bool(item["source_evidence_description"].strip()) != located:
                    issues.append({"code": "PREMISE_REPORT_LOCATION_INCONSISTENT", "detail": str(index)})
            try:
                bind_premise_report(candidate["premise_report"], sources)
                bind_clause_report(candidate["clause_report"], sources, node)
            except ValueError as error:
                issues.append({"code": "PREMISE_SOURCE_BINDING_FAILED", "detail": str(error)})
            return issues
        response = call_model(self.ledger, "autoformalization.premise" if premise else "autoformalization.lean",
            "HEAVY", instruction + json.dumps(payload, ensure_ascii=False), PROOF_SCHEMA, directory / "model",
            timeout=self.ledger.plan["limits"]["max_call_seconds"], candidate_validator=validate,
            image_references=images)
        write_json(directory / "model-result.json", response)
        if response["candidate"] is None:
            result = {"kernel_checked": False, "model_result": reference(directory / "model-result.json"),
                      "failure_reason": response["receipt"].get("error"), "prerequisite_manifest": prerequisite_manifest}
            if response["receipt"].get("error") == "MODEL_TIMEOUT":
                result.update(failure_kind="TIMEOUT", failure_basis="HOST_PROCESS_DEADLINE")
            write_json(directory / "result.json", result)
            return result
        candidate = response["candidate"]
        premise_evidence = write_json(directory / "premise-evidence.json",
            bind_premise_report(candidate["premise_report"], sources))
        clause_data = bind_clause_report(candidate["clause_report"], sources, node)
        clause_evidence = write_json(directory / "clause-evidence.json", clause_data)
        write_json(directory / "lamport.json", {key: candidate[key] for key in
                   ("lamport_steps", "alignment_notes", "remaining_obligations", "premise_report", "clause_report", "clause_scope_protocol")})
        coverage_status = candidate_clause_status([{"clause_coverage": clause_binding_coverage(clause_data)}])
        if coverage_status in {"INCOMPLETE", "MALFORMED"} or candidate["remaining_obligations"]:
            result = {"kernel_checked": False, "compile_disposition": "SKIPPED_SOURCE_COVERAGE",
                      "clause_coverage_status": coverage_status,
                      "failure_reason": "SOURCE_COVERAGE_REQUIRES_REVIEW",
                      "remaining_obligations": candidate["remaining_obligations"],
                      "model_result": reference(directory / "model-result.json"),
                      "lamport": reference(directory / "lamport.json"),
                      "premise_evidence": premise_evidence, "clause_evidence": clause_evidence,
                      "prerequisite_manifest": prerequisite_manifest,
                      "source_alignment_accepted": False, "promotion_allowed": False}
            write_json(directory / "result.json", result)
            return result
        kind = "DEFINITION" if premise or node["kind"].lower() == "definition" else "THEOREM"
        result, log = self._compile(node, candidate, directory, prerequisites, kind)
        result["model_result"] = reference(directory / "model-result.json")
        result["premise_evidence"] = premise_evidence
        result["clause_evidence"] = clause_evidence
        for binding in result.get("declaration_bindings", []):
            binding["clause_coverage"] = clause_binding_coverage(clause_data)
        result["prerequisite_manifest"] = prerequisite_manifest
        # Keep the actual compilation result even if a later classification
        # cannot reserve a call or its backend is unavailable.
        write_json(directory / "result.json", result)
        if premise and result["kernel_checked"]:
            result.update(lean_prop=candidate["lean_value"], declaration=result["audit_record"]["declaration"],
                elaborated_type=result["audit_record"]["type"],
                alignment_confidence={"source": "SELF_REPORTED", "value": 0, "calibration_ref": None})
        elif not result["kernel_checked"]:
            try:
                classification = call_model(self.ledger, "autoformalization.failure_classify", "DECISION",
                    "Classify this actual Lean failure. A failed tactic alone does not make the source claim false.\n" +
                    json.dumps({"candidate": candidate, "diagnostics": log}, ensure_ascii=False), FAILURE_SCHEMA,
                    directory / "failure-model", timeout=self.ledger.plan["limits"]["max_call_seconds"])
            except Exception as error:
                classification = {"candidate": None, "unavailable": {"type": type(error).__name__, "detail": str(error)}}
                result["classification_unavailable"] = classification["unavailable"]
            write_json(directory / "failure-classification.json", classification)
            if classification["candidate"]:
                row = classification["candidate"]
                result.update(failure_kind=row["failure_kind"], failure_reason=row["reason"],
                    failure_confidence={"source": "SELF_REPORTED", "value": row["confidence"], "calibration_ref": None})
        write_json(directory / "result.json", result)
        return result

    def attempt(self, node, number, prerequisites, reservation):
        return self._candidate(node, prerequisites, reservation)

    def render_premise(self, node, result, reservation):
        prerequisites = _verified_json(result["prerequisite_manifest"]) if result.get("prerequisite_manifest") else {}
        return self._candidate(node, prerequisites, reservation, premise=True, failed_result=result)
