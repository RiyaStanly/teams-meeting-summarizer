"""spaCy-based Named Entity Recognition."""

from collections import defaultdict
from typing import Dict, List

import spacy
from spacy.language import Language

from src.config import settings
from src.utils.logger import logger


class SpacyNER:
    """NER using spaCy models."""

    def __init__(self, model_name: str = None):
        """
        Initialize spaCy NER.

        Args:
            model_name: spaCy model name (default: from settings)
        """
        self.model_name = model_name or settings.spacy_model

        try:
            self.nlp: Language = spacy.load(self.model_name)
            logger.info(f"Loaded spaCy model: {self.model_name}")
        except OSError:
            logger.error(
                f"spaCy model '{self.model_name}' not found. "
                f"Please download it with: python -m spacy download {self.model_name}"
            )
            raise

    def extract_entities(self, text: str) -> Dict[str, List[Dict]]:
        """
        Extract named entities from text.

        Args:
            text: Input text

        Returns:
            Dictionary mapping entity types to lists of entity information
        """
        doc = self.nlp(text)

        # Group entities by type
        entities_by_type = defaultdict(list)

        for ent in doc.ents:
            entity_info = {
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char,
            }
            entities_by_type[ent.label_].append(entity_info)

        # Deduplicate and count frequencies
        result = {}
        for label, entities in entities_by_type.items():
            # Count occurrences
            entity_counts = defaultdict(int)
            entity_examples = defaultdict(list)

            for ent in entities:
                entity_counts[ent["text"]] += 1
                if len(entity_examples[ent["text"]]) < 3:  # Keep up to 3 examples
                    entity_examples[ent["text"]].append(
                        {"start": ent["start"], "end": ent["end"]}
                    )

            # Format results
            result[label] = [
                {
                    "entity": entity_text,
                    "count": count,
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
