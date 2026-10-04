"""Conservative reporting for candidate clause mappings, never semantic acceptance."""


def candidate_clause_status(bindings: list[dict]) -> str:
    if not any("clause_coverage" in binding for binding in bindings):
        return "UNRECORDED"
    # A mixture of mapped and unmapped declarations is not whole-node coverage.
    if any("clause_coverage" not in binding for binding in bindings):
        return "INCOMPLETE"
    for binding in bindings:
        rows = binding["clause_coverage"]
        if not isinstance(rows, list) or not rows:
            return "INCOMPLETE"
        seen = set()
        for row in rows:
            if not isinstance(row, dict):
                return "MALFORMED"
            clause_id = row.get("clause_id")
            if not isinstance(clause_id, str) or not clause_id.strip() or clause_id in seen:
                return "MALFORMED"
            seen.add(clause_id)
            if (not isinstance(row.get("statement"), str) or not row["statement"].strip() or
                    not isinstance(row.get("source_spans"), list) or not row["source_spans"] or
                    not isinstance(row.get("remaining_obligations"), list)):
                return "MALFORMED"
            relation = row.get("relation")
            if relation not in {"CANDIDATE_EQUIVALENT", "PARTIAL", "STRONGER", "WEAKER", "UNRESOLVED"}:
                return "MALFORMED"
            if relation != "CANDIDATE_EQUIVALENT" or row["remaining_obligations"]:
                return "INCOMPLETE"
    # Even all mapped rows lack evidence that the clause inventory is exhaustive.
    return "MAPPED_INVENTORY_UNREVIEWED"
