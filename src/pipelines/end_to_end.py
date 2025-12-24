"""End-to-end pipeline for meeting summarization."""

from pathlib import Path
from typing import Dict, Optional, Union

from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from src.ner.unified_ner import NERExtractor
from src.preprocess.cleaner import clean_transcript
from src.summarization.inference import generate_summary
from src.utils.io import load_transcript, save_json, save_markdown
from src.utils.logger import logger


class MeetingSummarizationPipeline:
    """End-to-end pipeline for meeting transcript summarization."""

    def __init__(
        self,
        model: AutoModelForSeq2SeqLM,
        tokenizer: AutoTokenizer,
        ner_backend: str = "spacy",
    ):
        """
        Initialize pipeline.

        Args:
            model: Summarization model
            tokenizer: Tokenizer for summarization model
            ner_backend: NER backend to use ('spacy' or 'huggingface')
        """
        self.model = model
        self.tokenizer = tokenizer
        self.ner_extractor = NERExtractor(backend=ner_backend)

        logger.info(f"Initialized pipeline with NER backend: {ner_backend}")

    def process_transcript(
        self,
        transcript: str,
        meeting_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        Process a single transcript through full pipeline.

        Args:
            transcript: Raw transcript text
            meeting_id: Optional meeting identifier
            metadata: Optional metadata dictionary

        Returns:
            Dictionary containing all outputs (summary, entities, metadata)
        """
        logger.info(f"Processing transcript for meeting: {meeting_id or 'unknown'}")

        # Step 1: Clean transcript
        logger.info("Step 1/3: Cleaning transcript...")
        cleaned_transcript = clean_transcript(transcript)

        # Step 2: Generate summary
        logger.info("Step 2/3: Generating summary...")
        summary = generate_summary(cleaned_transcript, self.model, self.tokenizer)

        # Step 3: Extract entities
        logger.info("Step 3/3: Extracting named entities...")
        entities = self.ner_extractor.extract_and_format(cleaned_transcript)

        # Compile results
        result = {
            "meeting_id": meeting_id or "unknown",
            "summary": summary,
            "entities": entities,
            "metadata": metadata or {},
            "transcript_length": len(transcript),
            "cleaned_transcript_length": len(cleaned_transcript),
            "summary_length": len(summary),
        }

        logger.info(f"Processing complete for meeting: {meeting_id or 'unknown'}")

        return result

    def process_file(
        self,
        input_path: Union[str, Path],
        output_dir: Union[str, Path],
        meeting_id: Optional[str] = None,
    ) -> Dict:
        """
        Process transcript from file and save outputs.

        Args:
            input_path: Path to transcript file (.txt or .json)
            output_dir: Directory to save outputs
            meeting_id: Optional meeting identifier (defaults to filename)

        Returns:
            Dictionary containing all outputs
        """
        input_path = Path(input_path)
        output_dir = Path(output_dir)

        # Use filename as meeting_id if not provided
        if meeting_id is None:
            meeting_id = input_path.stem

        logger.info(f"Processing file: {input_path}")

        # Load transcript
        transcript = load_transcript(input_path)

        # Process
        result = self.process_transcript(transcript, meeting_id=meeting_id)

        # Save outputs
        self._save_outputs(result, output_dir)

        return result

    def _save_outputs(self, result: Dict, output_dir: Path) -> None:
        """
        Save pipeline outputs to files.

        Args:
            result: Pipeline result dictionary
            output_dir: Output directory
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        meeting_id = result["meeting_id"]

        # Save full output as JSON
        full_output_path = output_dir / "full_output.json"
        save_json(result, full_output_path)

        # Save entities as separate JSON
        entities_path = output_dir / "entities.json"
        save_json(result["entities"], entities_path)

        # Generate and save Markdown summary
        markdown_content = self._generate_markdown_summary(result)
        summary_path = output_dir / "summary.md"
        save_markdown(markdown_content, summary_path)

        logger.info(f"Outputs saved to {output_dir}")

    def _generate_markdown_summary(self, result: Dict) -> str:
        """
        Generate Markdown-formatted summary report.

        Args:
            result: Pipeline result dictionary

        Returns:
            Markdown-formatted string
        """
        meeting_id = result["meeting_id"]
        summary = result["summary"]
        entities = result["entities"]

        # Build markdown
        lines = []

        # Title
        lines.append(f"# Meeting Summary: {meeting_id}")
        lines.append("")

        # Summary section
        lines.append("## Summary")
        lines.append("")
        lines.append(summary)
        lines.append("")

        # Entities section
        lines.append("## Named Entities")
        lines.append("")
        lines.append(
            f"**Total Unique Entities:** {entities['total_unique_entities']} "
            f"(extracted using {entities['backend']})"
        )
        lines.append("")

        for entity_type in sorted(entities["entities_by_type"].keys()):
            entity_list = entities["entities_by_type"][entity_type]
            if entity_list:
                lines.append(f"### {entity_type}")
                lines.append("")
                for item in entity_list[:10]:  # Show top 10 per type
                    entity_name = item["entity"]
                    count = item["count"]
                    lines.append(f"- **{entity_name}** (mentioned {count} time(s))")
                lines.append("")

        # Metadata section
        lines.append("## Metadata")
        lines.append("")
        lines.append(f"- **Original Transcript Length:** {result['transcript_length']} characters")
        lines.append(
            f"- **Cleaned Transcript Length:** {result['cleaned_transcript_length']} characters"
        )
        lines.append(f"- **Summary Length:** {result['summary_length']} characters")
        compression_ratio = (
            result["summary_length"] / result["transcript_length"] * 100
            if result["transcript_length"] > 0
            else 0
        )
        lines.append(f"- **Compression Ratio:** {compression_ratio:.1f}%")
        lines.append("")

        return "\n".join(lines)
