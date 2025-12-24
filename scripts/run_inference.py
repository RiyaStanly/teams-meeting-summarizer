#!/usr/bin/env python
"""Script to run inference on meeting transcripts."""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.pipelines.end_to_end import MeetingSummarizationPipeline
from src.summarization.model_loader import load_finetuned_model
from src.utils.logger import logger


def main():
    """Main inference function."""
    parser = argparse.ArgumentParser(description="Run inference on meeting transcripts")

    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to transcript file (.txt or .json) or directory",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=settings.outputs_dir,
        help="Output directory for results",
    )

    parser.add_argument(
        "--model-dir",
        type=Path,
        default=settings.finetuned_model_path,
        help="Directory containing fine-tuned model",
    )

    parser.add_argument(
        "--ner-backend",
        type=str,
        choices=["spacy", "huggingface"],
        default=settings.ner_backend,
        help="NER backend to use",
    )

    parser.add_argument(
        "--meeting-id", type=str, default=None, help="Optional meeting identifier"
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Meeting Summarization Inference")
    logger.info("=" * 60)

    # Load model
    logger.info(f"\nLoading model from: {args.model_dir}")
    model, tokenizer = load_finetuned_model(args.model_dir)

    # Initialize pipeline
    logger.info(f"Initializing pipeline with NER backend: {args.ner_backend}")
    pipeline = MeetingSummarizationPipeline(
        model=model, tokenizer=tokenizer, ner_backend=args.ner_backend
    )

    # Process input
    input_path = Path(args.input)

    if input_path.is_file():
        # Single file
        logger.info(f"\nProcessing file: {input_path}")

        output_dir = args.output
        if args.meeting_id:
            output_dir = output_dir / args.meeting_id

        result = pipeline.process_file(
            input_path=input_path, output_dir=output_dir, meeting_id=args.meeting_id
        )

        logger.info("\n" + "=" * 60)
        logger.info("Inference completed successfully!")
        logger.info(f"Results saved to: {output_dir}")
        logger.info(f"Summary length: {result['summary_length']} characters")
        logger.info(f"Entities found: {result['entities']['total_unique_entities']}")
        logger.info("=" * 60)

    elif input_path.is_dir():
        # Directory of files
        logger.info(f"\nProcessing directory: {input_path}")

        transcript_files = list(input_path.glob("*.txt")) + list(input_path.glob("*.json"))

        if not transcript_files:
            logger.error(f"No transcript files found in {input_path}")
            return 1

        logger.info(f"Found {len(transcript_files)} transcript files")

        for i, transcript_file in enumerate(transcript_files, 1):
            logger.info(f"\n[{i}/{len(transcript_files)}] Processing: {transcript_file.name}")

            meeting_id = transcript_file.stem
            output_dir = args.output / meeting_id

            try:
                pipeline.process_file(
                    input_path=transcript_file, output_dir=output_dir, meeting_id=meeting_id
                )
                logger.info(f"  ✓ Completed: {transcript_file.name}")
            except Exception as e:
                logger.error(f"  ✗ Failed: {transcript_file.name} - {e}")

        logger.info("\n" + "=" * 60)
        logger.info("Batch inference completed!")
        logger.info(f"Results saved to: {args.output}")
        logger.info("=" * 60)

    else:
        logger.error(f"Input path not found: {input_path}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
