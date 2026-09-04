from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[1]
CHARTER_ID = "AgtXIv-Charter/1.0"
ADOPTION_BASE = "c2b6bddd85a07e4903c10bed6bbef8f23256b772"
ADR = REPO / "docs/adr/0007-adopt-project-charter.md"
CONFORMANCE = REPO / "docs/governance/v2-charter-conformance.md"
ADOPTION_CHANGESET = {
    "CHARTER.md",
    "GOVERNANCE.md",
    "README.md",
    "AgtXIv.md",
    "docs/adr/0007-adopt-project-charter.md",
    "docs/governance/v2-charter-conformance.md",
    "docs/specifications/v2-paper-agentization.md",
    "tests/test_charter_governance.py",
}


def read(relative_path: str) -> str:
    return (REPO / relative_path).read_text(encoding="utf-8")


def normalized(text: str) -> str:
    return " ".join(text.casefold().split())


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def tree_entries(repo: Path, revision: str) -> dict[str, tuple[str, str, str]]:
    output = subprocess.run(
        ["git", "ls-tree", "-rz", "--full-tree", revision],
        cwd=repo,
        check=True,
        capture_output=True,
    ).stdout
    entries: dict[str, tuple[str, str, str]] = {}
    for record in output.split(b"\0"):
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", 1)
        mode, object_type, object_id = metadata.decode("ascii").split()
        entries[raw_path.decode("utf-8")] = (mode, object_type, object_id)
    return entries


def validate_tree_entry_manifest(
    repo: Path,
    base_revision: str,
    target_revision: str,
    manifest: dict[
        str,
        tuple[tuple[str, str, str] | None, tuple[str, str, str] | None],
    ],
) -> None:
    base_entries = tree_entries(repo, base_revision)
    target_entries = tree_entries(repo, target_revision)
    changed_paths = {
        path
        for path in base_entries.keys() | target_entries.keys()
        if base_entries.get(path) != target_entries.get(path)
    }
    assert changed_paths == manifest.keys(), "changed path set does not match manifest"
    for path, (expected_base, expected_target) in manifest.items():
        assert base_entries.get(path) == expected_base, f"wrong base entry for {path}"
        assert target_entries.get(path) == expected_target, f"wrong target entry for {path}"


def section(document: str, heading: str) -> str:
    lines = document.splitlines()
    heading_pattern = re.compile(rf"^(#+)\s+{re.escape(heading)}\s*$", re.IGNORECASE)
    for index, line in enumerate(lines):
        match = heading_pattern.match(line)
        if not match:
            continue
        level = len(match.group(1))
        end = len(lines)
        for candidate in range(index + 1, len(lines)):
            next_heading = re.match(r"^(#+)\s+", lines[candidate])
            if next_heading and len(next_heading.group(1)) <= level:
                end = candidate
                break
        return "\n".join(lines[index + 1 : end])
    raise AssertionError(f"missing section: {heading}")


def metadata_value(document: str, label: str) -> str:
    match = re.search(
        rf"(?im)^\s*(?:[-*]\s+)?(?:\*\*)?{re.escape(label)}:(?:\*\*)?\s*(.+?)\s*$",
        document,
    )
    assert match, f"missing metadata field: {label}"
    return normalized(match.group(1))


