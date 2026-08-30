# AgtXIv V2 M0 Lean bootstrap audit

- Audit status: REVIEW REQUIRED
- M0 Lean-bootstrap status: NOT COMPLETE
- Audit date: 2026-08-31
- Branch observed: `codex/agtxiv-v2`
- Committed `HEAD` observed: `6752c0d5bd3a0b7c8988e5c2ca7b30506b3eac8d`
- Scope: clean-checkout Lean/LeanQuantum acquisition, environment binding,
  cache isolation, dynamic formal validation, and continuous-integration (CI)
  evidence
- Intended mutation boundary: this audit adds only this document. Before/after
  Git inspection found no tracked formal source, manifest, validator, or
  verification-record change. Ignored caches and toolchain bytes were observed
  selectively, not exhaustively snapshotted, so this audit does not claim they
  were immutable merely because tracked Git status stayed unchanged
- Terminology: follows
  `docs/roadmaps/v2-end-to-end-implementation-plan.md` and
  `docs/security/v2-threat-model.md`

## 1. Executive finding

The three AgtXIv Lean projects declare a coherent toolchain and resolved Lake
dependency closure, and the locally present checkouts match the commits recorded
by the current evidence. That is useful content-pinning evidence. It is not yet a
clean-checkout bootstrap or an enforced-offline rebuild.

The missing chain is:

```text
versioned lock
  -> checksum-verified tool archives
  -> exact, content-verified source checkouts
  -> read-only environment qualification
  -> operating-system-enforced no-egress build in empty scratch
  -> placeholder/declaration/axiom audits
  -> immutable reproduction report
```

Today, `.tools/elan`, `Reference/LeanQuantum`, and the shared Lake package and
build directories are ignored local state. The aggregate validator checks that a
repository-local `lake` proxy exists, but no versioned procedure creates that
state from an empty checkout. At the start of this audit, the dynamic validators
could reuse approximately 7 GB of ignored Lake packages and compiled outputs.
After the independent-review incident, the exact Mathlib source is restored but
its compiled `.lake` cache is absent; other ignored caches remain. At audit start,
the environment variable named `AGTXIV_OFFLINE` was only a cooperative label,
not a network security boundary. A concurrent corrective slice subsequently
removed that false label and now reports the limitation explicitly; it still
does not enforce network isolation.

Consequently, the historical RootMath, Varela, and Stabilizerness results remain
valuable evidence for their stated scopes, but they must not be upgraded to
`CLEAN_CHECKOUT_REPRODUCED`, `SOURCE_REBUILT`, or
`NETWORK_ISOLATION_ENFORCED` on the basis of the current workstation run.

## 2. Intuition: receiving dock and clean laboratory

The easiest physical picture is a laboratory with a receiving dock.

- The **receiving dock** is allowed to use the network. It receives only named
  Elan, Lean, LeanQuantum, Mathlib, and transitive-dependency objects. It measures
  every object against a versioned digest before it is admitted. It does not run
  the received Lake files.
- The **freezer** is the content lock. It records the exact bytes or source tree,
  not merely a branch name such as `main` or a human-readable release label.
- The **clean laboratory** begins with an empty build surface. Its input shelves
  are read-only, its output bench is disposable, and the network door is closed
  below the application layer.
- The **independent inspection** checks the resulting declarations, placeholders,
  and axioms. A green build means that the formal conclusion follows in that
  exact formal environment. It still does not prove that the formal statement
  faithfully expresses the paper or that the assumptions apply physically.

The present repository has much of the recipe and several historical inspection
reports. It does not yet have a versioned receiving procedure or evidence that
the laboratory bench was empty and the network door physically closed.

## 3. Audit method and evidence boundary

This audit used repository inspection, local tool version and Git identity
queries, digest computation, and read-only queries to the official GitHub
release APIs for `leanprover/elan` and `leanprover/lean4`. The intended queries
did not write tracked source. A query through an Elan/Lake proxy cannot be
assumed side-effect free: it may resolve a toolchain or reconcile package state.
Only the tracked Git boundary was checked before and after; no complete
before/after inventory or digest of ignored caches was taken.

The working tree already contained unrelated modified and untracked user work.
It was not stashed, cleaned, reset, reformatted, or included in this audit. In
particular, the Stabilizerness dynamic validator and its tests were observed as
untracked working-tree work at the beginning of this audit. Observations about
that validator are therefore working-tree observations, not claims about the
committed baseline at the recorded `HEAD`.

No tool archive was downloaded and rehashed byte-for-byte during this audit.
Section 5 records SHA-256 digests returned by the official repository release
API. Those are primary-source metadata observations, not adopted AgtXIv pins.
The future bootstrap must download each selected archive, compute its digest
locally, compare it with the reviewed lock, and reject a mismatch before
extraction or execution.

### 3.1 Independent-review cache incident

During the later independent review of this document, a version query was run
through Lake while that shell command's `PATH` was accidentally empty. Lake
decided that the local Mathlib package URL needed reconciliation, deleted the
ignored `formal/AgtXIvRootMath/.lake/packages/mathlib` checkout, and then failed
to clone because `git` was no longer resolvable. Tracked Git status did not
change. The exact Mathlib source checkout was subsequently restored from the
official repository at commit
`c1e30e172c8fda21e6776bf1f10351e882ee31b9`, tree
`426094735539fc51969f67ac28a5de0bf55348c8`, with the expected origin and a clean
worktree. Its former multi-gigabyte compiled `.lake` cache was not restored.

