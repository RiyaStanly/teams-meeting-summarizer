"""Streamlit app for meeting summarization."""

import sys
from pathlib import Path

import streamlit as st

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.pipelines.end_to_end import MeetingSummarizationPipeline
from src.summarization.model_loader import load_finetuned_model
from src.utils.logger import logger

# Page config
st.set_page_config(
    page_title="Teams Meeting Summarizer", page_icon="📝", layout="wide"
)


@st.cache_resource
def load_models():
    """Load models (cached)."""
    try:
        model, tokenizer = load_finetuned_model()
        pipeline = MeetingSummarizationPipeline(
            model=model, tokenizer=tokenizer, ner_backend=settings.ner_backend
        )
        return pipeline
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        return None


def main():
    """Main Streamlit app."""
    st.title("📝 Teams Meeting Summarizer")
    st.markdown(
        "Upload a meeting transcript and get an AI-generated summary with named entity extraction."
    )

    # Sidebar
    with st.sidebar:
        st.header("Settings")
        ner_backend = st.selectbox("NER Backend", ["spacy", "huggingface"], index=0)

        st.markdown("---")
        st.markdown("### About")
        st.markdown(
            "This tool uses fine-tuned BART for summarization and spaCy/HuggingFace for NER."
        )

    # Load pipeline
    with st.spinner("Loading models..."):
        pipeline = load_models()

    if pipeline is None:
        st.error(
            "❌ Failed to load models. Please ensure models are downloaded and trained."
        )
        st.info("Run: `make setup` and `make train` to prepare the models.")
        return

    st.success("✅ Models loaded successfully!")

    # File upload
    st.header("Upload Transcript")
    uploaded_file = st.file_uploader(
        "Choose a transcript file", type=["txt", "json"], help="Upload a .txt or .json file"
    )

    # Text input
    st.markdown("**OR** paste transcript text:")
    text_input = st.text_area(
        "Transcript Text", height=200, placeholder="Paste meeting transcript here..."
    )

    meeting_id = st.text_input("Meeting ID (optional)", placeholder="e.g., meeting_001")

    # Process button
    if st.button("Generate Summary", type="primary"):
        transcript_text = None

        # Get transcript from file or text input
        if uploaded_file is not None:
            transcript_text = uploaded_file.read().decode("utf-8")
            if not meeting_id:
                meeting_id = Path(uploaded_file.name).stem
        elif text_input.strip():
            transcript_text = text_input
            if not meeting_id:
                meeting_id = "custom_input"
        else:
            st.warning("⚠️ Please upload a file or paste transcript text.")
            return

        # Process
        with st.spinner("Processing transcript..."):
            try:
                result = pipeline.process_transcript(
                    transcript=transcript_text,
                    meeting_id=meeting_id,
                    metadata={"source": "streamlit"},
                )

                # Display results
                st.header("Results")

                # Summary
                st.subheader("📄 Summary")
                st.write(result["summary"])

                # Metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Transcript Length", f"{result['transcript_length']:,} chars")
                with col2:
                    st.metric("Summary Length", f"{result['summary_length']:,} chars")
                with col3:
                    compression = (
                        result["summary_length"] / result["transcript_length"] * 100
                    )
                    st.metric("Compression", f"{compression:.1f}%")
                with col4:
                    st.metric(
                        "Entities Found", result["entities"]["total_unique_entities"]
                    )

                # Named Entities
                st.subheader("🏷️ Named Entities")

                entities = result["entities"]["entities_by_type"]

                if entities:
                    for entity_type in sorted(entities.keys()):
                        with st.expander(f"**{entity_type}** ({len(entities[entity_type])} unique)"):
                            for item in entities[entity_type][:20]:  # Show top 20
                                st.markdown(
                                    f"- **{item['entity']}** (mentioned {item['count']} time(s))"
                                )
                else:
                    st.info("No entities found in transcript.")

                # Download results
                st.subheader("💾 Download Results")

                import json

                col1, col2 = st.columns(2)

                with col1:
                    json_data = json.dumps(result, indent=2)
                    st.download_button(
                        label="Download JSON",
                        data=json_data,
                        file_name=f"{meeting_id}_results.json",
                        mime="application/json",
                    )

                with col2:
                    # Generate markdown
                    markdown = pipeline._generate_markdown_summary(result)
                    st.download_button(
                        label="Download Markdown",
                        data=markdown,
                        file_name=f"{meeting_id}_summary.md",
                        mime="text/markdown",
                    )

            except Exception as e:
                st.error(f"❌ Error processing transcript: {e}")
                logger.error(f"Streamlit error: {e}")


if __name__ == "__main__":
    main()
