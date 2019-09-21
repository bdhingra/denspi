"""Script to convert paragraphs file to Squad format with dummy questions."""

import sys
import json

version = "10K"
in_file = sys.argv[1]
out_file = sys.argv[2]
MINPARALEN = int(sys.argv[3])

data = {"version": version, "data": []}
article2idx = {}
with open(in_file) as f:
  for line in f:
    item = json.loads(line.strip())
    if len(item["context"].split()) < MINPARALEN:
        continue
    if item["wikidata_id"] not in article2idx:
      article2idx[item["wikidata_id"]] = len(data["data"])
      data["data"].append({
          "title": item["wikidata_id"],
          "paragraphs": [],
          })
    data["data"][article2idx[item["wikidata_id"]]]["paragraphs"].append({
        "context": item["context"],
        "qas": [{
            "answers": [{"answer_start": 0, "text": item["context"][:5]}],
            "question": "dummy",
            "id": item["id"],
            }]
        })

with open(out_file, "w") as f:
  json.dump(data, f)