This incident is direct evidence for the control boundary in this audit: future
identity checks must execute a reviewed direct binary against a disposable copy
or a qualified immutable input layout. A command described as a version query
must not be treated as read-only solely because tracked Git status is unchanged.

## 4. Environment and dependency state observed

### 4.1 Tracked project declarations

All three tracked `lean-toolchain` files contain:

```text
leanprover/lean4:v4.30.0-rc2
```

Their common file SHA-256 is:

```text
ce4c4e3d87434b9663f46de25ce34b48a0cf0d392e0a320a0787b4674a2d7b61
```

`formal/AgtXIvRootMath/lakefile.toml` declares:

- Mathlib at exact commit
  `c1e30e172c8fda21e6776bf1f10351e882ee31b9`;
- LeanQuantum as the local path `../../Reference/LeanQuantum`.

The RootMath `lake-manifest.json` records exact resolved commits for Mathlib and
eight transitive Git packages. Varela and Stabilizerness use path dependencies on
RootMath and share `formal/AgtXIvRootMath/.lake/packages`; their manifests record
the same resolved Git closure. Several inherited `inputRev` values are symbolic
names such as `main` or `v4.30.0-rc2`, but each corresponding `rev` is a full
commit. A bootstrap must consume the resolved `rev`, never resolve `inputRev`
again.

LeanQuantum's upstream `lakefile.lean` names the moving Mathlib repository
without a revision. Its checked-in manifest resolves the same Mathlib commit as
AgtXIv. Running `lake update` in LeanQuantum or regenerating the AgtXIv manifests
would therefore be a dependency update, not a reproducible bootstrap operation.

### 4.2 Ignored local state

The root `.gitignore` excludes:

- `.tools/`;
- every `**/.lake/` directory;
- `Reference/LeanQuantum/`.

This is correct for keeping toolchains, dependency checkouts, and compiled
outputs out of the source repository. It also means a clean tracked Git status
does not imply a clean formal build surface.

Approximate local sizes observed were:

| Local ignored state | Observed size |
|---|---:|
| `.tools/elan` | 2.5 GB |
| `Reference/LeanQuantum` including Git and build state | 72 MB |
| `formal/AgtXIvRootMath/.lake/packages` | 7.0 GB before the review incident |
| `formal/AgtXIvRootMath/.lake/build` | 289 MB |
| `formal/AgtXIvVarela/.lake` | 29 MB |
| `formal/AgtXIvStabilizerness/.lake` | 11 MB |

LeanQuantum and the Lake package repositories had no ordinary tracked changes,
but their ignored `.lake` outputs were present. Ordinary
`git status --porcelain` does not report those files.

### 4.3 Local tool identity

The ignored repository-local Elan installation reported:

```text
elan 4.2.3 (b6cec7e10 2026-06-08)
```

The local Elan proxy binary SHA-256 was:

```text
8754858b6549a9b06f4a019e7145a5e1e19f933983734388920a10781a7537db
```

When invoked from each formal project with the repository-local `ELAN_HOME`, the
installed toolchain reported:

```text
Lean (version 4.30.0-rc2, arm64-apple-darwin24.6.0,
      commit 3dc1a088b6d2d8eafe25a7cd7ec7b58d731bd7cc, Release)
Lake version 5.0.0-src+3dc1a08 (Lean version 4.30.0-rc2)
```

This qualifies the currently selected local binaries at the time of inspection.
It does not establish how their bytes arrived, nor does it prevent a later local
modification. A clean bootstrap must begin from the reviewed release archive
digest rather than inheriting this directory.

### 4.4 Git source identities

The following identities were observed from the current local checkouts. The
`source SHA-256` column was computed over the Git tree, in `git ls-tree` path
order, as:

```text
SHA256(concat(mode, NUL, path, NUL, byte-size, NUL,
              SHA256(blob-bytes), LF))
```

This secondary SHA-256 binds mode, path, size, and bytes independently of the
repository's native SHA-1 object identity. It is local audit evidence; a future
bootstrap must reproduce it from a fresh exact checkout before admission.

