# RAG System Implementation Journey & Thought Process

## Overview

This document chronicles the complete thought process and implementation journey of building a sophisticated RAG (Retrieval-Augmented Generation) system for financial annual reports. The journey demonstrates the iterative nature of building production-quality RAG systems, where each phase addressed specific challenges and built upon previous solutions.

## Phase 1: Initial RAG System Setup

### Goal
Build a basic RAG system for financial annual reports

### Implementation
- **PDF Text Extraction**: Used `pdfplumber` for reliable text extraction from financial reports
- **Text Chunking**: Implemented sliding window chunking (1200 chars, 300 overlap) to handle long documents
- **Embeddings**: Used OpenAI's `text-embedding-3-large` for high-quality vector representations
- **Vector Storage**: Chose FAISS (IndexFlatL2) for local, dependency-free vector storage
- **Query Processing**: Basic retrieval + OpenAI completion with citation formatting

### Key Design Decisions
- Local FAISS over cloud solutions for simplicity and cost control
- Fixed-size chunking over semantic chunking initially for reliability
- OpenAI embeddings for quality over open-source alternatives

### Files Created
- `utils.py`: PDF extraction and chunking utilities
- `ingest.py`: Embedding and indexing pipeline
- `query.py`: Basic retrieval and generation
- `streamlit_app.py`: Simple web UI
- `requirements.txt`: Dependencies

## Phase 2: UI/UX Improvements

### Issues Encountered
1. **Answer Formatting**: LLM was generating markdown with bold text causing display issues
2. **Citation Format**: Inconsistent citation format `[source: filename.pdf, chunk 3]`
3. **Source Accuracy**: LLM generating incorrect source filenames
4. **Answer Display**: Scrollable text areas with poor readability

### Solutions Implemented
- **Prompt Engineering**: Modified `PROMPT_TEMPLATE` to request plain text without markdown formatting
- **Citation Standardization**: Changed to numbered citations `[1], [2], [3]` with proper source mapping
- **UI Improvements**: Used `st.text_area()` with dynamic height for better answer display
- **Source Filtering**: Only show sources actually cited in the answer

### Code Changes
```python
# Updated PROMPT_TEMPLATE in query.py
PROMPT_TEMPLATE = """
You are a helpful financial analyst assistant. Use only the provided source passages to answer the user's question. 
Cite sources using numbered references like [1], [2], [3] etc. 
If the answer is not in the passages, say "I don't know based on the provided documents."

Passages:
{passages}

Question: {question}

Provide a clear, concise answer in plain text format. Do not use markdown formatting, bold text, or special formatting. Use numbered citations [1], [2], [3] etc. in your answer. Do NOT include a "Sources:" section at the end - just provide the answer with inline citations.
"""
```

## Phase 3: Data Extraction Challenges

### Issues Encountered
1. **Table Extraction**: Financial data in tables wasn't being captured
2. **Token Limits**: OpenAI API limits when processing large documents
3. **Data Gaps**: Missing specific financial metrics (e.g., Ford 2020 revenue)

### Solutions Implemented
- **Table Extraction**: Added `extract_tables_from_pdf()` using `pdfplumber` to capture financial tables
- **Batch Processing**: Implemented batch processing for embeddings to handle token limits
- **Combined Extraction**: Created `extract_text_and_tables_from_pdf()` to capture both text and tables

### Code Changes
```python
# Added to utils.py
def extract_tables_from_pdf(path):
    tables = []
    with pdfplumber.open(path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            page_tables = page.extract_tables()
            for table_num, table in enumerate(page_tables):
                if table and len(table) > 1:
                    table_str = format_table_as_text(table, page_num, table_num)
                    if table_str:
                        tables.append(table_str)
    return tables

def extract_text_and_tables_from_pdf(path):
    text = extract_text_from_pdf(path)
    tables = extract_tables_from_pdf(path)
    combined_content = [text]
    if tables:
        combined_content.append("\n\n" + "="*80)
        combined_content.append("FINANCIAL TABLES AND DATA:")
        combined_content.append("="*80)
        combined_content.extend(tables)
    return "\n".join(combined_content)
```

