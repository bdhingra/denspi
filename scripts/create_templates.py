"""Script to create template queries from 2-hop slot-filling queries."""

import json
import argparse
import random

def create_squad_questions(subject_list, relation_template, ans_object, id):
  qas = []
  _to_answer = lambda x: {"answer_start": 0, "text": x}
  for ii, subj in enumerate(subject_list):
    qas.append({
        "question": relation_template.replace("XXX", subj),
        "id": id + "_" + str(ii),
        "answers": [_to_answer(ans)
                    for ans in ans_object["aliases"].keys() + [ans_object["name"]]],
        })
  return {"context": "dummy", "qas": qas}

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("slot_filling_file", type=str, help="path to slot filling qrys.")
  parser.add_argument("out_file", type=str, help="path to output qrys.")
  parser.add_argument("hop", type=int, help="which hop to create template from.")
  parser.add_argument("--template_file", type=str, default=None,
                      help="JSON file with relation templates.")
  parser.add_argument("--answer_file", type=str, default=None,
                      help="answer predictions from previous hop.")
  parser.add_argument("--top_k", type=int, default=1,
                      help="number of answers to generate templates from.")
  args = parser.parse_args()

  templates = None
  if args.template_file is not None:
    with open(args.template_file) as f:
      templates = json.load(f)

  answers = None
  if args.answer_file is not None:
    with open(args.answer_file) as f:
      answers = json.load(f)

  with open(args.slot_filling_file) as f:
    paras = []
    for line in f:
      item = json.loads(line.strip())
      if templates is not None:
        if item["relation"][args.hop]["text"][0] not in templates:
          print("%s not found in templates, skipping." %
                item["relation"][args.hop]["text"][0])
          continue
        template = random.choice(
            templates[item["relation"][args.hop]["text"][0]])
      else:
        template = "XXX . " + item["relation"][args.hop]["text"][0]
      if args.hop == 0:
        subjs = [item["subject"]["name"]]
        obj = item["bridge"]
      else:
        if answers is None:
          subjs = [item["bridge"]["name"]]
        else:
          if item["id"] not in answers:
            print("answers for %s not found, skipping" % item["id"])
            continue
          subjs = answers[item["id"]][:args.top_k]
        obj = item["object"]
      paras.append(create_squad_questions(subjs, template, obj, item["id"]))

  with open(args.out_file, "w") as f:
    json.dump({"version": "2-hop", "data": [{"title": "", "paragraphs": paras}]}, f)
