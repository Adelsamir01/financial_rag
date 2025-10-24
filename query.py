# query.py
import os
import json
import numpy as np
import faiss
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

EMBED_MODEL = "text-embedding-3-large"
LLM_MODEL = "gpt-4o-mini"

INDEX_PATH = "faiss_index.bin"
META_PATH = "meta.json"

PROMPT_TEMPLATE = """
You are a helpful financial analyst assistant. Use only the provided source passages to answer the user's question. 
Cite sources using numbered references like [1], [2], [3] etc. 

IMPORTANT: When answering financial questions, provide comprehensive, detailed answers that include:
- Specific numbers and figures from the passages
- Year-over-year comparisons when available
- Key financial metrics and ratios
- Detailed breakdowns by segment or category
- Tables or structured data when relevant
- All relevant financial data found in the passages

If the answer is not in the passages, say "I don't know based on the provided documents."

Passages:
{passages}

Question: {question}

Provide a comprehensive, detailed answer that extracts all relevant financial information from the passages. Use numbered citations [1], [2], [3] etc. in your answer. Do NOT include a "Sources:" section at the end - just provide the answer with inline citations.
"""


def load_index(index_path=INDEX_PATH):
    """Load FAISS index from file.
    
    Args:
        index_path (str): Path to FAISS index file
        
    Returns:
        faiss.Index: Loaded FAISS index
    """
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"Index file not found: {index_path}")
    return faiss.read_index(index_path)


def load_meta(meta_path=META_PATH):
    """Load metadata from JSON file.
    
    Args:
        meta_path (str): Path to metadata JSON file
        
    Returns:
        dict: Metadata dictionary
    """
    if not os.path.exists(meta_path):
        raise FileNotFoundError(f"Metadata file not found: {meta_path}")
    
    with open(meta_path, "r", encoding="utf-8") as f:
        return json.load(f)


def embed_query(q):
    """Embed a query string using OpenAI.
    
    Args:
        q (str): Query string to embed
        
    Returns:
        np.ndarray: Query embedding
    """
    resp = client.embeddings.create(model=EMBED_MODEL, input=[q])
    return np.array(resp.data[0].embedding, dtype="float32")


def retrieve(query, k=4, target_year=None):
    """Retrieve top-k relevant chunks for a query with optional temporal filtering.
    
    Args:
        query (str): User query
        k (int): Number of chunks to retrieve
        target_year (int): Target year for temporal filtering (optional)
        
    Returns:
        list[dict]: List of retrieved chunk metadata
    """
    index = load_index()
    meta = load_meta()
    
    q_emb = embed_query(query)
    q_emb = q_emb.reshape(1, -1)
    
    # Search for more chunks initially to allow for temporal filtering
    search_k = k * 3 if target_year else k
    D, I = index.search(q_emb, search_k)
    
    results = []
    for idx in I[0]:
        sid = str(int(idx))
        if sid in meta:
            chunk = meta[sid]
            
            # Apply temporal filtering if target year is specified
            if target_year:
                chunk_year = chunk.get('year', 0)
                # Prioritize exact year match, then allow nearby years
                if chunk_year == target_year:
                    results.append(chunk)
                elif abs(chunk_year - target_year) <= 1:  # Allow ±1 year
                    results.append(chunk)
            else:
                results.append(chunk)
            
            # Stop when we have enough results
            if len(results) >= k:
                break
    
    return results[:k]


def extract_year_from_query(query):
    """Extract year from query for temporal filtering.
    
    Args:
        query (str): User query
        
    Returns:
        int: Year extracted from query, or None if not found
    """
    import re
    # Look for 4-digit year in query
    year_match = re.search(r'20\d{2}', query)
    if year_match:
        return int(year_match.group())
    return None


def decompose_question(question):
    """Decompose complex question into simpler sub-questions using GPT-4o.
    
    Args:
        question (str): Original complex question
        
    Returns:
        list[str]: List of decomposed sub-questions
    """
    decomposition_prompt = f"""
You are a financial analyst assistant. Given a complex question about financial data, break it down into 2-4 simple, independent sub-questions that can be answered separately but together help answer the main question.

IMPORTANT RULES:
- Each sub-question should focus on ONE company at a time
- Each sub-question should focus on ONE specific metric
- Keep sub-questions simple and focused
- Avoid asking for multiple companies in one question

Examples of GOOD sub-questions:
- "What was Ford's net profit margin in 2022?"
- "What was Tesla's EBIT margin in 2022?"
- "What was BMW's revenue in 2022?"

Examples of BAD sub-questions:
- "What was the net profit margin for Ford, Tesla, and BMW in 2022?"
- "How did Ford, Tesla, and BMW compare in 2022?"

Original question: {question}

Provide 2-4 simple sub-questions, one per line, that are:
1. Focused on ONE company at a time
2. Focused on ONE specific metric
3. Independent and can be answered separately
4. Helpful for answering the main question

Format each sub-question on a new line starting with "- "
"""
    
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful financial analyst assistant."},
            {"role": "user", "content": decomposition_prompt}
        ],
        max_tokens=300,
        temperature=0.1,
    )
    
    # Parse sub-questions from response
    response_text = resp.choices[0].message.content
    sub_questions = []
    for line in response_text.split('\n'):
        line = line.strip()
        if line.startswith('- '):
            sub_questions.append(line[2:].strip())
    
    return sub_questions


