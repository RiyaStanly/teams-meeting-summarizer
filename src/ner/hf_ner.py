"""HuggingFace-based Named Entity Recognition."""

from collections import defaultdict
from typing import Dict, List

from transformers import pipeline

from src.config import settings
from src.utils.logger import logger


class HuggingFaceNER:
    """NER using HuggingFace token classification models."""

    def __init__(self, model_name: str = None):
        """
        Initialize HuggingFace NER.

        Args:
            model_name: HuggingFace model name (default: from settings)
        """
        self.model_name = model_name or settings.hf_ner_model

        logger.info(f"Loading HuggingFace NER model: {self.model_name}")
        self.pipeline = pipeline(
            "ner",
            model=self.model_name,
            aggregation_strategy="simple",  # Aggregate sub-tokens
        )
        logger.info("HuggingFace NER model loaded successfully")

    def extract_entities(self, text: str) -> Dict[str, List[Dict]]:
        """
        Extract named entities from text.

        Args:
            text: Input text

        Returns:
            Dictionary mapping entity types to lists of entity information
        """
        # Run NER pipeline
        results = self.pipeline(text)

        # Group entities by type
        entities_by_type = defaultdict(list)

        for entity in results:
            # Map HuggingFace labels to standard labels
            label = self._normalize_label(entity["entity_group"])

            entity_info = {
                "text": entity["word"].strip(),
                "label": label,
                "score": entity["score"],
                "start": entity["start"],
                "end": entity["end"],
            }
            entities_by_type[label].append(entity_info)

        # Deduplicate and count frequencies
        result = {}
        for label, entities in entities_by_type.items():
            # Count occurrences
            entity_counts = defaultdict(int)
            entity_examples = defaultdict(list)
            entity_scores = defaultdict(list)

            for ent in entities:
                entity_text = ent["text"]
                entity_counts[entity_text] += 1
                entity_scores[entity_text].append(ent["score"])

                if len(entity_examples[entity_text]) < 3:  # Keep up to 3 examples
                    entity_examples[entity_text].append(
                        {"start": ent["start"], "end": ent["end"]}
                    )

            # Format results
            result[label] = [
                {
                    "entity": entity_text,
                    "count": count,
                    "avg_confidence": sum(entity_scores[entity_text])
                    / len(entity_scores[entity_text]),
                    "examples": entity_examples[entity_text],
                }
                for entity_text, count in sorted(
                    entity_counts.items(), key=lambda x: x[1], reverse=True
                )
            ]

        logger.info(f"Extracted {sum(len(v) for v in result.values())} unique entities")

        return dict(result)

    def get_entity_summary(self, text: str) -> Dict[str, int]:
        """
        Get a summary count of entities by type.

        Args:
            text: Input text

        Returns:
            Dictionary mapping entity types to counts
        """
        entities = self.extract_entities(text)
        return {label: len(ents) for label, ents in entities.items()}

    @staticmethod
    def _normalize_label(label: str) -> str:
        """
        Normalize HuggingFace entity labels to standard format.

        Args:
            label: Original label from HF model

        Returns:
            Normalized label
        """
        # Map common HF labels to standard labels
        label_map = {
            "PER": "PERSON",
            "LOC": "LOCATION",
            "ORG": "ORGANIZATION",
            "MISC": "MISCELLANEOUS",
        }

        # Remove B-, I- prefixes if present
        clean_label = label.replace("B-", "").replace("I-", "")

        return label_map.get(clean_label, clean_label)
