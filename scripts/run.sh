#!/bin/bash

# Run script for RAG System Docker container

set -e

echo "🚀 Starting RAG System..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env file with your OpenAI API key:"
    echo "OPENAI_API_KEY=sk-your-key-here"
    exit 1
fi

# Check if data directory exists and has PDFs
if [ ! -d "data" ] || [ -z "$(ls -A data/*.pdf 2>/dev/null)" ]; then
    echo "⚠️  Warning: No PDF files found in data/ directory"
    echo "Please add PDF files to data/ directory before running"
fi

# Check if index files exist
if [ ! -f "faiss_index.bin" ] || [ ! -f "meta.json" ]; then
    echo "⚠️  Warning: Index files not found"
    echo "You may need to run 'python ingest.py' first to create the index"
fi

# Run with docker-compose
echo "🐳 Starting with docker-compose..."
docker-compose up --build

