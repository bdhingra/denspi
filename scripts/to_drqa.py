"""Script to convert Squad format to DrQA format for sqlite db."""

import io
import json
import sys

in_file = sys.argv[1]
out_file = sys.argv[2]

id2text = {}
with io.open(in_file) as f:
  data = json.load(f)
  for article in data["data"]:
    my_title = u" ".join(article["title"].split("_"))
    if my_title not in id2text:
      id2text[my_title] = ""
    for item in article["paragraphs"]:
      id2text[my_title] += item["context"] + " "

with io.open(out_file, "w") as fo:
  for id, text in id2text.items():
    if isinstance(id, int):
      id = str(id)
    fo.write(json.dumps({"id": id, "text": text}) + "\n")
