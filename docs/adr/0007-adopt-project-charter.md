# ADR 0007: Adopt the AgtXIv project Charter

- Decision status: Proposed; accepted only when the qualifying ratification commit defined below exists
- Implementation status: Pending ratification; not currently effective
- Milestone: Project governance
- Charter identity: `AgtXIv-Charter/1.0`
- Canonical repository: `https://github.com/EugeneLIU2000/AgtXIv`
- Authoritative branch: `main`
- Stable adoption record: unavailable while pending; after ratification, the qualifying commit's full Git object ID
- Effective date: unavailable while pending; after ratification, the qualifying commit's Git committer timestamp
- Governance authority: `GOVERNANCE.md`, especially its authority-boundary and amendment procedures

## Context

AgtXIv already has version specifications, governance rules, ADRs, schemas,
contracts, plans, and implementations with deliberately bounded authority. It
also has immutable historical records whose meanings depend on the exact
contracts and policies they bound. The project needs a stable highest-level
normative authority that states its mission and preserves source attribution,
separate verification axes, uncertainty, role boundaries, provenance-preserving
reuse, contribution deltas, and query-independent auditability across versions.

Without an adopted Charter, a subordinate version document or machine contract
could appear to redefine the project's purpose or collapse protected
verification distinctions. Conversely, retroactively rewriting existing records
to mention a new Charter would violate their immutable history and could imply
status or authority they never received.

Existing `GOVERNANCE.md` requires authority-boundary changes to use a pull
request, public rationale, code-owner review, relevant specialist review, and an
explicitly recorded decision. This ADR supplies the public rationale and impact
analysis for Charter adoption. It does not invent a pull-request number,
reviewer identity, signature, or approval record.

## Decision

AgtXIv proposes to adopt [`CHARTER.md`](../../CHARTER.md) with canonical
identity `AgtXIv-Charter/1.0` as its highest-level normative authority. If
ratified, the resulting hierarchy is:

1. the Charter;
2. version specifications and repository governance;
3. ADRs, contracts, schemas, and plans; and
4. implementations, fixtures, generated views, and operational outputs.

This proposed adoption follows the existing `GOVERNANCE.md` procedure for an
authority-boundary change. Required project-maintainer or repository-authority
approval and every relevant specialist review must independently bind the exact
combined change before it is integrated. If those authorization conditions are
absent, the change is proposed or pending and has no constitutional effect,
regardless of an `ADOPTED` or `Accepted` label in file content.

### Ratification and effective-time rule

The **exact adoption proposal** is the complete reviewed governance unit formed
by the changes to these eight paths, and no others:

1. `CHARTER.md`
2. `GOVERNANCE.md`
3. `README.md`
4. `AgtXIv.md`
5. `docs/adr/0007-adopt-project-charter.md`
6. `docs/governance/v2-charter-conformance.md`
7. `docs/specifications/v2-paper-agentization.md`
8. `tests/test_charter_governance.py`

The reviewed object MUST be mechanically identified by an immutable adoption
proposal manifest. For this adoption only, its exact base is full commit
`c2b6bddd85a07e4903c10bed6bbef8f23256b772`. The manifest MUST record that full
base object ID, the exact eight-path set above, and, for every listed path, its
exact base and proposed target path entry. Each side MUST be either explicit
absence or the tuple `(Git tree-entry mode, Git object type, full object ID)`.
Equivalently, an isolated review candidate commit may supply the manifest when
its sole parent is that exact base, its first-parent changed-path set is exactly
those eight paths, and its parent and resulting trees supply those exact tuples
for every path. Either form uniquely identifies both sides of the proposed
delta; a path-only diff, branch name, abbreviated commit ID, mutable pull-request
head, blob-only identity, or aggregate prose description does not.

No target blob IDs or review-candidate ID are asserted while this working tree is
still changing. After the eight files reach their final bytes, an isolated
candidate and manifest may be generated without changing those bytes. Required
reviews and approval then bind that immutable candidate's full Git object ID or
the equivalent complete manifest. Before canonical integration:

1. every relevant specialist review required by `GOVERNANCE.md` MUST bind that
   same exact proposal and be complete before final project-authority approval;
