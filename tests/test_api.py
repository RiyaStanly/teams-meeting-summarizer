"""Tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from src.api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def mock_pipeline_global():
    """Mock the global pipeline to avoid loading models."""
    with patch("src.api.main.pipeline") as mock_pipe:
        with patch("src.api.endpoints.main.pipeline", mock_pipe):
            mock_pipe.process_transcript = MagicMock(
                return_value={
                    "meeting_id": "test",
                    "summary": "Test summary",
                    "entities": {"total_unique_entities": 5, "backend": "spacy"},
                    "metadata": {},
                    "transcript_length": 100,
                    "cleaned_transcript_length": 95,
                    "summary_length": 20,
                }
            )
            yield mock_pipe


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "model_loaded" in data
    assert "ner_backend" in data
    assert "version" in data


def test_summarize_endpoint(client):
    """Test summarize endpoint with text input."""
    request_data = {
        "transcript": "This is a test meeting transcript with enough content to be valid.",
        "meeting_id": "test_001",
        "metadata": {"source": "test"},
        "ner_backend": "spacy",
    }

    response = client.post("/summarize", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["meeting_id"] == "test_001"
    assert "summary" in data
    assert "entities" in data
    assert "compression_ratio" in data


def test_summarize_endpoint_validation(client):
    """Test validation on summarize endpoint."""
    # Too short transcript
    request_data = {"transcript": "short"}

    response = client.post("/summarize", json=request_data)

    assert response.status_code == 422  # Validation error


def test_summarize_file_endpoint(client, temp_transcript_file):
    """Test summarize-file endpoint."""
    with open(temp_transcript_file, "rb") as f:
        response = client.post(
            "/summarize-file",
            files={"file": ("test_meeting.txt", f, "text/plain")},
            data={"meeting_id": "file_test", "ner_backend": "spacy"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "entities" in data


def test_summarize_file_invalid_extension(client):
    """Test file upload with invalid extension."""
    response = client.post(
        "/summarize-file",
        files={"file": ("test.pdf", b"fake content", "application/pdf")},
    )

    assert response.status_code == 400
