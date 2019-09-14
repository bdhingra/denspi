"""Script to convert Squad format to DrQA format for sqlite db."""

import json
import sys

in_file = sys.argv[1]
out_file = sys.argv[2]

id2text = {}
with open(in_file) as f:
  data = json.load(f)
  for article in data["data"]:
    my_title = " ".join(article["title"].split("_"))
    if my_title not in id2text:
      id2text[my_title] = ""
    for item in article["paragraphs"]:
      id2text[my_title] += item["context"] + " "

with open(out_file, "w") as fo:
  for id, text in id2text.items():
    fo.write(json.dumps({"id": str(id), "text": text}) + "\n")
