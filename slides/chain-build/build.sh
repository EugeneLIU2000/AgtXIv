#!/bin/sh
# Rebuild the whole deck from its sources. Order matters: the figures first,
# then deck.js (which writes the pptx AND declares the frame order in
# deck-meters.json), then build_html.py (which reads that order back).
set -e
cd "$(dirname "$0")"
python3 front_native.py
python3 pptx2svg.py
python3 bridge.py
python3 motivation.py
python3 pipeline.py
python3 gen_chain.py
python3 frames.py
python3 gen_reduced.py
python3 gen_records.py
python3 opening.py          # frames 45,46,48,49 - the 613- and 74-node graphs
python3 gen_skeleton.py     # the omission model, asserted against the artefact
python3 closing.py          # frames 61-68, which read skeleton-geom.json
for f in rec-mathclaim rec-lamport; do
  rsvg-convert -w 3000 -b white "frames/$f.svg" -o "frames/$f.png"
done
node deck.js
python3 build_html.py
