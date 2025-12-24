"""API endpoints for meeting summarization."""

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from src import __version__
from src.api.schemas import (
    HealthResponse,
    SummarizeRequest,
    SummarizeResponse,
    AudioUploadResponse,
)
from src.config import settings
from src.transcription.azure_stt import AzureSpeechTranscriber
from src.utils.logger import logger

# Import global pipeline from main
from src.api import main

router = APIRouter()


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_transcript(request: SummarizeRequest):
    """
    Summarize a meeting transcript provided as text.

    Args:
        request: SummarizeRequest containing transcript and optional metadata

    Returns:
        SummarizeResponse with summary, entities, and metadata

    Raises:
        HTTPException: If model not loaded or processing fails
    """
    if main.pipeline is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        logger.info(f"Processing summarization request for meeting: {request.meeting_id}")

        # Process transcript
        result = main.pipeline.process_transcript(
            transcript=request.transcript,
            meeting_id=request.meeting_id or "api_request",
            metadata=request.metadata or {},
        )

        # Calculate compression ratio
        compression_ratio = (
            result["summary_length"] / result["transcript_length"] * 100
            if result["transcript_length"] > 0
            else 0
        )

        result["compression_ratio"] = compression_ratio

        logger.info(f"Successfully processed meeting: {request.meeting_id}")

        return result

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summarize-file", response_model=SummarizeResponse)
async def summarize_file(
    file: UploadFile = File(...), meeting_id: str = None, ner_backend: str = "spacy"
):
    """
    Summarize a meeting transcript from uploaded file.

    Args:
        file: Uploaded transcript file (.txt or .json)
        meeting_id: Optional meeting identifier
        ner_backend: NER backend to use

    Returns:
        SummarizeResponse with summary, entities, and metadata

    Raises:
        HTTPException: If model not loaded, invalid file, or processing fails
    """
    if main.pipeline is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    # Validate file extension
    if not file.filename.endswith((".txt", ".json")):
        raise HTTPException(
            status_code=400, detail="Invalid file type. Only .txt and .json are supported"
        )

    try:
        logger.info(f"Processing uploaded file: {file.filename}")

        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(
            mode="wb", delete=False, suffix=Path(file.filename).suffix
        ) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        # Read and process
        from src.utils.io import load_transcript

        transcript = load_transcript(tmp_path)

        # Use filename as meeting_id if not provided
        if meeting_id is None:
            meeting_id = Path(file.filename).stem

        # Process
        result = main.pipeline.process_transcript(
            transcript=transcript, meeting_id=meeting_id, metadata={"filename": file.filename}
        )

        # Calculate compression ratio
        compression_ratio = (
            result["summary_length"] / result["transcript_length"] * 100
            if result["transcript_length"] > 0
            else 0
        )

        result["compression_ratio"] = compression_ratio

        # Cleanup temp file
        Path(tmp_path).unlink()

        logger.info(f"Successfully processed file: {file.filename}")

        return result

    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/meetings/upload-audio", response_model=AudioUploadResponse)
async def upload_audio(file: UploadFile = File(...), meeting_id: str = None):
    """
    Upload and transcribe audio file using Azure Speech-to-Text.

    Args:
        file: Audio file (WAV, MP3, M4A)
        meeting_id: Optional meeting identifier

    Returns:
        Transcript and summary
    """
    if not file.filename.endswith((".wav", ".mp3", ".m4a", ".ogg")):
        raise HTTPException(
            status_code=400, detail="Invalid audio format. Supported: WAV, MP3, M4A, OGG"
        )

    try:
        logger.info(f"Processing audio upload: {file.filename}")

        # Save uploaded file
        with tempfile.NamedTemporaryFile(
            mode="wb", delete=False, suffix=Path(file.filename).suffix
        ) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        # Transcribe using Azure Speech
        transcript = AzureSpeechTranscriber.transcribe_audio_file(tmp_path)

        if not transcript:
            raise HTTPException(status_code=500, detail="Transcription failed")

        # Generate summary if pipeline loaded
        if main.pipeline:
            result = main.pipeline.process_transcript(
                transcript=transcript,
                meeting_id=meeting_id or Path(file.filename).stem,
            )
            summary = result["summary"]
            entities = result["entities"]
        else:
            summary = ""
            entities = {}

        # Cleanup
        Path(tmp_path).unlink()

        return {
            "meeting_id": meeting_id or Path(file.filename).stem,
            "transcript": transcript,
            "summary": summary,
            "entities": entities,
            "audio_file": file.filename,
        }

    except Exception as e:
        logger.error(f"Audio upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns:
        HealthResponse with service status and configuration
    """
    azure_configured = bool(settings.azure_speech_key)
    teams_configured = bool(settings.teams_client_id)

    return {
        "status": "healthy" if main.pipeline is not None else "degraded",
        "model_loaded": main.pipeline is not None,
        "ner_backend": settings.ner_backend,
        "version": __version__,
        "azure_speech_enabled": azure_configured,
        "teams_integration_enabled": teams_configured,
    }
