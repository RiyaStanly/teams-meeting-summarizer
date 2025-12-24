"""Central configuration module using Pydantic settings."""

import os
from pathlib import Path
from typing import List, Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Project paths
    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    data_dir: Path = Field(default="data")
    models_dir: Path = Field(default="models")
    outputs_dir: Path = Field(default="outputs")

    # Model configuration
    summarization_model: str = Field(default="facebook/bart-large-cnn")
    finetuned_model_path: Path = Field(default="models/summarizer")
    ner_backend: Literal["spacy", "huggingface"] = Field(default="spacy")
    spacy_model: str = Field(default="en_core_web_sm")
    hf_ner_model: str = Field(default="dslim/bert-base-NER")

    # Training hyperparameters
    learning_rate: float = Field(default=5e-5)
    batch_size: int = Field(default=2)
    gradient_accumulation_steps: int = Field(default=4)
    num_epochs: int = Field(default=3)
    max_input_length: int = Field(default=1024)
    max_target_length: int = Field(default=256)
    warmup_steps: int = Field(default=100)
    weight_decay: float = Field(default=0.01)
    eval_steps: int = Field(default=100)
    save_steps: int = Field(default=500)
    save_total_limit: int = Field(default=3)

    # Inference parameters
    num_beams: int = Field(default=4)
    temperature: float = Field(default=1.0)
    top_p: float = Field(default=0.95)
    do_sample: bool = Field(default=False)
    min_summary_length: int = Field(default=30)
    max_summary_length: int = Field(default=200)

    # API configuration
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_workers: int = Field(default=1)
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8501"]
    )

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO"
    )
    log_format: Literal["json", "text"] = Field(default="text")
    log_file: Path = Field(default="logs/app.log")

    # Cache directories
    hf_home: Path = Field(default=".cache/huggingface")
    transformers_cache: Path = Field(default=".cache/transformers")

    def __init__(self, **kwargs):
        """Initialize settings and resolve paths."""
        super().__init__(**kwargs)
        
        # Resolve relative paths to absolute
        if not self.data_dir.is_absolute():
            self.data_dir = self.project_root / self.data_dir
        if not self.models_dir.is_absolute():
            self.models_dir = self.project_root / self.models_dir
        if not self.outputs_dir.is_absolute():
            self.outputs_dir = self.project_root / self.outputs_dir
        if not self.finetuned_model_path.is_absolute():
            self.finetuned_model_path = self.project_root / self.finetuned_model_path
        if not self.log_file.is_absolute():
            self.log_file = self.project_root / self.log_file
        if not self.hf_home.is_absolute():
            self.hf_home = self.project_root / self.hf_home
        if not self.transformers_cache.is_absolute():
            self.transformers_cache = self.project_root / self.transformers_cache

        # Set environment variables for HuggingFace cache
        os.environ["HF_HOME"] = str(self.hf_home)
        os.environ["TRANSFORMERS_CACHE"] = str(self.transformers_cache)

    def ensure_dirs(self) -> None:
        """Create necessary directories if they don't exist."""
        directories = [
            self.data_dir,
            self.models_dir,
            self.outputs_dir,
            self.finetuned_model_path,
            self.log_file.parent,
            self.hf_home,
            self.transformers_cache,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
