"""Evaluation utilities for summarization model."""

from pathlib import Path
from typing import Dict, List

from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from src.summarization.inference import generate_summary
from src.utils.io import save_json
from src.utils.logger import logger
from src.utils.metrics import compute_rouge


def evaluate_model(
    model: AutoModelForSeq2SeqLM,
    tokenizer: AutoTokenizer,
    test_transcripts: List[str],
    test_summaries: List[str],
    output_path: Path = None,
) -> Dict[str, Dict[str, float]]:
    """
    Evaluate model on test set and compute ROUGE scores.

    Args:
        model: Fine-tuned model
        tokenizer: Tokenizer
        test_transcripts: List of test transcripts
        test_summaries: List of reference summaries
        output_path: Optional path to save metrics JSON

    Returns:
        Dictionary containing ROUGE scores
    """
    logger.info(f"Evaluating model on {len(test_transcripts)} examples")

    # Generate predictions
    predictions = []
    for transcript in test_transcripts:
        summary = generate_summary(transcript, model, tokenizer)
        predictions.append(summary)

    # Compute ROUGE scores
    logger.info("Computing ROUGE scores...")
    scores = compute_rouge(predictions, test_summaries)

    logger.info("Evaluation results:")
    for metric_name, metric_scores in scores.items():
        logger.info(
            f"{metric_name}: "
            f"P={metric_scores['precision']:.4f}, "
            f"R={metric_scores['recall']:.4f}, "
            f"F1={metric_scores['fmeasure']:.4f}"
        )

    # Save metrics if output path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        metrics_data = {
            "rouge_scores": scores,
            "num_examples": len(test_transcripts),
            "avg_prediction_length": sum(len(p) for p in predictions)
            / len(predictions),
            "avg_reference_length": sum(len(r) for r in test_summaries)
            / len(test_summaries),
        }

        save_json(metrics_data, output_path)
        logger.info(f"Metrics saved to {output_path}")

    return scores


def evaluate_from_files(
    model: AutoModelForSeq2SeqLM,
    tokenizer: AutoTokenizer,
    transcripts_dir: Path,
    summaries_dir: Path,
    output_path: Path = None,
) -> Dict[str, Dict[str, float]]:
    """
    Evaluate model using transcript and summary files.

    Args:
        model: Fine-tuned model
        tokenizer: Tokenizer
        transcripts_dir: Directory containing test transcripts
        summaries_dir: Directory containing reference summaries
        output_path: Optional path to save metrics

    Returns:
        Dictionary containing ROUGE scores
    """
    transcripts_dir = Path(transcripts_dir)
    summaries_dir = Path(summaries_dir)

    # Load test data
    test_transcripts = []
    test_summaries = []

    for transcript_file in sorted(transcripts_dir.glob("*.txt")):
        summary_file = summaries_dir / transcript_file.name

        if not summary_file.exists():
            logger.warning(f"Skipping {transcript_file.name}: summary not found")
            continue

        with open(transcript_file, "r", encoding="utf-8") as f:
            test_transcripts.append(f.read().strip())

        with open(summary_file, "r", encoding="utf-8") as f:
            test_summaries.append(f.read().strip())

    return evaluate_model(model, tokenizer, test_transcripts, test_summaries, output_path)
