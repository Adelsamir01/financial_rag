# RAG System for Financial Annual Reports

A simple, educational RAG (Retrieval-Augmented Generation) system that allows you to ask questions about financial annual reports using OpenAI embeddings, FAISS vector storage, and a Streamlit web interface.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- OpenAI API key

### Setup & Run

1. **Clone this repository**
   ```bash
   git clone https://github.com/Adelsamir01/financial_rag
   cd financial_rag
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

3. **Add PDF files:**
   - Place your annual report PDFs in the `data/` directory

4. **Build and run with Docker:**
   ```bash
   docker-compose up --build
   ```

5. **First-time setup - Ingest documents:**
   ```bash
   docker-compose exec rag-system python ingest.py
   ```

6. **Access the application:**
   - Open http://localhost:8501 in your browser

## 📁 Project Structure

```
rag_reports/
├── data/                 # Put your PDF files here
├── scripts/              # Docker utility scripts
├── utils.py             # PDF extraction and chunking utilities
├── ingest.py            # Embedding and indexing pipeline
├── query.py             # Retrieval and generation
├── streamlit_app.py     # Web UI
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose configuration
├── .env.example         # Environment variables template
└── README.md           # This file
```

## 🔧 Usage

### Docker Commands

```bash
# Start the application
docker-compose up -d

# Stop the application
docker-compose down

# View logs
docker-compose logs -f

# Re-ingest documents (if you add new PDFs)
docker-compose exec rag-system python ingest.py

# Access container shell
docker-compose exec rag-system bash
```

### Local Python Installation (Alternative)

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

4. **Add PDF files to `data/` directory**

5. **Create the index:**
   ```bash
   python ingest.py
   ```

6. **Start the web interface:**
   ```bash
   streamlit run streamlit_app.py
   ```

## 🛠️ Configuration

### Environment Variables

Create a `.env` file with:
```
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### System Parameters

- **Chunk Size**: 1200 characters (adjustable in `ingest.py`)
- **Overlap**: 300 characters between chunks
- **Retrieval**: Top 4 chunks per query
- **Embedding Model**: `text-embedding-3-large`
- **LLM Model**: `gpt-4o-mini`

## 🔍 Example Queries

Try these types of questions:
- "What was Tesla's revenue in 2023?"
- "What are the main financial highlights for BMW?"
- "What is Ford's profit margin?"
- "What are the key risks mentioned in the reports?"
- "Compare Tesla and BMW's performance in 2022"

## 🚨 Troubleshooting

### Common Issues

1. **"Index files not found"**
   - Run `docker-compose exec rag-system python ingest.py`
   - Make sure you have PDFs in the `data/` directory

2. **"No PDF files found"**
   - Add PDF files to the `data/` directory
   - Ensure files have `.pdf` extension

3. **OpenAI API errors**
   - Check your API key in `.env`
   - Verify you have sufficient API credits

4. **FAISS index errors**
   - Delete `faiss_index.bin` and `meta.json` inside container
   - Re-run ingestion: `docker-compose exec rag-system python ingest.py`

## 🧪 Testing

Test the system with sample queries:
```bash
# Inside container
docker-compose exec rag-system python -c "
from query import retrieve, generate_answer
hits = retrieve('What was Tesla revenue in 2023?', k=2)
print('Retrieved chunks:', len(hits))
if hits:
    answer = generate_answer('What was Tesla revenue in 2023?', hits)
    print('Answer:', answer[:200] + '...')
"
```

## 💰 Cost Considerations

- **Embeddings**: Charged per token (text-embedding-3-large)
- **Generation**: Charged per token (gpt-4o-mini)
- **Tips**: Use smaller models for testing, reduce chunk count

## 🔒 Security

- Keep API keys in `.env` file (never commit to git)
- Consider redacting PII from documents
- Limit logs that contain raw text

## 🚀 Next Steps

To improve the system:
1. **Better chunking**: Parse PDF structure, split on headings
2. **Add filters**: Filter by year, company, document type
3. **Reranking**: Use cross-encoder models for better results
4. **Evaluation**: Create test Q/A pairs with expected citations
5. **OCR support**: Add Tesseract for scanned PDFs
6. **Hosted vector DB**: Use Pinecone, Weaviate, or Chroma for production