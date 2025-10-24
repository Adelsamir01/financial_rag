# ingest.py
import os
import json
import numpy as np
import faiss
from openai import OpenAI
from dotenv import load_dotenv
from utils import extract_text_from_pdf, chunk_text, chunk_by_sections, extract_text_and_tables_from_pdf

load_dotenv()
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

EMBED_MODEL = "text-embedding-3-large"


def extract_year_from_filename(filename):
    """Extract year from filename for temporal metadata.
    
    Args:
        filename (str): PDF filename
        
    Returns:
        int: Year extracted from filename, or 0 if not found
    """
    import re
    # Look for 4-digit year in filename
    year_match = re.search(r'20\d{2}', filename)
    if year_match:
        return int(year_match.group())
    return 0  # Default to 0 if no year found


def embed_texts(texts, batch_size=100):
    """Create embeddings for a list of texts using OpenAI with batching.
    
    Args:
        texts (list[str]): List of texts to embed
        batch_size (int): Number of texts to process per batch
        
    Returns:
        np.ndarray: Array of embeddings
    """
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        print(f"  Processing batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size} ({len(batch)} texts)")
        
        try:
            resp = client.embeddings.create(model=EMBED_MODEL, input=batch)
            batch_embs = [r.embedding for r in resp.data]
            all_embeddings.extend(batch_embs)
        except Exception as e:
            print(f"  Error processing batch {i//batch_size + 1}: {e}")
            # Add zero embeddings for failed batch
            all_embeddings.extend([[0.0] * 3072 for _ in batch])  # text-embedding-3-large has 3072 dimensions
    
    return np.array(all_embeddings, dtype="float32")


def build_index(embeddings, ids, index_path="faiss_index.bin", meta_path="meta.json"):
    """Build and save FAISS index with metadata.
    
    Args:
        embeddings (np.ndarray): Array of embeddings
        ids (dict): Metadata mapping id -> metadata
        index_path (str): Path to save FAISS index
        meta_path (str): Path to save metadata JSON
    """
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    faiss.write_index(index, index_path)

    # Save metadata mapping id -> metadata
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(ids, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # Example: ingest all PDFs in data/
    data_dir = "data"
    all_chunks = []
    metadata = []  # list of dicts {id, source, chunk_text}
    id_counter = 0
    
    print("Scanning for PDF files...")
    pdf_files = [f for f in os.listdir(data_dir) if f.lower().endswith(".pdf")]
    
    if not pdf_files:
        print("No PDF files found in data/ directory. Please add some PDF files and try again.")
        exit(1)
    
    print(f"Found {len(pdf_files)} PDF files: {pdf_files}")
    
    for fname in pdf_files:
        path = os.path.join(data_dir, fname)
        print(f"Processing {fname}...")
        
        try:
            # Extract both text and tables for better financial data coverage
            text = extract_text_and_tables_from_pdf(path)
            # Use semantic chunking for better financial data grouping
            chunks = chunk_by_sections(text, chunk_size=1200, overlap=300)
            
            # Extract year from filename for temporal metadata
            year = extract_year_from_filename(fname)
            
            for i, c in enumerate(chunks):
                meta = {
                    "id": str(id_counter), 
                    "source": fname, 
                    "chunk_index": i, 
                    "text": c[:4000],  # Truncate for storage
                    "year": year,  # Add temporal metadata
                    "report_year": year  # For filtering
                }
                metadata.append(meta)
                all_chunks.append(c)
                id_counter += 1
            
            print(f"  Extracted {len(chunks)} chunks from {fname}")
            
        except Exception as e:
            print(f"  Error processing {fname}: {e}")
            continue

    if not all_chunks:
        print("No text extracted from any PDF files.")
        exit(1)

    print(f"\nTotal extracted {len(all_chunks)} chunks from PDFs")
    print("Creating embeddings...")
    
    try:
        embs = embed_texts(all_chunks)
        print(f"Created embeddings with shape {embs.shape}")
        
        ids_for_save = {
            meta["id"]: {
                "source": meta["source"], 
                "chunk_index": meta["chunk_index"], 
                "text": meta["text"],
                "year": meta.get("year", 0),  # Include year metadata
                "report_year": meta.get("report_year", 0)  # Include report_year metadata
            } 
            for meta in metadata
        }
        
        build_index(embeddings=embs, ids=ids_for_save)
        print("Index and metadata saved successfully.")
        print(f"Index file: faiss_index.bin")
        print(f"Metadata file: meta.json")
        
    except Exception as e:
        print(f"Error creating embeddings or building index: {e}")
        exit(1)
