"""I/O utilities for loading and saving data."""

import json
from pathlib import Path
from typing import Any, Dict, Union

from src.utils.logger import logger


def load_transcript(file_path: Union[str, Path]) -> str:
    """
    Load transcript from text or JSON file.

    Args:
        file_path: Path to transcript file

    Returns:
        Transcript text

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is unsupported
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Transcript file not found: {file_path}")

    if file_path.suffix == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        logger.info(f"Loaded text transcript from {file_path}")
        return content

    elif file_path.suffix == ".json":
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle Teams export format
        if "messages" in data:
            # Extract transcript from Teams format
            messages = data.get("messages", [])
            transcript_parts = []
            for msg in messages:
                speaker = msg.get("speaker", "Unknown")
                text = msg.get("text", "")
                timestamp = msg.get("timestamp", "")
                if timestamp:
                    transcript_parts.append(f"[{timestamp}] {speaker}: {text}")
                else:
                    transcript_parts.append(f"{speaker}: {text}")
            content = "\n".join(transcript_parts)
        elif "transcript" in data:
            content = data["transcript"]
        else:
            raise ValueError(f"Unsupported JSON structure in {file_path}")

        logger.info(f"Loaded JSON transcript from {file_path}")
        return content

    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")


def save_json(data: Dict[str, Any], file_path: Union[str, Path]) -> None:
    """
    Save data to JSON file.

    Args:
        data: Dictionary to save
        file_path: Output file path
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved JSON to {file_path}")


def save_markdown(content: str, file_path: Union[str, Path]) -> None:
    """
    Save content to Markdown file.

    Args:
        content: Markdown content
        file_path: Output file path
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"Saved Markdown to {file_path}")


def load_json(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        Loaded dictionary

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    logger.info(f"Loaded JSON from {file_path}")
    return data