def test_pending_metadata_and_adr_define_authorized_ratification() -> None:
    charter_path = REPO / "CHARTER.md"
    assert charter_path.is_file()
    charter = charter_path.read_text(encoding="utf-8")
    assert metadata_value(charter, "Ratification state").startswith("pending")
    assert "unless and until the qualifying ratification commit exists" in metadata_value(
        charter, "Ratification state"
    )
    assert metadata_value(charter, "Canonical document identity") == f"`{CHARTER_ID.casefold()}`"

    stable_record = metadata_value(charter, "Stable adoption record")
    effective_date = metadata_value(charter, "Effective date")
    assert "unavailable while pending" in stable_record
    assert "full git object id" in stable_record
    assert "qualifying ratification commit" in stable_record
    assert "unavailable while pending" in effective_date
    assert "git committer timestamp" in effective_date

    preamble = normalized(charter.split("\n## ", 1)[0])
    assert re.search(r"proposed.*before the qualifying ratification commit", preamble)
    assert re.search(
        r"`?adopted`? only in canonical authoritative `main` history.*at or after that commit",
        preamble,
    )
    assert "project-authority approval and relevant specialist reviews" in preamble
    assert "must independently bind the exact combined change" in preamble
    assert "copied status labels have no constitutional effect" in preamble

    assert ADR.is_file()
    adr = ADR.read_text(encoding="utf-8")
    assert metadata_value(adr, "Decision status").startswith("proposed")
    assert "accepted only when the qualifying ratification commit" in metadata_value(
        adr, "Decision status"
    )
    assert metadata_value(adr, "Implementation status").startswith("pending ratification")
    assert "not currently effective" in metadata_value(adr, "Implementation status")
    assert "unavailable while pending" in metadata_value(adr, "Stable adoption record")
    assert "full git object id" in metadata_value(adr, "Stable adoption record")
    assert "unavailable while pending" in metadata_value(adr, "Effective date")
    assert "committer timestamp" in metadata_value(adr, "Effective date")

    context = normalized(section(adr, "Context"))
    assert "does not invent a pull-request number" in context
    assert "reviewer identity" in context
    assert "signature" in context
    assert "approval record" in context

    decision = normalized(section(adr, "Decision"))
    assert f"proposes to adopt [`charter.md`](../../charter.md) with canonical identity `{CHARTER_ID.casefold()}`" in decision
    assert "existing `governance.md` procedure" in decision
    assert "project-maintainer or repository-authority approval" in decision
    assert "every relevant specialist review" in decision
    assert "exact combined change" in decision
    assert re.search(r"absent.*proposed or pending.*no constitutional effect", decision)
    assert "regardless of an `adopted` or `accepted` label" in decision

    ratification_source = section(adr, "Ratification and effective-time rule")
    ratification = normalized(ratification_source)
    declared_changeset = set(
        re.findall(r"(?m)^\d+\. `([^`]+)`\s*$", ratification_source)
    )
    assert declared_changeset == ADOPTION_CHANGESET
    assert "complete reviewed governance unit" in ratification
    assert "these eight paths, and no others" in ratification

    full_object_ids = set(re.findall(r"(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])", ratification))
    assert full_object_ids == {ADOPTION_BASE}
    assert f"exact base is full commit `{ADOPTION_BASE}`" in ratification
    assert "exact eight-path set above" in ratification
    assert "exact base and proposed target path entry" in ratification
    assert "explicit absence" in ratification
    assert "`(git tree-entry mode, git object type, full object id)`" in ratification
    assert "isolated review candidate commit" in ratification
    assert "sole parent is that exact base" in ratification
    assert "first-parent changed-path set is exactly those eight paths" in ratification
    assert "parent and resulting trees supply those exact tuples" in ratification
    for ambiguous_identity in (
        "path-only diff",
        "branch name",
        "abbreviated commit id",
        "mutable pull-request head",
        "blob-only identity",
        "aggregate prose description",
    ):
        assert ambiguous_identity in ratification

    assert "no target blob ids or review-candidate id are asserted" in ratification
    assert "after the eight files reach their final bytes" in ratification
    assert "candidate's full git object id or the equivalent complete manifest" in ratification
    assert re.search(
        r"every relevant specialist review required by `governance.md` must bind that same exact proposal",
        ratification,
    )
    assert "complete before final project-authority approval" in ratification
    assert re.search(
        r"public approval by the project maintainer or formally delegated repository authority must occur after those reviews",
        ratification,
    )
    assert "bind that same exact proposal" in ratification

    assert "pre-integration review candidate commit only identifies proposed bytes" in ratification
    assert "must not itself be the qualifying ratification commit" in ratification
    assert "dedicated **post-approval qualifying ratification commit**" in ratification
    assert "apply exactly the reviewed delta to canonical authoritative `main`" in ratification
    assert "no unrelated work-in-progress" in ratification
    assert "non-retrospective" in ratification
    assert "constitutional effect at an earlier time" in ratification

    assert "designate its git first parent" in ratification
    assert "first parent recorded in the commit object" in ratification
    assert "by full object id" in ratification
    assert "complete changed-path set, determined from any difference in absence, tree-entry mode, object type, or object id" in ratification
    assert "must be exactly the eight paths above and no others" in ratification
    assert "first-parent entry must equal its reviewed base entry" in ratification
    assert "including explicit absence" in ratification
    assert "resulting entry must equal its reviewed target entry" in ratification
    assert "every entry outside the reviewed path set must remain unchanged" in ratification
    assert "mode-only or type-only mutation is therefore rejected" in ratification
    assert "even when a blob object id is unchanged" in ratification
    assert "base-to-target tree delta exactly" in ratification
    assert "for a merge commit, only its designated git first parent defines the qualifying delta" in ratification
    assert "second or later parent cannot supply, replace, or obscure that delta" in ratification
    assert "merge qualifies only if the same first-parent path-entry tuple checks pass" in ratification
    assert "squash, rebase, cherry-pick, or non-merge integration" in ratification
    assert "new, dedicated post-approval commit" in ratification
    assert "avoids circularity" in ratification

    assert "reachable from canonical `main`" in ratification
    assert "a local or feature-branch commit is not enough" in ratification
    assert "are not authorization evidence" in ratification
    assert "predates approval" in ratification
    assert "reuses the review candidate as the integration commit" in ratification
    assert re.search(r"once such a dedicated post-approval commit exists.*adr is accepted.*charter is adopted", ratification)
    assert "stable adoption record is that commit's full git object id" in ratification
    assert "git **committer timestamp**" in ratification
    assert "not its author timestamp, candidate timestamp, review time" in ratification
    assert "must be later than the recorded final approval time" in ratification
    assert "asserts no candidate manifest, pull request, review, approval, integration, or qualifying commit" in ratification
    assert "remains pending rather than effective" in ratification


