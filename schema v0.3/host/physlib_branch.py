"""Explicitly frozen user-authored Physlib branch, outside the old Lean epoch.

The source came from untracked local PhyslibAlpha work. It is compiled as this
repository's candidate module; it is never described as a pinned upstream
Physlib theorem or silently imported into the old RootMath environment.
"""
from __future__ import annotations

import json
from pathlib import Path

from lean import ALLOWED_AXIOMS, _execute, _sha, _write, composition_witness


DECLARATIONS = [
    "MState.sq_exp_val_le_exp_val_sq",
    "Matrix.weighted_sum_sq_of_pairwise_anticommute",
    "MState.exp_val_finset_sum",
    "MState.sum_sq_exp_val_finset_le_one_of_pairwise_anticommute",
    "MState.sum_abs_exp_val_finset_le_sqrt_card_of_pairwise_anticommute",
    "AgtXIv.PhyslibCandidate.expectation_eq_real_trace",
    "AgtXIv.PhyslibCandidate.anticommuting_real_trace_l2_bound",
    "AgtXIv.PhyslibCandidate.graph_clique_expectation_bound",
    "AgtXIv.PhyslibCandidate.pauliZ",
    "AgtXIv.PhyslibCandidate.pauliZ_sq",
    "AgtXIv.PhyslibCandidate.pauliZ_ne_one",
    "AgtXIv.PhyslibCandidate.anticommuting_bound_nonvacuity",
]


def _paper_span(repo: Path, start_line: int, end_line: int) -> dict:
    source = repo / "Stabilizerness/arXiv-2607.26154v1/draft.tex"
    raw = source.read_bytes()
    lines = raw.splitlines(keepends=True)
    start = sum(map(len, lines[:start_line - 1]))
    end = sum(map(len, lines[:end_line]))
    return {"path": str(source), "source_sha256": _sha(raw),
            "byte_start": start, "byte_end": end, "span_sha256": _sha(raw[start:end]),
            "start_line": start_line, "end_line": end_line,
            "text": raw[start:end].decode()}


def summarize_branch(repo: Path, output_dir: Path, audit_receipt: dict,
                     *, physlib_root: Path | None = None) -> dict:
    repo, output_dir = Path(repo).resolve(), Path(output_dir).resolve()
    library = Path(physlib_root or repo.parent / "physlib").resolve()
    frozen = repo / "schema v0.3/lean/frozen/AnticommutingWitness.lean"
    provenance = json.loads((frozen.parent / "provenance.json").read_text())
    if _sha(frozen.read_bytes()) != provenance["source_sha256"]:
        raise ValueError("Frozen user-authored source changed without new provenance")
    manifest = json.loads((library / "lake-manifest.json").read_text())
    imported_modules = ["QuantumInfo/States/Mixed/MState", "Physlib/Relativity/PauliMatrices/Basic",
                        "Mathlib/Combinatorics/SimpleGraph/Clique"]
    module_hashes = {}
    for module in imported_modules:
        base = library / ".lake/packages/mathlib" if module.startswith("Mathlib/") else library
        path = base / (".lake/build/lib/lean/" + module + ".olean")
        module_hashes[module] = _sha(path.read_bytes())
    environment = {
        "toolchain": (library / "lean-toolchain").read_text().strip(),
        "resolved_manifest": manifest, "frozen_source_sha256": provenance["source_sha256"],
        "frozen_olean_sha256": _sha((output_dir / "AnticommutingWitness.olean").read_bytes()),
        "imported_module_sha256": module_hashes,
        "library_cache_freshness": "IMPORTED_PINNED_CACHE_NOT_REBUILT",
        "candidate_source_freshness": "FRESHLY_COMPILED_IN_THIS_RUN",
    }
    environment_sha256 = _sha(json.dumps(environment, sort_keys=True).encode())
    result = {
        "scope": "LOCAL_FROZEN_PHYSLIB_ANTICOMMUTING_BRANCH",
        "state": "CHAIN_INCOMPLETE", "human_accepted": False,
        "source_provenance": provenance, "environment": environment,
        "environment_sha256": environment_sha256, "receipt": audit_receipt,
        "attempt_receipts": [json.loads(path.read_text())
                             for path in sorted(output_dir.glob("audit-receipt*.json"))],
        "execution_status": "AUDIT_FAILED", "records": [], "composition_witnesses": [],
        "source_alignment": {
            "status": "AGENT_NORMALIZED_UNREVIEWED",
            "source_claim": "claim:anticommuting-l2-bound",
            "source_span": _paper_span(repo, 725, 755),
            "additional_supported_step": _paper_span(repo, 755, 763),
            "relation": "GENERAL_HERMITIAN_INVOLUTION_LEMMA_WITH_OPEN_PAULI_SPECIALIZATION",
            "matching_conditions": ["finite family", "density matrix (positive semidefinite, trace one)",
                                    "Hermitian observables", "square equals identity", "pairwise anticommutation"],
            "open_bridges": ["PAPER_PAULI_WINDOW_TO_HERMITIAN_OBSERVABLE_FAMILY",
                             "PAPER_FRUSTRATION_GRAPH_ADJACENCY_TO_ANTICOMMUTATION",
                             "REDUCED_ROM_CLOSED_FORM_TO_CLIQUE_MAXIMUM"],
        },
        "cross_epoch_composition_with_rootmath": "NOT_COMPOSED",
        "nonvacuity": {
            "declaration": "AgtXIv.PhyslibCandidate.anticommuting_bound_nonvacuity",
            "instance": "MState (Fin 2), one nonidentity Pauli Z observable, index Fin 1",
            "status": "NOT_YET_AUDITED",
            "scope": "CONCRETE_INSTANCE_OF_GENERAL_OPERATOR_FAMILY_PREMISES",
            "does_not_establish": "All paper-specific premises or a complete query-chain witness",
        },
    }
    if audit_receipt["status"] == "SUCCEEDED":
        for line in Path(audit_receipt["log"]).read_text().splitlines():
            if line.startswith("AGTXIV_AUDIT_JSON "):
                record = json.loads(line[len("AGTXIV_AUDIT_JSON "):])
                forbidden = sorted(set(record["axioms"]) - ALLOWED_AXIOMS)
                record.update(forbidden_axioms=forbidden, kernel_checked=not forbidden,
                              environment_sha256=environment_sha256, receipt=audit_receipt["log"],
                              statement_alignment="AGENT_NORMALIZED_UNREVIEWED", accepted=False)
                result["records"].append(record)
        records = {r["declaration"]: r for r in result["records"]}
        result["execution_status"] = ("AUDIT_COMPLETE" if set(records) == set(DECLARATIONS)
                                      else "AUDIT_TARGET_MISMATCH")
        witness = records.get(result["nonvacuity"]["declaration"], {})
        if witness.get("kernel_checked") and not witness["non_instance_prop_hypotheses"]:
            result["nonvacuity"]["status"] = "CONCRETE_EXISTENTIAL_WITNESS_KERNEL_CHECKED"
        for target in result["records"]:
            for dependency in target["term_constants"]:
                if dependency in records and dependency != target["declaration"]:
                    witness = composition_witness(result["records"], dependency, target["declaration"])
                    if witness["status"] == "COMPOSED":
                        result["composition_witnesses"].append(witness)
    _write(output_dir / "branch-evidence.json", result)
    return result