def generate_alternative_questions(original_question):
    """Generate alternative formulations of a question when the first attempt fails.
    
    Args:
        original_question (str): Original question that failed
        
    Returns:
        list[str]: List of alternative question formulations
    """
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
    
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful financial analyst assistant."},
            {"role": "user", "content": alternatives_prompt}
        ],
        max_tokens=200,
        temperature=0.3,
    )
    
    # Parse alternative questions
    response_text = resp.choices[0].message.content
    alternatives = []
    for line in response_text.split('\n'):
        line = line.strip()
        if line.startswith('- '):
            alternatives.append(line[2:].strip())
    
    return alternatives


def answer_sub_question_with_fallback(sub_question, target_year=None):
    """Answer a sub-question with fallback to alternative formulations.
    
    Args:
        sub_question (str): Sub-question to answer
        target_year (int): Target year for temporal filtering
        
    Returns:
        dict: Answer with chunks and sources
    """
    # Try the original question first
    result = answer_sub_question(sub_question, target_year)
    
    # Check if the answer indicates no data found
    if "I don't know" in result['answer'] or "No relevant information found" in result['answer']:
        # Generate alternative questions
        alternatives = generate_alternative_questions(sub_question)
        
        # Try each alternative
        for alt_question in alternatives:
            alt_result = answer_sub_question(alt_question, target_year)
            
            # If we found data, use this result
            if "I don't know" not in alt_result['answer'] and "No relevant information found" not in alt_result['answer']:
                # Update the question to show we used an alternative
                alt_result['question'] = f"{sub_question} (tried alternative: {alt_question})"
                return alt_result
        
        # If all alternatives failed, return the original result
        return result
    
    return result


def answer_sub_question(sub_question, target_year=None):
    """Answer a single sub-question using RAG.
    
    Args:
        sub_question (str): Sub-question to answer
        target_year (int): Target year for temporal filtering
        
    Returns:
        dict: Answer with chunks and sources
    """
    # Retrieve relevant chunks
    hits = retrieve(sub_question, k=4, target_year=target_year)
    
    if not hits:
        return {
            "question": sub_question,
            "answer": "No relevant information found.",
            "chunks": [],
            "sources": []
        }
    
    # Generate answer for this sub-question
    numbered_passages = []
    for i, chunk in enumerate(hits, 1):
        numbered_passages.append(f"[{i}] {chunk['text']}")
    
    passages = "\n\n".join(numbered_passages)
    prompt = PROMPT_TEMPLATE.format(passages=passages, question=sub_question)
    
    resp = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000,
        temperature=0.0,
    )
    
    answer = resp.choices[0].message.content
    
    # Extract cited sources
    import re
    cited_numbers = re.findall(r'\[(\d+)\]', answer)
    cited_numbers = [int(num) for num in cited_numbers]
    
    sources = []
    for num in cited_numbers:
        if 1 <= num <= len(hits):
            chunk = hits[num - 1]
            sources.append(f"[{num}] {chunk['source']}, chunk {chunk['chunk_index']}")
    
    return {
        "question": sub_question,
        "answer": answer,
        "chunks": hits,
        "sources": sources
    }


def synthesize_final_answer(original_question, sub_question_results):
    """Synthesize final answer from sub-question results using GPT-4o.
    
    Args:
        original_question (str): Original complex question
        sub_question_results (list[dict]): Results from sub-questions
        
    Returns:
        str: Final synthesized answer
    """
    # Prepare context from sub-questions
    context_parts = []
    all_sources = []
    
    for i, result in enumerate(sub_question_results, 1):
        context_parts.append(f"Sub-question {i}: {result['question']}")
        context_parts.append(f"Answer: {result['answer']}")
        if result['sources']:
            context_parts.append(f"Sources: {'; '.join(result['sources'])}")
        context_parts.append("")
        
        all_sources.extend(result['sources'])
    
    context = "\n".join(context_parts)
    
    synthesis_prompt = f"""
You are a financial analyst assistant. Based on the sub-question answers below, provide a comprehensive answer to the original question.

Original question: {original_question}

Sub-question analysis:
{context}

Provide a clear, comprehensive answer that:
1. Directly answers the original question
2. Synthesizes information from all sub-questions
3. Includes specific data and metrics where available
4. Creates tables or structured data when relevant
5. Provides year-over-year comparisons
6. Includes detailed breakdowns by segment or category
7. Cites sources appropriately
8. Is well-structured and easy to understand

IMPORTANT: Extract ALL relevant financial data from the sub-question answers. Include specific numbers, percentages, and detailed breakdowns. Create tables when comparing multiple years or metrics.

If the sub-questions don't provide enough information to answer the original question, say so clearly.
"""
    
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful financial analyst assistant."},
            {"role": "user", "content": synthesis_prompt}
        ],
        max_tokens=1500,
        temperature=0.1,
    )
    
    return resp.choices[0].message.content


