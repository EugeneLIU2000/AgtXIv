"""Unit tests for the schema v0.3 host. Run from the repository root:

    .venv/bin/python -m pytest 'schema v0.3/tests'

Tests use small synthetic fixtures; they call no model and run no Lean.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "host"))
