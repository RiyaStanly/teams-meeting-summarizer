"""Tests for end-to-end pipeline (mocked for speed)."""

import pytest
from unittest.mock import MagicMock, patch

from src.pipelines.end_to_end import MeetingSummarizationPipeline


@pytest.fixture
def mock_pipeline():
    """Create a mocked pipeline for testing."""
    mock_model = MagicMock()
    mock_tokenizer = MagicMock()

    with patch("src.pipelines.end_to_end.NERExtractor"):
        with patch("src.pipelines.end_to_end.generate_summary") as mock_gen:
            mock_gen.return_value = "Test summary"

            pipeline = MeetingSummarizationPipeline(
                model=mock_model, tokenizer=mock_tokenizer, ner_backend="spacy"
            )

            # Mock NER results
            pipeline.ner_extractor.extract_and_format = MagicMock(
                return_value={
                    "backend": "spacy",
                    "total_unique_entities": 5,
                    "entity_types": ["PERSON", "ORG"],
                    "entities_by_type": {
                        "PERSON": [{"entity": "Alice Smith", "count": 3, "examples": []}],
                        "ORG": [{"entity": "Acme Corp", "count": 1, "examples": []}],
                    },
                }
            )

            yield pipeline


def test_process_transcript(mock_pipeline, sample_transcript):
    """Test processing a transcript."""
    result = mock_pipeline.process_transcript(
        transcript=sample_transcript, meeting_id="test_meeting"
    )

    assert result["meeting_id"] == "test_meeting"
    assert "summary" in result
    assert "entities" in result
    assert "transcript_length" in result
    assert result["entities"]["total_unique_entities"] == 5


def test_process_file(mock_pipeline, temp_transcript_file):
    """Test processing from file."""
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "output"

        result = mock_pipeline.process_file(
            input_path=temp_transcript_file,
            output_dir=output_dir,
            meeting_id="file_test",
        )

        assert result["meeting_id"] == "file_test"
        assert output_dir.exists()
        assert (output_dir / "full_output.json").exists()
        assert (output_dir / "entities.json").exists()
        assert (output_dir / "summary.md").exists()


def test_markdown_generation(mock_pipeline, sample_transcript):
    """Test Markdown summary generation."""
    result = mock_pipeline.process_transcript(
        transcript=sample_transcript, meeting_id="md_test"
    )

    markdown = mock_pipeline._generate_markdown_summary(result)

    assert "# Meeting Summary" in markdown
    assert "## Summary" in markdown
    assert "## Named Entities" in markdown
    assert "## Metadata" in markdown
    assert "Alice Smith" in markdown
