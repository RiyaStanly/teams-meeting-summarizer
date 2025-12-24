"""Text cleaning utilities for transcript preprocessing."""

import re


def clean_transcript(text: str) -> str:
    """
    Clean transcript text by removing noise and normalizing whitespace.

    Args:
        text: Raw transcript text

    Returns:
        Cleaned transcript text
    """
    # Remove multiple spaces
    text = re.sub(r" {2,}", " ", text)

    # Remove multiple newlines (keep at most 2)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Fix common OCR errors
    text = text.replace("l1", "li")  # Common OCR mistake
    text = text.replace("0n", "on")

    # Remove special characters that don't add meaning
    text = re.sub(r"[^\w\s\.\,\!\?\:\;\-\[\]\(\)@\$\%\/]", "", text)

    # Normalize quotation marks
    text = text.replace(""", '"').replace(""", '"')
    text = text.replace("'", "'").replace("'", "'")

    # Strip leading/trailing whitespace
    text = text.strip()

    # Ensure consistent line endings
    text = text.replace("\r\n", "\n")

    return text


def normalize_speaker_names(text: str) -> str:
    """
    Normalize speaker name variations in transcript.

    Args:
        text: Transcript text with speaker names

    Returns:
        Transcript with normalized speaker names
    """
    # Common variations
    replacements = {
        r"(\w+)\s+\(.*?\):": r"\1:",  # Remove titles in parentheses
        r"(\w+)\s+-\s+": r"\1: ",  # Replace dash with colon
        r"\[[\d:APM\s]+\]\s+(\w+\s+\w+):": r"\1:",  # Remove timestamps in brackets
    }

    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)

    return text


def remove_filler_words(text: str) -> str:
    """
    Remove common filler words and verbal tics.

    Args:
        text: Input text

    Returns:
        Text with filler words removed
    """
    fillers = [
        r"\bum+\b",
        r"\buh+\b",
        r"\blike\b(?!\s+[A-Z])",  # Keep "like" when followed by proper noun
        r"\byou know\b",
        r"\bI mean\b",
        r"\bkind of\b",
        r"\bsort of\b",
    ]

    for filler in fillers:
        text = re.sub(filler, "", text, flags=re.IGNORECASE)

    # Clean up extra spaces created by removals
    text = re.sub(r" {2,}", " ", text)

    return text
