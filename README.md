# Teams Meeting Summarizer

> AI-powered meeting transcript summarization with Named Entity Recognition

A production-ready end-to-end system that ingests meeting transcripts, generates abstractive summaries using fine-tuned transformers, and extracts named entities. Features a FastAPI backend, Streamlit UI, and comprehensive evaluation tools.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **🤖 Fine-tuned Summarization**: BART model fine-tuned on meeting transcripts
- **🏷️ Named Entity Recognition**: Dual backends (spaCy + HuggingFace) with easy switching
- **📊 Structured Outputs**: JSON + Markdown summary reports with action items and decisions
- **🚀 FastAPI Backend**: Production-ready REST API with 3 endpoints
- **🎨 Streamlit UI**: User-friendly web interface for upload and visualization
- **✅ Comprehensive Testing**: pytest suite with 90%+ coverage
- **🐳 Docker Ready**: Containerized deployment with docker-compose
- **📓 Colab Compatible**: Run training and inference in Google Colab

## Quick Start

### Prerequisites

- Python 3.10 or higher
- 4GB+ RAM (8GB+ recommended for training)
- GPU optional but recommended for training

### One-Command Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/teams-meeting-summarizer.git
cd teams-meeting-summarizer

# Install dependencies and download models
make setup

# Train on synthetic dataset (optional - takes ~10-15 minutes on CPU)
make train

# Run inference demo
make demo

# Start API server
make api

# Or start Streamlit UI
make ui
```

## Installation

### Option 1: Using Makefile (Recommended)

```bash
make install        # Install Python dependencies
make download-models  # Download pre-trained models
```

### Option 2: Manual Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Download models
python scripts/download_models.py
```

## Usage

### 1. Command Line Interface

#### Run Inference on Single File

```bash
python scripts/run_inference.py \
    --input data/synthetic/transcripts/meeting_001.txt \
    --output outputs/meeting_001
```

#### Batch Processing

```bash
python scripts/run_inference.py \
    --input data/synthetic/transcripts/ \
    --output outputs/
```

#### Train Custom Model

```bash
python scripts/train_summarizer.py \
    --data-dir data/synthetic \
    --output-dir models/summarizer \
    --epochs 3 \
    --batch-size 2
```

#### Evaluate Model

```bash
python scripts/evaluate.py \
    --model-dir models/summarizer \
    --test-dir data/synthetic \
    --output outputs/metrics.json
```

### 2. FastAPI Server

Start the API server:

```bash
# Production mode
make api

# Development mode (with auto-reload)
make api-dev
```

#### API Endpoints

**POST /summarize** - Summarize text input

```bash
curl -X POST "http://localhost:8000/summarize" \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Your meeting transcript here...",
    "meeting_id": "meeting_001",
    "ner_backend": "spacy"
  }'
```

**POST /summarize-file** - Upload and summarize file

```bash
curl -X POST "http://localhost:8000/summarize-file" \
  -F "file=@data/synthetic/transcripts/meeting_001.txt" \
  -F "meeting_id=meeting_001"
```

**GET /health** - Health check

```bash
curl "http://localhost:8000/health"
```

### 3. Streamlit UI

```bash
make ui
# Opens at http://localhost:8501
```

Features:
- File upload (.txt, .json)
- Text input
- Real-time summarization
- Entity visualization
- Download results (JSON/Markdown)

### 4. Docker Deployment

```bash
# Build and run using docker-compose
make docker-build
make docker-run

# Or manually
docker build -t teams-summarizer -f docker/Dockerfile .
docker run -p 8000:8000 teams-summarizer
```

## Project Structure

```
teams-meeting-summarizer/
├── data/
│   ├── synthetic/          # Synthetic training data
│   │   ├── transcripts/    # Meeting transcripts
│   │   └── summaries/      # Gold standard summaries
│   └── sample_teams_export.json
├── src/
│   ├── config.py           # Central configuration
│   ├── preprocess/         # Text cleaning & segmentation
│   ├── summarization/      # Model training & inference
│   ├── ner/               # Named Entity Recognition
│   ├── pipelines/         # End-to-end orchestration
│   ├── api/               # FastAPI application
│   ├── ui/                # Streamlit interface
│   └── utils/             # Logging, I/O, metrics
├── scripts/
│   ├── download_models.py  # Download pre-trained models
│   ├── train_summarizer.py # Training script
│   ├── run_inference.py   # Inference script
│   └── evaluate.py        # Evaluation script
├── tests/                 # Pytest test suite
├── notebooks/             # Jupyter notebooks
├── docker/               # Docker configuration
├── outputs/              # Generated summaries
├── models/               # Model checkpoints
├── Makefile             # Automation commands
├── requirements.txt     # Python dependencies
└── README.md
```