| Package | Exact commit | Git tree | Source SHA-256 |
|---|---|---|---|
| LeanQuantum | `44fc4eb1f4ba512e659deacd3468fda0a764d162` | `98dec098800b988c5cb805e1614c68fbd8537229` | `94b9721fe663b8025125b1741bc3273ae6fb878e4f0fb09b62e537c4049513a8` |
| Mathlib | `c1e30e172c8fda21e6776bf1f10351e882ee31b9` | `426094735539fc51969f67ac28a5de0bf55348c8` | `642ae18c593378d4cea2ffc3e2eeb438730c17c636247ac9f5cf5cd9a7a6723d` |
| plausible | `86210d4ad1b08b086d0bd638637a75246523dbb8` | `bfbaf990f50b6c1428ede79ab945741d5a3cdd16` | `a1c6ca76d7d15e4c0a897f21ef1e1aead71fa054bff74e09417fe07fdc187e08` |
| LeanSearchClient | `c5d5b8fe6e5158def25cd28eb94e4141ad97c843` | `d0224b6df6c90cc0b4ed2db6218037d31bfd6f52` | `479620b97ddc75730c932fe7bb0a839e1f595d50d3fc7bae7b80f1792ab759fd` |
| importGraph | `cdab3938ccabbdb044be6896e251b5814bec932e` | `f02b64d855db070eb5e2f1f01a65286f1462448e` | `d63eec5c5a1e15339362c2ec47539c2598d70ff136d5c7f8050e95477572c998` |
| proofwidgets | `2db6054a44326f8c0230ee0570e2ddb894816511` | `d1674b8cf337e1e5fd2bc43a58ae2f7e16ddd9f3` | `8bf87cf6b371e154996df0056ce6865670d81abc67d2757592d0a1cc1ec5cf9b` |
| aesop | `f0c6e183ea26531e82773feb4b73ab6595ca17a5` | `4a1006c9183cf1e70a207a14653d28405d49e3c5` | `864c2b134e1c594715521fa07cad2d27edd4aed979047f6831532c3f386cb953` |
| Qq | `1cc7e819b9b9bc1e87c9edcccb62e0269e00a809` | `a515231cbf007e41a84bc2bb65ec91cc27684c70` | `eb09a1dc2ac4a3fcdcf628fcb9cbd66537de62ddd61d3cf3a9c98d010bd0e031` |
| batteries | `5c57f3857ba81924a88b2cdf4f062e34ec04ff11` | `1c86760fadbe6bf15d8e281431dbc92f93afda45` | `7d0dc647cc61c7cb567ea1c5e5539b9e9b235455c1ac2a919d204e8e5538e85b` |
| Cli | `13567aed1ac4f12aea9484178e07e51f8c9f7658` | `15b725754ebcf01202bb28e404ed0e42246efc54` | `d4ae2f9b52ea45cc5d9b3a7d7560cd5cc4505b382aa96b53d44589fd81b102cb` |

No Git submodule entry was observed in this closure. Mathlib and batteries do
contain tree-bound symbolic links; a safe checkout must reproduce only the links
already committed in the admitted tree and must not follow them while computing
or copying source inputs.

## 5. Official release-archive metadata observed

### 5.1 Verification method and status vocabulary

On 2026-08-31, the following read-only commands queried the official repositories'
GitHub release records:

```text
gh api repos/leanprover/elan/releases/tags/v4.2.3 \
  --jq '.assets[] | [.name, .digest, .browser_download_url] | @tsv'

gh api repos/leanprover/lean4/releases/tags/v4.30.0-rc2 \
  --jq '.assets[] | [.name, .digest, .browser_download_url] | @tsv'
```

The tables below transcribe the exact asset name, official release URL, and
`digest` returned by those primary-source API records.

Status used here:

- **PRIMARY-SOURCE METADATA VERIFIED; NOT ADOPTED** means the exact digest was
  read from the official repository release API, but AgtXIv has not yet accepted
  it into a versioned lock and this audit did not download and locally rehash the
  archive bytes.
- **UNVERIFIED** would mean the value was available only from a secondary source
  or was not reproduced from the official release record. No table entry below
  has that status.

The future bootstrap must convert a reviewed table entry into an adopted lock
only after a reviewer confirms the official record and a clean integration test
downloads and locally recomputes the same SHA-256.

### 5.2 Elan 4.2.3 archive candidates

