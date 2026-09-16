# Cross-record invariants and implementation boundaries

Version: experimental V3 contract `0.0.0`. Scope: explicitly supplied local records and bytes, with optional caller-held execution attestations. This document distinguishes record structure from mechanical relations and actual scientific evidence.

An intuitive example: a paper says a result holds for every state, while a proof only covers pure states. Preserving the original claim, creating the qualified proposition, proving that proposition, checking its translation and assessing its physical applicability are separate actions. No sequence of green schema checks turns the pure-state result into the original universal claim.

## Levels of evidence

| Level | What a positive result establishes | What it does not establish |
|---|---|---|
| JSON Schema | Fields, types, exact discriminators, closed objects and local conditional rules match the selected bundle | Referenced bytes exist; an actor really reviewed an object; a proof is valid |
| Supplied-record checks | The implemented exact bindings, denominators, dependencies and authority constraints hold within the supplied graph | The supplied corpus is complete; omitted external challenges do not exist; every scientific meaning is faithful |
| Local source inspection | Original files were read, hashed and examined by the bounded static parser | Actual published participation, full TeX expansion, complete claim discovery or source fidelity |
| Actual scientific / execution evidence | Only the target, method, environment and scope documented by an independently reviewed real result | Other axes, broader targets, whole-paper truth, release or admission by implication |

The current implementation provides the first level, substantial portions of the second, local source inspection, a pinned offline upstream capture parser, potential dependency analysis, and bounded transactional candidate storage. It has no general scientific oracle, production identity provider, controlled vibefeld execution gateway, Lean worker, official release/admission service or production knowledge database. See the bilingual [local mechanism guide](../docs/architecture/v3-local-mechanisms.md).

## Implemented mechanical checks

The following checks are implemented in `src/agtxiv_v3/contracts.py` and the focused obligation, upstream, dependency and storage modules, with positive and adversarial tests under `tests/v3`. This is a check inventory, not a declaration that the corresponding full roadmap phase is accepted.

| Boundary | Implemented behavior | Remaining limit |
|---|---|---|
| Canonical identity | Reject duplicate/normalized-colliding keys, floats, unsafe integers, unknown types, stale hashes, duplicate identity/revision and unresolved exact references; keep raw artifact hashes separate | The trusted bundle itself needs an externally adopted identity for production |
| Offline bundle | Verify each manifest byte digest, meta-schema, discriminator and all references without network retrieval | A caller-selected valid bundle is not thereby authorized |
| Source spans | Verify original artifact membership, nonempty half-open byte bounds, selected byte hashes, transformation output membership and normalized PDF boxes | No PDF page rendering/count validation or semantic extraction judgment |
| Inventory and scope | Exact source partition; frozen discovery equality; named-profile work and success stages retained; prior removed obligations require preserved dispositions and independent review of their old scope | No automatic guarantee that a human/agent discovered every scientific claim or gave a scientifically adequate removal reason |
| Claim mapping | Every source component accounted for; exact component identity; residual meaning preserved; missing approximation information rejected | Wording, physical interpretation and logical equivalence require assessment |
| Joint inference | Keep all premises together; reject self-premises, cycles within a chosen route and escaping local contexts; restrict discharge rules and require evidence plus immediate-parent scope | A referenced rule witness is not mechanically proven by this validator |
| Argument and handoff | Preserve exact scope, routes, local contexts and open obligations across snapshots and packets; reject a supported review with listed blocking gaps | Pinned offline ledger/export replay is available separately; complete external dependency discovery and independent proof verification remain unimplemented |
| Formal evidence bindings | Exact attempt/packet/environment, expected declarations, forbidden axiom inventory, independent review targets and exact alignment endpoints | Actual Lean execution, declaration introspection and environment isolation are not implemented here; claimed log bytes are not execution attestations |
| Six axes | Require all six axes in profiles/views; separate applicability, result and execution; bind typed positive evidence to exact targets; retain conditions; reject conditional-to-full promotion and synthetic support through declared load-bearing evidence closure | Semantic sufficiency, undeclared evidence ancestry and complete world-wide assessment coverage are not established |
| Relations, delta and reuse | Exact endpoint reviews, witnessed accepted relations, prior membership in the baseline, typed source support, required comparison dimensions, conditions and explicit incompatible environment rejection | Full evidence-policy coverage per use, conflict discovery and scientific comparison remain pending; a permission record alone is not safe operational reuse |
| Package structure | Total unique dispositions over the frozen scope; required record membership; positive audit and certificate bindings; completed mandatory work and immutable release binding | Scientific adequacy of success evidence and all required assessments per target are not fully operationalized; no publication command exists |
| Snapshot structure | Empty genesis; append-only prior entries, relations and admission provenance; exact authorized additions; receipt partition and before/after/decision agreement | Local candidate ingest and provisional snapshot CAS are transactional; a production admission policy, access-control separation and independent checkpoints do not yet exist |
| Queries | Reject unadmitted returned entries/relations for package-backed records; retain known relevant conflict endpoints; bind assertions to returned records | No deployed query endpoint; completeness outside the selected snapshot is unknown |
| Local view | Display every assessment of the exact target in the supplied set, all six axes, conditions and differing conclusions; do not overwrite by timestamp | It does not claim all assessments were supplied and does not merge disagreement into a truth score |
| Frozen obligation heads | Require one current disposition within an explicit historical universe, preserve predecessor history and require typed exact-target completion witnesses | Unsupported completion stages fail closed; universe completeness and actual scientific adequacy are not established |
| Pinned upstream capture | Verify the 35-event local profile, replay supplied ledger bytes, compare graph and context, preserve unknown/missing input and reported states | No upstream execution, actor authentication or independent historical checkpoint |
| Potential impact | Follow explicit typed dependencies and route-local inference uses, binding exact inputs without changing assessments | Missing declarations and axis-transfer semantics remain unknown; unreached routes are not certified independent |
| Candidate persistence | Immutable exact objects and raw bytes, full-set validation before commit, provisional CAS heads and historical queries retaining limiting relations | Trusted local filesystem/caller; 10,000-record bound; no official admission index or public query service |