## Phase 4: Temporal Awareness

### Critical Issue
RAG system was citing 2023 reports for 2021 questions

### Root Cause
No temporal filtering in retrieval - system retrieved most relevant chunks regardless of year

### Solution Implemented
- **Temporal Metadata**: Added year extraction from filenames during ingestion
- **Temporal Filtering**: Modified `retrieve()` function to prioritize chunks from target year
- **Year Extraction**: Added `extract_year_from_query()` to parse years from user questions
- **Fallback Logic**: If exact year not found, search within ±1 year range

### Code Changes
```python
# Added to ingest.py
def extract_year_from_filename(filename):
    import re
    year_match = re.search(r'20\d{2}', filename)
    if year_match:
        return int(year_match.group())
    return 0

# Updated metadata to include year
meta = {
    "id": str(id_counter), 
    "source": fname, 
    "chunk_index": i, 
    "text": c[:4000],
    "year": year,  # Add temporal metadata
    "report_year": year  # For filtering
}

# Updated retrieve() function in query.py
def retrieve(query, k=4, target_year=None):
    index = load_index()
    meta = load_meta()
    
    q_emb = embed_query(query)
    q_emb = q_emb.reshape(1, -1)
    
    search_k = k * 3 if target_year else k
    D, I = index.search(q_emb, search_k)
    
    results = []
    for idx in I[0]:
        sid = str(int(idx))
        if sid in meta:
            chunk = meta[sid]
            
            if target_year:
                chunk_year = chunk.get('year', 0)
                if chunk_year == target_year:
                    results.append(chunk)
                elif abs(chunk_year - target_year) <= 1:
                    results.append(chunk)
            else:
                results.append(chunk)
            
            if len(results) >= k:
                break
    
    return results[:k]
```

## Phase 5: Complex Question Handling

### Challenge
Simple RAG couldn't handle complex comparative questions like "Which company had better profitability?"

### Solution - Multi-Step RAG Approach
1. **Question Decomposition**: Use GPT-4o to break complex questions into simple sub-questions
2. **Independent Sub-Question Answering**: Answer each sub-question separately using RAG
3. **Synthesis**: Use GPT-4o to combine sub-question results into comprehensive final answer

### Implementation
- `decompose_question()`: Breaks down complex questions into focused sub-questions
- `answer_sub_question()`: Answers individual sub-questions with RAG
- `synthesize_final_answer()`: Combines results into comprehensive answer

### Code Changes
```python
# Added to query.py
def decompose_question(question):
    decomposition_prompt = f"""
You are a financial analyst assistant. Given a complex question about financial data, break it down into 2-4 simple, independent sub-questions that can be answered separately but together help answer the main question.

IMPORTANT RULES:
- Each sub-question should focus on ONE company at a time
- Each sub-question should focus on ONE specific metric
- Keep sub-questions simple and focused
- Avoid asking for multiple companies in one question

Original question: {question}

Provide 2-4 simple sub-questions, one per line, that are:
1. Focused on ONE company at a time
2. Focused on ONE specific metric
3. Independent and can be answered separately
4. Helpful for answering the main question

Format each sub-question on a new line starting with "- "
"""
    # ... implementation details
```

## Phase 6: Fallback Mechanisms

### Issue
Some queries failed to find relevant data (e.g., Ford 2020 revenue)

### Solution - Alternative Question Generation
- `generate_alternative_questions()`: Creates alternative formulations when initial query fails
- `answer_sub_question_with_fallback()`: Tries original question, then alternatives
- Different terminology, focus areas, and time references to improve retrieval

