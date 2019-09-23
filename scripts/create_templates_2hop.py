"""Script to create template queries from 2-hop slot-filling queries."""

import json
import argparse
import random
import collections

random.seed(123)

def create_squad_questions(subject_list, relation_template, ans_object, id):
  qas = []
  _to_answer = lambda x: {"answer_start": 0, "text": x}
  ii = 0
  for subj in subject_list:
    for tmpl in relation_template:
      qas.append({
          "question": tmpl.replace("XXX", subj[1]),
          "subject_confidence": subj[0],
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
  parser.add_argument("hop", type=int, help="which hop to create template from.")
  parser.add_argument("--template_file", type=str, default=None,
                      help="JSON file with relation templates.")
  parser.add_argument("--answer_file", type=str, default=None,
                      help="answer predictions from previous hop.")
  parser.add_argument("--top_k", type=int, default=1,
                      help="number of answers to generate templates from.")
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

  answers = None
  if args.answer_file is not None:
    with open(args.answer_file) as f:
      raw_answers = json.load(f)
      answers = collections.defaultdict(list)
      for id, ans in raw_answers.items():
        answers[id.rsplit("_", 1)[0]].extend(ans)
    answers = {k: sorted(v, key=lambda x: x[0], reverse=True)
            for k, v in answers.items()}
    print("%d answers available" % len(answers))

  with open(args.slot_filling_file) as f:
    paras = []
    total = 0
    for line in f:
      item = json.loads(line.strip())
      total += 1
      if templates is not None:
        if item["relation"][args.hop]["text"][0] not in templates:
          # print("%s not found in templates, skipping." %
          #       item["relation"][args.hop]["text"][0])
          continue
        max_ = min(len(templates[item["relation"][args.hop]["text"][0]]),
                   args.num_templates)
        template = random.sample(
            templates[item["relation"][args.hop]["text"][0]], max_)
      else:
        template = ["XXX . " + item["relation"][args.hop]["text"][0]]
      if args.hop == 0:
        subjs = [(1.0, item["subject"]["name"])]
        obj = item["bridge"] if "bridge" in item else item["bridge_0"]
      elif args.hop == 1:
        if answers is None:
          if "bridge" in item:
            subjs = [(1.0, item["bridge"]["name"])]
          else:
            subjs = [(1.0, item["bridge_0"]["name"])]
        else:
          if item["id"] not in answers:
            print("answers for %s not found, skipping (e.g. %s)" %
                    (item["id"], list(answers.keys())[0]))
            continue
        subjs = [ans[0:2] for ans in answers[item["id"]][:args.top_k]]
        obj = item["object"] if not "bridge_1" in item else item["bridge_1"]
      else:
        if answers is None:
          subjs = [(1.0, item["bridge_1"]["name"])]
        else:
          if item["id"] not in answers:
            print("answers for %s not found, skipping (e.g. %s)" %
                    (item["id"], list(answers.keys())[0]))
            continue
        subjs = [ans[0:2] for ans in answers[item["id"]][:args.top_k]]
        obj = item["object"]
      paras.append(create_squad_questions(subjs, template, obj, item["id"]))
  print("created %d queries, given %d inputs" % (len(paras), total))

  with open(args.out_file, "w") as f:
    json.dump({"version": "2-hop", "data": [{"title": "", "paragraphs": paras}]}, f)