def test_tree_entry_manifest_rejects_unreviewed_mode_only_mutation(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "manifest-repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Charter Test")
    git(repo, "config", "user.email", "charter-test@example.invalid")
    git(repo, "config", "core.fileMode", "true")

    reviewed_path = repo / "reviewed.md"
    unchanged_path = repo / "unchanged.sh"
    reviewed_path.write_text("base\n", encoding="utf-8")
    unchanged_path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    unchanged_path.chmod(0o644)
    git(repo, "add", "reviewed.md", "unchanged.sh")
    git(repo, "commit", "-qm", "base")
    base_commit = git(repo, "rev-parse", "HEAD")
    base_entries = tree_entries(repo, base_commit)

    reviewed_path.write_text("reviewed target\n", encoding="utf-8")
    git(repo, "add", "reviewed.md")
    git(repo, "commit", "-qm", "review candidate")
    candidate_commit = git(repo, "rev-parse", "HEAD")
    candidate_entries = tree_entries(repo, candidate_commit)
    manifest = {
        "reviewed.md": (
            base_entries["reviewed.md"],
            candidate_entries["reviewed.md"],
        )
    }
    validate_tree_entry_manifest(repo, base_commit, candidate_commit, manifest)

    git(repo, "checkout", "-q", "--detach", base_commit)
    reviewed_path.write_text("reviewed target\n", encoding="utf-8")
    unchanged_path.chmod(0o755)
    git(repo, "add", "reviewed.md", "unchanged.sh")
    git(repo, "commit", "-qm", "integration with unreviewed mode change")
    integration_commit = git(repo, "rev-parse", "HEAD")
    integration_entries = tree_entries(repo, integration_commit)

    assert base_entries["unchanged.sh"][2] == integration_entries["unchanged.sh"][2]
    assert base_entries["unchanged.sh"][0] == "100644"
    assert integration_entries["unchanged.sh"][0] == "100755"
    with pytest.raises(AssertionError, match="changed path set does not match manifest"):
        validate_tree_entry_manifest(repo, base_commit, integration_commit, manifest)