### Code Changes
```python
# Added to query.py
def generate_alternative_questions(original_question):
    alternatives_prompt = f"""
You are a financial analyst assistant. The original question failed to find relevant data. Generate 3 alternative ways to ask the same question that might find the information in financial reports.

Original question: {original_question}

Generate alternative questions that:
1. Use different terminology (e.g., "revenue" vs "sales" vs "income")
2. Focus on different aspects (e.g., segment revenue vs total revenue)
3. Use different time references (e.g., "2020" vs "full year 2020")
4. Ask for specific metrics (e.g., "total revenue" vs "consolidated revenue")

Provide 3 alternative questions, one per line, starting with "- ":
"""
    # ... implementation details

def answer_sub_question_with_fallback(sub_question, target_year=None):
    result = answer_sub_question(sub_question, target_year)
    if "I don't know" in result['answer'] or "No relevant information found" in result['answer']:
        alternatives = generate_alternative_questions(sub_question)
        for alt_question in alternatives:
            alt_result = answer_sub_question(alt_question, target_year)
            if "I don't know" not in alt_result['answer'] and "No relevant information found" not in alt_result['answer']:
                alt_result['question'] = f"{sub_question} (tried alternative: {alt_question})"
                return alt_result
        return result
    return result
```

## Phase 7: Context-Driven Approach

### Evolution
Moved from generic sub-questions to context-driven approach

### Implementation
- `generate_context_driven_sub_questions()`: Creates sub-questions based on initially retrieved context
- More targeted and relevant sub-questions
- Better success rate for complex queries

### Code Changes
```python
# Added to query.py
def generate_context_driven_sub_questions(original_question, available_chunks):
    chunk_summaries = []
    for chunk in available_chunks[:3]:
        chunk_summaries.append(chunk['text'][:300])
    
    context = "\n".join(chunk_summaries)
    
    context_prompt = f"""
You are a financial analyst assistant. The main question failed to find sufficient data, but we have some context. Generate 2-3 targeted sub-questions that would help answer the original question based on the available context.

Original question: {original_question}

Available context:
{context}

Generate 2-3 specific sub-questions that:
1. Focus on specific aspects mentioned in the context
2. Ask for specific metrics or data points
3. Target the most relevant information for answering the original question

Provide 2-3 sub-questions, one per line, starting with "- ":
"""
    # ... implementation details
```

## Phase 8: Comprehensive Answer Enhancement

### Final Challenge
Answers were too basic and missing comprehensive financial analysis

### Solution - Missing Information Analysis
1. **Analyze Main Answer**: Identify what information is missing from the initial answer
2. **Generate Targeted Follow-ups**: Create specific questions to collect missing information
3. **Always Enrich**: Don't wait for failure - always enhance answers with additional context

### Key Functions
- `analyze_missing_information()`: Identifies gaps in main answer
- `generate_enrichment_sub_questions()`: Creates targeted follow-up questions
- Enhanced synthesis with comprehensive financial analysis

### Code Changes
```python
# Added to query.py
def analyze_missing_information(original_question, main_answer, available_chunks):
    chunk_summaries = []
    for chunk in available_chunks[:3]:
        chunk_summaries.append(chunk['text'][:300])
    
    context = "\n".join(chunk_summaries)
    
    analysis_prompt = f"""
You are a financial analyst assistant. I have provided an initial answer to the user's question, but I need to analyze what information is missing and what additional data would make the answer more comprehensive.

Original question: {original_question}

Main answer provided: {main_answer}

Available context from retrieved documents:
{context}

Please analyze and provide:

1. What specific information is MISSING from the main answer that would be valuable to include?
2. What additional data points, metrics, or details would strengthen the answer?
3. What follow-up questions should be asked to collect this missing information?

Focus on identifying gaps in:
- Specific financial numbers or metrics
- Year-over-year comparisons
- Segment breakdowns
- Key factors or explanations
- Detailed analysis or context

Provide your analysis in this format:
MISSING INFORMATION:
- [List specific missing information]

FOLLOW-UP QUESTIONS NEEDED:
- [Question 1 to collect missing info]
- [Question 2 to collect missing info]
- [Question 3 to collect missing info]
"""
    # ... implementation details

def generate_answer(question, retrieved_chunks):
    # Step 1: Try to answer the main question directly
    print("🔍 Attempting to answer main question directly...")
    target_year = extract_year_from_query(question)
    
    main_result = answer_sub_question_with_fallback(question, target_year)
    print(f"Main question result: {main_result['answer'][:100]}...")
    
    # Step 2: Analyze what information is missing from the main answer
    print("🔍 Analyzing what information is missing from the main answer...")
    
    main_chunks = main_result.get('chunks', [])
    
    # Analyze missing information and generate follow-up questions
    analysis = analyze_missing_information(question, main_result['answer'], main_chunks)
    missing_info = analysis['missing_info']
    follow_up_questions = analysis['follow_up_questions']
    
    print(f"Missing information identified: {missing_info}")
    print(f"Generated {len(follow_up_questions)} follow-up questions: {follow_up_questions}")
    
    # Step 3: Answer each follow-up question to collect missing information
    follow_up_results = []
    for i, follow_up_q in enumerate(follow_up_questions, 1):
        print(f"📊 Answering follow-up question {i}: {follow_up_q}")
        result = answer_sub_question_with_fallback(follow_up_q, target_year)
        follow_up_results.append(result)
        print(f"   Result: {result['answer'][:100]}...")
    
    # Step 4: Synthesize comprehensive final answer from main question + follow-up information
    print("🎯 Synthesizing comprehensive final answer from main question and follow-up information...")
    all_results = [main_result] + follow_up_results
    final_answer = synthesize_final_answer(question, all_results)
    
    return final_answer
```

