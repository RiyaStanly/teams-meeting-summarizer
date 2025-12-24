"""Summarization module."""

from src.summarization.evaluator import evaluate_from_files, evaluate_model
from src.summarization.inference import (
    batch_generate,
    generate_structured_summary,
    generate_summary,
)
from src.summarization.model_loader import (
    get_device,
    load_base_model,
    load_finetuned_model,
)
from src.summarization.trainer import SummarizationTrainer, prepare_dataset

__all__ = [
    "load_base_model",
    "load_finetuned_model",
    "get_device",
    "SummarizationTrainer",
    "prepare_dataset",
    "generate_summary",
    "batch_generate",
    "generate_structured_summary",
    "evaluate_model",
    "evaluate_from_files",
]
