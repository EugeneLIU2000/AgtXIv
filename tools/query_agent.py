#!/usr/bin/env python3
"""Query the static AgtXIv pilot without filling scientific gaps with prose."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class Bundle:
    def __init__(self) -> None:
        self.statements: dict[str, dict[str, Any]] = {}
        self.anchors: dict[str, dict[str, Any]] = {}
        self.steps: dict[str, dict[str, Any]] = {}
        self.verifications: dict[str, dict[str, Any]] = {}
        self.contracts: dict[str, dict[str, Any]] = {}
        self.blockers: dict[str, dict[str, Any]] = {}
        self.foundations: dict[str, dict[str, Any]] = {}
        for path in REPO.glob("agents/*/knowledge/statements.jsonl"):
            self.statements.update((r["id"], r) for r in read_jsonl(path))
        for path in REPO.glob("agents/*/source/anchors.jsonl"):
            self.anchors.update((r["id"], r) for r in read_jsonl(path))
        for path in REPO.glob("agents/*/reasoning/chains.jsonl"):
            self.steps.update((r["id"], r) for r in read_jsonl(path))
        for path in REPO.glob("agents/*/verification/records.jsonl"):
            self.verifications.update((r["id"], r) for r in read_jsonl(path))
        for path in REPO.glob("agents/*/exports/*.json"):
            record = read_json(path)
            self.contracts[record["id"]] = record
        for path in REPO.glob("agents/*/blockers/*.json"):
            record = read_json(path)
            self.blockers[record["id"]] = record
        for path in REPO.glob("foundations/*.json"):
            record = read_json(path)
            self.foundations[record["statement_id"]] = record
        self.claims = self.statements | self.foundations
        self.producers: dict[str, list[dict[str, Any]]] = {}
        for step in self.steps.values():
            for output in step.get("outputs", []):
                self.producers.setdefault(output, []).append(step)
        self.contract_by_statement = {c["statement"]: c for c in self.contracts.values()}

    def basis(self, claim_id: str) -> str:
        contract = self.contract_by_statement.get(claim_id)
        if contract and contract.get("accepted") is not True:
            return "BLOCKED"
        producers = self.producers.get(claim_id, [])
        if any(step.get("status") == "BLOCKED" for step in producers):
            return "BLOCKED"
        if producers:
            return "DERIVED_FROM_ACCEPTED_CHAIN"
        if claim_id in self.foundations:
            foundation = self.foundations[claim_id]
            return "IMPORTED_CONTRACT" if foundation.get("source_fidelity") != "UNCHECKED" else "BLOCKED"
        origin = self.statements.get(claim_id, {}).get("origin", "")
        if origin.startswith("SOURCE_"):
            return "DIRECT_SOURCE"
        if origin == "COMPUTATIONALLY_REPRODUCED":
            return "DERIVED_FROM_ACCEPTED_CHAIN"
        return "UNVERIFIED_INFERENCE"

    def trace(self, claim_id: str) -> dict[str, Any]:
        if claim_id not in self.claims:
            raise KeyError(claim_id)
        seen: set[str] = set()
        ordered_claims: list[str] = []
        ordered_steps: list[dict[str, Any]] = []

        def visit(current: str) -> None:
            if current in seen:
                return
            seen.add(current)
            for step in self.producers.get(current, []):
                for premise in step.get("inputs", []):
                    visit(premise)
                ordered_steps.append(step)
            ordered_claims.append(current)

        visit(claim_id)
        assumptions = sorted(
            {assumption for step in ordered_steps for assumption in step.get("active_assumptions", [])}
            | set(self.statements.get(claim_id, {}).get("logical_form", {}).get("hypotheses", []))
        )
        relevant_contracts = [
            contract for statement in ordered_claims
            if (contract := self.contract_by_statement.get(statement)) is not None
        ]
        blocker_ids: list[str] = []
        affected = {claim_id, *(contract["id"] for contract in relevant_contracts)}
        for blocker_id, blocker in self.blockers.items():
            if affected.intersection(blocker.get("affects", [])):
                blocker_ids.append(blocker_id)
        for contract in relevant_contracts:
            blocker_ids.extend(contract.get("blockers", []))
            for imported in contract.get("imports", []):
                if not isinstance(imported, dict) or imported.get("status") != "BLOCKED":
                    continue
                imported_id = imported.get("contract")
                imported_contract = self.contracts.get(imported_id, {})
                imported_statement = imported_contract.get("statement")
                for blocker_id, blocker in self.blockers.items():
                    if imported_id in blocker.get("affects", []) or imported_statement in blocker.get("affects", []):
                        blocker_ids.append(blocker_id)
        blocker_ids = list(dict.fromkeys(blocker_ids))
        return {
            "basis": "BLOCKED" if blocker_ids or any(s.get("status") == "BLOCKED" for s in ordered_steps) else self.basis(claim_id),
            "claim": self.claims[claim_id],
            "dependency_claims": ordered_claims,
            "reasoning_steps": ordered_steps,
            "active_assumptions": assumptions,
            "earliest_blockers": [self.blockers[b] for b in blocker_ids if b in self.blockers],
        }


def source_response(bundle: Bundle, claim_id: str) -> dict[str, Any]:
    claim = bundle.claims.get(claim_id)
    if claim is None:
        raise KeyError(claim_id)
    records = []
    for anchor_id in claim.get("source_anchors", []):
        anchor = bundle.anchors[anchor_id]
        location = anchor["location"]
        path = REPO / anchor["artifact"]
        start, end = location.get("line_start"), location.get("line_end")
        excerpt = None
        if isinstance(start, int) and isinstance(end, int):
            excerpt = "".join(path.read_text(encoding="utf-8").splitlines(keepends=True)[start - 1 : end])
        records.append({"anchor": anchor, "excerpt": excerpt})
    return {"basis": bundle.basis(claim_id), "claim": claim_id, "sources": records}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=[
        "claims", "why", "source", "assumptions", "dependencies",
        "verification", "blockers", "exports",
    ])
    parser.add_argument("claim", nargs="?")
    args = parser.parse_args()
    bundle = Bundle()
    if args.command in {"why", "source", "assumptions", "dependencies", "verification"} and not args.claim:
        parser.error(f"{args.command} requires a claim id")
    try:
        if args.command == "claims":
            result = [
                {"id": claim_id, "kind": record.get("kind"), "basis": bundle.basis(claim_id), "text": record.get("text") or record.get("statement")}
                for claim_id, record in sorted(bundle.claims.items())
            ]
        elif args.command == "why":
            result = bundle.trace(args.claim)
        elif args.command == "source":
            result = source_response(bundle, args.claim)
        elif args.command == "assumptions":
            trace = bundle.trace(args.claim)
            result = {"basis": trace["basis"], "claim": args.claim, "active_assumptions": trace["active_assumptions"]}
        elif args.command == "dependencies":
            trace = bundle.trace(args.claim)
            result = {"basis": trace["basis"], "claim": args.claim, "claims": trace["dependency_claims"], "steps": [s["id"] for s in trace["reasoning_steps"]]}
        elif args.command == "verification":
            trace = bundle.trace(args.claim)
            ids = list(dict.fromkeys(v for step in trace["reasoning_steps"] for v in step.get("verification_records", [])))
            result = {"basis": trace["basis"], "claim": args.claim, "records": [bundle.verifications[v] for v in ids if v in bundle.verifications]}
        elif args.command == "blockers":
            result = {"basis": "BLOCKED" if bundle.blockers else "DIRECT_SOURCE", "open": [b for b in bundle.blockers.values() if b.get("status") == "OPEN"]}
        else:
            result = [
                {"basis": "IMPORTED_CONTRACT" if c.get("accepted") else "BLOCKED", **c}
                for c in bundle.contracts.values()
            ]
    except KeyError as exc:
        print(json.dumps({"basis": "BLOCKED", "error": f"unknown claim: {exc.args[0]}"}, indent=2))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
