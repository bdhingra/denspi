"""Script to convert PIQA outputs to simple outputs."""

import json
import sys

in_file = sys.argv[1]
out_file = sys.argv[2]

with open(in_file) as f:
  preds = json.load(f)

out = {}
for id_, pred in preds.items():
  out[id_] = pred[0][1]

with open(out_file, "w") as f:
  json.dump(out, f)