## Authority is an explicit caller boundary

`AuthorityContext` is supplied independently by the integrating Python caller. It checks recorded execution identity, visible inputs, principal aliases, policy authorization, minimum identity assurance and designated decision roles. Aggregate reviews include content producers hidden behind proof routes and package assembly. Certification must be separate from package production and audit; admission must be separate from package production, audit and certification. Initial backtranslation rejects directly visible source/target/alignment answer records.

These checks assume the caller controls and trusts the attestations, mappings and Python process. They are not evidence of legal identity, domain qualification, signature validity, independent institutional control, causal model independence or undisclosed information access. A malicious Python caller can replace the validator; this module is not a process security boundary. The CLI therefore does not accept an identity JSON file as authority.

Policy `separated_role_pairs` and `human_review_triggers` retain explicit governance requirements. Beyond the built-in role/producer constraints above, free-text policy requirements need an integrating policy evaluator; they are not silently treated as executable predicates. Formal decision services must fail closed until applicable requirements are implemented and independently authorized.

`valid: true` with `authority_checked: false` is deliberately possible: it describes a consistent candidate graph whose identity authority was not checked. It must not be consumed as a release or admission token. Even `authority_checked: true` only confirms the stated local caller boundary and implemented rules.

## Required future mechanisms

1. Exercise the pinned offline vibefeld adapter on independently captured real runs, then add a controlled command gateway. The implemented byte parser and synthetic replay tests do not supply runtime receipts. Unknown events or incomplete exports remain blocked; reported `validated`, `clean`, `admitted` and `closed` remain upstream labels.
2. Connect runtime identity evidence to exact produced outputs and code/environment identity; implement adopted role policy, confidentiality/visibility rules and qualifications. Do not create attestations by copying record fields.
3. Extend the implemented target-level success and historical-universe evidence checks to currently unsupported completion stages and actual scientific producers. `CONTRIBUTION` and `RELEASE` completion remain fail-closed. An arbitrary existing record in `result_refs` is not sufficient proof that work succeeded.
4. Reconstruct and assess the real scientific inventory, source conditions and claim transformations. Source omissions, additional hypotheses and newly discovered obligations must have different revision records.
5. Execute independent Lean checks, inspect actual target declarations and transitive axioms, and perform independent backtranslation/alignment. Preserve mathematical and scientific scope separately.
6. Evaluate complete dependencies and alternative proof routes; propagate new evidence along the affected dependency types and axes without rewriting historical states.
7. Extend the implemented local transactional candidate store with adopted admission policy, archive access-control separation, independent checkpoints and production durability/performance evidence. Local CAS and rollback tests do not provide independent tamper evidence or official knowledge admission.
8. Assess baseline-relative contributions and at least one real accepted and one real rejected reuse case under the same evidence standard. Engineering fixtures cannot substitute for these evaluations.

## Test interpretation

The catalog tests construct a minimal `SYNTHETIC` instance of every registered family to exercise schema branches, hashes and bilingual field correspondence. They deliberately do not fabricate a complete scientifically approved citation graph. Graph tests construct smaller coherent artificial source, scope, proof, release and transaction structures, then change one boundary to test rejection. Source tests exercise byte and archive hazards; no TeX, vibefeld, Lean or paper demo runs are needed.

The exact command, counts and remaining task boundaries are recorded in the [execution status](../docs/roadmaps/v3-execution-status.md). Keep claims at their actual evidence level; do not count 64 schema files as 64 working scientific services.

中文阅读提示：schema 像每一种记录的表格格式；跨记录校验像核对表格之间的编号、依据和职责；科学审阅才判断论证与物理含义是否成立。三者缺一不可，不能互相代替。当前已经实现的机制和仍需真实材料验收的部分，应始终分开阅读。
