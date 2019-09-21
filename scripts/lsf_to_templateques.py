"""Script to conver a squad file with LSF questions to template questions."""

import json
import argparse
import random

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("in_file", type=str, help="path to slot filling qrys.")
  parser.add_argument("out_file", type=str, help="path to output qrys.")
  parser.add_argument("template_file", type=str,
                      help="JSON file with relation templates.")
  parser.add_argument("--expand_contexts", default=False, action="store_true")
  args = parser.parse_args()

  with open(args.in_file) as f:
    data = json.load(f)

  if args.expand_contexts:
    sentence_pool = [item["context"] for item in data["data"][0]["paragraphs"]]

  with open(args.template_file) as f:
    templates = json.load(f)

  for item in data["data"][0]["paragraphs"]:
    for qa in item["qas"]:
      qa["question"] = random.choice(
          templates[qa["relation"]]).replace("XXX", qa["entity"])
    if args.expand_contexts:
      for _ in range(3):
        item["context"] += " " + random.choice(sentence_pool)

  with open(args.out_file, "w") as f:
    json.dump(data, f)
