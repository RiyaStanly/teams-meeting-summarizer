"""Inference utilities for generating summaries."""

from typing import List, Union

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from src.config import settings
from src.utils.logger import logger


def generate_summary(
    transcript: str,
    model: AutoModelForSeq2SeqLM,
    tokenizer: AutoTokenizer,
    max_length: int = None,
    min_length: int = None,
    num_beams: int = None,
    temperature: float = None,
    do_sample: bool = None,
) -> str:
    """
    Generate summary for a single transcript.

    Args:
        transcript: Input transcript text
        model: Fine-tuned model
        tokenizer: Tokenizer
        max_length: Maximum summary length (defaults to settings)
        min_length: Minimum summary length (defaults to settings)
        num_beams: Number of beams for beam search (defaults to settings)
        temperature: Sampling temperature (defaults to settings)
        do_sample: Whether to use sampling (defaults to settings)

    Returns:
        Generated summary text
    """
    # Use settings defaults if not provided
    max_length = max_length or settings.max_summary_length
    min_length = min_length or settings.min_summary_length
    num_beams = num_beams or settings.num_beams
    temperature = temperature or settings.temperature
    do_sample = do_sample if do_sample is not None else settings.do_sample

    # Get device
    device = next(model.parameters()).device

    # Tokenize input
    inputs = tokenizer(
        transcript,
        max_length=settings.max_input_length,
        truncation=True,
        return_tensors="pt",
    )

    inputs = {k: v.to(device) for k, v in inputs.items()}

    # Generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=max_length,
            min_length=min_length,
            num_beams=num_beams,
            temperature=temperature,
            do_sample=do_sample,
            top_p=settings.top_p if do_sample else None,
            early_stopping=True,
        )

    # Decode
    summary = tokenizer.decode(outputs[0], skip_special_tokens=True)

    logger.info(f"Generated summary ({len(summary)} chars)")

    return summary


def batch_generate(
    transcripts: List[str],
    model: AutoModelForSeq2SeqLM,
    tokenizer: AutoTokenizer,
    batch_size: int = 4,
) -> List[str]:
    """
    Generate summaries for multiple transcripts in batches.

    Args:
        transcripts: List of transcript texts
        model: Fine-tuned model
        tokenizer: Tokenizer
        batch_size: Batch size for inference

    Returns:
        List of generated summaries
    """
    summaries = []

    logger.info(f"Generating summaries for {len(transcripts)} transcripts")

    for i in range(0, len(transcripts), batch_size):
        batch = transcripts[i : i + batch_size]

        batch_summaries = [
            generate_summary(transcript, model, tokenizer) for transcript in batch
        ]

        summaries.extend(batch_summaries)

        logger.info(
            f"Processed {min(i + batch_size, len(transcripts))}/{len(transcripts)}"
        )

    return summaries


def generate_structured_summary(
    transcript: str,
    model: AutoModelForSeq2SeqLM,
    tokenizer: AutoTokenizer,
) -> dict:
    """
    Generate a structured summary with multiple components.

    This function generates the base summary and then creates
    structured sections (action items, decisions, etc.).

    Args:
        transcript: Input transcript text
        model: Fine-tuned model
        tokenizer: Tokenizer

    Returns:
        Dictionary with structured summary components
    """
    # Generate main summary
    main_summary = generate_summary(transcript, model, tokenizer)

    # Extract structured components using simple heuristics
    # (In production, you might fine-tune separate models for each component)

    lines = transcript.split("\n")
    action_items = []
    decisions = []

    # Simple keyword-based extraction
    for line in lines:
        lower_line = line.lower()

        # Action items
        if any(
            keyword in lower_line
            for keyword in ["will", "should", "need to", "action", "todo", "by"]
        ):
            if ":" in line:
                action_items.append(line.split(":", 1)[1].strip())

        # Decisions
        if any(
            keyword in lower_line
            for keyword in [
                "decided",
                "approved",
                "agreed",
                "consensus",
                "resolution",
                "determine",
            ]
        ):
            if ":" in line:
                decisions.append(line.split(":", 1)[1].strip())

    return {
        "summary": main_summary,
        "action_items": action_items[:10],  # Limit to top 10
        "decisions": decisions[:5],  # Limit to top 5
        "transcript_length": len(transcript),
        "summary_length": len(main_summary),
    }