def test_charter_defines_amendment_and_conditional_history_rules() -> None:
    charter = read("CHARTER.md")
    amendment = normalized(section(charter, "Amendment Procedure"))
    for required in (
        "pull request",
        "public rationale",
        "constitutional principle and version responsibility affected",
        "project maintainer or repository authority",
        "relevant scientific, contract, security, rights, or governance specialist",
        "explicit, publicly recorded approval",
        "new charter version",
        "effective date",
        "immutable, addressable git history",
        "never amends this charter",
    ):
        assert required in amendment
    assert "exact bytes of the proposed change" in amendment
    assert re.search(r"each required review binding the exact proposed bytes", amendment)
    assert re.search(r"approval binding the same exact proposed bytes", amendment)
    assert "exact full base commit id" in amendment
    assert "complete proposed path set" in amendment
    assert "exact base and target entries" in amendment
    assert "explicit absence or the tuple `(git tree-entry mode, git object type, full object id)`" in amendment
    assert "equivalent base-tree/target-tree formulation" in amendment
    assert "path list without exact entry tuples, blob-only identity" in amendment
    assert "recording the later qualifying commit is not part of the reviewed bytes" in amendment
    assert "no circularity" in amendment
    assert "dedicated post-approval qualifying amendment commit" in amendment
    assert "pre-integration review candidate must not itself be that qualifying commit" in amendment
    assert "integrated into canonical authoritative `main`" in amendment
    assert "after all required exact-change reviews and approval" in amendment
    assert "designate the qualifying commit's git first parent by full object id" in amendment
    assert "change exactly the reviewed path set and no other path" in amendment
    assert "any difference in absence, tree-entry mode, object type, or object id" in amendment
    assert "designated first-parent entry and every resulting entry must match its reviewed base or target tuple or explicit absence" in amendment
    assert "every entry outside the reviewed path set must remain unchanged" in amendment
    assert "mode-only or type-only mutation must be rejected even when the blob object id is unchanged" in amendment
    assert "if the qualifying commit is a merge, only its git first parent defines this delta" in amendment
    assert "no second or later parent may supply or obscure it" in amendment
    assert "squash, rebase, cherry-pick, or non-merge integration" in amendment
    assert "new, dedicated post-approval commit" in amendment
    assert "stable amendment record is that dedicated commit's full git object id" in amendment
    assert "git committer timestamp" in amendment
    assert "must be later than the recorded final approval time" in amendment
    assert "neither candidate creation nor later approval gives the amendment retrospective effect" in amendment
    assert re.search(r"version label, status label, stated date.*has no constitutional effect", amendment)
    assert "cannot make an amendment self-ratifying" in amendment

    editorial = amendment[amendment.index("an editorial correction") :]
    assert "does not change normative meaning" in editorial
    assert "proportionate to that meaning-preserving scope" in editorial
    assert "all relevant reviews" in editorial
    assert re.search(
        r"all relevant reviews and explicit .* approval must bind its exact full-base, path-set, and base/target entry tuples or explicit absences",
        editorial,
    )
    assert "its own dedicated post-approval qualifying amendment commit" in editorial
    assert "same first-parent, merge-handling, exact-entry, unchanged-other-entry, canonical-integration, stable-record, non-retrospective committer-timestamp rules" in editorial
    assert "mode-only or type-only mutation with an unchanged blob object id remains disqualifying" in editorial
    assert "pre-integration editorial review candidate can never itself qualify" in editorial

    history = normalized(section(charter, "Historical Applicability"))
    assert history.startswith("once adopted")
    assert "applies prospectively from the qualifying ratification commit's effective date" in history
    assert "created before that commit remains interpreted under the exact contracts" in history
    for prohibited_change in ("rewrite", "promote", "reclassify", "invalidate"):
        assert prohibited_change in history
    assert "new, separately attributable conformance assessment" in history
    assert "claim of charter conformance made at or after adoption" in history
    assert "qualifying ratification commit's full git object id" in history
    assert "if no such binding or citation exists, charter conformance must not be inferred" in history


def test_required_documents_keep_charter_authority_conditional_on_ratification() -> None:
    readme = read("README.md")
    start_here = section(readme, "Start here")
    assert start_here.index("](CHARTER.md)") < start_here.index("](AgtXIv.md)")
    assert "docs/adr/0007-adopt-project-charter.md" in start_here
    assert "only unversioned canonical system specification" not in readme.casefold()
    agtxiv_row = next(line for line in start_here.splitlines() if "](AgtXIv.md)" in line)
    normalized_row = normalized(agtxiv_row)
    assert "subordinate to the charter and applicable version specifications" not in normalized_row
    assert "subordinate to an adopted charter only after ratification" in normalized_row

    documents = {
        "README.md": readme,
        "GOVERNANCE.md": read("GOVERNANCE.md"),
        "AgtXIv.md": read("AgtXIv.md"),
        "V2 specification": read("docs/specifications/v2-paper-agentization.md"),
    }
    for name, document in documents.items():
        text = normalized(document)
        assert "charter" in text, name
        assert re.search(r"\b(pending|proposed)\b", text), name
        assert re.search(
            r"(only (after|when|upon).{0,80}ratification|only upon.{0,80}commit|if (the )?charter is ratified)",
            text,
        ), name
        assert "version specifications and governance" in text, name
        assert "adrs, contracts, schemas, and plans" in text, name
        assert "implementation" in text, name


