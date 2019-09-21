"""Script to create template queries from 1-hop slot-filling queries."""

import json
import argparse
import random

random.seed(123)

def create_squad_questions(subject_list, relation_template, ans_object, id):
  qas = []
  _to_answer = lambda x: {"answer_start": 0, "text": x}
  ii = 0
  for subj in subject_list:
    for tmpl in relation_template:
      qas.append({
          "question": tmpl.replace("XXX", subj),
          "id": id + "_" + str(ii),
          "answers": [_to_answer(ans)
                      for ans in list(ans_object["aliases"].keys()) + [ans_object["name"]]],
          })
      ii += 1
  return {"context": "dummy", "qas": qas}

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("slot_filling_file", type=str, help="path to slot filling qrys.")
  parser.add_argument("out_file", type=str, help="path to output qrys.")
  parser.add_argument("--template_file", type=str, default=None,
                      help="JSON file with relation templates.")
  parser.add_argument("--num_templates", type=int, default=1,
                      help="Max number of templates to use per question")
  parser.add_argument("--max_ques", type=int, default=None,
                      help="Max number of questions to output")
  args = parser.parse_args()

  templates = None
  if args.template_file is not None:
    with open(args.template_file) as f:
      templates = json.load(f)
      del templates["instance of"]
      del templates["subclass of"]

  with open(args.slot_filling_file) as f:
    paras = []
    total = 0
    for line in f:
      item = json.loads(line.strip())
      total += 1
      if templates is not None:
        if item["relation"]["text"][0] not in templates:
          # print("%s not found in templates, skipping." %
          #       item["relation"]["text"][0])
          continue
        max_ = min(len(templates[item["relation"]["text"][0]]),
                   args.num_templates)
        template = random.sample(
            templates[item["relation"]["text"][0]], max_)
      else:
        template = ["XXX . " + item["relation"][args.hop]["text"][0]]
      subjs = [item["subject"]["name"]]
      obj = item["object"]
      paras.append(create_squad_questions(subjs, template, obj, item["id"]))
  print("found templates for %d out of %d queries." % (len(paras), total))

  if args.max_ques is not None:
    paras = random.sample(paras, args.max_ques)

  with open(args.out_file, "w") as f:
    json.dump({"version": "1-hop", "data": [{"title": "", "paragraphs": paras}]}, f)
