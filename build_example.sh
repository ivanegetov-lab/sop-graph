#!/bin/sh
# Rebuild the Plant 2 example outputs from the extractions in examples/plant-2/work.
cd "$(dirname "$0")" || exit 1
W=examples/plant-2/work
python3 scripts/sop_graph.py build --extracted $W/extracted --pages $W/pages \
  --review $W/review.json --aliases $W/aliases.json --story $W/story.json \
  --today 2026-11-11 --sample --out examples/plant-2/out
