"""Training utilities for fine-tuning summarization model."""

from pathlib import Path
from typing import Optional

import torch
from datasets import Dataset, load_dataset
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    DataCollatorForSeq2Seq,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
)

from src.config import settings
from src.utils.logger import logger


class SummarizationTrainer:
    """Wrapper for HuggingFace Trainer for summarization fine-tuning."""

    def __init__(
        self,
        model: AutoModelForSeq2SeqLM,
        tokenizer: AutoTokenizer,
        train_dataset: Dataset,
        eval_dataset: Optional[Dataset] = None,
    ):
        """
        Initialize trainer.

        Args:
            model: Pre-trained model to fine-tune
            tokenizer: Tokenizer for the model
            train_dataset: Training dataset
            eval_dataset: Optional evaluation dataset
        """
        self.model = model
        self.tokenizer = tokenizer
        self.train_dataset = train_dataset
        self.eval_dataset = eval_dataset

    def train(self, output_dir: Optional[Path] = None) -> None:
        """
        Execute training.

        Args:
            output_dir: Directory to save checkpoints. If None, uses settings.
        """
        if output_dir is None:
            output_dir = settings.finetuned_model_path

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Starting training. Checkpoints will be saved to: {output_dir}")

        # Training arguments
        training_args = Seq2SeqTrainingArguments(
            output_dir=str(output_dir),
            evaluation_strategy="steps" if self.eval_dataset else "no",
            eval_steps=settings.eval_steps if self.eval_dataset else None,
            learning_rate=settings.learning_rate,
            per_device_train_batch_size=settings.batch_size,
            per_device_eval_batch_size=settings.batch_size,
            gradient_accumulation_steps=settings.gradient_accumulation_steps,
            num_train_epochs=settings.num_epochs,
            weight_decay=settings.weight_decay,
            save_steps=settings.save_steps,
            save_total_limit=settings.save_total_limit,
            warmup_steps=settings.warmup_steps,
            logging_dir=str(output_dir / "logs"),
            logging_steps=50,
            predict_with_generate=True,
            fp16=torch.cuda.is_available(),  # Use mixed precision if GPU available
            push_to_hub=False,
            load_best_model_at_end=True if self.eval_dataset else False,
        )

        # Data collator
        data_collator = DataCollatorForSeq2Seq(
            tokenizer=self.tokenizer, model=self.model
        )

        # Initialize trainer
        trainer = Seq2SeqTrainer(
            model=self.model,
            args=training_args,
            train_dataset=self.train_dataset,
            eval_dataset=self.eval_dataset,
            tokenizer=self.tokenizer,
            data_collator=data_collator,
        )

        # Train
        logger.info("Training started...")
        train_result = trainer.train()

        # Save final model
        logger.info(f"Saving final model to {output_dir}")
        trainer.save_model(str(output_dir))
        self.tokenizer.save_pretrained(str(output_dir))

        # Log training metrics
        metrics = train_result.metrics
        logger.info(f"Training completed. Metrics: {metrics}")


def prepare_dataset(
    transcripts_dir: Path, summaries_dir: Path, tokenizer: AutoTokenizer
) -> Dataset:
    """
    Prepare dataset from transcript and summary files.

    Args:
        transcripts_dir: Directory containing transcript files
        summaries_dir: Directory containing summary files
        tokenizer: Tokenizer to use for encoding

    Returns:
        Prepared HuggingFace Dataset
    """
    transcripts_dir = Path(transcripts_dir)
    summaries_dir = Path(summaries_dir)

    # Load transcript-summary pairs
    data = {"transcript": [], "summary": []}

    transcript_files = sorted(transcripts_dir.glob("*.txt"))

    for transcript_file in transcript_files:
        summary_file = summaries_dir / transcript_file.name

        if not summary_file.exists():
            logger.warning(f"Summary not found for {transcript_file.name}, skipping")
            continue

        with open(transcript_file, "r", encoding="utf-8") as f:
            transcript = f.read().strip()

        with open(summary_file, "r", encoding="utf-8") as f:
            summary = f.read().strip()

        data["transcript"].append(transcript)
        data["summary"].append(summary)

    logger.info(f"Loaded {len(data['transcript'])} transcript-summary pairs")

    # Create HuggingFace dataset
    dataset = Dataset.from_dict(data)

    # Tokenize
    def preprocess_function(examples):
        inputs = tokenizer(
            examples["transcript"],
            max_length=settings.max_input_length,
            truncation=True,
            padding="max_length",
        )

        labels = tokenizer(
            examples["summary"],
            max_length=settings.max_target_length,
            truncation=True,
            padding="max_length",
        )

        inputs["labels"] = labels["input_ids"]
        return inputs

    tokenized_dataset = dataset.map(
        preprocess_function, batched=True, remove_columns=dataset.column_names
    )

    return tokenized_dataset
