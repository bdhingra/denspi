"""Script to aggregate answer scores from multiple questions and evaluate."""

import json
import argparse
import collections
import string
import unicodedata
import numpy as np

PUNCTUATION = set(string.punctuation)

def compute_scores(ground_truth_file, predicted_answers_file):
  """Read predictions and ground truth and return P, R, F."""
  telemetry, incorrect = read_results(ground_truth_file, predicted_answers_file)
  micro = aprf(telemetry)
  relationwise = aprf_relationwise(telemetry)
  macro = sum([val[0] for _, val in relationwise.items()])
  macro = macro / len(relationwise)
  return micro, macro, relationwise, incorrect


def read_results(ground_truth_file, predicted_answers_file):
  """Read results and ground truth and return data structure with stats."""
  with open(ground_truth_file, "r") as read:
    data_ = {}
    for line in read:
      item = json.loads(line.strip())
      if isinstance(item["relation"], dict):
        relation = item["relation"]["wikidata_id"]
      elif isinstance(item["relation"], list):
        relation = (item["relation"][0]["wikidata_id"] + "_" +
                    item["relation"][1]["wikidata_id"])
      data_[item["id"]] = [relation, item["subject"]["wikidata_id"]]
      if "is_impossible" in item and item["is_impossible"]:
        continue
      if item["object"] is None:
        continue
      if isinstance(item["object"]["mention"], dict):
        data_[item["id"]] += [item["object"]["mention"]["text"]]
      if "name" in item["object"]:
        data_[item["id"]] += [item["object"]["name"]]
      if "aliases" in item["object"]:
        data_[item["id"]] += item["object"]["aliases"].keys()
  with open(predicted_answers_file, "r") as fin:
    predictions = json.load(fin)

    telemetry, incorrect = [], []
    n = 0
    for key in data_:
      if key not in predictions:
        continue
      g = data_[key][2:]
      a = predictions[key]
      m = data_[key][:2]
      stats = score(g, a)
      telemetry.append([m[0], m[1], g, a, stats])
      if stats[0] == 0. and stats[3] > 0.:
        incorrect.append(key)
      n += 1
    return telemetry, incorrect


def aprf_relationwise(g):
  """Returns precision, recall and F score for each relation."""
  rel_to_stats = collections.defaultdict(list)
  for item in g:
    rel_to_stats[item[0]].append(item)
  rel_to_scores = {}
  for rel, stats in rel_to_stats.items():
    rel_to_scores[rel] = [aprf(stats), len(stats)]
  return rel_to_scores


def aprf(g):
  """Returns precision, recall and F of the given statistics."""
  tp, _, sys_pos, real_pos = sum([x[-1] for x in g])
  if tp == 0:
    p = r = f = 0.0
  else:
    p = tp / float(sys_pos) if sys_pos > 0 else 0.
    r = tp / float(real_pos) if real_pos > 0 else 0.
    f = 2 * p * r / (p + r)
  return np.asarray([p, r, f])


def score(gold, answer):
  """Compares answer to ground truth to return TP / FP stats."""
  if gold:
    gold = set([simplify(g) for g in gold])
  answer = simplify(answer)
  result = np.zeros(4)
  if gold:
    result[3] += 1
    if answer in gold:
      result[0] += 1
  else:
    if not answer:
      result[1] += 1
  if answer:
    result[2] += 1
  return result


def strip_accents_and_punct(text):
  """Strips accents from a piece of text."""
  text = unicodedata.normalize("NFD", text)
  output = []
  for char in text:
    if char in PUNCTUATION:
      continue
    cat = unicodedata.category(char)
    if cat == "Mn":
      continue
    output.append(char)
  return "".join(output)


def simplify(answer):
  """Pre-process answer string."""
  toks = []
  articles = {"the", "a", "an", "and", ""}
  for t in answer.strip().lower().split():
    tok = strip_accents_and_punct(t)
    if tok not in articles:
      toks.append(tok)
  return "".join(toks)


import numpy as np

def softmax(x):
    """Compute softmax values for each sets of scores in x."""
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum()

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("gt_file", type=str, help="path to slot filling qrys.")
  parser.add_argument("prediction_file", type=str, help="path to predictions.")
  parser.add_argument("out_file", type=str, help="path to output qrys.")
  parser.add_argument("--question_file", type=str, default=None,
          help="path to intermediate questions with confidences of previous hop scores.")
  parser.add_argument("--hop_function", type=str, default="mul",
                      help="JSON file with relation templates.")
  args = parser.parse_args()

  with open(args.prediction_file) as f:
    predictions = json.load(f)

  confidences = None
  if args.question_file is not None:
    Z = collections.defaultdict(list)
    id2idxinZ = {}
    questions = json.load(open(args.question_file))
    for ques in questions["data"][0]["paragraphs"]:
      for q in ques["qas"]:
        true_id = q["id"].rsplit("_", 1)[0]
        Z[true_id].append(q["subject_confidence"])
        id2idxinZ[q["id"]] = len(Z[true_id]) - 1
    Z = {id_: softmax(v) for id_, v in Z.items()}
    confidences = {}
    for ques in questions["data"][0]["paragraphs"]:
      for q in ques["qas"]:
        true_id = q["id"].rsplit("_", 1)[0]
        confidences[q["id"]] = Z[true_id][id2idxinZ[q["id"]]]
    print("Found confidence scores for %d questions." % len(confidences))

  all_answers = collections.defaultdict(list)
  for id_, pred in predictions.items():
    pred_scores = softmax([p[0] for p in pred])
    if confidences is not None:
      assert id_ in confidences, (id_, list(confidences.keys())[0])
      if args.hop_function == "mul":
        myscore = confidences[id_] * pred_scores[0]
      elif args.hop_function == "sum":
        myscore = confidences[id_] + pred_scores[0]
    else:
      myscore = pred_scores[0]
    true_id = id_.rsplit("_", 1)[0]
    all_answers[true_id].append((myscore, pred[0][1]))
  print("Found %d questions and answers." % len(all_answers))

  def _best_ans(ans_list):
    sorted_ans = sorted(enumerate(ans_list), key=lambda x: x[1][0], reverse=True)
    return sorted_ans[0][1][1]

  final_answers = {id_: _best_ans(ans_list) for id_, ans_list in all_answers.items()}
  json.dump(final_answers, open(args.out_file, "w"))

  micro, macro, _, _ = compute_scores(args.gt_file, args.out_file)
  print("Micro:", micro)
  print("Macro:", micro)
