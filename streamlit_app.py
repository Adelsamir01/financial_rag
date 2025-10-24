# streamlit_app.py
import streamlit as st
import os
from query import retrieve, generate_answer
import time

# Page configuration
st.set_page_config(
    page_title="Financial Reports AI", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for ChatGPT-like interface
st.markdown("""
<style>
    .main {
        padding-top: 1rem;
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: flex-start;
    }
    
    .user-message {
        background-color: #f0f0f0;
        margin-left: 20%;
        flex-direction: row-reverse;
    }
    
    .assistant-message {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        margin-right: 20%;
    }
    
    .message-content {
        flex: 1;
        margin: 0 0.5rem;
    }
    
    .avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 14px;
    }
    
    .user-avatar {
        background-color: #007bff;
        color: white;
    }
    
    .assistant-avatar {
        background-color: #10a37f;
        color: white;
    }
    
    .thinking-process {
        background-color: #f8f9fa;
        border-left: 3px solid #10a37f;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.25rem;
    }
    
    .stTextInput > div > div > input {
        border-radius: 25px;
        padding: 0.5rem 1rem;
    }
    
    .stButton > button {
        border-radius: 25px;
        background-color: #10a37f;
        color: white;
        border: none;
    }
    
    .stButton > button:hover {
        background-color: #0d8a6b;
    }
</style>
""", unsafe_allow_html=True)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Check if index files exist
if not os.path.exists("faiss_index.bin") or not os.path.exists("meta.json"):
    st.error("❌ Index files not found. Please run 'python ingest.py' first to create the index.")
    st.markdown("### Steps to get started:")
    st.markdown("1. Add PDF files to the `data/` directory")
    st.markdown("2. Set your OpenAI API key in `.env` file")
    st.markdown("3. Run `python ingest.py` to create the index")
    st.stop()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about your financial reports..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant message
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Import the context-driven functions
                from query import generate_answer
                
                # Show thinking process
                thinking_container = st.container()
                with thinking_container:
                    st.markdown("**🔍 Analyzing your question...**")
                    
                    # Step 1: Try to answer main question directly
                    st.markdown("**Step 1: Attempting to answer your question directly...**")
                    
                    # Extract year for temporal filtering
                    from query import extract_year_from_query
                    target_year = extract_year_from_query(prompt)
                    if target_year:
                        st.markdown(f"**Applying temporal filtering for year {target_year}...**")
                    
                    # Try main question first
                    from query import answer_sub_question_with_fallback
                    main_result = answer_sub_question_with_fallback(prompt, target_year)
                    
                    st.markdown("✅ **Found main answer!**")
                    st.markdown(f"*Main answer preview: {main_result['answer'][:200]}...*")
                    
                    # Step 2: Analyze what information is missing from the main answer
                    st.markdown("**Step 2: Analyzing what information is missing from the main answer...**")
                    
                    # Get chunks from main question attempt
                    main_chunks = main_result.get('chunks', [])
                    
                    # Analyze missing information and generate follow-up questions
                    from query import analyze_missing_information
                    analysis = analyze_missing_information(prompt, main_result['answer'], main_chunks)
                    missing_info = analysis['missing_info']
                    follow_up_questions = analysis['follow_up_questions']
                    
                    if missing_info:
                        st.markdown("**Missing information identified:**")
                        for info in missing_info:
                            st.markdown(f"• {info}")
                    
                    if follow_up_questions:
                        st.markdown(f"**Generated {len(follow_up_questions)} follow-up questions to collect missing information:**")
                        for i, fq in enumerate(follow_up_questions, 1):
                            st.markdown(f"• {fq}")
                        
                        # Step 3: Answer follow-up questions to collect missing information
                        st.markdown("**Step 3: Processing follow-up questions to collect missing information...**")
                        follow_up_results = []
                        progress_bar = st.progress(0)
                        
                        for i, follow_up_q in enumerate(follow_up_questions, 1):
                            with st.expander(f"Follow-up question {i}: {follow_up_q}", expanded=False):
                                result = answer_sub_question_with_fallback(follow_up_q, target_year)
                                follow_up_results.append(result)
                                
                                if "I don't know" in result['answer']:
                                    st.markdown("❌ No additional data found")
                                else:
                                    st.markdown("✅ Found missing information")
                                    if "(tried alternative:" in result['question']:
                                        st.markdown(f"*Used alternative formulation*")
                                    # Show only a preview, not the full answer
                                    preview = result['answer'][:150] + "..." if len(result['answer']) > 150 else result['answer']
                                    st.markdown(f"*Preview: {preview}*")
                            
                            progress_bar.progress(i / len(follow_up_questions))
                        
                        # Step 4: Synthesize comprehensive final answer
                        st.markdown("**Step 4: Synthesizing comprehensive final answer...**")
                        
                        # Combine main result with follow-up results
                        all_results = [main_result] + follow_up_results
                        from query import synthesize_final_answer
                        final_answer = synthesize_final_answer(prompt, all_results)
                    else:
                        st.markdown("**No missing information identified - using main answer as final answer.**")
                        final_answer = main_result['answer']
                
                # Clear thinking process
                thinking_container.empty()
                
                # Display the final answer with proper formatting
                st.markdown(final_answer)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": final_answer})
                
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {e}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Show welcome message if no messages yet
if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown("👋 **Welcome to Financial Reports AI!**")
        st.markdown("I can help you analyze your financial reports. Ask me questions like:")
        st.markdown("• Which company had better profitability in 2022?")
        st.markdown("• What were Ford's key challenges in 2021?")
        st.markdown("• How did Tesla's revenue compare to BMW?")
        st.markdown("• What was the revenue growth for each company?")
        st.markdown("\n*I'll break down complex questions and provide comprehensive answers with sources.*")
