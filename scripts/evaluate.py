#!/usr/bin/env python
"""Script to evaluate the summarization model."""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.summarization.evaluator import evaluate_from_files
from src.summarization.model_loader import load_finetuned_model
from src.utils.logger import logger


def main():
    """Main evaluation function."""
    parser = argparse.ArgumentParser(description="Evaluate summarization model")

    parser.add_argument(
        "--model-dir",
        type=Path,
        default=settings.finetuned_model_path,
        help="Directory containing fine-tuned model",
    )

    parser.add_argument(
        "--test-dir",
        type=Path,
        default=settings.data_dir / "synthetic",
        help="Directory containing test transcripts and summaries",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=settings.outputs_dir / "metrics.json",
        help="Output path for metrics JSON",
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Meeting Summarization Model Evaluation")
    logger.info("=" * 60)

    # Prepare paths
    transcripts_dir = args.test_dir / "transcripts"
    summaries_dir = args.test_dir / "summaries"

    if not transcripts_dir.exists() or not summaries_dir.exists():
        logger.error(f"Test directories not found: {transcripts_dir}, {summaries_dir}")
        return 1

    # Load model
    logger.info(f"\nLoading model from: {args.model_dir}")
    model, tokenizer = load_finetuned_model(args.model_dir)

    # Evaluate
    logger.info(f"\nEvaluating on test set from {args.test_dir}")
    scores = evaluate_from_files(
        model=model,
        tokenizer=tokenizer,
        transcripts_dir=transcripts_dir,
        summaries_dir=summaries_dir,
        output_path=args.output,
    )

    # Print results
    logger.info("\n" + "=" * 60)
    logger.info("Evaluation Results (ROUGE Scores)")
    logger.info("=" * 60)

    for metric_name, metric_scores in scores.items():
        logger.info(f"\n{metric_name.upper()}:")
        logger.info(f"  Precision: {metric_scores['precision']:.4f}")
        logger.info(f"  Recall:    {metric_scores['recall']:.4f}")
        logger.info(f"  F1:        {metric_scores['fmeasure']:.4f}")

    logger.info("\n" + "=" * 60)
    logger.info(f"Metrics saved to: {args.output}")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
