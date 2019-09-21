"""Script to conver a txt corpus to squad format."""

import io
import json
import argparse

NUMPARA = 5

def _create_para(paras):
  return {
      "context": " ".join(paras),
      "qas": [],
      }

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("in_file", type=str, help="path to slot filling qrys.")
  parser.add_argument("out_file", type=str, help="path to output qrys.")
  args = parser.parse_args()

  data = {"version": "", "data": []}
  article2para = {}
  with io.open(args.in_file) as f:
    for line in f:
      title, para = line.strip().split("\t")
      if title not in article2para:
        article2para[title] = [para]
      else:
        article2para[title].append(para)
    for title, all_paras in article2para.items():
      data["data"].append({
          "title": str(title.encode("ascii", errors="ignore")),
          "paragraphs": [
              _create_para(all_paras[i:i+NUMPARA])
              for i in range(0, len(all_paras), NUMPARA)],
          })

  with open(args.out_file, "w") as f:
    json.dump(data, f)
