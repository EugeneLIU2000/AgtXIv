"""Explicit declaration audit for compiled candidates; does not accept paper claims."""
from __future__ import annotations

import json
from pathlib import Path
import re

from extension_migration import _check_context, _lean_path
from lean import ALLOWED_AXIOMS, _execute, _sha, _write, composition_witness
from candidate_compile import check_candidate_objects, check_candidate_receipts


def audit_candidates(repo: Path, bundle_dir: Path, targets: list[str], *,
                     plan_bytes: bytes | None = None, library: Path | None = None) -> dict:
    """Execute Lean for explicitly selected declarations after authorization.

    Target coverage is caller-selected and is never promoted to all-claim or
    all-declaration coverage. Existing attempts are not overwritten.
    """
    repo, bundle_dir = Path(repo).resolve(), Path(bundle_dir).resolve()
    if (not targets or len(targets) != len(set(targets)) or
            any(not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9']*(?:\.[A-Za-z_][A-Za-z_0-9']*)*", n)
                for n in targets)):
        raise ValueError("Require distinct explicit Lean declaration names")
    raw = (bundle_dir / "candidate-sources.json").read_bytes()
    bundle = json.loads(raw)
    progress_raw = (bundle_dir / "compile-progress.json").read_bytes()
    progress = json.loads(progress_raw)
    if (bundle.get("kind") != "UncompiledCandidateSourceBundle" or
            progress.get("kind") != "CandidateCompilationProgress" or
            progress.get("status") != "COMPILED_AUDIT_PENDING" or
            progress.get("bundle_sha256") != _sha(raw)):
        raise ValueError("Require matching completed candidate compilation")
    order = bundle["source_dependency_order"]
    if (len(order) != len(set(order)) or set(order) != set(bundle["modules"]) or
            [row["module"] for row in progress["compiled_modules"]] != order or
            any(not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", n) for n in order)):
        raise ValueError("Candidate module inventory disagrees")
    expected_kinds = {}
    if plan_bytes is not None:
        plan = json.loads(plan_bytes)
        if (plan.get("kind") != "CandidateDeclarationAuditPlan" or
                [row["declaration"] for row in plan["targets"]] != targets or
                plan.get("root_module") not in bundle["roots"] or
                plan.get("source_alignment_accepted") is not False or
                plan.get("all_query_claims_covered") is not False):
            raise ValueError("Audit plan does not match the unaccepted candidate scope")
        for target in plan["targets"]:
            if "expected_kind" in target:
                if target["expected_kind"] not in {"THEOREM", "DEFINITION"}:
                    raise ValueError("Unsupported expected declaration kind")
                expected_kinds[target["declaration"]] = target["expected_kind"]
    context = bundle["intended_context"]
    library = repo.parent / "physlib" if library is None else Path(library).resolve()
    objects = bundle_dir / "candidate-lib"

    def check_inputs() -> None:
        if ((bundle_dir / "candidate-sources.json").read_bytes() != raw or
                (bundle_dir / "compile-progress.json").read_bytes() != progress_raw):
            raise ValueError("Audit inputs changed")
        _check_context(context, library)
        for name, row in bundle["modules"].items():
            if row["snapshot"] != "sources/" + name + ".lean":
                raise ValueError("Unexpected snapshot path")
            if _sha((bundle_dir / row["snapshot"]).read_bytes()) != row["source_sha256"]:
                raise ValueError("Candidate source changed")
        check_candidate_objects(objects, progress["compiled_modules"])
        check_candidate_receipts(bundle_dir, bundle, progress, library)

    check_inputs()
    audit_dir = bundle_dir / "declaration-audit"
    audit_dir.mkdir(exist_ok=False)
    if plan_bytes is not None:
        (audit_dir / "plan.json").write_bytes(plan_bytes)
    source = ("\n".join("import " + name for name in order) + "\n" +
              (repo / "schema v0.3/lean/EnvironmentAudit.lean").read_text() + "\n" +
              "\n".join("#agtxiv_audit " + name for name in targets) + "\n")
    script = audit_dir / "CandidateAudit.lean"
    script.write_text(source)
    _write(audit_dir / "targets.json", targets)
    receipt = _execute(["env", "LEAN_PATH=" + _lean_path(context, objects),
                        "lake", "env", "lean", str(script)], library,
                       audit_dir / "audit.log", "lean.candidate_declaration_audit", _sha(source.encode()))
    _write(audit_dir / "receipt.json", receipt)
    environment = {"context": context, "candidate_artifacts": progress["compiled_modules"],
                   "bundle_sha256": _sha(raw), "audit_source_sha256": _sha(source.encode())}
    environment_sha = _sha(json.dumps(environment, sort_keys=True).encode())
    result = {"kind": "CandidateDeclarationAudit", "status": "AUDIT_FAILED",
              "bundle_sha256": _sha(raw), "compile_progress_sha256": _sha(progress_raw),
              "audit_source_sha256": _sha(source.encode()), "requested_targets": targets,
              "receipt": receipt, "records": [], "accepted": False,
              "environment": environment, "environment_sha256": environment_sha,
              "composition_witnesses": [], "unaudited_term_dependencies": [],
              "composition_scope": "DIRECT_TERM_EDGES_BETWEEN_SELECTED_DECLARATIONS_ONLY",
              "source_alignment_accepted": False, "query_chain_complete": False,
              "all_declarations_covered": False, "all_premises_reviewed": False}
    if plan_bytes is not None:
        result["plan_sha256"] = _sha(plan_bytes)
    try:
        check_inputs()
        if receipt["status"] == "SUCCEEDED":
            records = [json.loads(line.removeprefix("AGTXIV_AUDIT_JSON "))
                       for line in (audit_dir / "audit.log").read_text().splitlines()
                       if line.startswith("AGTXIV_AUDIT_JSON ")]
            for row in records:
                forbidden = sorted(set(row["axioms"]) - ALLOWED_AXIOMS)
                row.update(forbidden_axioms=forbidden, kernel_checked=False,
                           source_alignment_accepted=False, accepted=False,
                           environment_sha256=environment_sha, receipt=str(audit_dir / "receipt.json"))
            result["records"] = records
            names = [row["declaration"] for row in records]
            kind_mismatches = [{"declaration": row["declaration"],
                                "expected_kind": expected_kinds[row["declaration"]],
                                "actual_kind": row.get("kind")}
                               for row in records if row["declaration"] in expected_kinds
                               and row.get("kind") != expected_kinds[row["declaration"]]]
            result["declaration_kind_mismatches"] = kind_mismatches
            result["status"] = ("AUDIT_TARGET_MISMATCH" if sorted(names) != sorted(targets) else
                                "AUDIT_DECLARATION_KIND_MISMATCH" if kind_mismatches else
                                "AUDIT_AXIOMS_REJECTED" if any(row["forbidden_axioms"] for row in records) else
                                "SELECTED_DECLARATIONS_AUDITED")
            if result["status"] == "SELECTED_DECLARATIONS_AUDITED":
                for row in records:
                    row["kernel_checked"] = True
                selected = set(names)
                for row in records:
                    for dependency in sorted(set(row["term_constants"])):
                        if dependency not in selected:
                            result["unaudited_term_dependencies"].append({
                                "downstream_declaration": row["declaration"],
                                "upstream_declaration": dependency})
                        elif dependency != row["declaration"]:
                            witness = composition_witness(records, dependency, row["declaration"])
                            if witness["status"] == "COMPOSED":
                                result["composition_witnesses"].append(witness)
    except (ValueError, KeyError, OSError, TypeError) as exc:
        result.update(status="AUDIT_EVIDENCE_REJECTED", error=str(exc))
        result["composition_witnesses"] = []
        for row in result["records"]:
            row["kernel_checked"] = False
    checked = [row for row in result["records"] if row.get("kernel_checked") is True]
    result["declaration_kind_counts"] = {
        "scope": "SELECTED_DECLARATIONS_IN_THIS_AUDIT_ONLY",
        "kernel_checked_theorems": sum(row.get("kind") == "THEOREM" for row in checked),
        "kernel_checked_definitions": sum(row.get("kind") == "DEFINITION" for row in checked),
        "kernel_checked_other": sum(row.get("kind") not in {"THEOREM", "DEFINITION"} for row in checked),
        "source_claims_accepted": 0,
        "definition_semantics_verified": False,
        "counts_establish_paper_proof_discharge": False,
    }
    _write(audit_dir / "candidate-audit.json", result)
    return result


def audit_candidate_plan(repo: Path, bundle_dir: Path, plan_path: Path, *,
                         library: Path | None = None) -> dict:
    """Execute a retained target plan; this has the same Lean authorization requirement."""
    raw = Path(plan_path).read_bytes()
    plan = json.loads(raw)
    return audit_candidates(repo, bundle_dir, [row["declaration"] for row in plan["targets"]],
                            plan_bytes=raw, library=library)
