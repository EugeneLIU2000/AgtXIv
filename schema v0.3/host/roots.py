"""Candidate root bindings against a freshly audited environment, before proof funding."""
from __future__ import annotations

import re

CANDIDATE_BINDINGS = {
    "claim:perfect-graph-definition": ["AgtXIv.GraphFoundation.IsPerfect"],
    "claim:mwis-definition": ["AgtXIv.GraphFoundation.maxWeightIndependent"],
    "root:gottesman-stabilizer-formalism": [
        "AgtXIv.Stabilizer.IndependentSignedPauliFrame.finrank_commonFixed_eq_two_pow_sub",
        "AgtXIv.Stabilizer.stabilizerProjectorMatrix_range_finrank_one"],
    "root:howard-campbell-rom": ["AgtXIv.Stabilizer.fullStabilizerRoM_eq_one_iff_free",
                               "AgtXIv.Stabilizer.StabilizerAtomMap.fullStabilizerRoM_mono"],
    "root:veitch-stabilizer-resource-theory": ["AgtXIv.Stabilizer.pureStabilizerByFrame_iff_byCliffordOrbit",
                                             "AgtXIv.Stabilizer.stabilizerPolytopeByFrames_eq_byCliffordOrbit"],
    "root:varela-reduced-polytope": ["AgtXIv.Varela.reducedStabilizerPolytope_vrep_conditional"],
    "root:perfect-graph-weighted-duality": ["AgtXIv.GraphFoundation.WeightedPerfectGraphFoundation"],
}


def audit_roots(graph, lean_evidence):
    declarations = {d["declaration"]: d for d in lean_evidence.get("records", [])}
    nodes = {n["id"]: n for n in graph["nodes"]}
    result = []
    for root in graph["roots"]:
        node = nodes[root["id"]]
        bindings = []
        for name in CANDIDATE_BINDINGS.get(node["id"], []):
            record = declarations.get(name)
            if not record or not record.get("kernel_checked"):
                continue
            is_premise = name.endswith(".WeightedPerfectGraphFoundation")
            bindings.append({"library": "AgtXIv-local-case-foundation", "revision": record["environment_sha256"],
                             "declaration": name, "kind": record["kind"], "type": record["type"],
                             "role": "EXPLICIT_UNPROVED_PREMISE" if is_premise else "CANDIDATE_SOURCE_BINDING",
                             "hypotheses": record["non_instance_prop_hypotheses"],
                             "structure_hypotheses": record["structure_prop_hypotheses"],
                             "statement_alignment": "AGENT_NORMALIZED_UNREVIEWED", "receipt": record["receipt"]})
        result.append({"node_id": node["id"], "source_spans": node.get("source_spans", []),
                       "outcome": "BINDING_CANDIDATE_UNREVIEWED" if bindings else "COVERAGE_UNDETERMINED",
                       "bindings": bindings, "proof_funding_gate": "AWAITING_REVIEW",
                       "reason": "An elaborated local declaration is not a checked judgement of source coverage."
                                 if bindings else "No audited candidate binding in the current registry; no universal library-absence claim.",
                       "upstream_search": root["upstream_search"]})
    return {"scope": graph["scope"], "roots": result, "library_search_exhausted": False,
            "requested_library_epochs": lean_evidence.get("requested_library_audits", []),
            "status": "CANDIDATE_BINDING_AUDIT_ONLY"}


def junk_value_lint(source, *, requires_finite=False):
    """Conservative source alerts, never a proof of definedness or a pass badge."""
    findings = []
    for index, line in enumerate(source.splitlines(), 1):
        if re.search(r"\b(sSup|sInf)\b", line):
            findings.append({"line": index, "code": "EXTREMUM_DOMAIN_OBLIGATIONS",
                             "obligation": "Record nonempty and bounded set evidence, or explain the explicit junk-value convention."})
        if "chromaticNumber" in line and "cliqueNum" in line:
            findings.append({"line": index, "code": "NAT_ENAT_DOMAIN_REVIEW",
                             "obligation": "Check finiteness and the coercion between Nat and extended Nat."})
    if requires_finite and not re.search(r"\[(?:Fintype|Finite)\s", source):
        findings.append({"line": None, "code": "FINITE_DOMAIN_BINDER_MISSING",
                         "obligation": "The source requires a finite domain; the candidate signature lacks an explicit finite-domain instance."})
    return {"findings": findings, "analysis": "CONSERVATIVE_STATIC_LINT", "definedness_proved": False}
