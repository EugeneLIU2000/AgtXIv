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

# ---- v1: the same figures, re-ordered ------------------------------------
# build_v1.py reads the finished chain-build.html and writes a NEW file, so a
# restructure can never damage the deck that already works. Run order matters:
# frames_v1 makes the three new frames, build_v1 places them, gen_script_v1
# re-keys the speaking script against the order build_v1 declared.
python3 frames_v1.py
python3 build_v1.py
python3 gen_script_v1.py

# ---- aqa_talk_924.pptx: the v1 order as an editable PowerPoint -------------
# deck_v1.js draws the 43 frames this project owns; merge_pptx.py copies them
# into Slide_001.pptx, which stays the base so the author's own 22 slides keep
# their theme, layouts and media exactly as they were built.
node deck_v1.js
python3 merge_pptx.py
