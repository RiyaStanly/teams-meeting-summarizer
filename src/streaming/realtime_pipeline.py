"""Real-time summarization pipeline for streaming transcripts."""

import asyncio
from typing import Callable, Dict, Optional

from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from src.ner.unified_ner import NERExtractor
from src.streaming.transcript_buffer import TranscriptBuffer
from src.summarization.inference import generate_summary
from src.utils.logger import logger


class RealtimeSummarizationPipeline:
    """Real-time summarization pipeline with incremental processing."""

    def __init__(
        self,
        model: AutoModelForSeq2SeqLM,
        tokenizer: AutoTokenizer,
        ner_backend: str = "spacy",
        on_chunk_summarized: Optional[Callable[[str, Dict], None]] = None,
        on_entity_extracted: Optional[Callable[[Dict], None]] = None,
    ):
        """
        Initialize real-time pipeline.

        Args:
            model: Summarization model
            tokenizer: Tokenizer
            ner_backend: NER backend to use
            on_chunk_summarized: Callback for chunk summaries (chunk_text, summary_data)
            on_entity_extracted: Callback for extracted entities
        """
        self.model = model
        self.tokenizer = tokenizer
        self.ner_extractor = NERExtractor(backend=ner_backend)

        self.buffer = TranscriptBuffer()
        self.on_chunk_summarized = on_chunk_summarized
        self.on_entity_extracted = on_entity_extracted

        self.chunk_summaries = []
        self.all_entities = {}
        self.complete_transcript = []

        logger.info("Real-time summarization pipeline initialized")

    async def process_text_async(self, text: str, is_final: bool = False):
        """
        Process incoming text asynchronously.

        Args:
            text: New transcript text
            is_final: Whether this is the final text
        """
        self.complete_transcript.append(text)

        # Add to buffer
        chunk = self.buffer.add_text(text)

        if chunk:
            # Process chunk
            await self._process_chunk(chunk)

        # If final, process remaining buffer
        if is_final:
            remaining = self.buffer.get_remaining()
            if remaining:
                await self._process_chunk(remaining)

            # Generate final consolidated summary
            await self._generate_final_summary()

    async def _process_chunk(self, chunk_text: str):
        """
        Process a chunk of transcript.

        Args:
            chunk_text: Chunk to process
        """
        logger.info(f"Processing chunk ({len(chunk_text)} chars)...")

        # Generate summary for chunk
        summary = await asyncio.to_thread(
            generate_summary, chunk_text, self.model, self.tokenizer
        )

        # Extract entities
        entities = await asyncio.to_thread(
            self.ner_extractor.extract_and_format, chunk_text
        )

        # Store results
        chunk_data = {
            "chunk_number": len(self.chunk_summaries) + 1,
            "summary": summary,
            "entities": entities,
            "word_count": len(chunk_text.split()),
        }

        self.chunk_summaries.append(chunk_data)

        # Merge entities
        self._merge_entities(entities)

        # Notify callbacks
        if self.on_chunk_summarized:
            await asyncio.to_thread(self.on_chunk_summarized, chunk_text, chunk_data)

        if self.on_entity_extracted:
            await asyncio.to_thread(self.on_entity_extracted, entities)

        logger.info(f"Chunk processed: {len(summary)} char summary")

    def _merge_entities(self, new_entities: Dict):
        """
        Merge new entities with existing ones.

        Args:
            new_entities: New entities to merge
        """
        for entity_type, entity_list in new_entities.get("entities_by_type", {}).items():
            if entity_type not in self.all_entities:
                self.all_entities[entity_type] = {}

            for entity_info in entity_list:
                entity_text = entity_info["entity"]
                if entity_text not in self.all_entities[entity_type]:
                    self.all_entities[entity_type][entity_text] = entity_info["count"]
                else:
                    self.all_entities[entity_type][entity_text] += entity_info["count"]

    async def _generate_final_summary(self):
        """Generate final consolidated summary from all chunks."""
        logger.info("Generating final consolidated summary...")

        # Combine all chunk summaries
        all_summaries = " ".join([chunk["summary"] for chunk in self.chunk_summaries])

        # Generate meta-summary if we have multiple chunks
        if len(self.chunk_summaries) > 1:
            final_summary = await asyncio.to_thread(
                generate_summary,
                all_summaries,
                self.model,
                self.tokenizer,
                max_length=300,
            )
        else:
            final_summary = all_summaries

        logger.info(f"Final summary generated ({len(final_summary)} chars)")

        return final_summary

    def get_results(self) -> Dict:
        """
        Get current results.

        Returns:
            Dictionary with summaries, entities, and stats
        """
        return {
            "chunk_summaries": self.chunk_summaries,
            "entities": self.all_entities,
            "transcript_parts": self.complete_transcript,
            "buffer_stats": self.buffer.get_stats(),
        }

    def reset(self):
        """Reset pipeline state."""
        self.buffer.clear()
        self.chunk_summaries = []
        self.all_entities = {}
        self.complete_transcript = []
        logger.info("Pipeline reset")
