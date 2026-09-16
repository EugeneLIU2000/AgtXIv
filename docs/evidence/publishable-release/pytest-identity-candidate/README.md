# Independent pytest identity candidate

The official candidate operation passed for the standalone source commit
`4f770d807c08eee37b14dd5a3fdf5675bdef0f02`. It reproduced two identical guarded
collections: **2,258 collected and selected tests, zero collection skips or
deselections, and 20 marker declarations**. The existing locked Python
environment passed runtime qualification. The portable candidate identity also
passed `schemas/repository-validation/pytest-test-identity.schema.json`.

This is candidate review material. It does not activate or replace the parent
repository's baseline, establish that tests were executed successfully, or turn
the parent repository's failing baseline-binding gate into a pass. The official
assurance tier is `COMMIT_SNAPSHOT_UNSANDBOXED_DIAGNOSTIC`, with
`branch_evidence_eligible: false`; filesystem and network isolation are not
enforced by this tool.

## Evidence

| File | What it records |
|---|---|
| [candidate-evaluation.json](candidate-evaluation.json) | Unmodified official `--candidate --source-ref` output, exact source commit, validator binding, guarded collection identity, runtime qualification, and `PASS` outcome. |
| [test-identity-candidate.json](test-identity-candidate.json) | Only the portable `test_identity` object, serialized canonically for review; it is not the active baseline. |
| [source-freeze.json](source-freeze.json) | All 1,906 captured source paths, sizes and modes, each source hash before copying, immediately after copying, after the full copy, the copied-byte hash, and the exact committed-blob hash. |
| [review-summary.json](review-summary.json) | Comparison with the unchanged 1,483-test working baseline, evidence hashes, exact reproduction command, recovery-bundle location and hash, limits, and subsequent parent-source changes. |

The candidate adds **775** nodes and removes **zero** relative to the existing
working baseline. Existing nodes retain their relative order. The collection
contract, three runtime input bindings, and marker declarations are unchanged.
The candidate identity SHA-256 is
`ae62bffc5cee3b3b1283f0b9833204a065860ae8e82b15d0ab2de1abe2eb60dd`.

## Source selection and preservation

The source list came from the parent repository's
`git ls-files --cached --others --exclude-standard -z`. Existing regular source
files were copied to a new directory under `/private/tmp`; ignored caches,
`.git`, and `.venv` were not copied. The snapshot contains 157,105,407 bytes.
Every captured file matched its before/after source hashes and its committed
blob. No source changed during the capture check.

Only the independent temporary directory was initialized as a Git repository
and committed, on `codex/pytest-candidate`; no remote was configured or pushed.
The temporary Git `info/attributes` file disables text, filter, ident and
working-tree-encoding transformations. This preserves original bytes, including
CRLF in two bibliography files that the copied `.gitattributes` would otherwise
normalize. The committed tree is
`d29b0dda820de8e5ab8a669755bebaf0084c0d20`.

The parent HEAD remained
`4bc41cbd32a0bb6b5fa1ea2a0b69c972525b28bd` during capture. Its existing dirty
baseline was preserved byte for byte, with SHA-256
`596a03aa81bddeb4dde86271a59ae379f9d55cceb1f1800693e26303a87f1490`.
The standalone snapshot is **not** that parent HEAD. The parent website and
technical report continued changing after capture; seven changed captured
paths are recorded in `review-summary.json`. This evidence therefore identifies
the exact standalone commit and does not claim to certify the latest parent
working tree or a simultaneous atomic snapshot of concurrent edits.

## Reproduction and recovery

The actual invocation used the existing parent virtual environment without
copying it into the source:

```sh
cd /private/tmp/agtxiv-pytest-candidate-3tggn6bw/source
/Users/Yingjian/Documents/GitHub/AgtXIv/.venv/bin/python -B \
  tools/validate_pytest_inventory.py --candidate \
  --source-ref 4f770d807c08eee37b14dd5a3fdf5675bdef0f02
```

A self-contained 94,482,045-byte Git bundle is retained at
`/private/tmp/agtxiv-pytest-candidate-3tggn6bw/source-snapshot.bundle`.
`git bundle verify` passed and found a complete history with the candidate
branch and HEAD pointing to the recorded commit. Its SHA-256 is in
`review-summary.json`. The bundle is deliberately absent from the website and
repository evidence directory; it contains the private source snapshot.
Temporary storage is not durable custody: preserve this bundle elsewhere
before cleaning `/private/tmp` if the exact snapshot must remain recoverable.

The next baseline decision should review this candidate and then explicitly
choose whether and how to activate a newer baseline. It must not silently
overwrite the existing user's baseline or relabel this candidate operation as
a successful parent `--check --source-head` operation.
