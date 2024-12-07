# Hotpot:
# - названия параграфов и номера предложений,  соответствующие ответу (supporting facts)
# - сам ответ (answer)
# Musique:
# - Аналогично + есть вопросы, для которых нет ответа в контекстах, следовательно, модель должна так же распознать наличие/отсутствие ответа

# QA-metrics:
# - Exact Match: ответ полностью совпадает с реальным ответом (или одним из)
# - F1-macro: пересечение всех верных ответов с предсказанием (по токенам)

# Text quality metrics:
# - реализация тестирования другой LLM (библиотека deepeval с помощью gpt)
# 1. Create a prompt by concatenating the evaluation steps with all the arguments listed in your evaluation steps (eg., if you’re looking to evaluate coherence for an LLM output, the LLM output would be a required argument).
# 2. At the end of the prompt, ask it to generate a score between 1–5, where 5 is better than 1.
# 3. (Optional) Take the probabilities of the output tokens from the LLM to normalize the score and take their weighted summation as the final result.
# Можно взять методику сравнения ответов из статьи про граф-раг:
# Our head-to-head measures computed using an LLM evaluator are as follows:
# • Comprehensiveness. How much detail does the answer provide to cover all aspects and
# details of the question?
# • Diversity. How varied and rich is the answer in providing different perspectives and insights
# on the question?
# • Empowerment. How well does the answer help the reader understand and make informed
# judgements about the topic?
# • Directness. How specifically and clearly does the answer address the question?


# Hotpot
# Format of file with predictions: 
# {
#     'answer': {
#         'question1_id': 'answer', 
#         'question2_id': 'answer'
#     },
#     'sp': {
#         'question1_id': 'list of tuples [(name of paragraph, sentence number), (name of paragraph, sentence number)]', 
#         'question2_id': 'list of tuples [(name of paragraph, sentence number), (name of paragraph, sentence number)]'
#     }
# }
# Поле answer - это просто ответы на вопросы
# Поле sp - это  supporting facts, названия параграфа и номер предложения, в котором есть намек на ответ или сам ответ
# Таких параграфов всегда 2 в сете dev set (distractor), в сете dev set (fullwiki) их разное колчество (датасет Hotpot)


import sys
import json
import re
import string
from collections import Counter
# import pickle

def normalize_answer(s):

    def remove_articles(text):
        return re.sub(r'\b(a|an|the)\b', ' ', text)

    def white_space_fix(text):
        return ' '.join(text.split())

    def remove_punc(text):
        exclude = set(string.punctuation)
        return ''.join(ch for ch in text if ch not in exclude)

    def lower(text):
        return text.lower()

    return white_space_fix(remove_articles(remove_punc(lower(s))))


def f1_score(prediction, ground_truth):
    normalized_prediction = normalize_answer(prediction)
    normalized_ground_truth = normalize_answer(ground_truth)

    ZERO_METRIC = (0, 0, 0)

    if normalized_prediction in ['yes', 'no', 'noanswer'] and normalized_prediction != normalized_ground_truth:
        return ZERO_METRIC
    if normalized_ground_truth in ['yes', 'no', 'noanswer'] and normalized_prediction != normalized_ground_truth:
        return ZERO_METRIC

    prediction_tokens = normalized_prediction.split()
    ground_truth_tokens = normalized_ground_truth.split()
    common = Counter(prediction_tokens) & Counter(ground_truth_tokens)
    num_same = sum(common.values())
    if num_same == 0:
        return ZERO_METRIC
    precision = 1.0 * num_same / len(prediction_tokens)
    recall = 1.0 * num_same / len(ground_truth_tokens)
    f1 = (2 * precision * recall) / (precision + recall)
    return f1, precision, recall


def exact_match_score(prediction, ground_truth):
    return (normalize_answer(prediction) == normalize_answer(ground_truth))


def update_answer(metrics, prediction, gold):
    em = exact_match_score(prediction, gold)
    f1, prec, recall = f1_score(prediction, gold)
    metrics['em'] += float(em)
    metrics['f1'] += f1
    metrics['prec'] += prec
    metrics['recall'] += recall
    return em, prec, recall


def update_sp(metrics, prediction, gold):
    cur_sp_pred = set(map(tuple, prediction))
    gold_sp_pred = set(map(tuple, gold))
    tp, fp, fn = 0, 0, 0
    for e in cur_sp_pred:
        if e in gold_sp_pred:
            tp += 1
        else:
            fp += 1
    for e in gold_sp_pred:
        if e not in cur_sp_pred:
            fn += 1
    prec = 1.0 * tp / (tp + fp) if tp + fp > 0 else 0.0
    recall = 1.0 * tp / (tp + fn) if tp + fn > 0 else 0.0
    f1 = 2 * prec * recall / (prec + recall) if prec + recall > 0 else 0.0
    em = 1.0 if fp + fn == 0 else 0.0
    metrics['sp_em'] += em
    metrics['sp_f1'] += f1
    metrics['sp_prec'] += prec
    metrics['sp_recall'] += recall
    return em, prec, recall


def eval(prediction_file, gold_file):
    with open(prediction_file) as f:
        prediction = json.load(f)
    with open(gold_file) as f:
        gold = json.load(f)

    metrics = {'em': 0, 'f1': 0, 'prec': 0, 'recall': 0,
        'sp_em': 0, 'sp_f1': 0, 'sp_prec': 0, 'sp_recall': 0,
        'joint_em': 0, 'joint_f1': 0, 'joint_prec': 0, 'joint_recall': 0}
    for dp in gold:
        cur_id = dp['_id']
        can_eval_joint = True
        if cur_id not in prediction['answer']:
            print('missing answer {}'.format(cur_id))
            can_eval_joint = False
        else:
            em, prec, recall = update_answer(
                metrics, prediction['answer'][cur_id], dp['answer'])
        if cur_id not in prediction['sp']:
            print('missing sp fact {}'.format(cur_id))
            can_eval_joint = False
        else:
            sp_em, sp_prec, sp_recall = update_sp(
                metrics, prediction['sp'][cur_id], dp['supporting_facts'])

        if can_eval_joint:
            joint_prec = prec * sp_prec
            joint_recall = recall * sp_recall
            if joint_prec + joint_recall > 0:
                joint_f1 = 2 * joint_prec * joint_recall / (joint_prec + joint_recall)
            else:
                joint_f1 = 0.
            joint_em = em * sp_em

            metrics['joint_em'] += joint_em
            metrics['joint_f1'] += joint_f1
            metrics['joint_prec'] += joint_prec
            metrics['joint_recall'] += joint_recall

    N = len(gold)
    for k in metrics.keys():
        metrics[k] /= N

    print(metrics)


if __name__ == '__main__':
    eval(sys.argv[1], sys.argv[2])