"""Script to aggregate answer scores from multiple questions and evaluate."""

import json
import argparse
import collections
import numpy as np

def softmax(x):
    """Compute softmax values for each sets of scores in x."""
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum()

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("prediction_file", type=str, help="path to predictions.")
  parser.add_argument("out_file", type=str, help="path to output.")
  parser.add_argument("--top_k", type=int, default=1)
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
    true_id = id_.rsplit("_", 1)[0]
    for ip, pp in enumerate(pred):
      if confidences is not None:
        assert id_ in confidences, (id_, list(confidences.keys())[0])
        if args.hop_function == "mul":
          myscore = confidences[id_] * pred_scores[ip]
        elif args.hop_function == "sum":
          myscore = confidences[id_] + pred_scores[ip]
      else:
        myscore = pred_scores[ip]
      all_answers[true_id].append((myscore, pp[1]))
  print("Found %d questions and answers." % len(all_answers))

  def _best_ans(ans_list):
    sorted_ans = sorted(enumerate(ans_list), key=lambda x: x[1][0], reverse=True)
    return sorted_ans[0][1][1]

  def _top_k_ans(ans_list, k):
    sorted_ans = sorted(ans_list, key=lambda x: x[0], reverse=True)
    return [ans[0:2] for ans in sorted_ans[:k]]

  final_answers = {id_ + "_0": _top_k_ans(ans_list, args.top_k)
                   for id_, ans_list in all_answers.items()}
  json.dump(final_answers, open(args.out_file, "w"))
