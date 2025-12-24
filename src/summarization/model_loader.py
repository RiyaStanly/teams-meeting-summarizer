"""Model loading utilities for summarization."""

from pathlib import Path
from typing import Optional, Tuple

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from src.config import settings
from src.utils.logger import logger


def load_base_model() -> Tuple[AutoModelForSeq2SeqLM, AutoTokenizer]:
    """
    Load base pre-trained model from HuggingFace Hub.

    Returns:
        Tuple of (model, tokenizer)
    """
    logger.info(f"Loading base model: {settings.summarization_model}")

    tokenizer = AutoTokenizer.from_pretrained(
        settings.summarization_model,
        cache_dir=settings.transformers_cache,
    )

    model = AutoModelForSeq2SeqLM.from_pretrained(
        settings.summarization_model,
        cache_dir=settings.transformers_cache,
    )

    # Move to GPU if available
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)

    logger.info(f"Model loaded successfully on device: {device}")
    logger.info(f"Model parameters: {model.num_parameters():,}")

    return model, tokenizer


def load_finetuned_model(
    checkpoint_path: Optional[Path] = None,
) -> Tuple[AutoModelForSeq2SeqLM, AutoTokenizer]:
    """
    Load fine-tuned model from local checkpoint.

    Args:
        checkpoint_path: Path to model checkpoint directory.
                        If None, uses settings.finetuned_model_path

    Returns:
        Tuple of (model, tokenizer)

    Raises:
        FileNotFoundError: If checkpoint doesn't exist
    """
    if checkpoint_path is None:
        checkpoint_path = settings.finetuned_model_path

    checkpoint_path = Path(checkpoint_path)

    if not checkpoint_path.exists():
        logger.warning(
            f"Fine-tuned model not found at {checkpoint_path}. Loading base model instead."
        )
        return load_base_model()

    logger.info(f"Loading fine-tuned model from: {checkpoint_path}")

    tokenizer = AutoTokenizer.from_pretrained(checkpoint_path)
    model = AutoModelForSeq2SeqLM.from_pretrained(checkpoint_path)

    # Move to GPU if available
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)

    logger.info(f"Fine-tuned model loaded successfully on device: {device}")

    return model, tokenizer


def get_device() -> str:
    """
    Get the device to use for model inference.

    Returns:
        Device string ('cuda' or 'cpu')
    """
    if torch.cuda.is_available():
        device = "cuda"
        logger.info(f"Using GPU: {torch.cuda.get_device_name(0)}")
    else:
        device = "cpu"
        logger.info("Using CPU (GPU not available)")

    return device
