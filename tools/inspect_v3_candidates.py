#!/usr/bin/env python3
"""Produce or query offline provisional source packages; never execute sources."""
from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from agtxiv_v3.candidates import (build_candidate_package, persist_candidate_package,
    query_candidate_package, robustness_proposals, build_interpretation_records, build_local_proposed_context, ROBUSTNESS_QUESTIONS)
from agtxiv_v3.contracts import ContractError, SchemaBundle, SuppliedArtifact, canonical, parse
from agtxiv_v3.intake import inspect_source_directory
from agtxiv_v3.source import SourceError
from agtxiv_v3.storage import LocalStore
from inspect_v3_source import _write_new_file


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    build = commands.add_parser('build')
    build.add_argument('root', type=Path)
    build.add_argument('--main', required=True)
    build.add_argument('--working-directory', default='.')
    build.add_argument('--robustness', action='store_true', help='Use explicit unverified static-review proposals for the byte-pinned robustness TeX')
    build.add_argument('--review-note', type=Path, help='Retain supplied static review note bytes, not authority')
    context_options = build.add_mutually_exclusive_group()
    context_options.add_argument('--local-proposed-context', action='store_true', help='Explicitly generate an unadopted policy and declared local producer; no authority grant')
    build.add_argument('--observed-at', help='Replay a caller-known observation timestamp, not a new acquisition claim')
    context_options.add_argument('--record-context', type=Path, help='Explicit JSON source_snapshot, producer, policy_ref, created_at, context_records, and artifacts (artifact_id, media_type, bytes_hex); no defaults invent authority')
    build.add_argument('--database', type=Path)
    build.add_argument('--output', type=Path, help='New report path; never overwritten')
    query = commands.add_parser('query')
    query.add_argument('--database', type=Path, required=True)
    query.add_argument('--reference', type=Path, required=True, help='JSON exact artifact reference, or previous build report')
    query.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    try:
        if args.output and args.output.exists():
            raise SourceError('Output already exists and will not be overwritten')
        if args.command == 'build':
            # Outputs inside the captured tree would change its next denominator.
            root = args.root.resolve()
            for output in (args.output, args.database):
                if output and output.resolve().is_relative_to(root):
                    raise SourceError('Generated output/database must be outside the source directory')
            inspection = inspect_source_directory(args.root, args.main, working_directory=args.working_directory)
            if args.observed_at:
                if not args.local_proposed_context:
                    raise SourceError('--observed-at requires --local-proposed-context')
                inspection = replace(inspection, observed_at=args.observed_at)
            support = ()
            if args.review_note:
                from agtxiv_v3.candidates import _artifact
                support = (_artifact(args.review_note.read_bytes(), 'text/markdown'),)
            proposals = robustness_proposals(inspection) if args.robustness else ()
            records, context_records = (), ()
            bundle = SchemaBundle()
            if args.local_proposed_context:
                context = build_local_proposed_context(inspection, bundle=bundle,
                    corpus_bytes=(Path(__file__).resolve().parents[1] / 'schema v0.0/evaluation-corpus.json').read_bytes())
                context_records = context['context_records']
                support += context['artifacts']
                records = (context['source_snapshot'], context['paper_structure'],
                    *build_interpretation_records(inspection, proposals,
                        source_snapshot=context['source_snapshot'], bundle=bundle, producer=context['producer'],
                        policy_ref=context['policy_ref'], created_at=context['created_at']))
            if args.record_context:
                context = parse(args.record_context.read_bytes())
                source = context['source_snapshot']
                context_records = tuple(context['context_records'])
                support += tuple(SuppliedArtifact(a['artifact_id'], a['media_type'], bytes.fromhex(a['bytes_hex'])) for a in context['artifacts'])
                records = (source, *build_interpretation_records(inspection, proposals,
                    source_snapshot=source, bundle=bundle, producer=context['producer'],
                    policy_ref=context['policy_ref'], created_at=context['created_at']))
            package = build_candidate_package(inspection, proposals=proposals, records=records,
                open_questions=ROBUSTNESS_QUESTIONS if args.robustness else (), supporting_artifacts=support)
            # Validate even report-only generation; no unresolved policy/hash refs
            # are silently handed off as a contract-valid candidate record set.
            if args.database:
                with LocalStore(args.database, bundle) as store:
                    persist_candidate_package(store, package, context_records=context_records)
            else:
                with LocalStore(':memory:', bundle) as store:
                    persist_candidate_package(store, package, context_records=context_records)
            result = {'mode': 'PROVISIONAL', 'package_ref': package.reference(), 'package': package.report(),
                      'records': list(package.records), 'context_records': list(context_records)}
        else:
            reference = parse(args.reference.read_bytes())
            reference = reference.get('package_ref', reference)
            with LocalStore(args.database, SchemaBundle(), readonly=True) as store:
                result = query_candidate_package(store, reference)
        data = canonical(result) + b'\n'
        if args.output:
            _write_new_file(args.output, data)
        else:
            sys.stdout.buffer.write(data)
        return 0
    except (ContractError, SourceError, OSError, KeyError, TypeError, ValueError) as error:
        print('Candidate operation failed: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
