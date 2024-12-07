"""
Joint/grouped score of Answer and Sufficiency.
"""
from typing import List, Dict, Union
from dataclasses import dataclass, field
from collections import defaultdict
from copy import deepcopy


"""
Answer metric -- mostly taken directly from squad_tools of allennlp.
"""
import re
import string
import collections
from typing import Tuple, List


def normalize_answer(s):
    """Lower text and remove punctuation, articles and extra whitespace."""

    def remove_articles(text):
        regex = re.compile(r"\b(a|an|the)\b", re.UNICODE)
        return re.sub(regex, " ", text)

    def white_space_fix(text):
        return " ".join(text.split())

    def remove_punc(text):
        exclude = set(string.punctuation)
        return "".join(ch for ch in text if ch not in exclude)

    def lower(text):
        return text.lower()

    return white_space_fix(remove_articles(remove_punc(lower(s))))


def get_tokens(s):
    if not s:
        return []
    return normalize_answer(s).split()


def compute_exact(a_gold, a_pred):
    return int(normalize_answer(a_gold) == normalize_answer(a_pred))


def compute_f1(a_gold, a_pred):
    gold_toks = get_tokens(a_gold)
    pred_toks = get_tokens(a_pred)
    common = collections.Counter(gold_toks) & collections.Counter(pred_toks)
    num_same = sum(common.values())
    if len(gold_toks) == 0 or len(pred_toks) == 0:
        # If either is no-answer, then F1 is 1 if they agree, 0 otherwise
        return int(gold_toks == pred_toks)
    if num_same == 0:
        return 0
    precision = 1.0 * num_same / len(pred_toks)
    recall = 1.0 * num_same / len(gold_toks)
    f1 = (2 * precision * recall) / (precision + recall)
    return f1


def metric_max_over_ground_truths(metric_fn, prediction, ground_truths):
    scores_for_ground_truths = []
    for ground_truth in ground_truths:
        score = metric_fn(prediction, ground_truth)
        scores_for_ground_truths.append(score)
    return max(scores_for_ground_truths)


class AnswerMetric:
    def __init__(self) -> None:
        self._total_em = 0.0
        self._total_f1 = 0.0
        self._count = 0

    def __call__(
        self,
        predicted_answer: str,
        ground_truth_answers: List[str],
    ):

        exact_scores = metric_max_over_ground_truths(
            compute_exact, predicted_answer, ground_truth_answers
        )
        f1_scores = metric_max_over_ground_truths(
            compute_f1, predicted_answer, ground_truth_answers
        )

        self._total_em += int(exact_scores)
        self._total_f1 += f1_scores
        self._count += 1

    def get_metric(self, reset: bool = False) -> Tuple[float, float]:
        exact_match = self._total_em / self._count if self._count > 0 else 0
        f1_score = self._total_f1 / self._count if self._count > 0 else 0
        if reset:
            self.reset()
        return exact_match, f1_score

    def reset(self):
        self._total_em = 0.0
        self._total_f1 = 0.0
        self._count = 0


@dataclass
class GoldPredictionInstance:
    gold_answers: str = None
    predicted_answer: str = None

    gold_sufficiencies: List = field(default_factory=lambda: deepcopy([]))
    predicted_sufficiencies: List = field(default_factory=lambda: deepcopy([]))


class GroupAnswerSufficiencyMetric:
    def __init__(self) -> None:
        self.prediction_store = defaultdict(GoldPredictionInstance)
        self.answer_metric = AnswerMetric()

    def compute_question_scores(
        self, group: GoldPredictionInstance
    ) -> Dict[str, float]:

        # Call it only when reset=True
        assert group.gold_answers is not None
        assert group.predicted_answer is not None
        assert len(group.predicted_sufficiencies) == 2

        assert isinstance(group.gold_answers, list)
        self.answer_metric(group.predicted_answer, group.gold_answers)
        ans_em, ans_f1 = self.answer_metric.get_metric(reset=True)

        sufficiency_score = group.predicted_sufficiencies == group.gold_sufficiencies
        ans_f1 = ans_f1 if sufficiency_score else 0.0
        ans_em = ans_em if sufficiency_score else 0.0
        sufficiency_score = float(sufficiency_score)

        question_scores = {"f1": ans_f1, "em": ans_em, "suff": sufficiency_score}
        return question_scores

    def __call__(
        self,
        predicted_answer: str,
        gold_answers: str,
        predicted_sufficiency: int,
        gold_sufficiency: int,
        question_id: Union[int, str],
    ) -> None:

        question_id = str(question_id)

        if gold_sufficiency == 1:
            self.prediction_store[question_id].predicted_answer = predicted_answer
            self.prediction_store[question_id].gold_answers = gold_answers

        self.prediction_store[question_id].predicted_sufficiencies.append(
            predicted_sufficiency
        )
        self.prediction_store[question_id].gold_sufficiencies.append(gold_sufficiency)

    def reset(self):
        self.prediction_store = defaultdict(GoldPredictionInstance)

    def get_metric(self, reset: bool = False) -> Dict[str, float]:

        total_scores = {"f1": 0.0, "em": 0.0, "suff": 0.0}
        for question_id, question_group in self.prediction_store.items():
            question_scores = self.compute_question_scores(question_group)
            # self.score_store[question_id] = question_scores
            for key, value in question_scores.items():
                total_scores[key] += value
        dataset_scores = {
            name: total_score / len(self.prediction_store)
            if len(self.prediction_store) > 0
            else 0.0
            for name, total_score in total_scores.items()
        }

        if reset:
            self.reset()

        return dataset_scores