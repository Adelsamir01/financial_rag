#!/bin/bash

# Ingest script for RAG System - runs inside Docker container

set -e

echo "📚 Ingesting documents into RAG system..."

# Check if data directory has PDF files
if [ ! -d "data" ] || [ -z "$(ls -A data/*.pdf 2>/dev/null)" ]; then
    echo "❌ Error: No PDF files found in data/ directory"
    echo "Please add PDF files to data/ directory"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env file with your OpenAI API key"
    exit 1
fi

# Run ingestion
echo "🔄 Processing PDF files and creating embeddings..."
python ingest.py

echo "✅ Ingestion completed successfully!"
echo "🚀 You can now start the web interface with:"
echo "   streamlit run streamlit_app.py"

