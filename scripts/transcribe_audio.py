#!/usr/bin/env python
"""Script to transcribe audio files using Azure Speech-to-Text."""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.transcription.azure_stt import AzureSpeechTranscriber
from src.utils.io import save_json, save_markdown
from src.utils.logger import logger


def main():
    """Main transcription function."""
    parser = argparse.ArgumentParser(description="Transcribe audio files using Azure Speech")

    parser.add_argument(
        "--audio", type=Path, required=True, help="Path to audio file (WAV, MP3, etc.)"
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=settings.outputs_dir,
        help="Output directory for transcript",
    )

    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Use continuous recognition (better for long files)",
    )

    parser.add_argument(
        "--format", type=str, choices=["txt", "json", "both"], default="both", help="Output format"
    )

    args = parser.parse_args()

    if not args.audio.exists():
        logger.error(f"Audio file not found: {args.audio}")
        return 1

    logger.info("=" * 60)
    logger.info("Azure Speech-to-Text Transcription")
    logger.info("=" * 60)
    logger.info(f"Audio file: {args.audio}")
    logger.info(f"Output directory: {args.output}")

    # Ensure output directory exists
    args.output.mkdir(parents=True, exist_ok=True)

    # Transcribe
    try:
        if args.continuous:
            logger.info("Using continuous recognition mode...")

            def on_partial(text):
                logger.info(f"Partial: {text[:100]}...")

            transcript = AzureSpeechTranscriber.transcribe_audio_file_continuous(
                str(args.audio), on_partial=on_partial
            )
        else:
            logger.info("Using single-shot recognition mode...")
            transcript = AzureSpeechTranscriber.transcribe_audio_file(str(args.audio))

        if not transcript:
            logger.warning("No transcript generated")
            return 1

        logger.info(f"\nTranscript length: {len(transcript)} characters")
        logger.info(f"Word count: {len(transcript.split())}")

        # Save outputs
        meeting_id = args.audio.stem

        if args.format in ["txt", "both"]:
            txt_path = args.output / f"{meeting_id}_transcript.txt"
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(transcript)
            logger.info(f"Saved text transcript: {txt_path}")

        if args.format in ["json", "both"]:
            json_data = {
                "meeting_id": meeting_id,
                "audio_file": str(args.audio),
                "transcript": transcript,
                "character_count": len(transcript),
                "word_count": len(transcript.split()),
                "language": settings.azure_speech_language,
            }
            json_path = args.output / f"{meeting_id}_transcript.json"
            save_json(json_data, json_path)

        logger.info("\n" + "=" * 60)
        logger.info("Transcription completed successfully!")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
