# RAG System for Financial Annual Reports

A simple, educational RAG (Retrieval-Augmented Generation) system that allows you to ask questions about financial annual reports using OpenAI embeddings, FAISS vector storage, and a Streamlit web interface.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key

### Option 1: Docker (Recommended)

1. **Clone or download this project**

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

3. **Add PDF files:**
   - Place your annual report PDFs in the `data/` directory

4. **Build and run with Docker:**
   ```bash
   # Using docker-compose (recommended)
   docker-compose up --build
   
   # Or using the run script
   ./scripts/run.sh
   ```

5. **Access the application:**
   - Open http://localhost:8501 in your browser

### Option 2: Local Python Installation

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

4. **Add PDF files:**
   - Place your annual report PDFs in the `data/` directory

5. **Create the index:**
   ```bash
   python ingest.py
   ```

6. **Start the web interface:**
   ```bash
   streamlit run streamlit_app.py
   ```

## 📁 Project Structure

```
rag_reports/
├── data/                 # Put your PDF files here
├── scripts/              # Docker and utility scripts
│   ├── build.sh         # Build Docker image
│   ├── run.sh           # Run with Docker
│   └── ingest.sh        # Ingest documents
├── utils.py             # PDF extraction and chunking utilities
├── ingest.py            # Embedding and indexing pipeline
├── query.py             # Retrieval and generation
├── streamlit_app.py     # Web UI
├── test_query.py        # Test script
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose configuration
├── .dockerignore        # Docker ignore rules
├── .env.example         # Environment variables template
├── .gitignore           # Git ignore rules
└── README.md           # This file
```

## 🔧 Usage

### Docker Usage (Recommended)

#### 1. Build the Docker Image
```bash
# Using the build script
./scripts/build.sh

# Or manually
docker build -t rag-system:latest .
```

#### 2. Run with Docker Compose
```bash
# Start the application
docker-compose up --build

# Run in background
docker-compose up -d --build
```

#### 3. Ingest Documents (if needed)
```bash
# Run ingestion inside container
docker-compose exec rag-system python ingest.py

# Or use the ingest script
docker-compose exec rag-system ./scripts/ingest.sh
```

#### 4. Access the Application
- Open http://localhost:8501 in your browser

### Local Python Usage

#### 1. Ingest Documents
```bash
python ingest.py
```

This will:
- Extract text from all PDFs in `data/` directory
- Split text into overlapping chunks (1200 chars, 300 overlap)
- Create embeddings using OpenAI's `text-embedding-3-large`
- Build FAISS index and save metadata

#### 2. Query the System

**Command line:**
```bash
python query.py
```

**Web interface:**
```bash
streamlit run streamlit_app.py
```

**Test the system:**
```bash
python test_query.py
```

## 🛠️ Configuration

### Environment Variables

Create a `.env` file with:
```
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### Chunking Parameters

In `ingest.py`, you can adjust:
- `chunk_size`: Size of each text chunk (default: 1200)
- `overlap`: Overlap between chunks (default: 300)

### Retrieval Parameters

In `query.py` or the web interface:
- `k`: Number of chunks to retrieve (default: 4)

## 📊 Technical Details

- **Embedding Model**: `text-embedding-3-large`
- **LLM Model**: `gpt-4o-mini`
- **Vector Database**: FAISS (IndexFlatL2)
- **Chunking**: Sliding window with overlap
- **Citation Format**: `[source: filename.pdf, chunk 3]`

## 🧪 Testing

Run the test script to verify everything works:

```bash
python test_query.py
```

This will test:
- Index loading
- Query retrieval
- Answer generation
- Citation formatting

## 🔍 Example Queries

Try these types of questions:
- "What was the company's revenue in 2023?"
- "What are the main financial highlights?"
- "What is the company's profit margin?"
- "What are the key risks mentioned?"
- "What is the company's market position?"

## 🚨 Troubleshooting

### Common Issues

1. **"Index files not found"**
   - Run `python ingest.py` first
   - Make sure you have PDFs in the `data/` directory

2. **"No PDF files found"**
   - Add PDF files to the `data/` directory
   - Ensure files have `.pdf` extension

3. **OpenAI API errors**
   - Check your API key in `.env`
   - Verify you have sufficient API credits
   - Check your API rate limits

4. **Poor text extraction**
   - Some PDFs may be image-based (scanned)
   - Consider using OCR tools like Tesseract for scanned PDFs

5. **FAISS index errors**
   - Delete `faiss_index.bin` and `meta.json`
   - Re-run `python ingest.py`

### Performance Tips

- **Better chunking**: Split on headings or semantic boundaries
- **Add filters**: Include year/company in metadata for filtering
- **Rerank results**: Use cross-encoder models for better ranking
- **Answer grounding**: Require exact citations for factual claims

## 💰 Cost Considerations

- **Embeddings**: Charged per token (text-embedding-3-large)
- **Generation**: Charged per token (gpt-4o-mini)
- **Tips**: Use smaller models for testing, reduce chunk count

## 🔒 Security

- Keep API keys in `.env` file (never commit to git)
- Consider redacting PII from documents
- Limit logs that contain raw text

## 🐳 Docker Deployment

### Production Deployment

For production deployment, consider:

1. **Environment Variables**: Set production environment variables
2. **Volume Persistence**: Use named volumes for data persistence
3. **Resource Limits**: Set appropriate CPU and memory limits
4. **Health Checks**: Monitor application health
5. **Logging**: Configure proper logging
6. **Security**: Use secrets management for API keys

### Docker Compose for Production

```yaml
version: '3.8'

services:
  rag-system:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - rag-data:/app/data
      - rag-index:/app
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'

volumes:
  rag-data:
  rag-index:
```

## 🚀 Next Steps

To improve the system:

1. **Better chunking**: Parse PDF structure, split on headings
2. **Add filters**: Filter by year, company, document type
3. **Reranking**: Use cross-encoder models for better results
4. **Evaluation**: Create test Q/A pairs with expected citations
5. **OCR support**: Add Tesseract for scanned PDFs
6. **Hosted vector DB**: Use Pinecone, Weaviate, or Chroma for production


