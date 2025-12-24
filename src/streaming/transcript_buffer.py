"""Transcript buffer for real-time streaming."""

from collections import deque
from typing import List, Optional

from src.config import settings
from src.utils.logger import logger


class TranscriptBuffer:
    """Buffer management for streaming transcripts with sliding window."""

    def __init__(
        self,
        buffer_size: int = None,
        overlap: int = None,
    ):
        """
        Initialize transcript buffer.

        Args:
            buffer_size: Size of buffer in words (defaults to settings)
            overlap: Number of words to overlap between chunks (defaults to settings)
        """
        self.buffer_size = buffer_size or settings.streaming_buffer_size
        self.overlap = overlap or settings.streaming_overlap

        self.buffer: deque = deque()
        self.total_words = 0
        self.chunks_generated = 0

        logger.info(
            f"Transcript buffer initialized (size={self.buffer_size}, overlap={self.overlap})"
        )

    def add_text(self, text: str) -> Optional[str]:
        """
        Add text to buffer.

        Args:
            text: Text to add

        Returns:
            Chunk of text if buffer is full, None otherwise
        """
        words = text.split()
        self.buffer.extend(words)
        self.total_words += len(words)

        # Check if buffer is full
        if len(self.buffer) >= self.buffer_size:
            return self._extract_chunk()

        return None

    def _extract_chunk(self) -> str:
        """
        Extract a chunk from the buffer and maintain overlap.

        Returns:
            Chunk of text
        """
        # Extract words up to buffer_size
        chunk_words = list(self.buffer)[:self.buffer_size]
        chunk_text = " ".join(chunk_words)

        # Remove processed words but keep overlap
        for _ in range(self.buffer_size - self.overlap):
            if self.buffer:
                self.buffer.popleft()

        self.chunks_generated += 1
        logger.info(
            f"Generated chunk #{self.chunks_generated} "
            f"({len(chunk_words)} words, buffer remaining: {len(self.buffer)})"
        )

        return chunk_text

    def get_remaining(self) -> Optional[str]:
        """
        Get remaining text in buffer.

        Returns:
            Remaining text or None if buffer is empty
        """
        if not self.buffer:
            return None

        text = " ".join(self.buffer)
        self.buffer.clear()

        logger.info(f"Flushed remaining buffer ({len(text.split())} words)")
        return text

    def clear(self):
        """Clear the buffer."""
        self.buffer.clear()
        self.total_words = 0
        self.chunks_generated = 0
        logger.info("Buffer cleared")

    def get_stats(self) -> dict:
        """
        Get buffer statistics.

        Returns:
            Dictionary with buffer stats
        """
        return {
            "total_words_processed": self.total_words,
            "chunks_generated": self.chunks_generated,
            "current_buffer_size": len(self.buffer),
            "buffer_capacity": self.buffer_size,
        }
