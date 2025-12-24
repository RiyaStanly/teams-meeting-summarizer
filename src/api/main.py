"""FastAPI application main file."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src import __version__
from src.config import settings
from src.pipelines.end_to_end import MeetingSummarizationPipeline
from src.summarization.model_loader import load_finetuned_model
from src.utils.logger import logger

# Global variables for models (loaded at startup)
pipeline: MeetingSummarizationPipeline = None
model = None
tokenizer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for loading models at startup.

    This loads the model once when the server starts and keeps it in memory.
    """
    global pipeline, model, tokenizer

    logger.info("Loading models at startup...")

    try:
        # Load summarization model
        model, tokenizer = load_finetuned_model()

        # Initialize pipeline
        pipeline = MeetingSummarizationPipeline(
            model=model, tokenizer=tokenizer, ner_backend=settings.ner_backend
        )

        logger.info("Models loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        # Continue anyway - endpoints will handle missing models
        pipeline = None

    yield

    # Cleanup (if needed)
    logger.info("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Teams Meeting Summarizer API",
    description="AI-powered meeting transcript summarization with NER extraction",
    version=__version__,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Import routes
from src.api import endpoints

# Include routers
app.include_router(endpoints.router)
