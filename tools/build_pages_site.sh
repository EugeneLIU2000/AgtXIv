#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_ARG="${1:-_site}"

if [[ "$OUTPUT_ARG" = /* ]]; then
  OUTPUT_DIR="$OUTPUT_ARG"
else
  OUTPUT_DIR="$ROOT_DIR/$OUTPUT_ARG"
fi

case "$OUTPUT_DIR" in
  "$ROOT_DIR"/*) ;;
  *)
    echo "Refusing to write outside the repository: $OUTPUT_DIR" >&2
    exit 1
    ;;
esac

if [[ "$OUTPUT_DIR" == "$ROOT_DIR" ]]; then
  echo "Refusing to replace the repository root." >&2
  exit 1
fi

rm -rf "$OUTPUT_DIR"
mkdir -p \
  "$OUTPUT_DIR/Stabilizerness" \
  "$OUTPUT_DIR/Stabilizerness/dag" \
  "$OUTPUT_DIR/graph" \
  "$OUTPUT_DIR/formal"

cp "$ROOT_DIR/pages/index.html" "$OUTPUT_DIR/index.html"
cp -R \
  "$ROOT_DIR/Stabilizerness/MathContractRegistry" \
  "$OUTPUT_DIR/Stabilizerness/"
cp \
  "$ROOT_DIR/Stabilizerness/dag/claim-dag.json" \
  "$OUTPUT_DIR/Stabilizerness/dag/claim-dag.json"
cp \
  "$ROOT_DIR/graph/paper-dependencies.json" \
  "$OUTPUT_DIR/graph/paper-dependencies.json"

rsync -a \
  --exclude='.lake/' \
  --exclude='*/.lake/' \
  --exclude='__pycache__/' \
  --exclude='*/__pycache__/' \
  --include='*/' \
  --include='*.lean' \
  --include='verification-result.json' \
  --exclude='*' \
  "$ROOT_DIR/formal/" \
  "$OUTPUT_DIR/formal/"

touch "$OUTPUT_DIR/.nojekyll"

python3 "$ROOT_DIR/tools/validate_pages_site.py" "$OUTPUT_DIR"
