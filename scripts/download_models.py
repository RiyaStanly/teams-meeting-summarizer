#!/usr/bin/env python
"""Script to download and cache pre-trained models."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.utils.logger import logger


def download_models():
    """Download all required models."""
    logger.info("="* 60)
    logger.info("Downloading Pre-trained Models")
    logger.info("=" * 60)

    # Ensure directories exist
    settings.ensure_dirs()

    # 1. Download summarization model (BART)
    logger.info(f"\n1. Downloading summarization model: {settings.summarization_model}")
    try:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(
            settings.summarization_model, cache_dir=settings.transformers_cache
        )
        model = AutoModelForSeq2SeqLM.from_pretrained(
            settings.summarization_model, cache_dir=settings.transformers_cache
        )

        logger.info(f"✓ Successfully downloaded {settings.summarization_model}")
        logger.info(f"  Model size: {model.num_parameters():,} parameters")

    except Exception as e:
        logger.error(f"✗ Failed to download summarization model: {e}")
        return False

    # 2. Download spaCy model
    logger.info(f"\n2. Downloading spaCy model: {settings.spacy_model}")
    try:
        import spacy

        # Try to load model
        try:
            nlp = spacy.load(settings.spacy_model)
            logger.info(f"✓ spaCy model {settings.spacy_model} already installed")
        except OSError:
            # Model not found, download it
            logger.info(f"  Downloading {settings.spacy_model}...")
            import subprocess

            result = subprocess.run(
                ["python", "-m", "spacy", "download", settings.spacy_model],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                logger.info(f"✓ Successfully downloaded {settings.spacy_model}")
            else:
                logger.error(f"✗ Failed to download spaCy model: {result.stderr}")
                return False

    except Exception as e:
        logger.error(f"✗ Failed to download spaCy model: {e}")
        return False

    # 3. Download HuggingFace NER model
    logger.info(f"\n3. Downloading HuggingFace NER model: {settings.hf_ner_model}")
    try:
        from transformers import pipeline

        ner_pipeline = pipeline(
            "ner", model=settings.hf_ner_model, aggregation_strategy="simple"
        )

        logger.info(f"✓ Successfully downloaded {settings.hf_ner_model}")

    except Exception as e:
        logger.error(f"✗ Failed to download HuggingFace NER model: {e}")
        return False

    logger.info("\n" + "=" * 60)
    logger.info("All models downloaded successfully!")
    logger.info("=" * 60)

    return True


if __name__ == "__main__":
    success = download_models()
    sys.exit(0 if success else 1)
