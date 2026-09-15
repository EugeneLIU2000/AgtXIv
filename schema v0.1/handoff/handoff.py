#!/usr/bin/env python3
"""One bounded Paper-candidate -> Dependency local-citation handoff.

No model, network, semantic reuse decision, or general-purpose scheduler.
The host owns SQLite; the handler receives detached, explicitly visible inputs.
Task/Result stay in runtime tables, never in the V3 business records table.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
import time
import uuid

SPEC = Path(__file__).resolve().parents[1]
REPO = SPEC.parent
sys.path.insert(0, str(SPEC))
from validate import (Contracts, InterfaceError, MAX_TOTAL, read_bytes, read_json,
                      require, ref_key, short_type, walk)
from agtxiv_v3.contracts import (REF_KEYS, ContractError, RecordSet, SuppliedArtifact,
                                 canonical, digest, exact_ref, parse, validate_exact_ref)
from agtxiv_v3.storage import LocalStore
from jsonschema import Draft202012Validator

HANDLER = 'local-citations/1.0'
ART_KEYS = {'artifact_id', 'media_type', 'byte_size', 'sha256'}
DEFAULT_EXAMPLE = SPEC / 'Paper Agent/example/2608.14798v1-claude-opus-5-v1.1'
DEFAULT_CLAIM = {
    'record_type': 'agtxiv.v3.math-claim/0.0.0',
    'record_id': 'math:opus5-v11-2608.14798v1/A07-conclusion-1',
    'revision': 1,
    'content_hash': 'sha256:a6b36b3690a729d60af7462c6fd1de31ab772550daf0395deb1a8a027f03da68',
}


def now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')


def core_artifact(ref):
    return {key: ref[key] for key in sorted(ART_KEYS)}


def safe_member(root, relative):
    """Acquisition metadata supplies paths, never authority to escape its root."""
    root = Path(root).resolve()
    member = Path(relative)
    require(not member.is_absolute() and bool(member.parts)
            and '..' not in member.parts, 'Unsafe source member path')
    target = root
    for part in member.parts:
        target = target / part
        require(not target.is_symlink(), 'Symlink source member rejected')
    require(target.resolve().is_relative_to(root), 'Source member escapes root')
    return target


def closure(records, target):
    """Select only exact ancestors, including provenance/policy refs; never latest."""
    index = {}
    for record in records:
        key = ref_key(exact_ref(record))
        require(key[:3] not in index, 'Duplicate record identity/revision')
        index[key[:3]] = record
    selected, pending = {}, [target]
    while pending:
        ref = pending.pop()
        validate_exact_ref(ref)
        key = ref_key(ref)
        if key in selected:
            continue
        record = index.get(key[:3])
        require(record is not None and exact_ref(record) == ref, 'Missing or stale exact reference')
        selected[key] = record
        pending.extend(node for node in walk(record) if set(node) == REF_KEYS)
    return [selected[key] for key in sorted(selected)]


def pins():
    paths = [Path(__file__), SPEC / 'validate.py', SPEC / 'agents.json',
             SPEC / 'compatibility.lock.json', SPEC / 'storage/runtime.sql',
             SPEC / 'Dependency Agent/search-draft.schema.json',
             REPO / 'src/agtxiv_v3/contracts.py', REPO / 'src/agtxiv_v3/storage.py',
             REPO / 'src/agtxiv_v2/contracts/canonical.py', *sorted((SPEC / 'schemas').glob('*.json'))]
    return {str(p.relative_to(REPO)): digest(read_bytes(p)) for p in paths}


@contextmanager
def locked(directory):
    # Single-host advisory lock. Workers do not get DB credentials; trusted host
    # and filesystem remain outside the adversarial boundary.
    directory = Path(directory)
    require(not directory.is_symlink(), 'Symlink run directory rejected')
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / '.host.lock'
    require(not lock.is_symlink(), 'Symlink lock rejected')
    with lock.open('a+b') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise InterfaceError('Another local host owns this handoff') from error
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


@contextmanager
def database(directory):
    path = Path(directory) / 'handoff.sqlite'
    require(path.is_file() and not path.is_symlink(), 'Missing or unsafe handoff database')
    db = sqlite3.connect(path, isolation_level=None)
    db.execute('PRAGMA foreign_keys=ON')
    try:
        yield db
    finally:
        db.close()


@contextmanager
def transaction(db):
    db.execute('BEGIN IMMEDIATE')
    try:
        yield
        db.execute('COMMIT')
    except BaseException:
        db.execute('ROLLBACK')
        raise


def event(db, task_id, attempt_id, state, payload):
    raw = canonical(payload)
    db.execute('INSERT INTO runtime_events(task_id,attempt_id,event_type,payload,payload_sha256,created_at) '
               'VALUES(?,?,?,?,?,?)', (task_id, attempt_id, state, raw, digest(raw), now()))


def prepare(directory, example=DEFAULT_EXAMPLE, target=DEFAULT_CLAIM, repository=REPO):
    contracts = Contracts()
    require(short_type(target) == 'math-claim', 'This adapter requires one MathClaim')
    records = read_json(Path(example) / 'records.json')
    selected = closure(records, target)
    acquisition = read_json(Path(example) / 'acquisition.json')
    snapshots = [r for r in selected if short_type(r) == 'source-snapshot']
    require(len(snapshots) == 1, 'This acquisition adapter supports one source snapshot')
    source = safe_member(repository, acquisition['source_directory'])
    snapshot = snapshots[0]['payload']
    artifacts, total = [], 0
    for ref, path in [(u['artifact'], safe_member(source, u['relative_path'])) for u in snapshot['units']] + [
            (snapshot['archive'], safe_member(repository, acquisition['archive_path']))]:
        raw = read_bytes(path)
        total += len(raw)
        require(total <= MAX_TOTAL, 'Source closure exceeds byte budget')
        item = SuppliedArtifact(ref['artifact_id'], ref['media_type'], raw)
        require(item.reference() == core_artifact(ref), 'Source artifact bytes/hash mismatch')
        artifacts.append(item)
    RecordSet(contracts.base, selected, artifacts).validate().require_valid()
    full = RecordSet(contracts.base, records, artifacts).validate()
    # Bibliography + exact raw-text span files only; images/archive are host-only.
    visible_ids = {r['payload']['artifact']['artifact_id'] for r in selected if short_type(r) == 'source-span'}
    visible_ids.update(u['artifact']['artifact_id'] for u in snapshot['units']
                       if u['artifact']['media_type'] == 'text/x-bibtex')
    input_artifacts = [a.reference() for a in artifacts if a.artifact_id in visible_ids]
    seed = {'target': target, 'records': [exact_ref(r) for r in selected],
            'artifacts': input_artifacts, 'pins': pins(), 'handler': HANDLER}
    task_id = 'handoff:' + digest(canonical(seed))[7:]
    task = {
        'contract_version': '0.1.0', 'task_id': task_id, 'agent': 'dependency',
        'operation': 'dependency.search',
        'brief': 'Scan only visible raw-text source spans for literal TeX citations; resolve keys in '
                 'visible BibTeX bytes. Deliver a local findings artifact and search proposals. '
                 'Do not infer a mathematical dependency, reuse authorization, or absence of prior work.',
        'target_refs': [target], 'input_refs': seed['records'], 'input_artifacts': input_artifacts,
        'depends_on': [], 'expected_record_types': [],
        'limits': {'max_attempts': 2, 'max_seconds': 30, 'max_cost_units': 0, 'no_progress_limit': 2},
        'acceptance': 'DELIVERY', 'exclusions': [],
        'capabilities': ['records.read', 'dependency.search', 'candidates.propose'],
    }
    contracts.task(task)
    manifest = {
        'mode': 'CANDIDATE_LOCAL_CITATION_HANDOFF', 'handler': HANDLER,
        'implementation_pins': seed['pins'], 'schema_bundle_hash': contracts.base.bundle_hash,
        'input_records_sha256': digest(read_bytes(Path(example) / 'records.json')),
        'acquisition_sha256': digest(read_bytes(Path(example) / 'acquisition.json')),
        'closure_refs': seed['records'], 'closure_artifacts': [a.reference() for a in artifacts],
        'selected_closure_valid': True, 'selected_record_count': len(selected),
        'original_record_count': len(records), 'original_recordset_valid': full.valid,
        'original_issue_counts': dict(Counter(i.code for i in full.issues)),
        'whole_paper_delivery_accepted': False, 'authority_checked': False,
        'scientific_acceptance_checked': False, 'external_model_calls': 0,
        'cost_units_definition': 'Number of paid external API calls; local compute is not free.',
    }
    directory = Path(directory)
    with locked(directory):
        path = directory / 'handoff.sqlite'
        require(not path.is_symlink(), 'Symlink database rejected')
        if path.exists():
            with database(directory) as db:
                stored_task, stored_manifest = load(db, contracts)
                require(stored_task == task and stored_manifest == manifest, 'Run already contains different fixed inputs')
            return status(directory)
        # Build in a private staging directory, publish only a complete DB.
        # This is not a live-store migration or a general transactional outbox.
        with tempfile.TemporaryDirectory(prefix='.prepare-', dir=directory) as staging:
            staging = Path(staging)
            with LocalStore(staging / 'handoff.sqlite', contracts.base) as store:
                store.ingest(selected, artifacts)
            with database(staging) as db:
                db.executescript(read_bytes(SPEC / 'storage/runtime.sql').decode())
                db.executescript('''
                CREATE TABLE handoff_manifest(singleton INTEGER PRIMARY KEY CHECK(singleton=1), body BLOB NOT NULL, sha256 TEXT NOT NULL);
                CREATE TABLE handoff_outputs(artifact_id TEXT PRIMARY KEY, media_type TEXT NOT NULL, data BLOB NOT NULL);
                CREATE TRIGGER handoff_manifest_no_update BEFORE UPDATE ON handoff_manifest BEGIN SELECT RAISE(ABORT,'immutable manifest'); END;
                CREATE TRIGGER handoff_manifest_no_delete BEFORE DELETE ON handoff_manifest BEGIN SELECT RAISE(ABORT,'immutable manifest'); END;
                CREATE TRIGGER handoff_outputs_no_update BEFORE UPDATE ON handoff_outputs BEGIN SELECT RAISE(ABORT,'immutable output'); END;
                CREATE TRIGGER handoff_outputs_no_delete BEFORE DELETE ON handoff_outputs BEGIN SELECT RAISE(ABORT,'immutable output'); END;
                ''')
                with transaction(db):
                    raw = canonical(manifest)
                    db.execute('INSERT INTO handoff_manifest VALUES(1,?,?)', (raw, digest(raw)))
                    raw_task = canonical(task)
                    db.execute('INSERT INTO runtime_tasks VALUES(?,?,?,?,?,?)',
                               (task_id, raw_task.decode(), canonical(seed['records']).decode(), task_id, digest(raw_task), now()))
                    event(db, task_id, None, 'READY', {'meaning': 'Selected candidate inputs fixed; no parent Paper delivery asserted.'})
            os.rename(staging / 'handoff.sqlite', path)
    return status(directory)


def load(db, contracts):
    row = db.execute('SELECT task_ref_json,request_sha256 FROM runtime_tasks').fetchall()
    require(len(row) == 1, 'Expected exactly one registered task')
    raw = row[0][0].encode()
    require(digest(raw) == row[0][1], 'Stored Task hash mismatch')
    task = parse(raw)
    contracts.task(task)
    row = db.execute('SELECT body,sha256 FROM handoff_manifest WHERE singleton=1').fetchone()
    require(row is not None and digest(row[0]) == row[1], 'Stored manifest hash mismatch')
    manifest = parse(row[0])
    require(manifest['implementation_pins'] == pins(), 'Implementation/schema drift: prepare a new run')
    require(manifest['schema_bundle_hash'] == contracts.base.bundle_hash, 'Business bundle drift')
    return task, manifest


def uncomment(raw):
    # Mask TeX/BibTeX line comments without changing offsets; no macro execution.
    return re.sub(rb'(?<!\\)%[^\r\n]*', lambda m: b' ' * len(m[0]), raw)


def bib_entries(raw):
    """Bounded literal braced BibTeX entries; retain exact bytes, not interpreted metadata."""
    masked, entries = uncomment(raw), []
    pattern = rb'@([A-Za-z]+)\s*\{\s*([^,\s{}]+)\s*,'
    cursor = 0
    while match := re.search(pattern, masked[cursor:]):
        start, end = cursor + match.start(), cursor + match.end()
        depth, pos = 1, end
        while pos < len(masked) and depth:
            require(pos - start <= 128 * 1024, 'BibTeX entry exceeds local parser bound')
            char = masked[pos]
            if char == 92:
                pos += 2
                continue
            depth += (char == 123) - (char == 125)
            pos += 1
        if depth:
            raise InterfaceError('Unbalanced BibTeX entry; no reliable literal lookup')
        if match[1].lower() not in (b'comment', b'string', b'preamble'):
            entries.append((match[2].decode('utf-8'), start, pos))
            require(len(entries) <= 10000, 'Too many BibTeX entries for local handler')
        cursor = pos
    return entries


def scan(task, records, artifacts):
    """Dependency handler: pure local input -> output, without filesystem/DB/network access."""
    target = next(r for r in records if exact_ref(r) == task['target_refs'][0])
    spans = [r for r in records if short_type(r) == 'source-span']
    require(0 < len(spans) <= 256, 'Expected 1..256 source spans for local handler')
    require(sum(len(a.data) for a in artifacts) <= 10 * 1024 * 1024, 'Visible bytes exceed local scan bound')
    by_id = {a.artifact_id: a for a in artifacts}
    bibliography = []
    for item in artifacts:
        if item.media_type == 'text/x-bibtex':
            bibliography.extend((key, start, end, item) for key, start, end in bib_entries(item.data))
    findings, scanned = [], []
    cite_pattern = rb'\\cite(?:t|p|alp|author|year)?\*?(?:\[[^\]\r\n]*\]){0,2}\s*\{([^{}]+)\}'
    for span in spans:
        p = span['payload']
        require(p['locator_kind'] == 'RAW_TEXT_BYTES', 'Only raw-text byte spans supported')
        item = by_id.get(p['artifact']['artifact_id'])
        require(item is not None, 'Source artifact not visible to handler')
        raw = item.data[p['byte_start']:p['byte_end']]
        require(digest(raw) == p['span_sha256'], 'Span bytes changed')
        scanned.append(exact_ref(span))
        for match in re.finditer(cite_pattern, uncomment(raw)):
            for key in match[1].decode('utf-8').split(','):
                key = key.strip()
                if not key:
                    continue
                matches = []
                for bib_key, start, end, bib in bibliography:
                    if bib_key == key:
                        matches.append({'artifact_ref': bib.reference(), 'byte_start': start, 'byte_end': end,
                                        'raw_text': bib.data[start:end].decode('utf-8'),
                                        'slice_sha256': digest(bib.data[start:end])})
                findings.append({'citation_key': key, 'source_span_ref': exact_ref(span),
                                 'citation_byte_start': p['byte_start'] + match.start(),
                                 'citation_byte_end': p['byte_start'] + match.end(),
                                 'bibliography_matches': matches, 'meaning': 'CITATION_IN_CONTEXT_ONLY'})
                require(len(findings) <= 256, 'Too many citations for local handler')
    gaps = ['Only literal citations in supplied spans and supplied braced BibTeX were searched; '
            'macros, other locations, remote literature and historical completeness were not searched.',
            'No cited paper was fetched; no upstream MathClaim, dependency-binding, reuse approval, or Lean code was produced.',
            'The original candidate assumptions/quantifiers remain unchanged and require independent review.']
    if not findings:
        gaps.append('No literal citation found in this bounded scope; NOT evidence of no predecessor.')
    if any(len(f['bibliography_matches']) != 1 for f in findings):
        gaps.append('Some citation keys have zero or multiple local bibliography matches; do not choose silently.')
    queries = sorted({f['citation_key'] for f in findings})
    draft = {'draft_version': '1.0', 'search_requests': [
        {'target_ref': task['target_refs'][0], 'query': key,
         'sources': ['Citing-paper bibliography; fetch and inspect the cited work in a separately budgeted task.']}
        for key in queries], 'records': [], 'open_items': gaps, 'follow_up_requests': []}
    report = {'handler': HANDLER, 'target_ref': task['target_refs'][0],
              'target_payload_unchanged': target['payload'], 'scanned_span_refs': scanned,
              'scanned_bibliography_artifacts': [a.reference() for a in artifacts if a.media_type == 'text/x-bibtex'],
              'findings': findings, 'remote_retrieval_performed': False,
              'mathematical_dependency_established': False, 'open_items': gaps}
    return {'search-draft.json': draft, 'findings.json': report}


def checked_inputs(directory, task, manifest, contracts):
    with LocalStore(Path(directory) / 'handoff.sqlite', contracts.base, readonly=True) as store:
        records = [store.resolve(r) for r in manifest['closure_refs']]
        artifacts = [SuppliedArtifact(a['artifact_id'], a['media_type'], store.artifact(a))
                     for a in manifest['closure_artifacts']]
    RecordSet(contracts.base, records, artifacts).validate().require_valid()
    index = {ref_key(exact_ref(r)): r for r in records}
    visible_records = [index[ref_key(r)] for r in task['input_refs']]
    art_index = {a.artifact_id: a for a in artifacts}
    visible_artifacts = []
    for ref in task['input_artifacts']:
        item = art_index[ref['artifact_id']]
        require(item.reference() == core_artifact(ref), 'Visible artifact differs from fixed input')
        visible_artifacts.append(item)
    return visible_records, visible_artifacts


def finish(db, task, attempt, started, outcome, outputs, gaps, contracts):
    artifacts = [SuppliedArtifact(f'artifact:{attempt}:{name}', 'application/json', canonical(value))
                 for name, value in outputs.items()]
    result = {'contract_version': '0.1.0', 'task_id': task['task_id'], 'attempt_id': attempt,
              'outcome': outcome, 'output_refs': [], 'artifacts': [a.reference() for a in artifacts],
              'open_items': gaps, 'follow_up_requests': [],
              'execution': {'principal_id': 'service:local-citation-host', 'execution_id': attempt,
                            'visible_input_refs': task['input_refs'], 'visible_artifact_refs': task['input_artifacts'],
                            'started_at': started, 'finished_at': now(), 'cost_units': 0}}
    contracts.result(task, result)
    with transaction(db):
        for a in artifacts:
            db.execute('INSERT INTO handoff_outputs VALUES(?,?,?)', (a.artifact_id, a.media_type, a.data))
        event(db, task['task_id'], attempt, outcome, result)
    return result


def run(directory):
    directory, contracts = Path(directory), Contracts()
    with locked(directory), database(directory) as db:
        task, manifest = load(db, contracts)
        last = db.execute('SELECT event_type,payload,payload_sha256 FROM runtime_events ORDER BY event_seq DESC LIMIT 1').fetchone()
        require(last is not None and digest(last[1]) == last[2], 'Missing/corrupt runtime event')
        state, payload = last[0], parse(last[1])
        if state == 'DELIVERED':
            checked_inputs(directory, task, manifest, contracts)
            return verified_result(db, task, payload, contracts)
        # The exclusive host lock proves no cooperating local worker is alive.
        # Interrupted attempts stay recorded and consume the finite attempt budget.
        if state == 'RUNNING':
            finish(db, task, payload['attempt_id'], payload['started_at'], 'FAILED', {},
                   ['Previous local host exited without a receipt; completion time is unknown. '
                    'This is a host recovery observation, not a worker success.'], contracts)
        attempts = db.execute('SELECT COUNT(*) FROM runtime_attempts').fetchone()[0]
        require(attempts < min(task['limits']['max_attempts'], task['limits']['no_progress_limit']),
                'Attempt/no-progress budget exhausted; retain failure, create no new attempt')
        # Reject invalid inputs before consuming an attempt or invoking the handler.
        records, artifacts = checked_inputs(directory, task, manifest, contracts)
        attempt, started = 'attempt:' + uuid.uuid4().hex, now()
        with transaction(db):
            db.execute('INSERT INTO runtime_attempts VALUES(?,?,?,?,?,?)',
                       (attempt, task['task_id'], attempts + 1, digest(canonical(manifest)),
                        canonical({'principal_id': 'service:local-citation-host', 'handler': HANDLER,
                                   'identity_assurance': 'DECLARED', 'external_model_calls': 0}).decode(), started))
            event(db, task['task_id'], attempt, 'RUNNING', {'attempt_id': attempt, 'started_at': started})
        clock = time.monotonic()
        try:
            outputs = scan(parse(canonical(task)), parse(canonical(records)), artifacts)
            require(time.monotonic() - clock <= task['limits']['max_seconds'], 'Local scan exceeded elapsed-time budget')
            schema = read_json(SPEC / 'Dependency Agent/search-draft.schema.json')
            Draft202012Validator(schema, registry=contracts.registry).validate(outputs['search-draft.json'])
            visible = {ref_key(r) for r in task['input_refs']}
            require(all(ref_key(r['target_ref']) in visible for r in outputs['search-draft.json']['search_requests']),
                    'Search draft refers to invisible target')
            # This concrete handler cannot register business records or dispatch follow-ups.
            require(not outputs['search-draft.json']['records'] and not outputs['search-draft.json']['follow_up_requests'],
                    'Local citation handler cannot create business records or dispatch tasks')
            require(sum(len(canonical(v)) for v in outputs.values()) <= MAX_TOTAL, 'Outputs exceed byte budget')
        except Exception as error:
            return finish(db, task, attempt, started, 'FAILED', {},
                          [f'{type(error).__name__}: {str(error)[:7000]}'], contracts)
        return finish(db, task, attempt, started, 'DELIVERED', outputs,
                      outputs['search-draft.json']['open_items'], contracts)


def verified_result(db, task, result, contracts):
    contracts.result(task, result)
    for ref in result['artifacts']:
        row = db.execute('SELECT media_type,data FROM handoff_outputs WHERE artifact_id=?', (ref['artifact_id'],)).fetchone()
        require(row is not None, 'Missing saved output')
        item = SuppliedArtifact(ref['artifact_id'], row[0], row[1])
        require(item.reference() == core_artifact(ref), 'Saved output hash mismatch')
    return result


def status(directory, export=False):
    contracts = Contracts()
    with database(directory) as db:
        db.execute('BEGIN')  # One consistent runtime read snapshot.
        task, manifest = load(db, contracts)
        history, result = [], None
        for seq, state, raw, sha in db.execute('SELECT event_seq,event_type,payload,payload_sha256 FROM runtime_events ORDER BY event_seq'):
            require(digest(raw) == sha, 'Runtime event hash mismatch')
            payload = parse(raw)
            history.append({'sequence': seq, 'state': state})
            if 'outcome' in payload:
                result = verified_result(db, task, payload, contracts)
        checked_inputs(directory, task, manifest, contracts)
        report = {'task_id': task['task_id'], 'state': history[-1]['state'],
                  'attempts': db.execute('SELECT COUNT(*) FROM runtime_attempts').fetchone()[0],
                  'events': history, 'selected_record_count': manifest['selected_record_count'],
                  'whole_paper_delivery_accepted': False, 'scientific_acceptance_checked': False}
        if export:
            require(result is not None and result['outcome'] == history[-1]['state'],
                    'Export requires a terminal receipt for the current state')
            files = {'task.json': task, 'manifest.json': manifest, 'status.json': report}
            if result:
                files['result.json'] = result
                for ref in result['artifacts']:
                    name = ref['artifact_id'].rsplit(':', 1)[-1]
                    require(name in {'search-draft.json', 'findings.json'}, 'Unexpected export filename')
                    files[name] = parse(db.execute('SELECT data FROM handoff_outputs WHERE artifact_id=?',
                                                 (ref['artifact_id'],)).fetchone()[0])
            for name, value in files.items():
                target = Path(directory) / name
                raw = canonical(value)
                if target.exists():
                    require(read_bytes(target) == raw, 'Export exists with different bytes; choose a fresh export directory')
                else:
                    with target.open('xb') as stream:
                        stream.write(raw)
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'run', 'status', 'export'])
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--example', type=Path, default=DEFAULT_EXAMPLE)
    parser.add_argument('--target-ref', type=Path, help='Exact MathClaim reference JSON; default is the retained real A07 claim')
    args = parser.parse_args()
    try:
        if args.action == 'prepare':
            answer = prepare(args.run_dir, args.example, read_json(args.target_ref) if args.target_ref else DEFAULT_CLAIM)
        elif args.action == 'run':
            answer = run(args.run_dir)
        else:
            answer = status(args.run_dir, export=args.action == 'export')
        print(json.dumps(answer, ensure_ascii=False, indent=2))
        return 1 if answer.get('outcome', answer.get('state')) in {'FAILED', 'DEFERRED'} else 0
    except (InterfaceError, ContractError, sqlite3.Error, OSError, KeyError) as error:
        print(json.dumps({'error': str(error), 'scientific_acceptance_checked': False}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
