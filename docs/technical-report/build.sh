#!/usr/bin/env bash
set -euo pipefail
REPORT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPORT_DIR"
if [[ "${1:-}" == "--frozen-appendix" ]]; then
  echo "Compiling the included appendix snapshot; source-schema drift is not checked."
elif [[ "$#" -eq 0 ]]; then
  python3 generate_appendix.py --check
else
  echo "Usage: bash build.sh [--frozen-appendix]" >&2
  exit 2
fi
mkdir -p build
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex > build/compile-1.txt
bibtex build/main > build/bibtex.txt
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex > build/compile-2.txt
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex > build/compile-3.txt
echo "Built $REPORT_DIR/build/main.pdf"