## Technical Architecture Evolution

### Initial: Simple RAG
```
PDF → Text → Chunks → Embeddings → FAISS
Query → Embeddings → Retrieve → LLM → Answer
```

### Final: Multi-Step RAG with Missing Information Analysis
```
PDF → Text + Tables → Chunks → Embeddings → FAISS (with temporal metadata)
Query → Main Answer
├── Analyze Missing Information
├── Generate Follow-up Questions
├── Answer Follow-up Questions
└── Synthesize Comprehensive Final Answer
```

## Key Lessons Learned

### 1. Prompt Engineering is Critical
Small changes in prompts can dramatically improve output quality. The evolution from basic prompts to sophisticated, context-aware prompts was crucial for success.

### 2. Temporal Awareness Matters
Financial data is time-sensitive. Implementing temporal filtering was essential to prevent the system from citing irrelevant years.

### 3. Multi-Step Processing
Complex questions need decomposition and synthesis. The multi-step RAG approach significantly improved the system's ability to handle complex financial queries.

### 4. Missing Information Analysis
Always analyze what's missing rather than generic enrichment. This approach ensures comprehensive answers by identifying and filling specific gaps.

### 5. Fallback Mechanisms
Alternative question generation improves success rates. When initial queries fail, alternative formulations often succeed.

### 6. UI/UX Iteration
Continuous refinement based on user feedback is crucial. The ChatGPT-like interface with real-time progress display significantly improved user experience.

## Performance Improvements

- **Token Efficiency**: Batch processing reduced API costs
- **Retrieval Quality**: Temporal filtering improved relevance
- **Answer Comprehensiveness**: Missing information analysis ensures complete answers
- **Success Rate**: Fallback mechanisms increased query success rate
- **User Experience**: ChatGPT-like interface with real-time progress display

## Final System Capabilities

The final RAG system can:

1. **Extract Comprehensive Financial Data**: From both text and tables in PDF reports
2. **Handle Temporal Queries**: Correctly filter and prioritize data by year
3. **Answer Complex Questions**: Decompose complex comparative questions into manageable sub-questions
4. **Provide Detailed Analysis**: Generate comprehensive financial analysis with specific metrics, comparisons, and context
5. **Ensure Data Completeness**: Identify and fill gaps in information through targeted follow-up questions
6. **Offer Professional Quality**: Deliver answers that match the quality of expert financial analysis

## Conclusion

This implementation journey demonstrates the iterative nature of building production-quality RAG systems. Each phase addressed specific challenges and built upon previous solutions, resulting in a sophisticated system capable of providing comprehensive financial analysis from annual reports.

The key to success was continuous iteration, user feedback incorporation, and addressing each challenge systematically rather than trying to solve everything at once.
