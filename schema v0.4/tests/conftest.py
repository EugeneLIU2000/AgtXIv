"""Unit tests for the schema v0.4 host on small synthetic fixtures; no model, network, Neo4j or Lean.

The virtualenv lives in the main checkout (/Users/Yingjian/Documents/GitHub/AgtXIv/.venv), also for worktrees:

    PYTHONDONTWRITEBYTECODE=1 /Users/Yingjian/Documents/GitHub/AgtXIv/.venv/bin/python -m pytest 'schema v0.4/tests' -p no:cacheprovider
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for host in (ROOT.parent / "schema v0.3" / "host", ROOT / "host"):
    if str(host) not in sys.path:
        sys.path.insert(0, str(host))