def test_adoption_does_not_modify_the_checkpoint_e_roadmap_source() -> None:
    roadmap_path = "docs/roadmaps/v2-end-to-end-implementation-plan.md"
    expected = subprocess.run(
        ["git", "show", f"{ADOPTION_BASE}:{roadmap_path}"],
        cwd=REPO,
        check=True,
        capture_output=True,
    ).stdout
    assert (REPO / roadmap_path).read_bytes() == expected


def test_v2_conformance_remains_prospective_without_status_promotion() -> None:
    assert CONFORMANCE.is_file()
    conformance = CONFORMANCE.read_text(encoding="utf-8")
    assert CHARTER_ID in conformance
    status = metadata_value(conformance, "Status")
    assert status.startswith("prospective pre-adoption")
    assert "remains prospective after adoption" in status
    assert "never automatically operative" in status
    assert "not a production certificate" in status

    introduction = normalized(conformance.split("\n## ", 1)[0])
    assert "would relate to the proposed charter if adr 0007 is ratified" in introduction
    assert "does not promote a fixture, candidate, release, assessment, or knowledge entry" in introduction
    assert "only after the qualifying canonical-`main` ratification commit exists" in introduction
    assert "predates adoption" in introduction
    assert "cannot bind the qualifying commit's then-unknown stable adoption record" in introduction
    assert "remains prospective even after adoption" in introduction
    assert "never automatically acquires operative charter-conformance authority" in introduction

    machine_conflict = normalized(
        section(conformance, "Machine-contract conflict and its authority boundary")
    )
    assert "`assessmentrecord/2.0.0`" in machine_conflict
    assert "`knowledgeindexsnapshot`" in machine_conflict
    assert re.search(
        r"three aggregate axes.*rather than.*six separately applicable charter axes",
        machine_conflict,
    )
    assert not re.search(r"six .*rather than.*three", machine_conflict)
    assert "pre-charter and non-conforming for any post-adoption claim of full charter conformance" in machine_conflict
    assert re.search(
        r"nor may it imply broader release recommendation, certification, archival, scientific acceptance, knowledge admission",
        machine_conflict,
    )

    principles = normalized(section(conformance, "Constitutional Principles"))
    assert re.search(
        r"7 \| contribution as a traceable knowledge delta \| \*\*deferred\*\*",
        principles,
    )

    checkpoint = normalized(section(conformance, "Checkpoint E and future contract bundles"))
    for required in (
        "prospective charter-conformance assessment is partial",
        "proposed",
        "incomplete",
        "non-production",
        "candidate-only",
        "does not alter that lifecycle status",
    ):
        assert required in checkpoint
    assert re.search(
        r"does not .*establish production release, certification, archive, admission",
        checkpoint,
    )
    assert "must not be repaired, regenerated, or rewritten" in checkpoint

    decision = normalized(section(conformance, "Conformance decision"))
    assert "against the proposed charter" in decision
    assert "prospectively **partial with a recorded conflict**" in decision
    assert "before ratification it has no operative charter-conformance status" in decision
    assert "ratification does not activate this assessment" in decision
    assert "remains prospective after adoption" in decision
    assert "new, separately attributable post-adoption assessment" in decision
    assert CHARTER_ID.casefold() in decision
    assert "qualifying ratification commit's full git object id" in decision
    assert re.search(r"operative conformance claim requires.*binds or cites both", decision)
    assert "after ratification it may claim implementation" not in decision
    assert "even such a new assessment must not claim full conformance" in decision
    assert "six-axis machine-contract conflict" in decision
    assert "other applicable deferred responsibilities" in decision
    assert "charter adoption itself changes no historical record or pre-adoption assessment status" in decision