| Platform | Official asset and URL | Official SHA-256 metadata | Audit status |
|---|---|---|---|
| macOS arm64 | [`elan-aarch64-apple-darwin.tar.gz`](https://github.com/leanprover/elan/releases/download/v4.2.3/elan-aarch64-apple-darwin.tar.gz) | `7cae4c03b2f0de4053fb04a91359d5804551e6e37a6ddd1b2e0097dc561ae4a9` | PRIMARY-SOURCE METADATA VERIFIED; NOT ADOPTED |
| macOS x86_64 | [`elan-x86_64-apple-darwin.tar.gz`](https://github.com/leanprover/elan/releases/download/v4.2.3/elan-x86_64-apple-darwin.tar.gz) | `10d037a69731c0593723e018130c5f54afde175796b4af8ba1317e561e55598c` | PRIMARY-SOURCE METADATA VERIFIED; NOT ADOPTED |
| Linux arm64 | [`elan-aarch64-unknown-linux-gnu.tar.gz`](https://github.com/leanprover/elan/releases/download/v4.2.3/elan-aarch64-unknown-linux-gnu.tar.gz) | `cb69af0803b04157bc30201c29c12fca882bb3ad8b43476b8d2d3064810bc3ac` | PRIMARY-SOURCE METADATA VERIFIED; NOT ADOPTED |
| Linux x86_64 | [`elan-x86_64-unknown-linux-gnu.tar.gz`](https://github.com/leanprover/elan/releases/download/v4.2.3/elan-x86_64-unknown-linux-gnu.tar.gz) | `df0b2b3a439961ffcbb3985214365ffe40f49bc871df04dff268c7d8e21ca8b2` | PRIMARY-SOURCE METADATA VERIFIED; NOT ADOPTED |

The official `v4.2.3` annotated tag resolves through tag object
`82ff39161e90159477d27f2430607f1bdb6d95bc` to commit
`b6cec7e10fe4965a605aaf60d1cb4a5837f0462b`. The official GitHub Git-object
record reported the tag as unsigned. The release asset digest fixes bytes; it
does not create a missing maintainer signature.

### 5.3 Lean 4.30.0-rc2 ZIP archive candidates

ZIP candidates are listed because a future Python 3.12 bootstrap could extract
them without assuming a separately installed `zstd`. This is a design candidate,
not a decision; archive-member permissions and links must be preserved and
validated explicitly.

| Platform | Official asset and URL | Official SHA-256 metadata | Audit status |
|---|---|---|---|
| macOS arm64 | [`lean-4.30.0-rc2-darwin_aarch64.zip`](https://github.com/leanprover/lean4/releases/download/v4.30.0-rc2/lean-4.30.0-rc2-darwin_aarch64.zip) | `1bda6929976b2a034985fdfc85faa5e757421f6542c5e59c644e44dc1132fe51` | PRIMARY-SOURCE METADATA VERIFIED; NOT ADOPTED |
| macOS x86_64 | [`lean-4.30.0-rc2-darwin.zip`](https://github.com/leanprover/lean4/releases/download/v4.30.0-rc2/lean-4.30.0-rc2-darwin.zip) | `822b5a802763c3833c748ba6dd781fdf16426a16b7b7b2b753783ff3435feb7b` | PRIMARY-SOURCE METADATA VERIFIED; NOT ADOPTED |
| Linux arm64 | [`lean-4.30.0-rc2-linux_aarch64.zip`](https://github.com/leanprover/lean4/releases/download/v4.30.0-rc2/lean-4.30.0-rc2-linux_aarch64.zip) | `62c60766b850e1d5b4405742c4aefff097441105e51f5fb5c1bf90434b8e0960` | PRIMARY-SOURCE METADATA VERIFIED; NOT ADOPTED |
| Linux x86_64 | [`lean-4.30.0-rc2-linux.zip`](https://github.com/leanprover/lean4/releases/download/v4.30.0-rc2/lean-4.30.0-rc2-linux.zip) | `0006942b918c7fb9751a5e50b9e5ad570c5cc6aa758c980a3abc054dd8739d35` | PRIMARY-SOURCE METADATA VERIFIED; NOT ADOPTED |

The official Lean tag `v4.30.0-rc2` resolves directly to commit
`3dc1a088b6d2d8eafe25a7cd7ec7b58d731bd7cc`. The official GitHub commit record
reported `verification.verified=true` and `reason=valid`. This is useful
provider-reported signature/repository metadata in addition to content identity;
it is not locally qualified authorship, maintainer authorization, release
authorization, or project-adoption evidence. The selected archive must still be
verified independently by SHA-256 during bootstrap.

## 6. Content reproducibility is not author identity

The lock must keep two different questions separate:

1. **Content identity:** are these the same archive bytes and the same Git source
   trees every time?
2. **Origin/authorship assurance:** is there a trusted signature or reviewed
   chain showing who authorized those bytes?

A release SHA-256, full Git commit, Git tree, and secondary source-tree SHA-256
can make the content repeatable. They do not prove that the author is who a
project expects, that an unsigned upstream commit was reviewed, or that an
upstream account was uncompromised.

The official GitHub record reported the Lean release commit as
`verification.verified=true`. That means GitHub reported a valid signature; it
does not by itself prove Lean maintainer identity, release authorization, or
AgtXIv adoption. The observed Elan release tag, LeanQuantum commit, and Mathlib
commit object contained no `gpgsig` header. Each of the eight other transitive
package commit objects contained a signature payload, but this audit did not
establish a local signer identity or trust chain for those signatures.

These states must not be collapsed:

- `signature_present` records whether an object carries a signature;
- `local_verification` records whether it was checked with a qualified key;
- `provider_metadata` records a hosting provider's separate verification claim;
- `project_adoption` records AgtXIv's independent review decision.

AgtXIv must record these axes honestly. Possible future controls are independent
source review, a project-maintained signed mirror manifest, or a signed
content-addressed source bundle. Pinning or a provider's green badge alone must
not be described as author identity or project release authorization.

## 7. Current control gaps

### 7.1 No clean-checkout installer

There is no tracked command that creates `.tools/elan`, installs the exact Lean
release, obtains LeanQuantum, and populates the complete exact Lake source
closure from an empty checkout. The README documents commands that assume those
ignored inputs already exist.

### 7.2 `NO_PROXY=*` was not offline

The aggregate runner's `_offline_environment` and the observed Stabilizerness
working-tree validator remove common proxy variables and then set:

```text
AGTXIV_OFFLINE=1
NO_PROXY=*
no_proxy=*
```

`NO_PROXY=*` generally tells network clients to bypass a configured proxy for
every destination. It does not disable sockets, DNS, direct HTTPS, subprocess
networking, or custom client code. Removing proxies can therefore make a direct
connection more likely. `AGTXIV_OFFLINE=1` has an effect only when every invoked
program voluntarily implements that convention.

This audit also demonstrated that an ambient invalid `ELAN_TOOLCHAIN` caused the
repository-local Elan proxy to attempt a request to `release.lean-lang.org`.
Environment decoration is not a security boundary. A release-grade no-egress
claim requires an operating-system network namespace, sandbox, firewall policy,
or container network policy that the unprivileged build cannot undo.

During this audit, a separate working-tree correction replaced the aggregate
runner's `_offline_environment` with a preloaded-input intent, stopped changing
the caller's proxy policy, and now emits
`network_isolation_enforced=false`. The concurrent Stabilizerness validator made
the same correction. This removes an overclaim and the `NO_PROXY=*` hazard; it
does not close the no-egress implementation gap described in Section 11.

### 7.3 Ambient toolchain selection remains possible

The validators execute `.tools/elan/bin/lake`, which is an Elan proxy. The proxy
normally discovers the project's `lean-toolchain`, but `ELAN_TOOLCHAIN`, Elan
directory overrides, or modified ignored Elan settings can alter resolution.
Checking only that the proxy is executable does not prove which real `lake` or
`lean` will run.

The qualified runner should resolve and verify the direct pinned toolchain
binaries first, then execute the direct absolute `bin/lake` path. It should
remove toolchain, search-path, compiler-injection, and dynamic-loader override
variables from the child environment.

### 7.4 Existing caches weaken a clean-rebuild claim

`lake build` is incremental. It can accept existing `.olean`, `.ilean`, generated
C, executable, hash, trace, and configuration outputs when Lake considers them
current. A successful incremental build is useful, but it is not evidence that
all declarations were rebuilt from the pinned source during that run.

At the start of the audit, the ignored tree contained compiled outputs for
AgtXIv, LeanQuantum, Mathlib, and other packages. After the review incident, the
Mathlib compiled cache is absent while the exact source checkout and other
ignored caches remain. Any malicious or corrupted ignored cache is outside
ordinary Git review. A release-grade clean lane must use an empty project and
dependency build surface. If a faster lane uses an upstream or CI cache, the
report must name the cache trust root and say `CACHE_ASSISTED`, not
`SOURCE_CLEAN_REBUILD`.

Bit-for-bit equality of generated `.olean` files across operating systems is not
currently an AgtXIv promise. The required reproducibility target is exact input
identity plus the same kernel/declaration/axiom result under a recorded supported
platform. Bit-reproducible outputs would require a separate specification and
test.

### 7.5 Validator coverage is inconsistent

- RootMath checks the LeanQuantum HEAD and ordinary working-tree cleanliness but
  does not bind the Elan archive, real Lean binary, Mathlib/transitive checkout
  identities, or ignored build state.
- Varela relies on the already prepared shared RootMath packages and does not
  independently qualify that closure.
- At the audit snapshot, the observed untracked Stabilizerness validator checked
  manifest structure and dependency-directory existence. A first concurrent
  revision added pre-build HEAD and ordinary tracked-cleanliness checks for
  LeanQuantum and nine Lake Git packages and checked selected declared fields in
  the RootMath/Varela evidence. Independent review then showed that the evidence
  hashes were still self-certifying, the path-dependency source closure was not
  exact-bound, and dependency cleanliness was not rechecked after build. A
  further corrective revision is in progress and is not yet branch evidence.
  Until that revision is independently reviewed, the only observed successful
  result is a cache-assisted local WIP run over seven declarations (four local
  and three imported), with no source-alignment, scientific-acceptance, registry,
  release, or admission effect.

These checks should consume one qualified environment report rather than
duplicating only part of the dependency policy in each scientific validator.

### 7.6 CI does not rebuild Lean

The committed CI baseline runs fast Python validation and the static site smoke
test. It does not execute `make check-full`, bootstrap the formal toolchain, or
rebuild any Lean project. A local full-profile pass therefore has no independent
clean-run counterpart in the current CI evidence.

## 8. Recommended versioned lock

Add one reviewed, machine-readable lock, proposed as:

```text
formal/lean-environment.lock.json
```

It should contain at least:

- lock schema and canonicalization version;
- supported operating-system/architecture keys;
- Elan version, tag object, underlying commit, signature observation, exact
  archive filename, exact official URL, SHA-256, and maximum byte count per
  supported platform;
- Lean toolchain string, release commit, signature observation, exact archive
  filename, exact official URL, SHA-256, expected `lean --version`, expected
  `lean --githash`, expected `lake --version`, and maximum byte count;
- every Git dependency's canonical HTTPS URL, destination, commit, Git tree,
  canonical source-tree SHA-256, submodule policy, symbolic-link policy, and
  observed signature status;
- every tool and dependency's exact license/notice asset identity plus reviewed
  permissions for download, local caching, CI caching, mirroring, source or
  binary redistribution, and public evidence publication;
- exact hashes of the three `lean-toolchain` and `lake-manifest.json` files that
  the lock qualifies;
- source-build and cache policy identifiers;
- the supported no-egress executor identifiers;
- the review identity and supersession reference for the lock release.

The lock must be the authority for bootstrap inputs. Lake manifests remain
necessary package-manager inputs, but the verifier must prove that their
resolved closure agrees with the reviewed lock. A manifest change without a
corresponding reviewed lock supersession must fail.

The lock should reject unknown fields or assign them a defined canonical
meaning. URLs must be exact allowlisted HTTPS origins; redirects must be bounded
and recorded. The bootstrap must never interpret a URL, destination, or command
from unreviewed paper or model content.

## 9. Recommended bootstrap design

Add a network-enabled acquisition command, proposed as:

```text
tools/bootstrap_lean_environment.py
```

This command belongs to a trusted developer/CI supply-chain acquisition plane,
not ADR 0006's paper-processing acquisition plane. It must run under a distinct
identity, credential set, network policy, and audit trail. No paper, query,
archive member, extracted TeX, model output, generated code, or Paper Agent may
invoke it or influence its URLs, revisions, destinations, commands, or policy.

Its responsibilities should be limited to obtaining and qualifying bytes. It
must not build a Lake package or execute an upstream `lakefile`.

Required behavior:

1. Require the repository's pinned Python 3.12 environment and strict lock
   schema.
2. Map the detected platform only to an explicitly supported lock entry. An
   unknown platform is a typed failure, not a fallback to the latest release.
3. Download into a newly created, narrowly scoped temporary directory with
   connect/read/total timeouts and byte limits.
4. Recompute SHA-256 before extraction. A mismatch must stop before any archive
   member or installer is executed.
5. Extract defensively: reject absolute paths, `..`, NUL, duplicate/conflicting
   paths, devices, FIFOs, sockets, unsupported links, links escaping the
   destination, excessive file count, and excessive expanded bytes.
6. Install the verified Lean archive without asking Elan to resolve or download a
   moving toolchain. Elan may still be installed for editor/developer proxy use,
   but validators should execute the qualified direct Lean/Lake binaries.
7. For each Git dependency, create a fresh temporary repository with system and
   global Git configuration disabled, prompts disabled, hooks disabled, local
   transport disabled, and no credentials. Fetch only the exact admitted commit.
8. Verify the commit, Git tree, canonical source-tree SHA-256, allowed file
   modes, absence of undeclared submodules, and remote URL before installation.
9. Atomically rename a fully qualified temporary result into its ignored final
   destination.
10. Be idempotent. If an existing destination matches completely, reuse it. If it
    differs, fail with a structured diagnostic; do not delete, overwrite, clean,
    or repair it implicitly.
11. Emit a machine-readable acquisition report with URLs, redirect chain,
    downloaded byte counts, digests, source identities, platform, commands, and
    terminal status.

The bootstrap must not run `lake update`, resolve a branch or tag in place of an
exact commit, run `lake exe cache get`, edit a tracked manifest, set a default
global toolchain, modify shell profiles, or use a global Lean installation.

## 10. Recommended read-only environment verification

Add a separate command, proposed as:

```text
tools/verify_lean_environment.py
```

It should perform no download and no build. It should:

- validate the lock and all platform entries;
- validate the exact tracked toolchain and manifest hashes;
- verify direct Lean/Lake paths are regular executable files inside the admitted
  toolchain directory, not links escaping it;
- compare `lean --githash`, Lean version, Lake version, and resolved prefix with
  the lock;
- verify every dependency's remote, commit, tree, source-tree SHA-256, tracked
  cleanliness, submodule policy, and allowed link inventory;
- distinguish allowed build-output directories from source identity, and reject
  any build output in `--require-empty-build-state` mode;
- prove the three project manifests resolve to the same admitted external
  closure;
- reject ambient toolchain or loader overrides rather than silently inheriting
  them;
- emit one qualified-environment JSON record consumed by all three dynamic
  validators.

A directory existing at the right path is not sufficient evidence. The report
must bind actual bytes and source trees.

## 11. Recommended no-egress formal runner

Add a formal runner, proposed as:

```text
tools/run_lean_validation_offline.py
```

Its high-assurance mode should:

1. require a passing qualified-environment record bound to the current lock and
   tracked formal source hashes;
2. construct a disposable workspace with the three AgtXIv projects and exact
   dependency source trees but no inherited `.lake` build outputs;
3. mount or copy source inputs read-only and expose only a bounded writable
   scratch/output area;
4. execute the direct admitted toolchain's `lake`, not an ambient command or Elan
   proxy;
5. start under an operating-system-enforced deny-by-default network policy;
6. pass an allowlisted environment without tokens, proxy settings, SSH agents,
   cloud credentials, host sockets, `ELAN_TOOLCHAIN`, `LEAN_PATH`, `LAKE_HOME`,
   compiler injection, or dynamic-loader injection;
7. set deterministic cooperative inputs such as UTC and a fixed locale where
   supported, while recording unavoidable platform variation;
8. enforce CPU, memory, process, open-file, disk, output-byte, and wall-clock
   limits and terminate the whole process group on timeout;
9. run each build, placeholder scan, exact declaration audit, and axiom audit;
10. copy only declared outputs out of the sandbox, bound and redact logs, hash the
    outputs externally, and emit an immutable result;
11. verify no tracked historical evidence or formal source changed.

The runner must fail with a status such as `NO_EGRESS_EXECUTOR_UNAVAILABLE` if it
cannot establish the promised isolation. It must not silently fall back to an
ordinary subprocess while retaining an `offline` label.

Candidate enforcement mechanisms require a platform decision:

- macOS can use an audited `sandbox-exec` profile for network denial, but that
  alone does not provide all filesystem and resource controls;
- Linux CI can use a network namespace or a container with `--network=none`, a
  pinned image digest, a non-root user, dropped capabilities, no host socket, a
  read-only base, and explicit resource limits.

Setting an invalid proxy or trusting `NO_PROXY` is not an acceptable substitute.

## 12. Cache policy

Two distinct lanes are recommended:

| Lane | Cache policy | Permitted claim |
|---|---|---|
| Pull-request quick formal lane | May restore an exact-lock-keyed dependency cache after revalidating its source identities and documenting the compiled-cache trust root | `CACHE_ASSISTED_REVALIDATION` |
| Scheduled/release clean formal lane | Starts without project, LeanQuantum, Mathlib, or transitive `.lake` build outputs and compiles from admitted source under no egress | `SOURCE_CLEAN_REBUILD` |

An Actions or local cache is an optimization, never an authority. A cache hit
must still pass lock verification. Project build outputs must not cross the
clean-lane boundary. If an official Mathlib compiled cache is used, its delivery,
integrity mechanism, and trust implications must be recorded explicitly; it
cannot be relabeled as a source-clean build.

The current ignored caches should not be deleted automatically. Local validation
can either use them in a clearly labeled quick lane or construct a new isolated
workspace. This preserves user state while avoiding a false clean-rebuild claim.

## 13. CI lane design

### 13.1 Static lock lane on every pull request

This inexpensive, required lane needs no Lean download. It should verify:

- lock schema and canonical form;
- toolchain/manifest hashes and closure equality;
- exact URL, commit, tree, and platform inventory shape;
- no floating dependency enters a resolved field;
- bootstrap and verifier unit tests.

### 13.2 Formal quick lane

For changes to formal sources, locks, manifests, validators, or formal evidence,
and for every default-branch update:

- check out with `persist-credentials: false` and read-only repository
  permission;
- reproduce Python, acquire exact formal inputs, and verify them;
- remove all job tokens and credentials before executing Lake code;
- enforce no egress during build;
- run RootMath, Varela, and Stabilizerness dynamic validators;
- mark any permitted compiled-cache use in the result;
- reject tracked-file drift.

### 13.3 Scheduled and release clean lane

At least nightly and before a release candidate:

- use an empty `.tools`, `Reference/LeanQuantum`, and `.lake` state;
- download only reviewed lock objects;
- run the source-clean no-egress build for all three projects;
- run a network-denial canary that attempts a harmless connection and must fail;
- verify exact declarations, placeholders, and axioms;
- publish the environment, build, and audit report as immutable CI evidence;
- bind the report to the exact commit and lock hash.

Every third-party Action and container image must be pinned by immutable digest.
Restored caches are untrusted until verified. No formal job should retain a
checkout credential in `.git/config` or expose a GitHub token to Lake or generated
formal code.

## 14. Test matrix

### 14.1 Lock and manifest tests

| Test | Expected result |
|---|---|
| All three `lean-toolchain` files equal the lock | Pass |
| All three manifests have the exact lock closure | Pass |
| Symbolic `inputRev` is used in place of resolved `rev` | Reject |
| One transitive commit, URL, tree, or source SHA-256 changes | Reject |
| Unknown lock field or unsupported lock schema appears | Reject |
| Undeclared Git submodule appears | Reject |

### 14.2 Download and extraction tests

| Test | Expected result |
|---|---|
| Supported-platform archive has exact SHA-256 | Admit |
| Archive digest differs by one bit | Reject before extraction |
| Unsupported operating system or architecture | Typed failure |
| Redirect leaves the reviewed acquisition policy | Reject |
| Download exceeds byte or time limit | Reject and discard temporary data |
| Absolute, `..`, NUL, duplicate, device, FIFO, socket, or escaping-link member | Reject entire archive |
| Partial extraction or interrupted download remains | Never install it |

### 14.3 Git checkout tests

| Test | Expected result |
|---|---|
| Fresh exact commit/tree/source SHA-256 | Admit |
| HEAD, tree, blob, mode, or remote differs | Reject |
| Checkout has tracked, staged, or undeclared source files | Reject |
| Global Git filter, hook, credential, prompt, or local transport is attempted | Disabled/reject |
| Destination already exists and matches | Idempotent success |
| Destination already exists and differs | Fail without deleting it |

### 14.4 Tool-resolution tests

| Test | Expected result |
|---|---|
| Host `PATH` begins with fake `lean` and `lake` | Direct admitted binaries still run |
| Ambient `ELAN_TOOLCHAIN` or Elan override is present | Reject or remove before qualification |
| Lean version is right but `--githash` is wrong | Reject |
| Lake proxy exists but real toolchain is absent | Reject without download |
| Tool binary or prefix escapes admitted directory | Reject |

### 14.5 No-egress and clean-build tests

| Test | Expected result |
|---|---|
| Build code opens a direct socket, uses DNS, or invokes `curl` | Kernel/container denial and failed canary |
| Dependency directory is missing during offline build | Fail; do not fetch |
| Old project `.olean` is planted outside clean scratch | It is not visible to the build |
| Malicious cached output is planted in a cache-assisted lane | Cache verification rejects it or result remains explicitly cache-assisted |
| Build tries to read a token, SSH agent, cloud metadata, or host socket | Resource absent/denied |
| Build exceeds process, memory, disk, log, or wall-clock limit | Whole process group terminated; typed failure |
| Build rewrites formal source or historical verification evidence | Reject result |

### 14.6 End-to-end clean-checkout tests

For each supported release platform:

1. create a fresh checkout at an exact commit;
2. prove `.tools`, `Reference/LeanQuantum`, and every `.lake` are absent;
3. run the one documented formal bootstrap;
4. run read-only environment qualification;
5. run all three projects under no egress and empty build state;
6. verify declaration and axiom inventories;
7. verify tracked Git status remains empty;
8. record exact input and output roots;
9. repeat from another fresh checkout and compare the specified reproducibility
   outputs.

The comparison should require identical lock, source, declaration, axiom, and
terminal-status evidence. It should not claim cross-platform bit-identical
compiled files unless that stronger property is separately specified and shown.

## 15. Exact implementation surface proposed

The following focused implementation can be added without rewriting historical
formal evidence:

| Path | Responsibility |
|---|---|
| `formal/lean-environment.lock.json` | Reviewed platform, archive, source, and policy inputs |
| `tools/bootstrap_lean_environment.py` | Network-enabled acquisition and safe installation only |
| `tools/verify_lean_environment.py` | Read-only lock, tool, manifest, and source qualification |
| `tools/run_lean_validation_offline.py` | Clean scratch, no-egress, resource-bounded orchestration |
| `tests/test_lean_bootstrap.py` | Lock, archive, Git, resolution, and idempotency negatives |
| `tests/test_lean_offline_runner.py` | Isolation, cache, credential, timeout, and side-effect negatives |
| `docs/security/lean-supply-chain.md` | Trust boundary, operator workflow, cache policy, and incident handling |
| `.github/workflows/ci.yml` or a pinned formal workflow | Static, quick, nightly/release lanes and required status aggregation |
| `Makefile` | `bootstrap-lean`, `verify-lean-env`, and `check-formal` entry points |
| `README.md` | Supported platforms, disk/time expectations, and claim boundaries |

The aggregate repository validator should gain a static lock-consistency check
that runs without Lean and a runtime environment check that reports
`MISSING_TOOL` or a typed environment failure. It should stop calling a process
`offline` unless the selected runner proves no-egress enforcement.

Historical `verification-result.json` records should remain immutable. A clean
rebuild should produce a new, separately identified reproduction record bound to
the old evidence and the new environment lock. If existing validator source is
itself part of a historical hash inventory, changing it requires an explicit
superseding record rather than silently editing the old hash.

## 16. Decisions still required

1. **Supported platforms.** Recommended M0 minimum: developer macOS arm64 and CI
   Ubuntu Linux x86_64. macOS x86_64, Linux arm64, and Windows should fail closed
   until tested and admitted.
2. **Tool installation form.** Decide whether validators use a directly extracted
   verified Lean release or a verified Elan-managed layout. Direct execution of
   the admitted real `bin/lake` is recommended in either case.
3. **Linux no-egress executor.** Choose a pinned container implementation or an
   audited network-namespace implementation and its exact image/tool digest.
4. **macOS evidence tier.** Decide whether `sandbox-exec` is sufficient for a
   local quick check or whether only Linux CI can issue release-grade isolation
   evidence.
5. **Cache trust.** Decide whether pull requests may use the Mathlib compiled
   cache and require a source-clean scheduled/release lane. The recommendation is
   yes, with the two statuses kept distinct.
6. **Resource budget.** A full environment currently occupies several gigabytes;
   CI disk, time, cache, and concurrency limits need measured values.
7. **Unsigned upstreams.** Decide how LeanQuantum and other unsigned commits are
   reviewed, mirrored, attested, and superseded.
8. **Bootstrap interface.** Decide whether the heavyweight formal acquisition is
   part of default `make bootstrap` or an explicit `make bootstrap-lean`. The
   latter is clearer if the fast Python bootstrap must remain small.
9. **Archive format.** Decide ZIP versus `tar.zst` per platform after testing
   permission/link preservation and the safe extractor. The metadata in Section
   5 is not yet an adopted lock.
10. **Reproduction record.** Define the schema and signing/review policy for the
    new clean-build report without rewriting historical results.
11. **Third-party rights.** Record and independently review exact license and
    notice bytes plus the permitted download, cache, mirror, and redistribution
    treatment for Elan, Lean, LeanQuantum, Mathlib, and every transitive package.
    This is part of the unresolved third-party-material gate in `GOVERNANCE.md`;
    official digests and official-repository identity do not grant arbitrary
    redistribution rights.

## 17. M0 Lean-bootstrap exit proposal

This blocker can be closed only when all of the following are true:

- the reviewed environment lock and acquisition policy are versioned;
- exact third-party license/notice identities and the permitted download, cache,
  mirror, redistribution, and evidence-publication dispositions are reviewed
  and versioned;
- selected official archives are locally rehashed in clean integration tests and
  their reviewed values are adopted explicitly;
- a clean checkout can acquire every exact input without executing upstream Lake
  code during the network-enabled phase;
- read-only qualification binds actual tool binaries, manifests, commits, trees,
  and source SHA-256 values;
- RootMath, Varela, and Stabilizerness build from an empty formal build state
  under operating-system-enforced no egress;
- the exact placeholder, declaration, and axiom audits pass;
- the result names whether any compiled cache was used;
- no tracked formal source, manifest, historical evidence, or unrelated user
  file changes;
- CI reproduces the result at an exact commit and publishes the environment and
  build report;
- an independent reviewer approves the lock, isolation evidence, and claim
  wording.

Until then, the correct status is:

```text
PINNED_LOCAL_ENVIRONMENT_OBSERVED
CLEAN_CHECKOUT_BOOTSTRAP_NOT_IMPLEMENTED
NETWORK_ISOLATION_NOT_ENFORCED
SOURCE_CLEAN_REBUILD_NOT_ESTABLISHED
```

## 18. Non-implications

Completing this bootstrap would establish a reproducible formal build
environment and a stronger kernel-evidence chain. It would not by itself prove:

- that a Lean statement matches the source paper;
- that omitted assumptions, units, regimes, or approximations are acceptable;
- that a theorem applies to a physical experiment;
- that every theorem in a paper has been formalized;
- that an unsigned upstream commit has authenticated authorship;
- that a formal build is scientifically reviewed or eligible for knowledge
  admission;
- that generated binaries are bit-identical across platforms;
- that later V2 release, archive, signature, and admission gates have passed.

Those remain independent evidence and review axes in the V2 architecture.
