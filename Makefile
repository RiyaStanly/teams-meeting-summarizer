.PHONY: setup install download-models train demo api api-dev ui test clean docker-build docker-run help

# Default target
help:
	@echo "Teams Meeting Summarizer - Available Commands"
	@echo "=============================================="
	@echo "make setup          - Complete setup (install + download models)"
	@echo "make install        - Install Python dependencies"
	@echo "make download-models - Download pre-trained models"
	@echo "make train          - Train summarization model"
	@echo "make demo           - Run inference demo on sample data"
	@echo "make api            - Start FastAPI server (production)"
	@echo "make api-dev        - Start FastAPI server (development with reload)"
	@echo "make ui             - Start Streamlit UI"
	@echo "make test           - Run pytest test suite"
	@echo "make clean          - Clean generated files and caches"
	@echo "make docker-build   - Build Docker image"
	@echo "make docker-run     - Run Docker container"

# Complete setup
setup: install download-models
	@echo "✓ Setup complete! You can now run 'make train' or 'make demo'"

# Install dependencies
install:
	@echo "Installing dependencies..."
	pip install --upgrade pip
	pip install -r requirements.txt
	@echo "✓ Dependencies installed"

# Download models
download-models:
	@echo "Downloading models..."
	python scripts/download_models.py
	@echo "✓ Models downloaded"

# Train model
train:
	@echo "Training summarization model..."
	python scripts/train_summarizer.py \
		--data-dir data/synthetic \
		--output-dir models/summarizer \
		--epochs 3 \
		--batch-size 2
	@echo "✓ Training complete"

# Run inference demo
demo:
	@echo "Running inference demo..."
	python scripts/run_inference.py \
		--input data/synthetic/transcripts/meeting_001.txt \
		--output outputs/meeting_001
	@echo "✓ Demo complete. Check outputs/meeting_001/"

# Evaluate model
evaluate:
	@echo "Evaluating model..."
	python scripts/evaluate.py \
		--model-dir models/summarizer \
		--test-dir data/synthetic
	@echo "✓ Evaluation complete. Check outputs/metrics.json"

# Start API (production)
api:
	@echo "Starting API server..."
	uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Start API (development)
api-dev:
	@echo "Starting API server (development mode)..."
	uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# Start Streamlit UI
ui:
	@echo "Starting Streamlit UI..."
	streamlit run src/ui/streamlit_app.py

# Run tests
test:
	@echo "Running tests..."
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing
	@echo "✓ Tests complete. Coverage report: htmlcov/index.html"

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	rm -rf __pycache__ */__pycache__ */*/__pycache__
	rm -rf .pytest_cache .coverage htmlcov
	rm -rf outputs/*
	rm -rf logs/*
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	@echo "✓ Cleaned"

# Docker build
docker-build:
	@echo "Building Docker image..."
	docker build -t teams-meeting-summarizer:latest -f docker/Dockerfile .
	@echo "✓ Docker image built"

# Docker run
docker-run:
	@echo "Starting Docker container..."
	docker-compose -f docker/docker-compose.yml up
	@echo "✓ Container stopped"

# Install dev dependencies
install-dev:
	@echo "Installing dev dependencies..."
	pip install -r requirements-dev.txt
	@echo "✓ Dev dependencies installed"