2. a public approval by the project maintainer or formally delegated repository
   authority MUST occur after those reviews and bind that same exact proposal;
   and
3. the immutable review and approval records MUST retain the full candidate or
   manifest identity and their times.

The pre-integration review candidate commit only identifies proposed bytes. It
MUST NOT itself be the qualifying ratification commit, even if later made
reachable from `main`. After all required reviews and approval, a dedicated
**post-approval qualifying ratification commit** MUST apply exactly the reviewed
delta to canonical authoritative `main`, with no unrelated work-in-progress.
This ordering makes ratification non-retrospective: neither the candidate's
creation nor a later approval can confer constitutional effect at an earlier
time.

The qualifying commit's integration evidence MUST designate its Git first parent
(the first parent recorded in the commit object) by full object ID. Against that
designated first parent:

- the complete changed-path set, determined from any difference in absence,
  tree-entry mode, object type, or object ID, MUST be exactly the eight paths
  above and no others;
- each listed path's first-parent entry MUST equal its reviewed base entry,
  including explicit absence; and
- each listed path's resulting entry MUST equal its reviewed target entry.

Every entry outside the reviewed path set MUST remain unchanged as the same
exact tuple or absence. A mode-only or type-only mutation is therefore rejected,
even when a blob object ID is unchanged. These checks make the qualifying commit
apply the reviewed base-to-target tree delta exactly, rather than merely arrive
at byte-identical file contents or a similar description. For a merge commit,
only its designated Git first parent defines the qualifying delta; a second or
later parent cannot supply, replace, or obscure that delta. A merge qualifies
only if the same first-parent path-entry tuple checks pass. A squash, rebase,
cherry-pick, or non-merge integration may qualify only through a new, dedicated
post-approval commit satisfying those same checks. This avoids circularity:
reviews bind the pre-integration manifest or candidate, while the later
qualifying commit is identified and tested against it.

The qualifying commit must be reachable from canonical `main`; a local or
feature-branch commit is not enough. File status labels, author or committer
identity, timestamps alone, and this ADR's own text are not authorization
evidence and cannot make a commit qualify. A commit that predates approval,
reuses the review candidate as the integration commit, changes another path, has
the wrong first-parent base blobs, or produces any unreviewed resulting blob does
not qualify.

Once such a dedicated post-approval commit exists, this ADR is accepted and the
Charter is adopted. The stable adoption record is that commit's full Git object
ID. The effective date is its Git **committer timestamp**, not its author
timestamp, candidate timestamp, review time, or a date inferred from surrounding
files; to prevent backdating, that committer timestamp MUST be later than the
recorded final approval time. The current working-tree proposal asserts only the
base identity above: it asserts no candidate manifest, pull request, review,
approval, integration, or qualifying commit, and remains pending rather than
effective.

## Affected-principle analysis

| Charter principle | Adoption effect | Compatibility and implementation consequence |
|---|---|---|
| 1. Exact and attributable sources | Establishes exact source attribution as constitutional. | Existing exact-source contracts remain usable. Historical records are not rewritten; future Charter-conformance claims bind or cite `AgtXIv-Charter/1.0`. |
| 2. Explicit reasoning and applicability | Makes load-bearing reasoning and applicability boundaries mandatory. | Existing bounded explanations remain bounded. Missing producer records stay unknown, blocked, deferred, or out of scope. |
| 3. Independent verification axes and no silent promotion | Constitutionally requires six separately applicable axes and forbids cross-axis promotion. | The current V2 three-axis machine-contract shape is recorded as a prospective conformance conflict; no schema is redesigned by this adoption. |
| 4. Preserve uncertainty, conflict, and bounded completeness | Protects unresolved and conflicting outcomes and scope-relative completion. | Existing immutable frontier, conflict, and mixed-disposition records retain their exact meanings. |
| 5. Auditable authority and non-self-certification | Places explicit authority and role separation above version implementations. | Existing Coordinator, Root Agent, Certifier, and reviewer boundaries remain bounded; adoption grants none of them broader authority. |
| 6. Provenance-preserving reuse and accumulation | Makes non-destructive, provenance-bearing reuse constitutional. | Existing exact references and append-only history are preserved; future accumulation mechanisms must retain their assumptions and limitations. |
| 7. Contribution as a traceable knowledge delta | Establishes the long-term contribution model. | Current V2 contribution-as-knowledge-delta remains deferred. Existing experimental contribution records are not promoted. |
| 8. Query-independent, human- and agent-auditable knowledge | Protects canonical records and scopes from query-driven mutation. | Existing provisional and package-backed query distinctions remain bounded; adoption does not imply a production query service. |

