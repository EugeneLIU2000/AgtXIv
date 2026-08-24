# ContributionClaim fixtures

These seven records are accepted source-grounded fixtures for the
`CONTRIBUTION` role/profile of `ScientificClaim`. They use the existing
`claim:` identity family and remain in `ScientificClaimRegistry`; they are
paper-narrative entry points, not proof objects. The validator rejects
`claim:contribution:` IDs in available mathematical dependency-DAG inputs.

The existing **1,645 provisional candidates** are discovery inventory, not
accepted `ContributionClaim` records. Candidate promotion requires source
calibration, an explicit primary occurrence, body-support locating, and an
explicit ContributionClaim profile record. Merely adding a same-paper
`MathClaimIR` cannot create or promote a ContributionClaim.

## Facet navigation, not global coverage

Each combined narrative has stable ordered facets. Its
`ClaimSupportAssociation` pins `/facets` of the exact immutable claim revision
and maps every support TargetRef to one facet. The aggregate is explicitly a
provisional navigation summary at that basis. It is not truth, verification, or
eternal coverage. `QueryResolution` will compute final query-relative coverage
against a pinned decomposition and registry snapshot. The thesis's technical
MathClaimIR records are `TOPICAL_NAVIGATION_ONLY` with `NONE` coverage.

## Calibration direction

Calibration relations are always source-relative-to-normalized-claim.
`BROADER_THAN` means the source entails a wider scope or weaker restrictions;
`NARROWER_THAN` means it entails a strictly smaller scope or stronger
restrictions. Use `PARTIAL_OVERLAP` when neither entails the other or their
facets differ. Abstract statements combined with body-only facets are therefore
classified conservatively as partial overlap unless directional entailment is
clear.

## Deterministic hashing

The schema-pinned profile is
`schemas/record-canonical-json-v1.profile.json`, ID
`agtxiv.record-canonical-json/1.0.0`. For this slice it supports JSON `null`,
Booleans, integers, strings, arrays, and objects; non-integral numbers are not
implemented. Strings and keys use Unicode NFC and LF normalization. Map keys
are ordered by normalized Unicode code point. Primitive serialization is
RFC-8785-compatible for this supported subset; this is not a claim of complete
RFC 8785 number support. Ordered arrays preserve order. Declared set arrays are
sorted by canonical member bytes and canonical duplicates are rejected.

The semantic payload contains paper identity, role/granularity, broad
contribution kind and tags, orthogonal source characterization, normalized
statement, canonical scope hints, and ordered facets. Occurrences, provenance,
revision, and serialization metadata do not alter semantic identity. The
artifact hash detects those fields while omitting its own slot and the derived
record content hash; record content hash then covers the complete record with
only its own slot omitted. External record hashes omit only `content_hash`.

Validate without modifying files:

```bash
python3 tools/validate_contribution_claims.py --check
python3 tests/test_contribution_claims.py -v
```