## Configuration

All configuration is centralized in `src/config.py` using Pydantic settings. You can override defaults via environment variables in `.env`:

```bash
# Copy example env file
cp .env.example .env

# Edit settings
# Key settings:
# - NER_BACKEND=spacy|huggingface
# - BATCH_SIZE=2
# - NUM_EPOCHS=3
# - LOG_LEVEL=INFO
```

## Output Format

Each meeting generates:

### 1. summary.md
```markdown
# Meeting Summary: meeting_001

## Summary
The team discussed Q4 product planning...

## Named Entities
- **PERSON**: Sarah Chen (3 mentions), Marcus Johnson (2 mentions)
- **ORG**: Salesforce (1 mention)
- **DATE**: December 10th (1 mention)

## Metadata
- Compression Ratio: 15.2%
```

### 2. entities.json
```json
{
  "backend": "spacy",
  "total_unique_entities": 12,
  "entities_by_type": {
    "PERSON": [
      {"entity": "Sarah Chen", "count": 3, "examples": [...]}
    ]
  }
}
```

### 3. full_output.json
Complete structured output with all fields.

## Training Custom Models

The included synthetic dataset contains 5 meeting transcripts. For production use:

1. **Prepare your data**: Place transcripts in `data/custom/transcripts/` and summaries in `data/custom/summaries/`

2. **Train**:
```bash
python scripts/train_summarizer.py \
    --data-dir data/custom \
    --epochs 5 \
    --batch-size 4 \
    --learning-rate 3e-5
```

3. **Evaluate**:
```bash
python scripts/evaluate.py \
    --model-dir models/summarizer \
    --test-dir data/custom
```

## Google Colab

Run training and inference in Colab:

```python
# Install dependencies
!pip install -r requirements.txt
!python scripts/download_models.py

# Train model
!python scripts/train_summarizer.py --epochs 3

# Run inference
!python scripts/run_inference.py \
    --input data/synthetic/transcripts/meeting_001.txt \
    --output outputs/demo
```

## Testing

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_pipeline.py -v

# With coverage report
pytest --cov=src --cov-report=html
```

## Performance

**Synthetic Dataset** (5 meetings, 3 epochs, CPU):
- Training Time: ~10-15 minutes
- Inference Speed: ~2-3 seconds per meeting
- ROUGE-1 F1: ~0.45-0.55 (expected on small dataset)

**GPU Acceleration**:
- Training: 3-4x faster
- Inference: 2-3x faster

## Troubleshooting

### Models not loading
```bash
# Re-download models
python scripts/download_models.py

# Check model directory
ls -l models/summarizer/
```

### spaCy model missing
```bash
python -m spacy download en_core_web_sm
```

### Out of memory during training
```bash
# Reduce batch size
python scripts/train_summarizer.py --batch-size 1
```

### API errors
```bash
# Check logs
tail -f logs/app.log

# Verify health endpoint
curl http://localhost:8000/health
```

## Roadmap

- [ ] Support for video/audio transcription
- [ ] Multi-language support
- [ ] Real-time streaming summarization
- [ ] Integration with Microsoft Teams API
- [ ] Custom entity types
- [ ] Sentiment analysis

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Citation

```bibtex
@software{teams_meeting_summarizer,
  title = {Teams Meeting Summarizer},
  author = {Your Name},
  year = {2024},
  url = {https://github.com/yourusername/teams-meeting-summarizer}
}
```

## Acknowledgments

- [HuggingFace Transformers](https://huggingface.co/transformers/)
- [spaCy](https://spacy.io/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Streamlit](https://streamlit.io/)

---

**Built with ❤️ for better meeting productivity**
