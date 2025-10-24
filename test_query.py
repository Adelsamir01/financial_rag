# test_query.py
"""
Simple test script to verify the RAG system is working correctly.
"""
import os
from query import retrieve, generate_answer


def test_rag_system():
    """Test the RAG system with sample queries."""
    print("🧪 Testing RAG System")
    print("=" * 50)
    
    # Check if index files exist
    if not os.path.exists("faiss_index.bin") or not os.path.exists("meta.json"):
        print("❌ Index files not found. Please run 'python ingest.py' first.")
        return False
    
    # Test queries
    test_queries = [
        "What was the company's revenue in 2023?",
        "What are the main financial highlights?",
        "What is the company's profit margin?",
        "What are the key risks mentioned?",
        "What is the company's market position?"
    ]
    
    print(f"Running {len(test_queries)} test queries...\n")
    
    success_count = 0
    
    for i, query in enumerate(test_queries, 1):
        print(f"Test {i}: {query}")
        print("-" * 40)
        
        try:
            # Retrieve relevant chunks
            print("  🔍 Retrieving chunks...")
            hits = retrieve(query, k=3)
            
            if not hits:
                print("  ⚠️  No relevant chunks found")
                continue
            
            print(f"  📄 Found {len(hits)} relevant chunks:")
            for j, h in enumerate(hits, 1):
                print(f"    {j}. {h['source']}#{h['chunk_index']}")
            
            # Generate answer
            print("  🤖 Generating answer...")
            answer = generate_answer(query, hits)
            
            print(f"  💡 Answer: {answer[:200]}{'...' if len(answer) > 200 else ''}")
            print()
            
            success_count += 1
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            print()
    
    # Summary
    print("=" * 50)
    print(f"✅ Tests completed: {success_count}/{len(test_queries)} successful")
    
    if success_count == len(test_queries):
        print("🎉 All tests passed! The RAG system is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the error messages above.")
        return False


def test_specific_query():
    """Test with a specific query and show detailed results."""
    print("\n🔬 Detailed Test")
    print("=" * 50)
    
    query = "What was the company's revenue in 2023?"
    print(f"Query: {query}")
    
    try:
        # Retrieve chunks
        hits = retrieve(query, k=4)
        print(f"\nRetrieved {len(hits)} chunks:")
        
        for i, h in enumerate(hits, 1):
            print(f"\nChunk {i}: {h['source']}#{h['chunk_index']}")
            print(f"Text preview: {h['text'][:300]}...")
        
        # Generate answer
        print(f"\nGenerating answer...")
        answer = generate_answer(query, hits)
        print(f"\nAnswer:\n{answer}")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # Run basic tests
    success = test_rag_system()
    
    if success:
        # Run detailed test
        test_specific_query()
    
    print("\n🏁 Testing complete!")
