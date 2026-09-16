#!/usr/bin/env python3
"""Explicit live smoke check: submit a public arXiv paper, validate and retain HTTP evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:8787')
    parser.add_argument('--arxiv', default='2405.08863v1')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    base = args.base_url.rstrip('/')
    started = datetime.now(timezone.utc).isoformat()

    def call(path, body=None):
        request = Request(base + path, data=None if body is None else json.dumps(body).encode(),
                          headers={} if body is None else {'Content-Type': 'application/json'})
        with urlopen(request, timeout=30) as response:
            raw = response.read()
            return response.status, {k.lower(): v for k, v in response.headers.items()}, raw, json.loads(raw)

    job_schema = json.loads((ROOT / 'web/public/api/v1/job.schema.json').read_text())
    result_schema = json.loads((ROOT / 'src/agtxiv_web/analysis.schema.json').read_text())
    validator = lambda schema, value: Draft202012Validator(schema, format_checker=FormatChecker()).validate(value)
    code, _, _, job = call('/api/v1/jobs', {'arxiv': args.arxiv})
    assert code == 202
    validator(job_schema, job)
    events = [{'observed_at': datetime.now(timezone.utc).isoformat(), 'job': job}]
    deadline = time.monotonic() + 90
    while job['status'] not in ('COMPLETED', 'FAILED', 'INTERRUPTED') and time.monotonic() < deadline:
        time.sleep(1)
        _, _, _, job = call('/api/v1/jobs/' + job['id'])
        validator(job_schema, job)
        events.append({'observed_at': datetime.now(timezone.utc).isoformat(), 'job': job})
    if job['status'] != 'COMPLETED':
        raise RuntimeError(f'No completed result: {job}')
    _, headers, raw, result = call(job['result_url'])
    validator(result_schema, result)
    assert result['paper']['arxiv']['version'] is not None
    assert result['provenance']['sourceStored'] is True
    assert result['transport']['archive_sha256'] == result['provenance']['archiveSha256']
    assert result['scientific_assessment'] == 'NOT_PERFORMED'
    assert all(set(c['assessments'].values()) == {'NO_ASSESSMENT'} for c in result['candidates'])
    _, _, reread, _ = call(job['result_url'])
    assert reread == raw
    digest = 'sha256:' + hashlib.sha256(raw).hexdigest()
    report = {'kind': 'AGTXIV_LIVE_HTTP_VERIFICATION', 'started_at': started,
              'finished_at': datetime.now(timezone.utc).isoformat(), 'base_url': base,
              'request': {'arxiv': args.arxiv}, 'events': events, 'result_sha256': digest,
              'etag': headers.get('etag'), 'analysis_id': result['analysisId'],
              'resolved_arxiv': result['paper']['arxiv'], 'title': result['paper']['title'],
              'candidates': len(result['candidates']), 'sources': len(result['sources']),
              'limits': result['limits'], 'source_sha256': result['provenance']['archiveSha256'],
              'checks': {'job_schema': 'PASS', 'full_http_result_schema': 'PASS',
                         'exact_version': 'PASS', 'retained_source': 'PASS',
                         'identical_repeat_read': 'PASS', 'six_axes_unassessed': 'PASS'},
              'scientific_acceptance': False}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'result.json').write_bytes(raw)
    (args.output / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('title', 'analysis_id', 'candidates', 'sources', 'checks')}, indent=2))


if __name__ == '__main__':
    main()
