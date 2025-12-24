#!/usr/bin/env python
"""Script to train the summarization model."""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.summarization.model_loader import load_base_model
from src.summarization.trainer import SummarizationTrainer, prepare_dataset
from src.utils.logger import logger


def main():
    """Main training function."""
    parser = argparse.ArgumentParser(description="Train meeting summarization model")

    parser.add_argument(
        "--data-dir",
        type=Path,
        default=settings.data_dir / "synthetic",
        help="Directory containing transcripts and summaries subdirectories",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=settings.finetuned_model_path,
        help="Directory to save fine-tuned model",
    )

    parser.add_argument(
        "--epochs", type=int, default=settings.num_epochs, help="Number of training epochs"
    )

    parser.add_argument(
        "--batch-size", type=int, default=settings.batch_size, help="Training batch size"
    )

    parser.add_argument(
        "--learning-rate",
        type=float,
        default=settings.learning_rate,
        help="Learning rate",
    )

    parser.add_argument(
        "--eval-split",
        type=float,
        default=0.2,
        help="Fraction of data to use for evaluation",
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Meeting Summarization Model Training")
    logger.info("=" * 60)

    # Prepare paths
    transcripts_dir = args.data_dir / "transcripts"
    summaries_dir = args.data_dir / "summaries"

    if not transcripts_dir.exists() or not summaries_dir.exists():
        logger.error(f"Data directories not found: {transcripts_dir}, {summaries_dir}")
        return 1

    # Load base model
    logger.info(f"\nLoading base model: {settings.summarization_model}")
    model, tokenizer = load_base_model()

    # Prepare dataset
    logger.info(f"\nPreparing dataset from {args.data_dir}")
    dataset = prepare_dataset(transcripts_dir, summaries_dir, tokenizer)

    # Split into train/eval
    if args.eval_split > 0:
        split_dataset = dataset.train_test_split(test_size=args.eval_split, seed=42)
        train_dataset = split_dataset["train"]
        eval_dataset = split_dataset["test"]
        logger.info(f"Train size: {len(train_dataset)}, Eval size: {len(eval_dataset)}")
    else:
        train_dataset = dataset
        eval_dataset = None
        logger.info(f"Train size: {len(train_dataset)} (no evaluation set)")

    # Update settings with command-line args
    settings.num_epochs = args.epochs
    settings.batch_size = args.batch_size
    settings.learning_rate = args.learning_rate

    # Create trainer and train
    logger.info(f"\nStarting training for {args.epochs} epochs...")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Learning rate: {args.learning_rate}")
    logger.info(f"Output directory: {args.output_dir}")

    trainer = SummarizationTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
    )

    trainer.train(output_dir=args.output_dir)

    logger.info("\n" + "=" * 60)
    logger.info("Training completed successfully!")
    logger.info(f"Model saved to: {args.output_dir}")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