def audit_frozen_branch(repo: Path, output_dir: Path, physlib_root: Path | None = None) -> dict:
    """Compile the exact frozen bytes, then compile and audit the actual bridge."""
    repo, output_dir = Path(repo).resolve(), Path(output_dir).resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("Use a fresh output directory; preserve earlier run evidence")
    output_dir.mkdir(parents=True, exist_ok=True)
    library = Path(physlib_root or repo.parent / "physlib").resolve()
    frozen = repo / "schema v0.3/lean/frozen/AnticommutingWitness.lean"
    build = _execute(["lake", "env", "lean", "-R", str(frozen.parent), "-o",
                      str(output_dir / "AnticommutingWitness.olean"), str(frozen)], library,
                     output_dir / "frozen-build.log", "lean.compile_frozen_user_source", _sha(frozen.read_bytes()))
    _write(output_dir / "frozen-build-receipt.json", build)
    if build["status"] != "SUCCEEDED":
        result = {"state": "CHAIN_INCOMPLETE", "execution_status": "BUILD_FAILED", "receipt": build}
        _write(output_dir / "branch-evidence.json", result)
        return result
    extra = (repo / "schema v0.3/lean/AnticommutingNonvacuity.lean").read_text()
    extra = "\n".join(line for line in extra.splitlines() if not line.startswith("import "))
    template = (repo / "schema v0.3/lean/EnvironmentAudit.lean").read_text()
    source = ("import AnticommutingWitness\nimport Physlib.Relativity.PauliMatrices.Basic\n"
              "import Mathlib.Combinatorics.SimpleGraph.Clique\n" + template + "\n" + extra + "\n")
    source += "\n".join("#agtxiv_audit " + name for name in DECLARATIONS) + "\n"
    script = output_dir / "CandidateAudit.lean"
    script.write_text(source)
    receipt = _execute(["env", "LEAN_PATH=" + str(output_dir), "lake", "env", "lean", "-R",
                        str(output_dir), "-o", str(output_dir / "CandidateAudit.olean"), str(script)],
                       library, output_dir / "candidate-audit.log", "lean.frozen_physlib_candidate_audit",
                       _sha(script.read_bytes()))
    _write(output_dir / "audit-receipt.json", receipt)
    return summarize_branch(repo, output_dir, receipt, physlib_root=library)