## Version Responsibility and compatibility analysis

If ratified, adoption requires each future version specification to identify
the Charter mission it serves, define a bounded deliverable, state scope and non-implications,
preserve applicable principles, mark unimplemented principles as future work,
retain later interpretability, and distinguish constitutional requirements from
implementation choices. The V2 conformance statement records current
`IMPLEMENTED`, `PARTIAL`, `DEFERRED`, and `CONFLICT` dispositions rather than
silently declaring full compliance.

This is a prospective authority change, not a migration of historical records.
Pre-adoption records, releases, contract bundles, schemas, assessments, and
decisions remain interpreted under the exact contracts, policies, scopes, and
authority boundaries they originally bound. Adoption does not promote,
reclassify, invalidate, certify, admit, or rewrite them. A later Charter
assessment is a new attributable record.

The current assessment schemas, Checkpoint E candidate, and immutable fixtures
are not versioned, regenerated, or repaired by this proposal. Future
post-adoption contract-bundle candidates claiming Charter conformance must bind
or cite both the adopted Charter identity and the qualifying ratification
commit's full Git object ID and carry updated conformance analysis.

## Consequences

### Positive

- Upon ratification, the project gains one explicit highest-level normative
  authority.
- Version-specific precision can evolve without implied constitutional change.
- Historical immutability and prospective Charter conformance are reconciled.
- Known V2 gaps are visible without granting them broader release, certification,
  admission, or scientific authority.

### Costs and constraints

- Charter amendments require the constitutional procedure rather than an
  ordinary specification edit.
- Future conformance claims and contract-bundle candidates need an exact Charter
  binding or citation.
- Full V2 conformance remains unavailable while the recorded six-axis conflict
  and applicable deferred responsibilities remain unresolved.
- Project-authority approval and specialist-review evidence must be retained with
  the ratification change; this ADR cannot substitute for those acts.

## Invariants

1. No subordinate document or implementation amends the Charter implicitly.
2. No adoption label is effective without the authorized ratification commit.
3. The effective date is the qualifying commit's committer timestamp.
4. No pre-adoption immutable object is rewritten or silently promoted.
5. A Charter-conformance claim binds or cites the exact adopted Charter version.
6. Charter adoption itself grants no release, certification, archive, admission,
   scientific-review, or whole-paper authority.

## Acceptance tests

| Test | Expected result |
|---|---|
| Inspect Charter metadata and this ADR in the ratification commit | Both identify `AgtXIv-Charter/1.0`; the ADR is accepted and the Charter is adopted. |
| Inspect the ratification change's governance evidence | Required specialist reviews and later project-authority approval bind the immutable eight-path proposal manifest; otherwise adoption remains pending. |
| Compare the canonical integration with the approved changeset | Against its designated first parent, the dedicated post-approval commit changes exactly the eight listed paths from the reviewed base path-entry tuples or absences to the reviewed target tuples or absences; every other entry is unchanged. |
| Resolve the adoption record and date | The full commit ID is the stable record and its Git committer timestamp is the effective date. |
| Inspect a pre-adoption immutable record | Its bytes, status, and exact bound authority are unchanged. |
| Claim full V2 Charter conformance with only the current three-axis contracts | The claim is rejected because the six-axis conflict remains recorded. |
| Use Charter adoption to infer release, certification, or admission | The inference is rejected as unauthorized promotion. |

## Related records

- [`CHARTER.md`](../../CHARTER.md)
- [`GOVERNANCE.md`](../../GOVERNANCE.md)
- [`docs/governance/v2-charter-conformance.md`](../governance/v2-charter-conformance.md)
- [`docs/specifications/v2-paper-agentization.md`](../specifications/v2-paper-agentization.md)