def generate_answer(question, retrieved_chunks):
    """Generate answer using comprehensive enrichment approach.
    
    Args:
        question (str): User question
        retrieved_chunks (list[dict]): Retrieved chunk metadata (not used in new approach)
        
    Returns:
        str: Generated answer with citations
    """
    # Step 1: Try to answer the main question directly
    print("🔍 Attempting to answer main question directly...")
    target_year = extract_year_from_query(question)
    
    # Try the main question first
    main_result = answer_sub_question_with_fallback(question, target_year)
    print(f"Main question result: {main_result['answer'][:100]}...")
    
    # Step 2: Analyze what information is missing from the main answer
    print("🔍 Analyzing what information is missing from the main answer...")
    
    # Get the chunks we found for the main question
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


def analyze_missing_information(original_question, main_answer, available_chunks):
    """Analyze what information is missing from the main answer.
    
    Args:
        original_question (str): Original question
        main_answer (str): Answer from main question
        available_chunks (list[dict]): Chunks we already retrieved
        
    Returns:
        dict: Analysis with missing_info and follow_up_questions
    """
    # Analyze what data we have and what might be missing
    chunk_summaries = []
    for chunk in available_chunks[:3]:  # Use top 3 chunks for context
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
    
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful financial analyst assistant."},
            {"role": "user", "content": analysis_prompt}
        ],
        max_tokens=300,
        temperature=0.1,
    )
    
    # Parse the analysis response
    response_text = resp.choices[0].message.content
    
    # Extract missing information and follow-up questions
    missing_info = []
    follow_up_questions = []
    
    lines = response_text.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        if line.startswith('MISSING INFORMATION:'):
            current_section = 'missing'
        elif line.startswith('FOLLOW-UP QUESTIONS NEEDED:'):
            current_section = 'questions'
        elif line.startswith('- ') and current_section == 'missing':
            missing_info.append(line[2:].strip())
        elif line.startswith('- ') and current_section == 'questions':
            follow_up_questions.append(line[2:].strip())
    
    return {
        'missing_info': missing_info,
        'follow_up_questions': follow_up_questions
    }


def generate_context_driven_sub_questions(original_question, available_chunks):
    """Generate sub-questions based on the context we already have.
    
    Args:
        original_question (str): Original question that failed
        available_chunks (list[dict]): Chunks we already retrieved
        
    Returns:
        list[str]: List of targeted sub-questions
    """
    # Analyze what data we have
    chunk_summaries = []
    for chunk in available_chunks[:3]:  # Use top 3 chunks for context
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
    
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful financial analyst assistant."},
            {"role": "user", "content": context_prompt}
        ],
        max_tokens=200,
        temperature=0.2,
    )
    
    # Parse sub-questions from response
    response_text = resp.choices[0].message.content
    sub_questions = []
    for line in response_text.split('\n'):
        line = line.strip()
        if line.startswith('- '):
            sub_questions.append(line[2:].strip())
    
    return sub_questions


if __name__ == "__main__":
    print("RAG Query System")
    print("=" * 50)
    
    try:
        # Check if index files exist
        if not os.path.exists(INDEX_PATH) or not os.path.exists(META_PATH):
            print(f"Index files not found. Please run 'python ingest.py' first.")
            exit(1)
        
        while True:
            q = input("\nQuestion (or 'quit' to exit): ").strip()
            
            if q.lower() in ['quit', 'exit', 'q']:
                break
                
            if not q:
                continue
            
            try:
                # Extract year from query for temporal filtering
                target_year = extract_year_from_query(q)
                if target_year:
                    print(f"Detected year {target_year} in query - applying temporal filtering...")
                
                print("Retrieving relevant chunks...")
                retrieved = retrieve(q, k=4, target_year=target_year)
                print(f"Retrieved {len(retrieved)} sources:")
                for r in retrieved:
                    year_info = f" (year: {r.get('year', 'unknown')})" if 'year' in r else ""
                    print(f"  - {r['source']}#{r['chunk_index']}{year_info}")
                
                print("\nGenerating answer...")
                answer = generate_answer(q, retrieved)
                print(f"\nAnswer:\n{answer}")
                
            except Exception as e:
                print(f"Error: {e}")
                
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Error: {e}")
