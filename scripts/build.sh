#!/bin/bash

# Build script for RAG System Docker image

set -e

echo "🐳 Building RAG System Docker Image..."

# Build the Docker image
docker build -t rag-system:latest .

echo "✅ Docker image built successfully!"
echo ""
echo "📋 Available commands:"
echo "  docker run -p 8501:8501 -v \$(pwd)/data:/app/data -v \$(pwd)/.env:/app/.env rag-system:latest"
echo "  docker-compose up"
echo ""
echo "🚀 To run with docker-compose:"
echo "  1. Make sure you have PDF files in ./data/"
echo "  2. Set your OPENAI_API_KEY in .env file"
echo "  3. Run: docker-compose up"

