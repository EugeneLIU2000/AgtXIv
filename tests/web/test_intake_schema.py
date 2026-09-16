"""Validate the public intake contract against actual JavaScript engine output."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import subprocess

import jsonschema
import pytest


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT / "src/agtxiv_web/analysis.schema.json").read_text())
VALIDATOR = jsonschema.Draft202012Validator(SCHEMA, format_checker=jsonschema.FormatChecker())


@pytest.fixture(scope="module")
def report():
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required to exercise the actual Web API intake engine")
    source = r"""\documentclass{article}
\title{An exact source contract}
\author{Ada Example}
\begin{definition}\label{def:x}Let $x=1$.\end{definition}
\begin{theorem}By \ref{def:x}, $x+x=2$. See \cite{source}.\end{theorem}
"""
    command = (
        'import {analyzeSource} from "./src/agtxiv_web/intake.mjs"; '
        f"const r=await analyzeSource({json.dumps(source)}); console.log(JSON.stringify(r));"
    )
    return json.loads(subprocess.check_output([node, "--input-type=module", "-e", command], cwd=ROOT, text=True, timeout=20))


def test_schema_itself_and_actual_engine_report(report):
    jsonschema.Draft202012Validator.check_schema(SCHEMA)
    VALIDATOR.validate(report)


def test_private_storage_adapter_extension_is_explicit_and_valid(report):
    hosted = copy.deepcopy(report)
    hosted["provenance"]["sourceStored"] = True
    hosted["provenance"]["sourceStorage"] = "PRIVATE_CONTENT_ADDRESSED_OBJECT_STORE"
    hosted["transport"] = {
        "requested_arxiv": "2401.01234v1",
        "retrieved_url": "https://arxiv.org/src/2401.01234v1",
        "retrieved_at": "2026-09-07T22:00:00Z",
        "archive_sha256": report["provenance"]["archiveSha256"],
    }
    hosted["scientific_assessment"] = "NOT_PERFORMED"
    VALIDATOR.validate(hosted)


@pytest.mark.parametrize("mutation", [
    lambda r: r["candidates"][0]["assessments"].update(mathematical_correctness="VERIFIED"),
    lambda r: r["candidates"][0].update(scientificallyApproved=True),
    lambda r: r.update(status="SCIENTIFICALLY_APPROVED"),
    lambda r: r["frontier"].update(scientificAssessment="PASSED"),
    lambda r: r["candidates"][0]["anchor"].update(spanSha256="unverified"),
    lambda r: r["candidates"][0]["anchor"].update(startByte=-1),
    lambda r: r["candidates"][0]["anchor"].update(path="../outside.tex"),
    lambda r: r["candidates"][1]["dependencies"][0].update(targetIds=[]),
    lambda r: r["limits"].update(maxDownloadBytes=10**12),
    lambda r: r["provenance"].update(sourceStored="probably"),
    lambda r: r["candidates"][0].pop("assessments"),
])
def test_contract_rejects_promotion_and_malformed_evidence(report, mutation):
    invalid = copy.deepcopy(report)
    mutation(invalid)
    with pytest.raises(jsonschema.ValidationError):
        VALIDATOR.validate(invalid)


@pytest.mark.parametrize("path", ["main.tex", "sections/results.tex", "论文.tex", "a b.tex"])
def test_relative_paths_accept_real_names(path):
    VALIDATOR.evolve(schema=SCHEMA["$defs"]["path"]).validate(path)


@pytest.mark.parametrize("path", ["../main.tex", "a/../main.tex", "/main.tex", "a\\main.tex", "C:/main.tex", "a\x00.tex"])
def test_relative_paths_reject_unsafe_names(path):
    with pytest.raises(jsonschema.ValidationError):
        VALIDATOR.evolve(schema=SCHEMA["$defs"]["path"]).validate(path)
