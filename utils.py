# utils.py
import pdfplumber
import re
import pandas as pd


def extract_text_from_pdf(path):
    """Extract text from PDF file using pdfplumber.
    
    Args:
        path (str): Path to PDF file
        
    Returns:
        str: Extracted text with basic cleanup
    """
    texts = []
    with pdfplumber.open(path) as pdf:
        for p in pdf.pages:
            txt = p.extract_text()
            if txt:
                texts.append(txt)
    full = "\n".join(texts)
    # Basic cleanup - normalize multiple newlines
    full = re.sub(r"\n{2,}", "\n\n", full)
    return full


def extract_tables_from_pdf(path):
    """Extract tables from PDF file using pdfplumber.
    
    Args:
        path (str): Path to PDF file
        
    Returns:
        list[str]: List of formatted table strings
    """
    tables = []
    with pdfplumber.open(path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            # Extract tables from each page
            page_tables = page.extract_tables()
            
            for table_num, table in enumerate(page_tables):
                if table and len(table) > 1:  # Ensure table has data
                    # Convert table to formatted string
                    table_str = format_table_as_text(table, page_num, table_num)
                    if table_str:
                        tables.append(table_str)
    
    return tables


def format_table_as_text(table, page_num, table_num):
    """Format a table as readable text with context.
    
    Args:
        table (list): Table data from pdfplumber
        page_num (int): Page number
        table_num (int): Table number on page
        
    Returns:
        str: Formatted table text
    """
    if not table or len(table) < 2:
        return ""
    
    # Create a formatted table string
    table_lines = []
    table_lines.append(f"Table {table_num + 1} from page {page_num + 1}:")
    table_lines.append("=" * 50)
    
    # Add table data with proper formatting
    for row in table:
        if row and any(cell for cell in row if cell):  # Skip empty rows
            # Clean and format row data
            cleaned_row = [str(cell).strip() if cell else "" for cell in row]
            table_lines.append(" | ".join(cleaned_row))
    
    table_lines.append("=" * 50)
    return "\n".join(table_lines)


def extract_text_and_tables_from_pdf(path):
    """Extract both text and tables from PDF file.
    
    Args:
        path (str): Path to PDF file
        
    Returns:
        str: Combined text and tables
    """
    # Extract regular text
    text = extract_text_from_pdf(path)
    
    # Extract tables
    tables = extract_tables_from_pdf(path)
    
    # Combine text and tables
    combined_content = [text]
    if tables:
        combined_content.append("\n\n" + "="*80)
        combined_content.append("FINANCIAL TABLES AND DATA:")
        combined_content.append("="*80)
        combined_content.extend(tables)
    
    return "\n".join(combined_content)


def chunk_text(text, chunk_size=1000, overlap=200):
    """Split text into overlapping chunks.
    
    Args:
        text (str): Text to chunk
        chunk_size (int): Size of each chunk in characters
        overlap (int): Number of characters to overlap between chunks
        
    Returns:
        list[str]: List of text chunks
    """
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end]
        chunks.append(chunk.strip())
        start += chunk_size - overlap
    
    return chunks


def chunk_by_sections(text, chunk_size=1200, overlap=300):
    """Split text into semantic chunks based on financial report sections.
    
    Args:
        text (str): Text to chunk
        chunk_size (int): Target size of each chunk in characters
        overlap (int): Number of characters to overlap between chunks
        
    Returns:
        list[str]: List of semantically meaningful text chunks
    """
    # Define section headers that indicate important financial information
    section_headers = [
        "Financial Results", "Revenue", "Income Statement", "Financial Performance",
        "Key Metrics", "Financial Highlights", "Revenue and Sales", "Financial Summary",
        "Consolidated Statements", "Management Discussion", "Results of Operations",
        "Financial Condition", "Cash Flow", "Balance Sheet", "Profit and Loss",
        "Earnings", "EBIT", "EBITDA", "Net Income", "Gross Revenue", "Total Revenue"
    ]
    
    # Split text into paragraphs
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
            
        # Check if this paragraph contains a section header
        is_section_header = any(header.lower() in paragraph.lower() for header in section_headers)
        
        # If adding this paragraph would exceed chunk size, save current chunk
        if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            # Start new chunk with overlap from previous chunk
            overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
            current_chunk = overlap_text + "\n\n" + paragraph
        else:
            # Add paragraph to current chunk
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph
    
    # Add the last chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    # If chunks are too large, split them further using regular chunking
    final_chunks = []
    for chunk in chunks:
        if len(chunk) > chunk_size * 2:  # If chunk is too large, split it
            sub_chunks = chunk_text(chunk, chunk_size, overlap)
            final_chunks.extend(sub_chunks)
        else:
            final_chunks.append(chunk)
    
    # If no semantic chunks were created, fall back to regular chunking
    if not final_chunks:
        return chunk_text(text, chunk_size, overlap)
    
    return final_chunks
