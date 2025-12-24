"""Unified NER interface with backend switching."""

from typing import Dict, List, Literal

from src.config import settings
from src.ner.hf_ner import HuggingFaceNER
from src.ner.spacy_ner import SpacyNER
from src.utils.logger import logger


class NERExtractor:
    """Unified interface for NER with switchable backends."""

    def __init__(self, backend: Literal["spacy", "huggingface"] = None):
        """
        Initialize NER extractor with specified backend.

        Args:
            backend: NER backend to use ('spacy' or 'huggingface').
                    If None, uses settings.ner_backend
        """
        self.backend = backend or settings.ner_backend

        logger.info(f"Initializing NER with backend: {self.backend}")

        if self.backend == "spacy":
            self.ner = SpacyNER()
        elif self.backend == "huggingface":
            self.ner = HuggingFaceNER()
        else:
            raise ValueError(
                f"Invalid NER backend: {self.backend}. Must be 'spacy' or 'huggingface'"
            )

    def extract_entities(self, text: str) -> Dict[str, List[Dict]]:
        """
        Extract named entities from text.

        Args:
            text: Input text

        Returns:
            Dictionary mapping entity types to lists of entity information
        """
        return self.ner.extract_entities(text)

    def get_entity_summary(self, text: str) -> Dict[str, int]:
        """
        Get a summary count of entities by type.

        Args:
            text: Input text

        Returns:
            Dictionary mapping entity types to counts
        """
        return self.ner.get_entity_summary(text)

    def format_entities(self, entities: Dict[str, List[Dict]]) -> Dict:
        """
        Format entities into a structured output.

        Args:
            entities: Raw entities dictionary from extract_entities

        Returns:
            Formatted entities dictionary with metadata
        """
        # Count total entities
        total_entities = sum(len(ents) for ents in entities.values())

        # Format for output
        formatted = {
            "backend": self.backend,
            "total_unique_entities": total_entities,
            "entity_types": list(entities.keys()),
            "entities_by_type": entities,
        }

        return formatted

    def extract_and_format(self, text: str) -> Dict:
        """
        Extract entities and return formatted output.

        Args:
            text: Input text

        Returns:
            Formatted entities dictionary
        """
        entities = self.extract_entities(text)
        return self.format_entities(entities)
