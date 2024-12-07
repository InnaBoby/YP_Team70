"""
Joint/grouped score of Support and Sufficiency.
"""
from typing import Tuple, List, Dict, Union
from dataclasses import dataclass, field
from collections import defaultdict
from copy import deepcopy

class SupportMetric:
    """
    SupportMetric: Em and F1 (Similar to HotpotQA Sp metric)
    """

    def __init__(self) -> None:
        self._total_em = 0.0
        self._total_f1 = 0.0
        self._total_precision = 0.0
        self._total_recall = 0.0
        self._count = 0

    def __call__(self, predicted_support_idxs: List[int], gold_support_idxs: List[int]):

        # Taken from hotpot_eval
        cur_sp_pred = set(map(int, predicted_support_idxs))
        gold_sp_pred = set(map(int, gold_support_idxs))
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

        # In case everything is empty, set both f1, em to be 1.0.
        # Without this change, em gets 1 and f1 gets 0
        if not cur_sp_pred and not gold_sp_pred:
            f1, em = 1.0, 1.0
            f1, em = 1.0, 1.0

        self._total_em += float(em)
        self._total_f1 += f1
        self._total_precision += prec
        self._total_recall += recall
        self._count += 1

    def get_metric(self, reset: bool = False) -> Tuple[float, float]:
        """
        Returns
        -------
        Average exact match and F1 score (in that order).
        """
        exact_match = self._total_em / self._count if self._count > 0 else 0
        f1_score = self._total_f1 / self._count if self._count > 0 else 0
        # precision_score = self._total_precision / self._count if self._count > 0 else 0
        # recall_score = self._total_recall / self._count if self._count > 0 else 0

        if reset:
            self.reset()
        return exact_match, f1_score

    def reset(self):
        self._total_em = 0.0
        self._total_f1 = 0.0
        self._total_precision = 0.0
        self._total_recall = 0.0
        self._count = 0


@dataclass
class GoldPredictionInstance:
    gold_supporting_facts: List = field(default_factory=lambda: deepcopy([]))
    predicted_supporting_facts: List = field(default_factory=lambda: deepcopy([]))

    gold_sufficiencies: List = field(default_factory=lambda: deepcopy([]))
    predicted_sufficiencies: List = field(default_factory=lambda: deepcopy([]))


class GroupSupportSufficiencyMetric:
    def __init__(self) -> None:
        self.prediction_store = defaultdict(GoldPredictionInstance)
        self.support_metric = SupportMetric()

    def compute_question_scores(
        self, group: GoldPredictionInstance
    ) -> Dict[str, float]:

        # Call it only when reset=True
        assert group.gold_supporting_facts is not None
        assert group.predicted_supporting_facts is not None
        assert len(group.predicted_sufficiencies) == 2

        self.support_metric(
            group.predicted_supporting_facts, group.gold_supporting_facts
        )
        sp_em, sp_f1 = self.support_metric.get_metric(reset=True)

        sufficiency_score = group.predicted_sufficiencies == group.gold_sufficiencies
        sp_f1 = sp_f1 if sufficiency_score else 0.0
        sp_em = sp_em if sufficiency_score else 0.0
        sufficiency_score = float(sufficiency_score)

        question_scores = {"f1": sp_f1, "em": sp_em, "suff": sufficiency_score}
        return question_scores

    def __call__(
        self,
        predicted_supporting_facts: List,
        gold_supporting_facts: List,
        predicted_sufficiency: int,
        gold_sufficiency: int,
        question_id: Union[int, str],
    ) -> None:

        question_id = str(question_id)

        if gold_sufficiency == 1:
            self.prediction_store[
                question_id
            ].gold_supporting_facts = gold_supporting_facts
            self.prediction_store[
                question_id
            ].predicted_supporting_facts = predicted_supporting_facts

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