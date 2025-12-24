"""Tests for preprocessing modules."""

import pytest

from src.preprocess.cleaner import clean_transcript, normalize_speaker_names
from src.preprocess.segmenter import parse_teams_format, segment_by_speaker


def test_clean_transcript():
    """Test transcript cleaning."""
    dirty_text = "Hello    world\n\n\n\nMultiple   spaces"
    cleaned = clean_transcript(dirty_text)

    assert "  " not in cleaned  # No double spaces
    assert "\n\n\n" not in cleaned  # Max 2 newlines
    assert cleaned == "Hello world\n\nMultiple spaces"


def test_normalize_speaker_names():
    """Test speaker name normalization."""
    text = "[10:00 AM] John Doe: Hello\n[10:01 AM] Jane Smith: Hi"
    normalized = normalize_speaker_names(text)

    assert "John Doe:" in normalized
    assert "[10:00 AM]" not in normalized or ":" in normalized


def test_segment_by_speaker(sample_transcript):
    """Test speaker segmentation."""
    segments = segment_by_speaker(sample_transcript)

    assert len(segments) > 0
    assert all(hasattr(seg, "speaker") for seg in segments)
    assert all(hasattr(seg, "text") for seg in segments)

    # Check specific speakers
    speakers = [seg.speaker for seg in segments]
    assert "Alice Smith" in speakers
    assert "Bob Johnson" in speakers
    assert "Carol Davis" in speakers


def test_parse_teams_format():
    """Test Teams JSON format parsing."""
    teams_data = {
        "messages": [
            {
                "timestamp": "2024-10-15T10:00:00Z",
                "speaker": "John Doe",
                "text": "Hello everyone",
            },
            {
                "timestamp": "2024-10-15T10:01:00Z",
                "speaker": "Jane Smith",
                "text": "Hi John",
            },
        ]
    }

    transcript = parse_teams_format(teams_data)

    assert "John Doe" in transcript
    assert "Jane Smith" in transcript
    assert "Hello everyone" in transcript
    assert "Hi John" in transcript


def test_parse_teams_format_invalid():
    """Test Teams format parsing with invalid data."""
    with pytest.raises(ValueError):
        parse_teams_format({"invalid": "data"})
