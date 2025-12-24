"""Metrics computation utilities."""

from typing import Dict, List

from rouge_score import rouge_scorer


def compute_rouge(
    predictions: List[str], references: List[str]
) -> Dict[str, Dict[str, float]]:
    """
    Compute ROUGE scores for predictions against references.

    Args:
        predictions: List of predicted summaries
        references: List of reference summaries

    Returns:
        Dictionary containing ROUGE-1, ROUGE-2, and ROUGE-L scores
        with precision, recall, and F1 for each
    """
    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)

    scores = {
        "rouge1": {"precision": [], "recall": [], "fmeasure": []},
        "rouge2": {"precision": [], "recall": [], "fmeasure": []},
        "rougeL": {"precision": [], "recall": [], "fmeasure": []},
    }

    for pred, ref in zip(predictions, references):
        score = scorer.score(ref, pred)
        for metric_name in ["rouge1", "rouge2", "rougeL"]:
            scores[metric_name]["precision"].append(score[metric_name].precision)
            scores[metric_name]["recall"].append(score[metric_name].recall)
            scores[metric_name]["fmeasure"].append(score[metric_name].fmeasure)

    # Calculate averages
    avg_scores = {}
    for metric_name in ["rouge1", "rouge2", "rougeL"]:
        avg_scores[metric_name] = {
            "precision": sum(scores[metric_name]["precision"])
            / len(scores[metric_name]["precision"]),
            "recall": sum(scores[metric_name]["recall"]) / len(scores[metric_name]["recall"]),
            "fmeasure": sum(scores[metric_name]["fmeasure"])
            / len(scores[metric_name]["fmeasure"]),
        }

    return avg_scores
